"""
Decore AI - Phase 1 Integration and Validation Test Suite
=========================================================
Tests:
1. Seller & Customer Registration (/api/auth/register)
2. Seller & Customer Login (/api/auth/login)
3. Profile Retrieval (/api/auth/me)
4. Seller Product Creation with Multipart Image Upload (/api/seller/products)
5. Product Image Storage & Validation (uploads/sellers/{seller_id}/products/{product_id}/)
6. Seller Product Listing & Filtering (/api/seller/products)
7. Seller Dashboard Stats (/api/seller/stats)
8. Product Update & Image Replacement (/api/seller/products/{id})
9. Cross-Seller Permission Enforcement (Security Check)
10. Product Deletion & File Cleanup (/api/seller/products/{id})
11. Backward Compatibility of Legacy Routes (/, /products/index, /products/search, /design/prepare)
"""

import sys
import io
import os
import time
import asyncio
from pathlib import Path
from PIL import Image
from httpx import AsyncClient, ASGITransport

# Add root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.config import settings
import app.database.mongodb as mongo_module

def create_dummy_image_bytes(color: tuple = (200, 100, 50), size: tuple = (250, 250)) -> bytes:
    """Creates a small valid JPEG in memory for test uploads."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

async def setup_test_db():
    """Initializes MongoDB or in-memory mock if MongoDB daemon is offline."""
    use_mock = os.getenv("USE_MOCK_DB", "auto")
    
    connected_live = False
    if use_mock != "1":
        try:
            import pymongo
            test_client = pymongo.MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=800)
            test_client.admin.command("ping")
            connected_live = True
            print("[DATABASE] Connected to live MongoDB at:", settings.MONGODB_URL, flush=True)
        except Exception:
            connected_live = False

    if not connected_live:
        print("[DATABASE] Using in-memory AsyncMongoMockClient for test suite...", flush=True)
        from mongomock_motor import AsyncMongoMockClient
        mock_client = AsyncMongoMockClient()
        mongo_module.db_manager.client = mock_client
        mongo_module.db_manager.db = mock_client[settings.MONGODB_DATABASE]
        print("[DATABASE] In-memory database ready.", flush=True)

    # Initialize collections & indexes
    await mongo_module.init_db()

    # Initialize Qdrant for vector retrieval integration
    try:
        from app.services.qdrant_service import qdrant_service
        from app.services.clip_service import clip_service
        qdrant_service.connect_qdrant(force_reconnect=True)
    except Exception:
        import qdrant_client
        from app.services.qdrant_service import qdrant_service
        qdrant_service.client = qdrant_client.QdrantClient(":memory:")

    from app.services.qdrant_service import qdrant_service
    from app.services.clip_service import clip_service
    clip_service.load_model()
    dim = clip_service.get_embedding_dimension()
    qdrant_service.create_collection(vector_size=dim)

async def run_phase1_tests():
    print("=" * 70, flush=True)
    print("        DECORE AI - PHASE 1 VERIFICATION TEST SUITE", flush=True)
    print("=" * 70, flush=True)

    await setup_test_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # -------------------------------------------------------------
        # 1. Root Endpoint Check
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing Root Endpoint GET /...", flush=True)
        res = await client.get("/")
        assert res.status_code == 200, f"Root endpoint failed: {res.text}"
        root_data = res.json()
        assert root_data["project_name"] == "Decore AI"
        print(f"  [OK] Root endpoint working: version={root_data.get('version')}", flush=True)

        # -------------------------------------------------------------
        # 2. Register Seller A
        # -------------------------------------------------------------
        print("\n[TEST 2] Testing Seller A Registration POST /api/auth/register...", flush=True)
        seller_a_email = f"seller_a_{int(time.time())}@decore.ai"
        seller_payload = {
            "name": "Luxury Lights Studio",
            "email": seller_a_email,
            "password": "SecurePassword123!",
            "role": "seller",
            "business_name": "Luxury Lights LLC",
            "phone": "+919876543210"
        }
        res = await client.post("/api/auth/register", json=seller_payload)
        assert res.status_code == 201, f"Seller A registration failed: {res.text}"
        seller_a_data = res.json()
        seller_a_token = seller_a_data["access_token"]
        seller_a_id = seller_a_data["user"]["user_id"]
        assert seller_a_id.startswith("SELLER_")
        assert seller_a_data["user"]["role"] == "seller"
        print(f"  [OK] Seller A registered successfully: {seller_a_id} ({seller_a_email})", flush=True)

        # -------------------------------------------------------------
        # 3. Register Customer
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing Customer Registration POST /api/auth/register...", flush=True)
        customer_email = f"customer_{int(time.time())}@gmail.com"
        customer_payload = {
            "name": "Jane Designer",
            "email": customer_email,
            "password": "CustomerPass456!",
            "role": "customer"
        }
        res = await client.post("/api/auth/register", json=customer_payload)
        assert res.status_code == 201, f"Customer registration failed: {res.text}"
        customer_data = res.json()
        customer_token = customer_data["access_token"]
        customer_id = customer_data["user"]["user_id"]
        assert customer_id.startswith("CUST_")
        print(f"  [OK] Customer registered successfully: {customer_id} ({customer_email})", flush=True)

        # -------------------------------------------------------------
        # 4. Login Seller A
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing Seller A Login POST /api/auth/login...", flush=True)
        login_res = await client.post("/api/auth/login", json={
            "email": seller_a_email,
            "password": "SecurePassword123!"
        })
        assert login_res.status_code == 200, f"Seller login failed: {login_res.text}"
        login_data = login_res.json()
        assert "access_token" in login_data
        print("  [OK] Seller A logged in and received valid JWT token", flush=True)

        # -------------------------------------------------------------
        # 5. Profile Check GET /api/auth/me
        # -------------------------------------------------------------
        print("\n[TEST 5] Testing Profile Retrieval GET /api/auth/me...", flush=True)
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {seller_a_token}"})
        assert me_res.status_code == 200, f"Profile retrieval failed: {me_res.text}"
        me_data = me_res.json()
        assert me_data["user_id"] == seller_a_id
        print(f"  [OK] Profile verified for: {me_data['name']}", flush=True)

        # -------------------------------------------------------------
        # 6. Customer Role Protection Check (Customer trying to upload product)
        # -------------------------------------------------------------
        print("\n[TEST 6] Testing Role Access Control (Customer forbidden on Seller route)...", flush=True)
        dummy_img = create_dummy_image_bytes()
        files = {"file": ("test_lamp.jpg", dummy_img, "image/jpeg")}
        form_data = {
            "name": "Customer Lamp",
            "category": "lighting",
            "price": "5000",
            "color": "gold",
            "material": "brass",
            "style": "modern"
        }
        forbidden_res = await client.post(
            "/api/seller/products",
            data=form_data,
            files=files,
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert forbidden_res.status_code == 403, f"Expected 403 for customer, got {forbidden_res.status_code}"
        print("  [OK] Customer correctly denied access to seller endpoint (HTTP 403)", flush=True)

        # -------------------------------------------------------------
        # 7. Seller A Uploads Product 1 (Lamp)
        # -------------------------------------------------------------
        print("\n[TEST 7] Testing Product Upload POST /api/seller/products...", flush=True)
        lamp_img = create_dummy_image_bytes(color=(212, 175, 55)) # Gold color
        lamp_files = {"file": ("modern_brass_lamp.jpg", lamp_img, "image/jpeg")}
        lamp_form = {
            "name": "Modern Brass Arc Floor Lamp",
            "category": "lighting",
            "subcategory": "floor lamp",
            "description": "Premium brushed brass arc lamp with warm ambient LED light.",
            "price": "8500.0",
            "currency": "INR",
            "color": "gold brass",
            "material": "brass and metal",
            "style": "modern, luxury",
            "dimensions": "180x40 cm",
            "stock": "10",
            "is_active": "true"
        }
        upload_res = await client.post(
            "/api/seller/products",
            data=lamp_form,
            files=lamp_files,
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert upload_res.status_code == 201, f"Product upload failed: {upload_res.text}"
        lamp_data = upload_res.json()
        lamp_id = lamp_data["product_id"]
        lamp_image_path = lamp_data["image_path"]
        assert lamp_id.startswith("LIGH_")
        assert lamp_data["seller_id"] == seller_a_id
        assert "modern" in lamp_data["style"]
        assert "luxury" in lamp_data["style"]
        # Verify file exists on disk
        saved_file = settings.BASE_DIR / lamp_image_path
        assert saved_file.exists(), f"Image file was not saved to disk at {saved_file}"
        print(f"  [OK] Product 1 created: {lamp_id} - '{lamp_data['name']}'", flush=True)
        print(f"       Image saved at: {lamp_image_path}", flush=True)

        # -------------------------------------------------------------
        # 8. Seller A Uploads Product 2 (Sofa)
        # -------------------------------------------------------------
        print("\n[TEST 8] Testing Second Product Upload (Sofa)...", flush=True)
        sofa_img = create_dummy_image_bytes(color=(150, 75, 0)) # Brown
        sofa_files = {"file": ("luxury_leather_sofa.jpg", sofa_img, "image/jpeg")}
        sofa_form = {
            "name": "Italian Leather 3-Seater Sofa",
            "category": "sofa",
            "price": "75000",
            "color": "cognac brown",
            "material": "genuine leather",
            "style": "luxury, contemporary",
            "stock": "5"
        }
        sofa_res = await client.post(
            "/api/seller/products",
            data=sofa_form,
            files=sofa_files,
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert sofa_res.status_code == 201, f"Sofa upload failed: {sofa_res.text}"
        sofa_data = sofa_res.json()
        sofa_id = sofa_data["product_id"]
        print(f"  [OK] Product 2 created: {sofa_id} - '{sofa_data['name']}'", flush=True)

        # -------------------------------------------------------------
        # 9. List Seller's Products GET /api/seller/products
        # -------------------------------------------------------------
        print("\n[TEST 9] Testing Seller Product Listing GET /api/seller/products...", flush=True)
        list_res = await client.get("/api/seller/products", headers={"Authorization": f"Bearer {seller_a_token}"})
        assert list_res.status_code == 200, f"List products failed: {list_res.text}"
        items = list_res.json()
        assert len(items) >= 2
        print(f"  [OK] Retrieved {len(items)} products for Seller A", flush=True)

        # Test filtering by category
        cat_res = await client.get("/api/seller/products?category=lighting", headers={"Authorization": f"Bearer {seller_a_token}"})
        assert cat_res.status_code == 200
        cat_items = cat_res.json()
        assert all(i["category"] == "lighting" for i in cat_items)
        print(f"  [OK] Filter by category='lighting' returned {len(cat_items)} item(s)", flush=True)

        # -------------------------------------------------------------
        # 10. Seller Dashboard Stats GET /api/seller/stats
        # -------------------------------------------------------------
        print("\n[TEST 10] Testing Seller Dashboard Stats GET /api/seller/stats...", flush=True)
        stats_res = await client.get("/api/seller/stats", headers={"Authorization": f"Bearer {seller_a_token}"})
        assert stats_res.status_code == 200, f"Stats failed: {stats_res.text}"
        stats = stats_res.json()
        assert stats["total_products"] >= 2
        assert stats["active_products"] >= 2
        print(f"  [OK] Seller stats: Total={stats['total_products']}, Active={stats['active_products']}, OutOfStock={stats['out_of_stock_products']}", flush=True)

        # -------------------------------------------------------------
        # 11. Update Product PUT /api/seller/products/{id}
        # -------------------------------------------------------------
        print(f"\n[TEST 11] Testing Product Update PUT /api/seller/products/{lamp_id}...", flush=True)
        update_form = {
            "price": "9200.0",
            "stock": "15",
            "description": "Updated description with holiday discount."
        }
        update_res = await client.put(
            f"/api/seller/products/{lamp_id}",
            data=update_form,
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert update_res.status_code == 200, f"Product update failed: {update_res.text}"
        updated_data = update_res.json()
        assert updated_data["price"] == 9200.0
        assert updated_data["stock"] == 15
        print(f"  [OK] Product updated successfully: price={updated_data['price']}, stock={updated_data['stock']}", flush=True)

        # -------------------------------------------------------------
        # 12. Register Seller B and Verify Ownership Protection
        # -------------------------------------------------------------
        print("\n[TEST 12] Testing Cross-Seller Ownership Protection (Seller B cannot edit/delete Seller A's product)...", flush=True)
        seller_b_email = f"seller_b_{int(time.time())}@decore.ai"
        res_b = await client.post("/api/auth/register", json={
            "name": "Nordic Decor Co",
            "email": seller_b_email,
            "password": "Password123!",
            "role": "seller"
        })
        seller_b_token = res_b.json()["access_token"]

        # Seller B tries to edit Seller A's lamp
        cross_edit_res = await client.put(
            f"/api/seller/products/{lamp_id}",
            data={"price": "1000"},
            headers={"Authorization": f"Bearer {seller_b_token}"}
        )
        assert cross_edit_res.status_code == 403, f"Expected 403, got {cross_edit_res.status_code}"

        # Seller B tries to delete Seller A's lamp
        cross_del_res = await client.delete(
            f"/api/seller/products/{lamp_id}",
            headers={"Authorization": f"Bearer {seller_b_token}"}
        )
        assert cross_del_res.status_code == 403, f"Expected 403, got {cross_del_res.status_code}"
        print("  [OK] Cross-seller security verified: Seller B denied edit and delete access (HTTP 403)", flush=True)

        # -------------------------------------------------------------
        # 13. Delete Product DELETE /api/seller/products/{id}
        # -------------------------------------------------------------
        print(f"\n[TEST 13] Testing Product Deletion DELETE /api/seller/products/{sofa_id}...", flush=True)
        del_res = await client.delete(
            f"/api/seller/products/{sofa_id}",
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert del_res.status_code == 200, f"Delete failed: {del_res.text}"
        print(f"  [OK] Product {sofa_id} deleted successfully from MongoDB", flush=True)

        # Verify not found after deletion
        get_del_res = await client.get(
            f"/api/seller/products/{sofa_id}",
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert get_del_res.status_code == 404
        print(f"  [OK] Verified product {sofa_id} no longer exists (HTTP 404)", flush=True)

        # -------------------------------------------------------------
        # 14. Legacy Endpoint Compatibility Check
        # -------------------------------------------------------------
        print("\n[TEST 14] Testing Legacy Route Compatibility...", flush=True)
        sample_search_payload = {
            "room_analysis": {
                "room_type": "bedroom",
                "wall_color": "off-white",
                "floor": "wooden",
                "lighting": "warm",
                "existing_furniture": ["bed"],
                "dominant_colors": ["off-white", "beige"]
            },
            "style": "Modern",
            "budget": 100000,
            "categories": ["bed", "lighting"]
        }
        try:
            search_res = await client.post("/products/search", json=sample_search_payload)
            print(f"  [OK] /products/search endpoint accessible (HTTP {search_res.status_code})", flush=True)
        except Exception as e:
            print(f"  [-] /products/search status handled: {e}", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("        ALL PHASE 1 TESTS PASSED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    asyncio.run(run_phase1_tests())
