"""
Product Schemas for Decore AI
=============================
Defines schemas for catalog items, seller CRUD payloads, and vector search results.
Maintains full backward compatibility with legacy Product and ProductSearchResult classes.
"""

from typing import List, Union, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ProductBase(BaseModel):
    """Base fields shared across product models."""
    name: str = Field(..., min_length=2, max_length=200, description="Product display name")
    category: str = Field(..., description="Product category (e.g. bed, sofa, curtain, wallpaper, lighting, decor, table, chair)")
    subcategory: Optional[str] = Field(None, description="Optional subcategory (e.g. platform bed, chandelier)")
    description: Optional[str] = Field("", description="Detailed product description")
    price: float = Field(..., gt=0, description="Product price in INR or specified currency")
    currency: str = Field(default="INR", description="Currency code (e.g. INR, USD)")
    color: str = Field(..., description="Primary color tone (e.g. walnut brown, beige, brass)")
    material: str = Field(..., description="Product material (e.g. solid wood, velvet, leather, brass)")
    style: Union[List[str], str] = Field(..., description="Associated styles (e.g. ['luxury', 'modern'] or 'modern')")
    dimensions: Optional[str] = Field(None, description="Physical dimensions or specs (e.g. '80x60x45 cm')")
    stock: int = Field(default=1, ge=0, description="Available inventory count")
    is_active: bool = Field(default=True, description="Whether product is active and visible in catalog")

    @field_validator("style", mode="before")
    @classmethod
    def normalize_style(cls, v):
        if isinstance(v, str):
            # Parse comma-separated or single string into list
            parts = [s.strip().lower() for s in v.split(",") if s.strip()]
            return parts if parts else [v.strip().lower()]
        elif isinstance(v, list):
            return [str(s).strip().lower() for s in v if str(s).strip()]
        return v

class ProductCreate(ProductBase):
    """Payload for creating a new seller product."""
    pass

class ProductUpdate(BaseModel):
    """Payload for updating an existing product (all fields optional)."""
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    style: Optional[Union[List[str], str]] = None
    dimensions: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("style", mode="before")
    @classmethod
    def normalize_style(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            parts = [s.strip().lower() for s in v.split(",") if s.strip()]
            return parts if parts else [v.strip().lower()]
        elif isinstance(v, list):
            return [str(s).strip().lower() for s in v if str(s).strip()]
        return v

class Product(BaseModel):
    """
    Legacy & Catalog Product Schema
    ===============================
    Represents an interior product catalog item.
    Maintained for full backward compatibility with existing routes and indexing scripts.
    """
    product_id: str = Field(..., description="Unique product ID (e.g. BED001)")
    seller_id: Optional[str] = Field(default="SYSTEM", description="Owner seller identifier")
    name: str = Field(..., description="Product display name")
    category: str = Field(..., description="Product category (bed, sofa, curtain, wallpaper, lighting, decor)")
    subcategory: Optional[str] = Field(default=None, description="Product subcategory")
    description: Optional[str] = Field(default="", description="Product description")
    color: str = Field(..., description="Primary color tone")
    material: str = Field(..., description="Product material (e.g. solid wood, velvet, leather)")
    style: Union[List[str], str] = Field(..., description="Associated interior styles (e.g. ['luxury', 'modern'])")
    price: float = Field(..., description="Product price in INR")
    currency: Optional[str] = Field(default="INR", description="Currency code (e.g. INR)")
    dimensions: Optional[str] = Field(default=None, description="Physical dimensions or specs")
    image_path: str = Field(..., description="Relative local path or URL to the product image file")
    stock: Optional[int] = Field(default=1, description="Available stock quantity")
    is_active: Optional[bool] = Field(default=True, description="Active status in catalog")

class ProductResponse(BaseModel):
    """Full Decore AI Product details model."""
    product_id: str
    seller_id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = ""
    price: float
    currency: str = "INR"
    color: str
    material: str
    style: List[str]
    dimensions: Optional[str] = None
    stock: int = 1
    image_path: str
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ProductSearchResult(Product):
    """
    Product Search Result Schema
    ============================
    Includes the vector similarity match score (Cosine Similarity range: -1.0 to 1.0, typically 0.0 to 1.0).
    """
    score: float = Field(default=0.0, description="Qdrant cosine vector similarity score (higher = more similar)")

class SellerStatsResponse(BaseModel):
    """Summary dashboard statistics for a seller."""
    total_products: int = 0
    active_products: int = 0
    out_of_stock_products: int = 0
    recent_products: List[ProductResponse] = []
