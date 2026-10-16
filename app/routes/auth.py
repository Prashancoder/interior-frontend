"""
Authentication API Routes for Decore AI
=======================================
Endpoints for User and Seller registration, login, and profile retrieval.
"""

from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, status, Depends

from app.database.mongodb import get_users_collection
from app.models.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    UserRole
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Customer or Seller",
    description="Creates a new account with hashed password and returns an active JWT access token."
)
async def register_user(request: UserRegisterRequest):
    """
    POST /api/auth/register
    Creates a new user or seller profile.
    """
    users_col = get_users_collection()
    normalized_email = request.email.lower().strip()

    # Check for existing email
    existing_user = await users_col.find_one({"email": normalized_email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Generate structured user_id prefix based on role
    prefix = "SELLER" if request.role == UserRole.SELLER else "CUST"
    user_id = f"{prefix}_{uuid.uuid4().hex[:8].upper()}"

    now_iso = datetime.now(timezone.utc).isoformat()
    hashed_pwd = hash_password(request.password)

    user_doc = {
        "user_id": user_id,
        "name": request.name.strip(),
        "email": normalized_email,
        "password_hash": hashed_pwd,
        "role": request.role.value,
        "business_name": request.business_name.strip() if request.business_name else None,
        "phone": request.phone.strip() if request.phone else None,
        "is_active": True,
        "created_at": now_iso,
        "updated_at": now_iso
    }

    try:
        await users_col.insert_one(user_doc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account: {str(e)}"
        )

    # Generate JWT Token
    token_payload = {
        "sub": user_id,
        "email": normalized_email,
        "role": request.role.value,
        "name": request.name.strip()
    }
    access_token = create_access_token(token_payload)

    user_response = UserResponse(
        user_id=user_id,
        name=user_doc["name"],
        email=user_doc["email"],
        role=request.role,
        business_name=user_doc.get("business_name"),
        phone=user_doc.get("phone"),
        is_active=user_doc["is_active"],
        created_at=user_doc["created_at"]
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,
        user=user_response
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login Customer or Seller",
    description="Authenticates user credentials and returns a JWT access token."
)
async def login_user(request: UserLoginRequest):
    """
    POST /api/auth/login
    Authenticates user and returns JWT token.
    """
    users_col = get_users_collection()
    normalized_email = request.email.lower().strip()

    user_doc = await users_col.find_one({"email": normalized_email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(request.password, user_doc.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact support."
        )

    user_id = user_doc["user_id"]
    token_payload = {
        "sub": user_id,
        "email": normalized_email,
        "role": user_doc["role"],
        "name": user_doc["name"]
    }
    access_token = create_access_token(token_payload)

    user_response = UserResponse(
        user_id=user_id,
        name=user_doc["name"],
        email=user_doc["email"],
        role=UserRole(user_doc["role"]),
        business_name=user_doc.get("business_name"),
        phone=user_doc.get("phone"),
        is_active=user_doc.get("is_active", True),
        created_at=user_doc.get("created_at")
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,
        user=user_response
    )

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns profile information for the currently authenticated user."
)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    GET /api/auth/me
    Returns current user info from JWT.
    """
    return UserResponse(
        user_id=current_user["user_id"],
        name=current_user["name"],
        email=current_user["email"],
        role=UserRole(current_user["role"]),
        business_name=current_user.get("business_name"),
        phone=current_user.get("phone"),
        is_active=current_user.get("is_active", True),
        created_at=current_user.get("created_at")
    )
