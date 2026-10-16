from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.models.product import ProductSearchResult

class RoomAnalysis(BaseModel):
    """
    Room Analysis Schema
    ====================
    Represents the structured output produced by Groq/Vision AI analyzing a room photo.
    Adheres to strict visual inspection rules (no hallucinated furniture, exact materials,
    confidence metrics, and fallback transparency).
    """
    room_type: str = Field(
        default="living room",
        example="living room",
        description="Identified room space (e.g. living room, bedroom, kitchen, bathroom, balcony, dining room, hallway, office)"
    )
    wall_color: str = Field(
        default="white / off-white painted walls",
        example="white / off-white painted walls",
        description="Primary wall color and texture (synced with wall_color_finish)"
    )
    wall_color_finish: Optional[str] = Field(
        default=None,
        example="white / off-white painted walls",
        description="Detailed wall finish and color"
    )
    floor: str = Field(
        default="glossy light-colored tile",
        example="glossy light-colored tile",
        description="Flooring material (synced with flooring_material)"
    )
    flooring_material: Optional[str] = Field(
        default=None,
        example="glossy light-colored tile",
        description="Detailed flooring material, finish, and tone"
    )
    lighting: str = Field(
        default="bright natural daylight with artificial light",
        example="cool white artificial lighting with daylight from balcony",
        description="Observed lighting environment and light fixtures"
    )
    target_style: Optional[str] = Field(
        default="undetermined",
        example="undetermined",
        description="Detected visual style, or 'undetermined' / 'minimal / unfinished' if unstyled"
    )
    design_style: Optional[str] = Field(
        default="undetermined",
        example="undetermined",
        description="Detected architectural or interior style (synced with target_style)"
    )
    existing_furniture: List[str] = Field(
        default_factory=list,
        example=[],
        description="Only physically visible furniture items. Must be empty [] if the room is empty"
    )
    visible_objects: List[str] = Field(
        default_factory=list,
        example=["two ceiling fans", "sliding glass balcony door", "balcony railing", "wall-mounted light fixture"],
        description="All visible objects, fixtures, and appliances identified in the image"
    )
    dominant_colors: List[str] = Field(
        default_factory=list,
        example=["white", "off-white", "light grey", "dark brown/black"],
        description="Dominant color palette observed directly from the image"
    )
    architectural_features: List[str] = Field(
        default_factory=list,
        example=["large sliding glass door", "balcony", "balcony railing", "open floor area"],
        description="Visible structural and architectural details"
    )
    room_features: Optional[List[str]] = Field(
        default_factory=list,
        example=["large sliding glass door", "balcony", "balcony railing", "open floor area"],
        description="Architectural features (synced with architectural_features)"
    )
    room_condition: Optional[str] = Field(
        default="mostly empty / unfinished",
        example="mostly empty / unfinished",
        description="Visual condition (mostly empty / unfinished / furnished / partially furnished / under renovation)"
    )
    confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores (0.0 to 1.0) for key attributes"
    )
    uncertain_items: List[str] = Field(
        default_factory=list,
        example=["interior design style"],
        description="List of attributes or elements that could not be determined with high certainty"
    )
    description: Optional[str] = Field(
        default="",
        description="Precise visual assessment of the room layout, visible features, and condition"
    )
    is_fallback: bool = Field(
        default=False,
        description="True if analysis was generated via heuristic fallback rather than live Vision AI"
    )
    provider: str = Field(
        default="groq_vision",
        description="Vision analysis provider used (e.g. groq_vision, openai_vision, heuristic_fallback)"
    )

    @model_validator(mode="before")
    @classmethod
    def sync_and_normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        # Normalize room_type
        rt = values.get("room_type")
        if not rt or rt in ("unknown", "undetermined", "null", "None"):
            values["room_type"] = "living room"
        else:
            values["room_type"] = str(rt).lower().strip()

        # Sync wall_color and wall_color_finish
        wall_finish = values.get("wall_color_finish") or values.get("wall_color") or "white / off-white painted walls"
        values["wall_color_finish"] = str(wall_finish).strip()
        values["wall_color"] = str(wall_finish).strip()

        # Sync floor and flooring_material
        floor_mat = values.get("flooring_material") or values.get("floor") or "glossy light-colored tile"
        values["flooring_material"] = str(floor_mat).strip()
        values["floor"] = str(floor_mat).strip()

        # Normalize lighting
        lt = values.get("lighting")
        if not lt:
            values["lighting"] = "bright lighting with ambient daylight"
        else:
            values["lighting"] = str(lt).strip()

        # Sync target_style and design_style
        style_val = values.get("target_style") or values.get("design_style") or "undetermined"
        values["target_style"] = str(style_val).strip()
        values["design_style"] = str(style_val).strip()

        # Sync architectural_features and room_features
        arch_feat = values.get("architectural_features") or values.get("room_features") or []
        if isinstance(arch_feat, list):
            clean_arch = [str(x).strip() for x in arch_feat if x]
        else:
            clean_arch = [str(arch_feat).strip()]
        values["architectural_features"] = clean_arch
        values["room_features"] = clean_arch

        # Normalize existing_furniture
        furn = values.get("existing_furniture", [])
        if isinstance(furn, list):
            values["existing_furniture"] = [str(x).strip() for x in furn if x]
        else:
            values["existing_furniture"] = []

        # Normalize visible_objects
        objs = values.get("visible_objects", [])
        if isinstance(objs, list):
            values["visible_objects"] = [str(x).strip() for x in objs if x]
        else:
            values["visible_objects"] = []

        # Normalize dominant_colors
        colors = values.get("dominant_colors", [])
        if isinstance(colors, list):
            values["dominant_colors"] = [str(x).strip() for x in colors if x]
        else:
            values["dominant_colors"] = ["white", "off-white", "light grey"]

        # Default confidence map if missing
        conf = values.get("confidence")
        if not isinstance(conf, dict) or not conf:
            values["confidence"] = {
                "room_type": 0.9 if not values.get("is_fallback") else 0.5,
                "wall_color_finish": 0.85 if not values.get("is_fallback") else 0.5,
                "flooring_material": 0.85 if not values.get("is_fallback") else 0.4,
                "lighting": 0.85 if not values.get("is_fallback") else 0.5,
                "target_style": 0.3 if values.get("target_style") in ("undetermined", "unknown") else 0.8
            }

        return values

class RoomAnalyzeResponse(BaseModel):
    """
    Room Image Analysis API Response Schema
    """
    room_analysis: RoomAnalysis
    room_image_path: str = Field(..., description="Saved relative path of the room image")
    room_id: Optional[str] = Field(None, description="Unique identifier for the room session")
    message: Optional[str] = Field("Room image analyzed successfully", description="Status or info message")
    is_mock_fallback: Optional[bool] = Field(False, description="True if analysis was generated via heuristic fallback")

class ProductSearchRequest(BaseModel):
    """
    Product Search Request Schema
    =============================
    Contains user inputs & room analysis required for vector search.
    """
    room_analysis: RoomAnalysis
    style: str = Field(..., example="Luxury Modern", description="Target interior design style")
    budget: float = Field(..., example=150000, description="Total budget in INR")
    categories: Optional[List[str]] = Field(
        default=["bed", "curtain", "wallpaper", "lighting", "decor"],
        description="List of product categories to retrieve"
    )

class ProductSearchResponse(BaseModel):
    """
    Product Search Response Schema
    ==============================
    Returns the generated semantic query string and matched products per category.
    """
    search_query: str = Field(..., description="Programmatically constructed text search query passed to CLIP")
    products: List[ProductSearchResult] = Field(..., description="List of top matching products with similarity scores")

class BudgetRecommendationRequest(BaseModel):
    """
    Budget-Aware Product Recommendation Request
    """
    room_analysis: RoomAnalysis
    style: str = Field(..., example="Modern Contemporary", description="Preferred design style")
    budget: float = Field(..., example=95000, description="Customer total budget in INR")
    categories: List[str] = Field(
        default=["sofa", "curtain", "lighting", "decor"],
        description="List of desired product categories"
    )
    room_image_path: Optional[str] = Field(None, description="Optional path to uploaded room image")

class BudgetRecommendationResponse(BaseModel):
    """
    Budget-Aware Product Recommendation Response
    """
    search_query: str = Field(..., description="Constructed semantic search query")
    budget: float = Field(..., description="Customer total budget in INR")
    estimated_total: float = Field(..., description="Sum of recommended products' prices")
    budget_remaining: float = Field(..., description="Remaining budget (budget - estimated_total)")
    budget_status: str = Field(..., description="Budget status: 'within_budget', 'slightly_over_budget', 'exceeds_budget'")
    recommended_products: List[ProductSearchResult] = Field(..., description="List of recommended seller products")
    categories_covered: List[str] = Field(default_factory=list, description="Categories successfully matched")

class SelectedProductInfo(BaseModel):
    """Summary of selected reference product."""
    product_id: str
    name: str
    price: float
    category: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    image_path: Optional[str] = None
    seller_id: Optional[str] = None

class DesignPrepareRequest(BaseModel):
    """
    Design Preparation Request Schema
    =================================
    Supports both legacy auto-search mode and explicit customer product selections.
    """
    room_analysis: RoomAnalysis
    style: str = Field(..., example="Luxury Modern", description="Target interior design style")
    budget: float = Field(..., example=150000, description="Total budget in INR")
    categories: Optional[List[str]] = Field(default=None, description="Optional categories list")
    selected_products: Optional[List[ProductSearchResult]] = Field(
        default=None,
        description="Optional list of explicitly selected products by the customer"
    )
    room_image_path: Optional[str] = Field(default=None, description="Optional path to uploaded room image")

class ImageGenerationStatus(BaseModel):
    """Structured mock / future image generation model payload."""
    provider: str = Field(default="mock", description="Image generation provider identifier (mock, sdxl, flux, etc.)")
    status: str = Field(default="ready", description="Generation status (e.g. ready, processing, completed)")
    message: Optional[str] = Field(None, description="Status detail or provider info")

class DesignPrepareResponse(BaseModel):
    """
    Design Preparation Response Schema
    ==================================
    Output model containing the final generative prompt, reference image paths,
    budget breakdown, and mock generation status.
    """
    final_prompt: str = Field(..., description="Final text prompt ready for image generation model")
    reference_images: List[str] = Field(..., description="Paths to selected product reference images")
    selected_products: List[SelectedProductInfo] = Field(..., description="List of selected product summaries")
    status_message: str = Field(..., description="Status message indicating ready for image generation API")
    room_analysis: Optional[RoomAnalysis] = Field(default=None, description="Structured room analysis")
    search_query: Optional[str] = Field(default=None, description="Semantic search query used")
    budget: Optional[float] = Field(default=None, description="Customer budget")
    estimated_total: Optional[float] = Field(default=None, description="Sum of selected products")
    budget_remaining: Optional[float] = Field(default=None, description="Remaining budget")
    budget_status: Optional[str] = Field(default=None, description="Budget status")
    original_room_image: Optional[str] = Field(default=None, description="Original uploaded room image path")
    image_generation: Optional[Dict[str, Any]] = Field(default=None, description="Provider status information")
