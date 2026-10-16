from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.mongodb import init_db, close_db
from app.routes.auth import router as auth_router
from app.routes.seller import router as seller_router
from app.routes.products import router as products_router
from app.routes.design import router as design_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle manager."""
    # Startup
    try:
        await init_db()
    except Exception as e:
        print(f"[Decore AI] Database initialization warning: {e}")

    try:
        from app.services.clip_service import clip_service
        from app.services.qdrant_service import qdrant_service
        # Warm up OpenCLIP model and ensure Qdrant collection is ready
        clip_service.load_model()
        dim = clip_service.get_embedding_dimension()
        qdrant_service.create_collection(vector_size=dim)
    except Exception as e:
        print(f"[Decore AI] Vector service initialization warning: {e}")

    yield
    # Shutdown
    await close_db()

# Initialize FastAPI application
app = FastAPI(
    title="Decore AI - Multi-Vendor AI Interior Design Platform API",
    description=(
        "Production backend for Decore AI: A multi-vendor AI Interior Design platform. "
        "Supports Seller onboarding, product inventory management, safe image uploads, "
        "Vision AI room analysis, OpenCLIP vector embeddings with Qdrant retrieval, and design generation."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth_router)
app.include_router(seller_router)
app.include_router(products_router)
app.include_router(design_router)

# Mount static directories for image assets
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/products", StaticFiles(directory=str(settings.PRODUCTS_DIR)), name="products")

# Custom Global Exception Handlers
@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError):
    return JSONResponse(
        status_code=533,
        content={
            "error": "Database Connection Failure",
            "message": str(exc),
            "hint": "Ensure MongoDB (port 27017) and Qdrant (port 6333) are running."
        }
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Resource Not Found",
            "message": str(exc),
            "hint": "Run `python scripts/create_sample_products.py` to generate sample images and dataset."
        }
    )

@app.get("/", summary="Root Endpoint - API Information")
async def root():
    """
    Root endpoint returning system info and interactive Swagger documentation links.
    """
    return {
        "project_name": "Decore AI",
        "status": "running",
        "version": "2.0.0",
        "description": "Multi-Vendor AI Interior Design Platform Backend",
        "documentation": "/docs",
        "qdrant_dashboard": f"{settings.QDRANT_URL}/dashboard",
        "modules": {
            "Authentication": {
                "POST /api/auth/register": "Register Customer or Seller",
                "POST /api/auth/login": "Authenticate user and get JWT token",
                "GET /api/auth/me": "Get current profile"
            },
            "Seller Dashboard": {
                "POST /api/seller/products": "Upload product with image and metadata",
                "GET /api/seller/products": "List seller's products",
                "GET /api/seller/products/{product_id}": "Get product details",
                "PUT /api/seller/products/{product_id}": "Update product details or image",
                "DELETE /api/seller/products/{product_id}": "Delete product and remove image",
                "GET /api/seller/stats": "Seller dashboard statistics"
            },
            "Vector Search & Pipeline (Legacy Compatible)": {
                "POST /products/index": "Index catalog product images into Qdrant",
                "POST /products/search": "Perform category-wise CLIP vector search in Qdrant",
                "POST /design/prepare": "Synthesize final image generation prompt & reference images"
            },
            "Customer AI Interior Design": {
                "POST /api/design/analyze-room": "Analyze room image using Groq Vision AI",
                "POST /api/design/recommend-products": "Budget-aware OpenCLIP + Qdrant product recommendations",
                "POST /api/design/prepare": "Prepare final design prompt, reference assets, and mock image generation"
            }
        }
    }
