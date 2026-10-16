"""
Prompt Builder & Design Synthesis Service
=========================================
What Information downstream AI Image Generators (ControlNet / SDXL / FLUX) receive:
------------------------------------------------------------------------------------
In a complete AI interior redesign application, an image generation model requires 3 inputs:
1. Original Room Image: Passed to ControlNet (e.g. MLSD edge detector or depth map) to preserve exact room layout, windows, doors, and architectural dimensions.
2. Selected Product Reference Images: Passed to IP-Adapter (Image Prompt Adapter) to guide visual style & texture of actual real-world catalog items.
3. Final Textual Prompt: Comprehensive text description synthesized from room analysis, style, and selected product catalog metadata.

This service builds the final textual prompt and organizes reference images for downstream generation.
"""

from typing import List, Tuple, Dict, Any, Optional, Union
from app.models.room import RoomAnalysis, SelectedProductInfo
from app.models.product import ProductSearchResult
from app.services.image_generation_service import image_generation_service

def build_final_prompt(
    room_analysis: RoomAnalysis,
    style: str,
    selected_products: List[Union[ProductSearchResult, Dict[str, Any], Any]],
    original_room_image: Optional[str] = None
) -> Tuple[str, List[str], List[SelectedProductInfo]]:
    """
    Dynamically synthesizes a comprehensive final generative interior design prompt
    and collects reference image paths and structured product summaries.
    """
    product_descriptions = []
    reference_images = []
    selected_info_list = []

    for item in selected_products:
        if isinstance(item, ProductSearchResult):
            prod_dict = item.model_dump()
        elif isinstance(item, dict):
            prod_dict = item
        elif hasattr(item, "model_dump"):
            prod_dict = item.model_dump()
        elif hasattr(item, "__dict__"):
            prod_dict = item.__dict__
        else:
            continue

        p_id = str(prod_dict.get("product_id", ""))
        p_name = str(prod_dict.get("name", "Product"))
        p_price = float(prod_dict.get("price", 0.0))
        p_cat = str(prod_dict.get("category", "")).strip()
        p_color = str(prod_dict.get("color", "")).strip()
        p_mat = str(prod_dict.get("material", "")).strip()
        p_dims = str(prod_dict.get("dimensions", "") or "").strip()
        p_img = str(prod_dict.get("image_path", "")).strip()
        p_seller = str(prod_dict.get("seller_id", "")).strip()

        desc_parts = [p_name]
        details = []
        if p_color:
            details.append(p_color)
        if p_mat:
            details.append(p_mat)
        if p_dims:
            details.append(f"dimensions {p_dims}")
        if details:
            desc_parts.append(f"({', '.join(details)})")

        product_descriptions.append(" ".join(desc_parts))
        if p_img:
            reference_images.append(p_img)

        selected_info_list.append(
            SelectedProductInfo(
                product_id=p_id,
                name=p_name,
                price=p_price,
                category=p_cat,
                color=p_color,
                material=p_mat,
                image_path=p_img,
                seller_id=p_seller
            )
        )

    products_str = "; ".join(product_descriptions) if product_descriptions else "curated seller interior items"
    colors_str = ", ".join(room_analysis.dominant_colors) if room_analysis.dominant_colors else "harmonious balanced tones"
    
    # Handle furniture context
    has_furniture = bool(room_analysis.existing_furniture and any(f.lower() not in ("none", "unknown", "—", "") for f in room_analysis.existing_furniture))
    if has_furniture:
        furniture_clause = f"Complement existing {', '.join(room_analysis.existing_furniture)} and seamlessly integrate the following selected seller catalog products: {products_str}."
    else:
        furniture_clause = f"This room is currently empty and unfurnished. Fully stage and furnish the open living area with the following selected seller catalog products: {products_str}."

    # Handle architectural features
    arch_list = room_analysis.architectural_features or room_analysis.room_features or []
    features_str = ", ".join(arch_list) if arch_list else "clean architectural lines and room geometry"

    wall_str = room_analysis.wall_color_finish or room_analysis.wall_color
    floor_str = room_analysis.flooring_material or room_analysis.floor

    # Construct dynamic, detailed photorealistic prompt
    final_prompt = (
        f"Redesign this {room_analysis.room_type} in an exquisite {style.strip()} interior style. "
        f"Preserve the original room architecture, wall structure with {wall_str}, "
        f"{floor_str}, window placements, and camera perspective. "
        f"{furniture_clause} "
        f"Harmonize with {colors_str} color palette and {room_analysis.lighting} lighting conditions. "
        f"Preserve structural features such as {features_str}. "
        f"Maintain precise scale, realistic perspective, natural shadows, depth of field, and accurate material textures. "
        f"Do not invent unrelated or conflicting furniture when selected catalog products are specified. "
        f"Ultra-high resolution, architectural digest photography, ray-traced ambient lighting, masterwork interior design."
    )

    return final_prompt, reference_images, selected_info_list

def generate_design(
    original_room_image: Optional[str],
    reference_images: List[str],
    final_prompt: str
) -> str:
    """
    Executes mock image generation via image_generation_service.
    Maintains backward compatibility with legacy tests.
    """
    result = image_generation_service.generate_design(
        original_room_image=original_room_image,
        reference_images=reference_images,
        final_prompt=final_prompt
    )
    return result.get("message", "Image generation step is ready for integration.")
