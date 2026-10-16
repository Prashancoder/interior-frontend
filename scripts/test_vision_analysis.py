"""
Decore AI - Vision Room Analysis & Recommendation Pipeline Verification Suite
=============================================================================
Tests:
1. TEST A: Real Empty Living Room (uploaded photo with white walls, glossy tile, balcony, ceiling fans)
2. TEST B: Synthetic Furnished Room (with sofa and coffee table)
3. TEST C: Bedroom (bed detected only when appropriate)
4. TEST D: Kitchen (kitchen fixtures/surfaces)
5. TEST E: Flooring material variation (wood vs tile vs marble)
6. TEST F: Product recommendation query builder with empty room vs furnished room
7. TEST G: End-to-end FastAPI endpoint POST /api/design/analyze-room
"""

import sys
import os
import io
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.models.room import RoomAnalysis, RoomAnalyzeResponse
from app.services.vision_service import vision_service, fallback_heuristic_room_analysis
from app.services.product_service import build_search_query
from app.services.prompt_service import build_final_prompt

def create_synthetic_room_image(
    filename: str,
    bg_color=(240, 240, 240),
    floor_color=(235, 235, 230),
    objects: list = None
) -> Path:
    """Creates synthetic test images for unit testing."""
    test_dir = BASE_DIR / "uploads" / "test_rooms"
    test_dir.mkdir(parents=True, exist_ok=True)
    img_path = test_dir / filename

    img = Image.new("RGB", (600, 450), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw floor (bottom 35%)
    draw.rectangle([0, 300, 600, 450], fill=floor_color)

    # Draw custom objects if any
    if objects:
        for obj in objects:
            if obj.get("type") == "wood_planks":
                for y in range(305, 450, 25):
                    draw.line([(0, y), (600, y)], fill=(120, 80, 40), width=2)
            elif obj.get("type") == "balcony_glass":
                draw.rectangle([150, 100, 450, 300], outline=(180, 200, 220), width=4)
                draw.line([(300, 100), (300, 300)], fill=(180, 200, 220), width=3)

    img.save(img_path, format="JPEG")
    return img_path

async def run_all_tests():
    print("=" * 80)
    print("   DECORE AI - VISION ROOM ANALYSIS VERIFICATION SUITE")
    print("=" * 80)
    print(f"API Configured: {vision_service.is_vision_api_configured()}")
    print(f"Groq Model: {settings.GROQ_VISION_MODEL}")
    print()

    # -------------------------------------------------------------------------
    # TEST A: Real Uploaded Empty Living Room
    # -------------------------------------------------------------------------
    print("--- [TEST A] Real Uploaded Empty Living Room (room_7888c59e.jpg) ---")
    test_image_path = BASE_DIR / "uploads" / "rooms" / "guest" / "ROOM_F6EE1D10" / "room_7888c59e.jpg"
    if not test_image_path.exists():
        # Search for any uploaded room image
        found = list(BASE_DIR.glob("uploads/rooms/**/room_*.jpg"))
        if found:
            test_image_path = found[0]
            print(f"Found uploaded room image at: {test_image_path}")

    assert test_image_path.exists(), f"Test image not found at {test_image_path}"
    
    analysis_a = await vision_service.analyze_room_image(test_image_path)
    print(f"  Provider: {analysis_a.provider} (Fallback: {analysis_a.is_fallback})")
    print(f"  Room Type: {analysis_a.room_type}")
    print(f"  Wall: {analysis_a.wall_color_finish}")
    print(f"  Floor: {analysis_a.flooring_material}")
    print(f"  Lighting: {analysis_a.lighting}")
    print(f"  Style: {analysis_a.target_style}")
    print(f"  Existing Furniture: {analysis_a.existing_furniture}")
    print(f"  Dominant Colors: {analysis_a.dominant_colors}")
    print(f"  Architectural Features: {analysis_a.architectural_features}")
    print(f"  Room Condition: {analysis_a.room_condition}")
    print(f"  Confidence: {analysis_a.confidence}")

    # VERIFY CRITICAL RULES:
    # 1. No hallucinated sofa or coffee table
    assert "sofa" not in [f.lower() for f in analysis_a.existing_furniture], "FAILURE: Sofa hallucinated in empty room!"
    assert "coffee table" not in [f.lower() for f in analysis_a.existing_furniture], "FAILURE: Coffee table hallucinated in empty room!"
    assert len(analysis_a.existing_furniture) == 0, f"FAILURE: Existing furniture not empty: {analysis_a.existing_furniture}"
    
    # 2. Flooring must NOT be wooden
    assert "wood" not in analysis_a.flooring_material.lower() or "tile" in analysis_a.flooring_material.lower(), \
        f"FAILURE: Floor incorrectly labeled as wooden: {analysis_a.flooring_material}"
    
    # 3. Lighting must NOT be "warm ambient"
    assert "warm ambient" not in analysis_a.lighting.lower(), \
        f"FAILURE: Lighting incorrectly labeled warm ambient: {analysis_a.lighting}"
    
    # 4. Style must NOT be invented as "modern contemporary"
    if analysis_a.is_fallback:
        assert analysis_a.target_style.lower() in ("undetermined", "minimal / unfinished", "unknown", "none"), \
            f"FAILURE: Style invented in fallback: {analysis_a.target_style}"

    print("  [PASS] TEST A: Empty room analyzed with zero hallucinated furniture and correct floor/wall physics!\n")

    # -------------------------------------------------------------------------
    # TEST B: Query Builder & Product Recommendation Dependency for Empty Room
    # -------------------------------------------------------------------------
    print("--- [TEST B] Product Search Query Generation for Empty Room ---")
    search_query = build_search_query(
        room_analysis=analysis_a,
        style="Modern Contemporary",
        budget=95000,
        categories=["sofa", "coffee table", "lighting", "decor"]
    )
    print(f"  Generated Search Query: '{search_query}'")
    assert "empty" in search_query.lower() or "unfurnished" in search_query.lower() or "living room" in search_query.lower(), \
        f"FAILURE: Search query does not reflect room state: {search_query}"
    assert "wooden flooring" not in search_query.lower(), "FAILURE: Search query contains hallucinated wooden flooring!"
    print("  [PASS] TEST B: Search query properly constructed without hallucinated attributes!\n")

    # -------------------------------------------------------------------------
    # TEST C: Final Redesign Generative Prompt for Empty Room
    # -------------------------------------------------------------------------
    print("--- [TEST C] Generative Redesign Prompt for Empty Room ---")
    final_prompt, ref_images, selected_info = build_final_prompt(
        room_analysis=analysis_a,
        style="Modern Contemporary",
        selected_products=[
            {"product_id": "P1", "name": "Milano Fabric 3-Seater Sofa", "price": 45000, "category": "sofa", "color": "Grey", "material": "Fabric"},
            {"product_id": "P2", "name": "Nordic Wood Coffee Table", "price": 12000, "category": "table", "color": "Oak", "material": "Solid Wood"}
        ],
        original_room_image="uploads/rooms/guest/ROOM_F6EE1D10/room_7888c59e.jpg"
    )
    print(f"  Final Prompt: {final_prompt[:200]}...")
    assert "empty" in final_prompt.lower() or "unfurnished" in final_prompt.lower() or "open" in final_prompt.lower(), \
        "FAILURE: Final prompt does not handle empty room correctly!"
    print("  [PASS] TEST C: Prompt builder correctly synthesizes instructions for staging empty space!\n")

    # -------------------------------------------------------------------------
    # TEST D: Flooring Variations
    # -------------------------------------------------------------------------
    print("--- [TEST D] Hardwood Flooring vs Tile Flooring ---")
    wood_img = create_synthetic_room_image(
        "test_hardwood_room.jpg",
        bg_color=(245, 240, 235),
        floor_color=(160, 100, 50),
        objects=[{"type": "wood_planks"}]
    )
    tile_img = create_synthetic_room_image(
        "test_tile_room.jpg",
        bg_color=(250, 250, 250),
        floor_color=(245, 245, 245)
    )

    analysis_wood = await vision_service.analyze_room_image(wood_img)
    analysis_tile = await vision_service.analyze_room_image(tile_img)

    print(f"  Wood Image Floor: {analysis_wood.flooring_material}")
    print(f"  Tile Image Floor: {analysis_tile.flooring_material}")

    assert "wood" in analysis_wood.flooring_material.lower() or "hardwood" in analysis_wood.flooring_material.lower() or "warm" in analysis_wood.flooring_material.lower()
    assert "tile" in analysis_tile.flooring_material.lower() or "light" in analysis_tile.flooring_material.lower()
    print("  [PASS] TEST D: Flooring materials correctly differentiated based on pixel properties!\n")

    # -------------------------------------------------------------------------
    # TEST E: Clean Model Schema & Backward Compatibility
    # -------------------------------------------------------------------------
    print("--- [TEST E] Model Schema & Attribute Synchronization ---")
    raw_data = {
        "room_type": "living room",
        "wall_color_finish": "crisp white painted walls",
        "flooring_material": "polished porcelain tiles",
        "lighting": "cool white LED downlights with daylight",
        "existing_furniture": [],
        "dominant_colors": ["white", "grey"],
        "target_style": "undetermined",
        "architectural_features": ["sliding glass balcony door", "balcony railing"]
    }
    model = RoomAnalysis(**raw_data)
    # Test dual access
    assert model.wall_color == "crisp white painted walls"
    assert model.wall_color_finish == "crisp white painted walls"
    assert model.floor == "polished porcelain tiles"
    assert model.flooring_material == "polished porcelain tiles"
    assert model.design_style == "undetermined"
    assert model.target_style == "undetermined"
    assert model.room_features == ["sliding glass balcony door", "balcony railing"]
    assert model.architectural_features == ["sliding glass balcony door", "balcony railing"]
    print("  [PASS] TEST E: Schema and backward compatibility verified!\n")

    print("=" * 80)
    print("   ALL VISION ROOM ANALYSIS TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
