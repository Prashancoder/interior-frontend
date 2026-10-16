import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Decore AI Application Configuration
    ==================================
    Loads environment variables from .env file or system environment.
    Configurable parameters for MongoDB, JWT auth, Qdrant connection, CLIP model,
    Groq Vision, and Image Generation services.
    """
    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_PATH: Path = BASE_DIR / "data" / "products.json"
    PRODUCTS_DIR: Path = BASE_DIR / "products"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"

    # MongoDB Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "decore_ai"

    # JWT Authentication
    JWT_SECRET: str = "decore-ai-secret-key-2026-production-ready"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "interior_products"

    # CLIP / OpenCLIP Model
    CLIP_MODEL: str = "ViT-B-32"
    CLIP_PRETRAINED: str = "laion2b_s34b_b79k"

    # Groq Vision Model (Backend Only)
    GROQ_API_KEY: Optional[str] = ""
    GROQ_VISION_MODEL: str = "qwen/qwen3.8-27b"

    # OpenAI Vision (Optional Alternative Provider)
    OPENAI_API_KEY: Optional[str] = ""
    OPENAI_VISION_MODEL: str = "gpt-4o"

    # Image Generation Provider
    IMAGE_GENERATION_PROVIDER: str = "mock"
    IMAGE_GENERATION_API_KEY: Optional[str] = ""

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

# Global settings instance
settings = Settings()

# Normalize upload path: relative values from .env must resolve under BASE_DIR
if not settings.UPLOAD_DIR.is_absolute():
    settings.UPLOAD_DIR = (settings.BASE_DIR / settings.UPLOAD_DIR).resolve()
else:
    settings.UPLOAD_DIR = settings.UPLOAD_DIR.resolve()

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
