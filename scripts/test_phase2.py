"""
Decore AI - Phase 2 Automatic OpenCLIP Embeddings & Qdrant Sync Test Suite
==========================================================================
Tests the full lifecycle of seller products synchronized with OpenCLIP and Qdrant:
A. Register seller
B. Login seller
C. Upload product image + metadata (POST /api/seller/products)
D. Verify MongoDB product document exists
E. Verify Qdrant point exists with deterministic UUID5 point ID
F. Verify Qdrant payload has all required multi-vendor fields:
   product_id, seller_id, name, category, subcategory, description, price, currency,
   color, material, style (list), dimensions, stock, image_path, is_active
G. Perform semantic vector search (POST /products/search)
H. Confirm uploaded product appears in search results with cosine similarity score
I. Update product metadata only (PUT /api/seller/products/{id})
J. Verify Qdrant payload updates without re-generating vector embedding
K. Replace product image (PUT /api/seller/products/{id} with new file)
L. Verify vector is re-generated in Qdrant with new embedding values
M. Delete product (DELETE /api/seller/products/{id})
N. Verify MongoDB product is deleted
O. Verify Qdrant point is deleted
P. Verify product image file is deleted from uploads
Q. Verify cross-seller ownership security (Seller B cannot update/delete Seller A's product)
R. Verify active product filtering in semantic search
"""

import sys
import io
import os
import time
import asyncio
import numpy as np
from pathlib import Path
from PIL import Image
from httpx import AsyncClient, ASGITransport

# Add root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.config import settings
import app.database.mongodb as mongo_module
from app.services.clip_service import clip_service
from app.services.qdrant_service import qdrant_service

def create_test_image_bytes(color: tuple = (180, 120, 60), size: tuple = (300, 300)) -> bytes:
    """Creates a distinct test JPEG in memory."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

async def setup_test_environment():
    """Initializes MongoDB and Qdrant connections."""
    print("[SETUP] Verifying MongoDB connection...", flush=True)
    try:
        import pymongo
        test_client = pymongo.MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        test_client.admin.command("ping")
        print(f"  [OK] Connected to live MongoDB at: {settings.MONGODB_URL}", flush=True)
    except Exception as e:
        print(f"  [!] Live MongoDB not reachable ({e}), using mock...", flush=True)
        from mongomock_motor import AsyncMongoMockClient
        mock_client = AsyncMongoMockClient()
        mongo_module.db_manager.client = mock_client
        mongo_module.db_manager.db = mock_client[settings.MONGODB_DATABASE]

    await mongo_module.init_db()

    print("[SETUP] Verifying Qdrant connection...", flush=True)
    try:
        qdrant_service.connect_qdrant(force_reconnect=True)
        print(f"  [OK] Connected to live Qdrant at: {settings.QDRANT_URL}", flush=True)
    except Exception as e:
        print(f"  [!] Live Qdrant not reachable ({e}), using in-memory Qdrant engine for tests...", flush=True)
        import qdrant_client
        qdrant_service.client = qdrant_client.QdrantClient(":memory:")

    clip_service.load_model()
    dim = clip_service.get_embedding_dimension()
    qdrant_service.create_collection(vector_size=dim)
    print(f"  [OK] Qdrant collection ready (Vector Dimension: {dim})", flush=True)

async def run_phase2_tests():
    print("=" * 75, flush=True)
    print("       DECORE AI - PHASE 2 INTEGRATION & VALIDATION TEST SUITE", flush=True)
    print("=" * 75, flush=True)

    await setup_test_environment()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # -------------------------------------------------------------
        # Step A & B: Register & Login Seller A
        # -------------------------------------------------------------
        print("\n[STEP A & B] Registering and Logging in Seller A...", flush=True)
        seller_a_email = f"seller_phase2_{int(time.time())}@decore.ai"
        reg_payload = {
            "name": "Emerald Studio",
            "email": seller_a_email,
            "password": "PasswordPhase2!",
            "role": "seller",
            "business_name": "Emerald Furnishings Pvt Ltd",
            "phone": "+919876543210"
        }
        reg_res = await client.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code == 201, f"Seller registration failed: {reg_res.text}"
        seller_a_data = reg_res.json()
        seller_a_token = seller_a_data["access_token"]
        seller_a_id = seller_a_data["user"]["user_id"]
        print(f"  [OK] Seller A registered & authenticated: ID={seller_a_id}, Email={seller_a_email}", flush=True)

        # -------------------------------------------------------------
        # Step C: Upload Product with Image and Metadata (POST /api/seller/products)
        # -------------------------------------------------------------
        print("\n[STEP C] Seller A Uploads Product (POST /api/seller/products)...", flush=True)
        # Green velvet armchair
        armchair_img = create_test_image_bytes(color=(34, 139, 34), size=(250, 250))
        upload_files = {"file": ("emerald_armchair.jpg", armchair_img, "image/jpeg")}
        upload_form = {
            "name": "Emerald Velvet Accent Armchair",
            "category": "sofa",
            "subcategory": "armchair",
            "description": "Luxurious emerald green velvet accent armchair with gold legs.",
            "price": "24999.0",
            "currency": "INR",
            "color": "emerald green",
            "material": "velvet and brass",
            "style": "luxury, modern, contemporary",
            "dimensions": "85x80x90 cm",
            "stock": "8",
            "is_active": "true"
        }
        upload_res = await client.post(
            "/api/seller/products",
            data=upload_form,
            files=upload_files,
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert upload_res.status_code == 201, f"Product upload failed: {upload_res.text}"
        product = upload_res.json()
        product_id = product["product_id"]
        saved_image_path = product["image_path"]
        print(f"  [OK] Product created: {product_id} - '{product['name']}'", flush=True)
        print(f"       Saved image: {saved_image_path}", flush=True)

        # -------------------------------------------------------------
        # Step D: Verify MongoDB Product Record
        # -------------------------------------------------------------
        print("\n[STEP D] Verifying MongoDB product record...", flush=True)
        products_col = mongo_module.get_products_collection()
        mongo_doc = await products_col.find_one({"product_id": product_id})
        assert mongo_doc is not None, f"Product {product_id} not found in MongoDB!"
        assert mongo_doc["seller_id"] == seller_a_id
        assert mongo_doc["name"] == "Emerald Velvet Accent Armchair"
        assert mongo_doc["category"] == "sofa"
        assert mongo_doc["price"] == 24999.0
        assert mongo_doc["is_active"] is True
        print(f"  [OK] MongoDB document verified: {mongo_doc['product_id']} owned by {mongo_doc['seller_id']}", flush=True)

        # -------------------------------------------------------------
        # Step E: Verify Qdrant Point Exists with Deterministic UUID5 ID
        # -------------------------------------------------------------
        print("\n[STEP E] Verifying Qdrant Point & Deterministic UUID5 ID...", flush=True)
        expected_point_id = qdrant_service.get_point_id(product_id)
        qdrant_point = qdrant_service.get_product_point(product_id)
        assert qdrant_point is not None, f"Point for product {product_id} not found in Qdrant!"
        assert qdrant_point["id"] == expected_point_id, f"Point ID mismatch: got {qdrant_point['id']}, expected {expected_point_id}"
        
        vector = qdrant_point.get("vector")
        assert vector is not None, "Vector is missing in Qdrant point!"
        assert len(vector) == 512, f"Expected 512-dim vector, got {len(vector)}"
        initial_vector = list(vector)
        print(f"  [OK] Qdrant point verified: Point ID={expected_point_id}", flush=True)
        print(f"       Vector dimension={len(vector)} (512-d OpenCLIP ViT-B-32)", flush=True)

        # -------------------------------------------------------------
        # Step F: Verify Qdrant Payload Contains All Required Fields
        # -------------------------------------------------------------
        print("\n[STEP F] Verifying Qdrant Payload Schema & Multi-vendor Fields...", flush=True)
        payload = qdrant_point["payload"]
        assert payload["product_id"] == product_id
        assert payload["seller_id"] == seller_a_id
        assert payload["name"] == "Emerald Velvet Accent Armchair"
        assert payload["category"] == "sofa"
        assert payload["subcategory"] == "armchair"
        assert payload["description"] == "Luxurious emerald green velvet accent armchair with gold legs."
        assert payload["price"] == 24999.0
        assert payload["currency"] == "INR"
        assert payload["color"] == "emerald green"
        assert payload["material"] == "velvet and brass"
        assert isinstance(payload["style"], list)
        assert "luxury" in payload["style"]
        assert "modern" in payload["style"]
        assert payload["dimensions"] == "85x80x90 cm"
        assert payload["stock"] == 8
        assert payload["image_path"] == saved_image_path
        assert payload["is_active"] is True
        print(f"  [OK] All 15 required payload fields verified in Qdrant point payload:", flush=True)
        for k, v in payload.items():
            print(f"       - {k}: {v}", flush=True)

        # -------------------------------------------------------------
        # Step G & H: Semantic Vector Search & Retrieval of Uploaded Product
        # -------------------------------------------------------------
        print("\n[STEP G & H] Testing Semantic Vector Search (POST /products/search)...", flush=True)
        search_req = {
            "room_analysis": {
                "room_type": "living room",
                "wall_color": "warm white",
                "floor": "hardwood",
                "lighting": "warm",
                "existing_furniture": ["coffee table"],
                "dominant_colors": ["emerald green", "gold", "white"]
            },
            "style": "Luxury Modern",
            "budget": 50000.0,
            "categories": ["sofa"]
        }
        search_res = await client.post("/products/search", json=search_req)
        assert search_res.status_code == 200, f"Search failed: {search_res.text}"
        search_data = search_res.json()
        print(f"  [OK] Generated Search Query: \"{search_data['search_query']}\"", flush=True)
        found_products = search_data["products"]
        assert len(found_products) > 0, "No products returned in search results!"
        
        # Check if our uploaded emerald armchair is retrieved
        matched_ids = [p["product_id"] for p in found_products]
        print(f"  [OK] Retrieved products: {matched_ids}", flush=True)
        assert product_id in matched_ids, f"Uploaded product {product_id} was not returned in search results {matched_ids}"
        
        target_hit = next(p for p in found_products if p["product_id"] == product_id)
        assert target_hit["seller_id"] == seller_a_id
        assert target_hit["score"] > 0.0
        print(f"  [OK] Uploaded product '{target_hit['name']}' successfully matched with score {target_hit['score']:.4f}", flush=True)

        # -------------------------------------------------------------
        # Step I & J: Update Product Metadata Only (Vector Preserved)
        # -------------------------------------------------------------
        print("\n[STEP I & J] Testing Metadata-Only Update (PUT /api/seller/products/{id})...", flush=True)
        update_form = {
            "name": "Emerald Velvet Accent Armchair (Special Edition)",
            "price": "22500.0",
            "stock": "12",
            "description": "Updated holiday special price."
        }
        update_res = await client.put(
            f"/api/seller/products/{product_id}",
            data=update_form,
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert update_res.status_code == 200, f"Update failed: {update_res.text}"
        updated_product = update_res.json()
        assert updated_product["price"] == 22500.0
        assert updated_product["stock"] == 12

        # Verify Qdrant payload is updated
        updated_point = qdrant_service.get_product_point(product_id)
        assert updated_point is not None
        assert updated_point["payload"]["price"] == 22500.0
        assert updated_point["payload"]["stock"] == 12
        assert updated_point["payload"]["name"] == "Emerald Velvet Accent Armchair (Special Edition)"
        
        # Verify vector was NOT changed (exact match)
        vector_after_meta_update = updated_point["vector"]
        assert np.allclose(initial_vector, vector_after_meta_update, atol=1e-5), "Vector should remain identical when only metadata is updated!"
        print("  [OK] Metadata updated in Qdrant payload without re-generating vector embedding.", flush=True)

        # -------------------------------------------------------------
        # Step K & L: Replace Product Image (Vector Re-generated)
        # -------------------------------------------------------------
        print("\n[STEP K & L] Testing Product Image Replacement (PUT /api/seller/products/{id})...", flush=True)
        # Create a new distinctly colored image (Bright Blue)
        new_blue_img = create_test_image_bytes(color=(0, 100, 220), size=(250, 250))
        new_img_files = {"file": ("blue_armchair.jpg", new_blue_img, "image/jpeg")}
        new_img_form = {
            "color": "sapphire blue"
        }
        img_update_res = await client.put(
            f"/api/seller/products/{product_id}",
            data=new_img_form,
            files=new_img_files,
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert img_update_res.status_code == 200, f"Image update failed: {img_update_res.text}"
        img_updated_product = img_update_res.json()
        new_image_path = img_updated_product["image_path"]
        assert new_image_path != saved_image_path, "New image path should differ from old image path!"
        assert (settings.BASE_DIR / new_image_path).exists(), "New image file does not exist on disk!"
        assert not (settings.BASE_DIR / saved_image_path).exists(), "Old image file should be cleaned up!"

        # Verify Qdrant vector has been re-generated
        point_after_img_update = qdrant_service.get_product_point(product_id)
        assert point_after_img_update is not None
        new_vector = point_after_img_update["vector"]
        assert not np.allclose(initial_vector, new_vector, atol=1e-3), "Vector MUST change when image is replaced!"
        assert point_after_img_update["payload"]["color"] == "sapphire blue"
        assert point_after_img_update["payload"]["image_path"] == new_image_path
        print(f"  [OK] Vector successfully re-generated in Qdrant after image update.", flush=True)
        print(f"       New image path: {new_image_path}", flush=True)

        # -------------------------------------------------------------
        # Step Q: Cross-Seller Security Check
        # -------------------------------------------------------------
        print("\n[STEP Q] Testing Cross-Seller Ownership Protection...", flush=True)
        seller_b_email = f"seller_b_sec_{int(time.time())}@decore.ai"
        reg_b_res = await client.post("/api/auth/register", json={
            "name": "Nordic Interiors",
            "email": seller_b_email,
            "password": "PasswordB123!",
            "role": "seller"
        })
        seller_b_token = reg_b_res.json()["access_token"]
        
        # Seller B attempts to edit Seller A's product
        cross_edit = await client.put(
            f"/api/seller/products/{product_id}",
            data={"price": "100"},
            headers={"Authorization": f"Bearer {seller_b_token}"}
        )
        assert cross_edit.status_code == 403, f"Expected 403, got {cross_edit.status_code}"

        # Seller B attempts to delete Seller A's product
        cross_del = await client.delete(
            f"/api/seller/products/{product_id}",
            headers={"Authorization": f"Bearer {seller_b_token}"}
        )
        assert cross_del.status_code == 403, f"Expected 403, got {cross_del.status_code}"
        print("  [OK] Cross-seller security verified (HTTP 403 Forbidden for unauthorized modifications).", flush=True)

        # -------------------------------------------------------------
        # Step R: Active Status Filtering Check
        # -------------------------------------------------------------
        print("\n[STEP R] Testing is_active Filter Synchronization...", flush=True)
        # Deactivate the product
        deact_res = await client.put(
            f"/api/seller/products/{product_id}",
            data={"is_active": "false"},
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert deact_res.status_code == 200
        
        # Verify search excludes deactivated product
        deact_search_res = await client.post("/products/search", json=search_req)
        assert deact_search_res.status_code == 200
        deact_found_ids = [p["product_id"] for p in deact_search_res.json()["products"]]
        assert product_id not in deact_found_ids, f"Deactivated product {product_id} should NOT appear in search!"
        print(f"  [OK] Deactivated product correctly excluded from semantic search results.", flush=True)

        # -------------------------------------------------------------
        # Step M, N, O, P: Delete Product & Verify Cleanup across Layers
        # -------------------------------------------------------------
        print("\n[STEP M, N, O, P] Testing Product Deletion & Multi-Layer Cleanup...", flush=True)
        del_res = await client.delete(
            f"/api/seller/products/{product_id}",
            headers={"Authorization": f"Bearer {seller_a_token}"}
        )
        assert del_res.status_code == 200, f"Delete failed: {del_res.text}"
        print(f"  [OK] Product {product_id} deleted via DELETE /api/seller/products/{product_id}", flush=True)

        # N: Verify MongoDB document is deleted
        mongo_check = await products_col.find_one({"product_id": product_id})
        assert mongo_check is None, "Product document still exists in MongoDB!"
        print("  [OK] Layer 1 (MongoDB): Product document successfully deleted.", flush=True)

        # O: Verify Qdrant point is deleted
        qdrant_check = qdrant_service.get_product_point(product_id)
        assert qdrant_check is None, "Product vector point still exists in Qdrant!"
        print("  [OK] Layer 2 (Qdrant): Vector point successfully deleted (No orphan vectors).", flush=True)

        # P: Verify image file is deleted from filesystem
        assert not (settings.BASE_DIR / new_image_path).exists(), "Image file still exists on filesystem!"
        print(f"  [OK] Layer 3 (Filesystem): Image file deleted successfully from uploads.", flush=True)

    print("\n" + "=" * 75, flush=True)
    print("    ALL PHASE 2 TESTS PASSED! FULL PIPELINE VERIFIED SUCCESSFULLY!")
    print("=" * 75, flush=True)

if __name__ == "__main__":
    asyncio.run(run_phase2_tests())
