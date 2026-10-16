"""
Decore AI - Customer AI Design Flow End-to-End Test
===================================================
Validates the customer design pipeline continuing from Phase 1/2:

1. Customer register/login
2. Room image upload + Groq Vision (or heuristic fallback)
3. Structured room analysis
4. Budget-aware OpenCLIP + Qdrant recommendations
5. Product selection totals
6. Final prompt + reference images + mock image generation
7. Legacy POST /products/search still works
"""

import sys
import io
import time
import asyncio
from pathlib import Path
from PIL import Image
from httpx import AsyncClient, ASGITransport

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.config import settings
import app.database.mongodb as mongo_module
from app.services.clip_service import clip_service
from app.services.qdrant_service import qdrant_service


def create_room_image_bytes(color=(210, 190, 160), size=(640, 480)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


async def setup_environment():
    print("[SETUP] MongoDB...", flush=True)
    try:
        import pymongo
        client = pymongo.MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        print(f"  [OK] Live MongoDB at {settings.MONGODB_URL}", flush=True)
    except Exception as e:
        print(f"  [!] Using mongomock ({e})", flush=True)
        from mongomock_motor import AsyncMongoMockClient
        mock_client = AsyncMongoMockClient()
        mongo_module.db_manager.client = mock_client
        mongo_module.db_manager.db = mock_client[settings.MONGODB_DATABASE]

    await mongo_module.init_db()

    print("[SETUP] Qdrant...", flush=True)
    try:
        qdrant_service.connect_qdrant(force_reconnect=True)
        print(f"  [OK] Live Qdrant at {settings.QDRANT_URL}", flush=True)
    except Exception as e:
        print(f"  [!] Using in-memory Qdrant ({e})", flush=True)
        import qdrant_client
        qdrant_service.client = qdrant_client.QdrantClient(":memory:")

    clip_service.load_model()
    dim = clip_service.get_embedding_dimension()
    qdrant_service.create_collection(vector_size=dim)
    print(f"  [OK] OpenCLIP ready (dim={dim})", flush=True)

    # Ensure catalog vectors exist for recommendation tests
    print("[SETUP] Indexing catalog products into Qdrant...", flush=True)
    from app.ingestion.index_products import index_all_products
    index_result = index_all_products()
    print(f"  [OK] Indexed: {index_result}", flush=True)


async def run_customer_flow_tests():
    print("=" * 75, flush=True)
    print("   DECORE AI - CUSTOMER AI DESIGN FLOW E2E TEST", flush=True)
    print("=" * 75, flush=True)

    await setup_environment()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=120.0) as client:
        # ---------------------------------------------------------
        # 1. Customer register + login
        # ---------------------------------------------------------
        print("\n[1] Customer register/login...", flush=True)
        email = f"customer_flow_{int(time.time())}@decore.ai"
        reg = await client.post("/api/auth/register", json={
            "name": "Flow Customer",
            "email": email,
            "password": "CustomerPass123!",
            "role": "customer"
        })
        assert reg.status_code == 201, reg.text
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = await client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["role"] == "customer"
        print("  [OK] Customer auth working", flush=True)

        # ---------------------------------------------------------
        # 2-4. Analyze room
        # ---------------------------------------------------------
        print("\n[2-4] Room upload + Vision analysis...", flush=True)
        room_bytes = create_room_image_bytes()
        analyze = await client.post(
            "/api/design/analyze-room",
            headers=headers,
            files={"file": ("living_room_test.jpg", room_bytes, "image/jpeg")},
            data={"style": "Modern Contemporary"}
        )
        assert analyze.status_code == 200, analyze.text
        analyze_data = analyze.json()
        room_analysis = analyze_data["room_analysis"]
        room_path = analyze_data["room_image_path"]

        required_fields = [
            "room_type", "wall_color", "floor", "lighting",
            "existing_furniture", "dominant_colors", "design_style",
            "room_features", "description"
        ]
        for field in required_fields:
            assert field in room_analysis, f"Missing room analysis field: {field}"

        assert room_path.startswith("uploads/rooms/"), room_path
        assert (settings.BASE_DIR / room_path).exists()
        print(f"  [OK] Structured analysis: room_type={room_analysis['room_type']}", flush=True)
        print(f"  [OK] Saved room image: {room_path}", flush=True)
        if settings.GROQ_API_KEY:
            print("  [OK] Groq Vision API key present (live/fallback path exercised)", flush=True)
        else:
            print("  [OK] Groq key absent — heuristic Vision fallback used (expected)", flush=True)

        # ---------------------------------------------------------
        # 5-9. Budget-aware recommendations
        # ---------------------------------------------------------
        print("\n[5-9] Budget-aware product recommendations...", flush=True)
        budget = 95000
        categories = ["sofa", "curtain", "lighting", "decor"]
        recommend = await client.post("/api/design/recommend-products", json={
            "room_analysis": room_analysis,
            "style": "Modern Contemporary",
            "budget": budget,
            "categories": categories,
            "room_image_path": room_path
        })
        assert recommend.status_code == 200, recommend.text
        rec = recommend.json()

        assert "search_query" in rec
        assert "INR" not in rec["search_query"] and "95000" not in rec["search_query"], (
            f"Budget should not be embedded in CLIP search text: {rec['search_query']}"
        )
        assert rec["budget"] == budget
        assert "estimated_total" in rec
        assert "budget_remaining" in rec
        assert rec["budget_status"] in {"within_budget", "slightly_over_budget", "exceeds_budget"}
        assert isinstance(rec["recommended_products"], list)
        assert len(rec["recommended_products"]) > 0, "Expected at least one recommended product"

        total = 0.0
        for p in rec["recommended_products"]:
            for key in ["product_id", "seller_id", "name", "category", "price", "image_path", "score"]:
                assert key in p, f"Missing product field {key}"
            assert p["price"] > 0
            total += p["price"]

        assert abs(total - rec["estimated_total"]) < 0.01, (
            f"estimated_total {rec['estimated_total']} != sum {total}"
        )
        assert abs((budget - total) - rec["budget_remaining"]) < 0.01

        print(f"  [OK] Search query: {rec['search_query']}", flush=True)
        print(f"  [OK] Products: {len(rec['recommended_products'])}", flush=True)
        print(
            f"  [OK] Budget={budget}, total={rec['estimated_total']}, "
            f"remaining={rec['budget_remaining']}, status={rec['budget_status']}",
            flush=True
        )

        # ---------------------------------------------------------
        # 10-14. Prepare design with selected products
        # ---------------------------------------------------------
        print("\n[10-14] Prepare final design...", flush=True)
        selected = rec["recommended_products"]
        prepare = await client.post("/design/prepare", json={
            "room_analysis": room_analysis,
            "style": "Modern Contemporary",
            "budget": budget,
            "categories": categories,
            "selected_products": selected,
            "room_image_path": room_path
        })
        assert prepare.status_code == 200, prepare.text
        prep = prepare.json()

        assert prep.get("final_prompt")
        assert isinstance(prep.get("reference_images"), list)
        assert len(prep["reference_images"]) > 0
        assert isinstance(prep.get("selected_products"), list)
        assert prep.get("image_generation", {}).get("provider") == "mock"
        assert prep.get("image_generation", {}).get("status") == "ready"
        assert prep.get("original_room_image") == room_path
        assert prep.get("budget") == budget
        print("  [OK] Final prompt generated", flush=True)
        print(f"  [OK] Reference images: {prep['reference_images']}", flush=True)
        print(f"  [OK] Mock generation: {prep['image_generation']}", flush=True)

        # ---------------------------------------------------------
        # 15. Legacy /products/search still works
        # ---------------------------------------------------------
        print("\n[15] Legacy POST /products/search...", flush=True)
        search = await client.post("/products/search", json={
            "room_analysis": room_analysis,
            "style": "Modern Contemporary",
            "budget": budget,
            "categories": ["sofa", "curtain"]
        })
        assert search.status_code == 200, search.text
        search_data = search.json()
        assert "search_query" in search_data
        assert "products" in search_data
        print(f"  [OK] /products/search returned {len(search_data['products'])} products", flush=True)

    print("\n" + "=" * 75, flush=True)
    print("   CUSTOMER AI DESIGN FLOW E2E TESTS PASSED", flush=True)
    print("=" * 75, flush=True)


if __name__ == "__main__":
    asyncio.run(run_customer_flow_tests())
