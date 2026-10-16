"""
Customer AI Interior Design API Routes for Decore AI
====================================================
Provides end-to-end endpoints for customer AI interior redesign flow:
1. POST /api/design/analyze-room: Groq Vision image analysis
2. POST /api/design/recommend-products: Budget-aware semantic vector retrieval
3. POST /design/prepare & POST /api/design/prepare: Dynamic prompt synthesis & mock generation
"""

from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.room import (
    RoomAnalysis,
    RoomAnalyzeResponse,
    BudgetRecommendationRequest,
    BudgetRecommendationResponse,
    DesignPrepareRequest,
    DesignPrepareResponse,
    SelectedProductInfo
)
from app.services.storage_service import save_customer_room_image
from app.services.vision_service import vision_service
from app.services.product_service import (
    build_search_query,
    search_products_by_category,
    recommend_products_budget_aware
)
from app.services.prompt_service import build_final_prompt
from app.services.image_generation_service import image_generation_service
from app.services.auth_service import decode_access_token

router = APIRouter(tags=["Design Pipeline"])
security_bearer = HTTPBearer(auto_error=False)

def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> str:
    """Helper to extract user_id if valid JWT token is supplied, else defaults to 'guest'."""
    if credentials and credentials.credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            return payload.get("sub") or payload.get("user_id") or "guest"
        except Exception:
            return "guest"
    return "guest"

# --------------------------------------------------------------------------
# 1. Room Image Analysis Endpoint (Groq Vision)
# --------------------------------------------------------------------------
@router.post(
    "/api/design/analyze-room",
    response_model=RoomAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Customer Room Image with Groq Vision",
    description="Uploads a room photo (JPG, JPEG, PNG, WEBP), saves it server-side under uploads/rooms/{user_id}/{room_id}/, and analyzes it using Groq Vision AI."
)
@router.post("/design/analyze-room", response_model=RoomAnalyzeResponse, include_in_schema=False)
async def analyze_room(
    file: UploadFile = File(..., description="Customer interior or room photo"),
    style: Optional[str] = Form(None, description="Optional target style preference"),
    user_id: str = Depends(get_optional_user_id)
):
    """
    POST /api/design/analyze-room
    Accepts multipart form-data image and returns structured RoomAnalysis JSON.
    """
    try:
        # Step 1: Save room image securely
        room_id, rel_path = await save_customer_room_image(file=file, user_id=user_id)

        # Step 2: Perform Vision server-side analysis
        analysis = await vision_service.analyze_room_image(image_path=rel_path, preferred_style=style)

        if analysis.is_fallback:
            msg = "Vision API key not configured in environment. Analyzed room using offline fallback (no furniture assumed)."
        else:
            provider_label = "Groq Vision AI" if "groq" in analysis.provider else "Vision AI"
            msg = f"Room analysis completed successfully via {provider_label}."

        return RoomAnalyzeResponse(
            room_analysis=analysis,
            room_image_path=rel_path,
            room_id=room_id,
            message=msg,
            is_mock_fallback=analysis.is_fallback
        )

    except HTTPException:
        raise
    except ConnectionError as ce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(ce)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Room analysis failed: {str(e)}"
        )

# --------------------------------------------------------------------------
# 2. Budget-Aware Product Recommendation Endpoint
# --------------------------------------------------------------------------
@router.post(
    "/api/design/recommend-products",
    response_model=BudgetRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Budget-Aware Semantic Product Recommendation",
    description="Encodes room analysis into OpenCLIP space, queries Qdrant vector database, and returns products filtered and ranked against the customer's total budget."
)
@router.post("/design/recommend-products", response_model=BudgetRecommendationResponse, include_in_schema=False)
async def recommend_products(request: BudgetRecommendationRequest):
    """
    POST /api/design/recommend-products
    Accepts room analysis, style, budget, and desired categories.
    Returns budget-aware recommended seller products.
    """
    if not request.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select at least one product category."
        )

    if request.budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than 0."
        )

    try:
        (
            query_text,
            recommended_products,
            estimated_total,
            budget_remaining,
            budget_status,
            categories_covered
        ) = recommend_products_budget_aware(
            room_analysis=request.room_analysis,
            style=request.style,
            budget=request.budget,
            categories=request.categories,
            top_candidates_per_category=3
        )

        return BudgetRecommendationResponse(
            search_query=query_text,
            budget=request.budget,
            estimated_total=estimated_total,
            budget_remaining=budget_remaining,
            budget_status=budget_status,
            recommended_products=recommended_products,
            categories_covered=categories_covered
        )
    except ConnectionError as ce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(ce)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Product recommendation failed: {str(e)}"
        )

# --------------------------------------------------------------------------
# 3. Final Design Preparation Endpoint
# --------------------------------------------------------------------------
@router.post(
    "/design/prepare",
    response_model=DesignPrepareResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare Final Generative Design & Reference Assets",
    description="Synthesizes dynamic generative interior prompt, aggregates selected catalog product reference images, and prepares downstream mock image generation."
)
@router.post("/api/design/prepare", response_model=DesignPrepareResponse, include_in_schema=False)
async def prepare_design(request: DesignPrepareRequest):
    """
    POST /design/prepare and POST /api/design/prepare
    Supports both legacy auto-search mode and explicit customer product selection.
    """
    try:
        query_text = build_search_query(
            room_analysis=request.room_analysis,
            style=request.style,
            budget=request.budget,
            categories=request.categories
        )

        # If customer provided explicit product selections, use them
        if request.selected_products and len(request.selected_products) > 0:
            chosen_products = request.selected_products
        else:
            # Fallback: search Qdrant for top matching products
            categories = request.categories or ["bed", "curtain", "wallpaper", "lighting", "decor"]
            _, chosen_products = search_products_by_category(
                room_analysis=request.room_analysis,
                style=request.style,
                budget=request.budget,
                categories=categories,
                limit_per_category=1
            )

        # Synthesize dynamic final prompt & collect reference images
        final_prompt, ref_images, selected_info = build_final_prompt(
            room_analysis=request.room_analysis,
            style=request.style,
            selected_products=chosen_products,
            original_room_image=request.room_image_path
        )

        # Calculate estimated total and budget status
        estimated_total = round(sum(item.price for item in selected_info), 2)
        budget_remaining = round(request.budget - estimated_total, 2)
        if budget_remaining >= 0:
            budget_status_val = "within_budget"
        elif abs(budget_remaining) <= (request.budget * 0.20):
            budget_status_val = "slightly_over_budget"
        else:
            budget_status_val = "exceeds_budget"

        # Execute mock / downstream generation service
        gen_result = image_generation_service.generate_design(
            original_room_image=request.room_image_path,
            reference_images=ref_images,
            final_prompt=final_prompt,
            metadata={
                "budget": request.budget,
                "estimated_total": estimated_total,
                "selected_products_count": len(selected_info)
            }
        )

        return DesignPrepareResponse(
            final_prompt=final_prompt,
            reference_images=ref_images,
            selected_products=selected_info,
            status_message=gen_result.get("message", "Image generation step is ready for integration."),
            room_analysis=request.room_analysis,
            search_query=query_text,
            budget=request.budget,
            estimated_total=estimated_total,
            budget_remaining=budget_remaining,
            budget_status=budget_status_val,
            original_room_image=request.room_image_path,
            image_generation={
                "provider": gen_result.get("provider", "mock"),
                "status": gen_result.get("status", "ready"),
                "message": gen_result.get("message")
            }
        )
    except ConnectionError as ce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(ce)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Design prompt preparation failed: {str(e)}"
        )
