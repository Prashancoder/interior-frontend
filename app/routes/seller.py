"""
Seller Dashboard & Product Management API Routes for Decore AI
==============================================================
Provides CRUD endpoints for authenticated sellers to manage their products,
upload images, view statistics, and manage inventory with automatic OpenCLIP
embedding generation and Qdrant vector synchronization (Phase 2).
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Query

from app.config import settings
from app.database.mongodb import get_products_collection
from app.models.product import (
    ProductResponse,
    ProductUpdate,
    SellerStatsResponse
)
from app.services.auth_service import get_current_seller
from app.services.storage_service import (
    save_seller_product_image,
    delete_file_safely,
    validate_image_file
)
from app.services.clip_service import clip_service
from app.services.qdrant_service import qdrant_service

router = APIRouter(prefix="/api/seller", tags=["Seller Management"])

def _parse_styles(style_input: str) -> List[str]:
    """Helper to parse comma-separated or list-like style string into a clean list."""
    if not style_input:
        return []
    cleaned = style_input.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
    return [s.strip().lower() for s in cleaned.split(",") if s.strip()]

@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create & Upload Seller Product",
    description="Uploads product image, validates metadata, stores product in MongoDB, generates 512-d OpenCLIP image embedding, and indexes vector + payload into Qdrant."
)
async def create_product(
    file: UploadFile = File(..., description="Product image file (JPG, PNG, WEBP)"),
    name: str = Form(..., min_length=2, max_length=200, description="Product display name"),
    category: str = Form(..., description="Category (bed, sofa, curtain, wallpaper, lighting, decor, etc.)"),
    subcategory: Optional[str] = Form(None, description="Optional subcategory"),
    description: Optional[str] = Form("", description="Product description"),
    price: float = Form(..., gt=0, description="Product price in INR"),
    currency: str = Form("INR", description="Currency code"),
    color: str = Form(..., description="Primary color (e.g. walnut brown, brass, beige)"),
    material: str = Form(..., description="Material (e.g. solid wood, velvet, steel)"),
    style: str = Form(..., description="Comma-separated styles (e.g. 'luxury, modern')"),
    dimensions: Optional[str] = Form(None, description="Dimensions (e.g. '200x180x100 cm')"),
    stock: int = Form(1, ge=0, description="Available stock quantity"),
    is_active: bool = Form(True, description="Active status in catalog"),
    current_seller: dict = Depends(get_current_seller)
):
    """
    POST /api/seller/products
    Creates a product for the authenticated seller with automatic Qdrant vector indexing.
    """
    seller_id = current_seller["user_id"]
    clean_cat = category.strip().lower()
    cat_code = clean_cat[:4].upper()
    product_id = f"{cat_code}_{uuid.uuid4().hex[:6].upper()}"

    # Step 1: Validate and safely save image to uploads directory
    try:
        saved_image_path = await save_seller_product_image(
            file=file,
            seller_id=seller_id,
            product_id=product_id
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and store product image: {str(e)}"
        )

    # Step 2: Assemble MongoDB document
    now_iso = datetime.now(timezone.utc).isoformat()
    parsed_styles = _parse_styles(style)

    product_doc = {
        "product_id": product_id,
        "seller_id": seller_id,
        "name": name.strip(),
        "category": clean_cat,
        "subcategory": subcategory.strip() if subcategory else None,
        "description": description.strip() if description else "",
        "price": float(price),
        "currency": currency.strip().upper(),
        "color": color.strip().lower(),
        "material": material.strip().lower(),
        "style": parsed_styles,
        "dimensions": dimensions.strip() if dimensions else None,
        "stock": int(stock),
        "image_path": saved_image_path,
        "is_active": bool(is_active),
        "created_at": now_iso,
        "updated_at": now_iso
    }

    # Step 3: Insert into MongoDB (Source of Truth)
    products_col = get_products_collection()
    try:
        await products_col.insert_one(product_doc)
    except Exception as e:
        # Clean up uploaded image if database insert fails
        delete_file_safely(saved_image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while saving product: {str(e)}"
        )

    # Step 4: Generate OpenCLIP Embedding & Synchronize with Qdrant Vector DB
    try:
        # Generate 512-dim embedding vector from saved image file
        vector = clip_service.encode_image(saved_image_path)

        # Upsert vector + payload into Qdrant collection
        qdrant_service.upsert_product_vector(
            product_data=product_doc,
            vector=vector
        )
    except Exception as qerr:
        print(f"[ERROR] Qdrant automatic indexing failed for product '{product_id}': {str(qerr)}")

    return ProductResponse(**product_doc)

@router.get(
    "/products",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Seller Products",
    description="Retrieves catalog products owned by the authenticated seller with optional filters."
)
async def get_seller_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    in_stock: Optional[bool] = Query(None, description="Filter in-stock only"),
    search: Optional[str] = Query(None, description="Search term for product name"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_seller: dict = Depends(get_current_seller)
):
    """
    GET /api/seller/products
    Lists current seller's products from MongoDB.
    """
    seller_id = current_seller["user_id"]
    products_col = get_products_collection()

    filter_query: dict = {"seller_id": seller_id}

    if category:
        filter_query["category"] = category.strip().lower()
    if is_active is not None:
        filter_query["is_active"] = is_active
    if in_stock is True:
        filter_query["stock"] = {"$gt": 0}
    elif in_stock is False:
        filter_query["stock"] = {"$lte": 0}
    if search:
        filter_query["name"] = {"$regex": search.strip(), "$options": "i"}

    cursor = products_col.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)

    return [ProductResponse(**item) for item in items]

@router.get(
    "/stats",
    response_model=SellerStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Seller Dashboard Stats",
    description="Returns aggregate stats (total products, active, out of stock, recent additions) for seller dashboard."
)
async def get_seller_stats(current_seller: dict = Depends(get_current_seller)):
    """
    GET /api/seller/stats
    Aggregates dashboard statistics for the seller from MongoDB.
    """
    seller_id = current_seller["user_id"]
    products_col = get_products_collection()

    total = await products_col.count_documents({"seller_id": seller_id})
    active = await products_col.count_documents({"seller_id": seller_id, "is_active": True})
    out_of_stock = await products_col.count_documents({"seller_id": seller_id, "stock": {"$lte": 0}})

    cursor = products_col.find({"seller_id": seller_id}).sort("created_at", -1).limit(5)
    recent_docs = await cursor.to_list(length=5)
    recent_products = [ProductResponse(**doc) for doc in recent_docs]

    return SellerStatsResponse(
        total_products=total,
        active_products=active,
        out_of_stock_products=out_of_stock,
        recent_products=recent_products
    )

@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Product by ID",
    description="Retrieves full details of a specific product owned by the authenticated seller."
)
async def get_seller_product_by_id(
    product_id: str,
    current_seller: dict = Depends(get_current_seller)
):
    """
    GET /api/seller/products/{product_id}
    """
    seller_id = current_seller["user_id"]
    products_col = get_products_collection()

    product_doc = await products_col.find_one({"product_id": product_id})
    if not product_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' was not found."
        )

    if product_doc.get("seller_id") != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view or edit this product."
        )

    return ProductResponse(**product_doc)

@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Seller Product",
    description="Updates product metadata and optionally replaces product image with synchronized Qdrant updates."
)
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    subcategory: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    currency: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    style: Optional[str] = Form(None),
    dimensions: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_seller: dict = Depends(get_current_seller)
):
    """
    PUT /api/seller/products/{product_id}
    Updates product information and/or image. Synchronizes changes with Qdrant:
    - Metadata-only change: updates Qdrant payload without re-encoding vector.
    - Image replacement: re-generates OpenCLIP embedding and upserts new vector.
    """
    seller_id = current_seller["user_id"]
    products_col = get_products_collection()

    existing_doc = await products_col.find_one({"product_id": product_id})
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' was not found."
        )

    if existing_doc.get("seller_id") != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only modify your own products."
        )

    updates: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if name is not None:
        updates["name"] = name.strip()
    if category is not None:
        updates["category"] = category.strip().lower()
    if subcategory is not None:
        updates["subcategory"] = subcategory.strip()
    if description is not None:
        updates["description"] = description.strip()
    if price is not None:
        if price <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be greater than 0.")
        updates["price"] = float(price)
    if currency is not None:
        updates["currency"] = currency.strip().upper()
    if color is not None:
        updates["color"] = color.strip().lower()
    if material is not None:
        updates["material"] = material.strip().lower()
    if style is not None:
        updates["style"] = _parse_styles(style)
    if dimensions is not None:
        updates["dimensions"] = dimensions.strip()
    if stock is not None:
        if stock < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock cannot be negative.")
        updates["stock"] = int(stock)
    if is_active is not None:
        updates["is_active"] = bool(is_active)

    # Handle image replacement if provided
    old_image_path = existing_doc.get("image_path")
    new_image_uploaded = file is not None and bool(file.filename)

    if new_image_uploaded:
        new_image_path = await save_seller_product_image(
            file=file,
            seller_id=seller_id,
            product_id=product_id
        )
        updates["image_path"] = new_image_path
        # Clean up old image if different
        if old_image_path and old_image_path != new_image_path:
            delete_file_safely(old_image_path)

    # Update MongoDB
    await products_col.update_one({"product_id": product_id}, {"$set": updates})
    updated_doc = await products_col.find_one({"product_id": product_id})

    # Synchronize Qdrant Vector Index
    try:
        if new_image_uploaded:
            # Re-generate OpenCLIP embedding with new image and upsert vector + updated payload
            new_vector = clip_service.encode_image(updated_doc["image_path"])
            qdrant_service.upsert_product_vector(
                product_data=updated_doc,
                vector=new_vector
            )
        else:
            # Metadata only: update Qdrant payload without re-encoding
            qdrant_service.update_product_payload(
                product_id=product_id,
                payload_updates=updates
            )
    except Exception as qerr:
        print(f"[ERROR] Failed to synchronize Qdrant for updated product '{product_id}': {str(qerr)}")

    return ProductResponse(**updated_doc)

@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Seller Product",
    description="Deletes product from MongoDB, removes vector point from Qdrant, and cleans up image files."
)
async def delete_product(
    product_id: str,
    current_seller: dict = Depends(get_current_seller)
):
    """
    DELETE /api/seller/products/{product_id}
    Deletes product from MongoDB and Qdrant vector index.
    """
    seller_id = current_seller["user_id"]
    products_col = get_products_collection()

    existing_doc = await products_col.find_one({"product_id": product_id})
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' was not found."
        )

    if existing_doc.get("seller_id") != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only delete your own products."
        )

    # 1. Delete from MongoDB
    await products_col.delete_one({"product_id": product_id})

    # 2. Delete point from Qdrant
    try:
        qdrant_service.delete_product_vector(product_id)
    except Exception as qerr:
        print(f"[ERROR] Failed to delete Qdrant vector point for '{product_id}': {str(qerr)}")

    # 3. Delete image file and directory from filesystem
    image_path = existing_doc.get("image_path")
    if image_path:
        delete_file_safely(image_path)
        try:
            prod_dir = (settings.BASE_DIR / image_path).parent
            if prod_dir.exists() and not any(prod_dir.iterdir()):
                prod_dir.rmdir()
        except Exception:
            pass

    return {
        "message": f"Product '{product_id}' deleted successfully.",
        "product_id": product_id
    }

