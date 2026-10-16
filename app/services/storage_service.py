"""
Storage & Image Validation Service for Decore AI
================================================
Handles safe saving of uploaded product and room images, MIME type checking,
size validation, path traversal prevention, and cleanup.
"""

import os
import uuid
import re
from pathlib import Path
from typing import Set, Tuple, Optional, Union
from fastapi import UploadFile, HTTPException, status
from PIL import Image

from app.config import settings

# Allowed image MIME types and extensions
ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp"
}

ALLOWED_EXTENSIONS: Set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename and replaces dangerous characters."""
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    return clean.strip("_")

async def validate_image_file(file: UploadFile) -> Tuple[str, bytes]:
    """
    Validates uploaded file MIME type, extension, size, and verifies Pillow can parse it.
    Returns the file extension and raw bytes.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{file.content_type}'. Must be an image (JPEG, PNG, WEBP)."
        )

    # Read content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Verify actual image content using Pillow
    try:
        import io
        img = Image.open(io.BytesIO(content))
        img.verify()  # Verify image integrity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid image file: {str(e)}"
        )

    return ext, content

async def save_seller_product_image(
    file: UploadFile,
    seller_id: str,
    product_id: str
) -> str:
    """
    Saves a product image under uploads/sellers/{seller_id}/products/{product_id}/
    Returns relative path from project root (e.g. 'uploads/sellers/SELLER001/products/BED001/product.jpg').
    """
    ext, content = await validate_image_file(file)

    # Clean IDs to prevent path traversal
    safe_seller_id = re.sub(r"[^a-zA-Z0-9_-]", "_", seller_id)
    safe_product_id = re.sub(r"[^a-zA-Z0-9_-]", "_", product_id)

    target_dir = settings.UPLOAD_DIR / "sellers" / safe_seller_id / "products" / safe_product_id
    target_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"product_{uuid.uuid4().hex[:8]}{ext}"
    target_path = target_dir / file_name

    with open(target_path, "wb") as f:
        f.write(content)

    # Return relative path with forward slashes for cross-platform URL consistency
    rel_path = target_path.relative_to(settings.BASE_DIR).as_posix()
    return rel_path

async def save_customer_room_image(
    file: UploadFile,
    user_id: str = "guest",
    room_id: Optional[str] = None
) -> Tuple[str, str]:
    """
    Saves a customer uploaded room image under uploads/rooms/{user_id}/{room_id}/
    Returns (room_id, rel_path) where rel_path is relative to project root.
    """
    ext, content = await validate_image_file(file)

    if not room_id:
        room_id = f"ROOM_{uuid.uuid4().hex[:8].upper()}"

    # Clean IDs to prevent path traversal
    safe_user_id = re.sub(r"[^a-zA-Z0-9_-]", "_", user_id)
    safe_room_id = re.sub(r"[^a-zA-Z0-9_-]", "_", room_id)

    target_dir = settings.UPLOAD_DIR / "rooms" / safe_user_id / safe_room_id
    target_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"room_{uuid.uuid4().hex[:8]}{ext}"
    target_path = target_dir / file_name

    with open(target_path, "wb") as f:
        f.write(content)

    rel_path = target_path.relative_to(settings.BASE_DIR).as_posix()
    return room_id, rel_path

def delete_file_safely(relative_path: str):
    """Deletes a file if it exists inside the project's upload directory."""
    try:
        if not relative_path:
            return
        full_path = settings.BASE_DIR / relative_path
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
    except Exception:
        pass
