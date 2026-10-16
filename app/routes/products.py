from fastapi import APIRouter, HTTPException, status
from app.models.room import ProductSearchRequest, ProductSearchResponse
from app.ingestion.index_products import index_all_products
from app.services.product_service import search_products_by_category

router = APIRouter(prefix="/products", tags=["Products & Vector Retrieval"])

@router.post(
    "/index",
    status_code=status.HTTP_200_OK,
    summary="Index Catalog Products into Qdrant",
    description="Loads product catalog images, generates CLIP image embedding vectors, and stores them in Qdrant with payload metadata."
)
async def index_products():
    """
    POST /products/index
    Indexes all catalog images into Qdrant vector database.
    """
    try:
        result = index_all_products()
        return result
    except ConnectionError as ce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(ce)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Product indexing failed: {str(e)}"
        )

@router.post(
    "/search",
    response_model=ProductSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Search Products",
    description="Converts room analysis JSON + style + budget into a CLIP text embedding query and retrieves matching products from Qdrant per category."
)
async def search_products(request: ProductSearchRequest):
    """
    POST /products/search
    Accepts room analysis, style, budget, and target categories.
    Returns generated search query and top matching products with cosine similarity scores.
    """
    if not request.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one product category must be specified for search."
        )

    try:
        query_text, matched_products = search_products_by_category(
            room_analysis=request.room_analysis,
            style=request.style,
            budget=request.budget,
            categories=request.categories,
            limit_per_category=2
        )

        return ProductSearchResponse(
            search_query=query_text,
            products=matched_products
        )
    except ConnectionError as ce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(ce)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Product vector search failed: {str(e)}"
        )
