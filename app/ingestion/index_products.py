"""
Product Ingestion Script
========================
This module reads product catalog metadata from `data/products.json`, loads product images,
generates CLIP image embedding vectors, and indexes them into Qdrant vector database along with metadata payloads.

Can be run as a standalone CLI script (`python -m app.ingestion.index_products`) or triggered via FastAPI POST /products/index endpoint.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

from app.config import settings
from app.services.clip_service import clip_service
from app.services.qdrant_service import qdrant_service
from scripts.create_sample_products import generate_sample_images, generate_products_json

def index_all_products() -> Dict[str, Any]:
    """
    Reads catalog products, generates CLIP image embeddings, ensures Qdrant collection,
    and indexes all products with payload metadata into Qdrant.
    """
    json_path = settings.DATA_PATH

    # Ensure dataset and sample images exist
    if not json_path.exists():
        print(f"[Ingestion] Catalog file {json_path} not found. Generating sample products...")
        generate_sample_images()
        generate_products_json()

    # Read product catalog JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            products_list = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read product catalog JSON at {json_path}: {str(e)}")

    if not products_list:
        raise ValueError("Product catalog in products.json is empty!")

    print("\nIndexing products...")
    
    # Pre-load CLIP model & get dynamic vector dimension
    clip_service.load_model()
    vector_dim = clip_service.get_embedding_dimension()

    # Ensure Qdrant collection exists with matching vector size
    qdrant_service.create_collection(vector_size=vector_dim)

    image_vectors = []
    processed_products = []

    total = len(products_list)
    for index, product in enumerate(products_list, start=1):
        product_id = product.get("product_id", f"PROD_{index}")
        img_rel_path = product.get("image_path", "")
        img_full_path = settings.BASE_DIR / img_rel_path

        print(f"[{index}/{total}] {product_id} - {product.get('name', 'Unknown')}")

        # Ensure image file exists (generate placeholder if missing)
        if not img_full_path.exists():
            print(f"  [!] Warning: Image missing at {img_rel_path}. Generating placeholder...")
            generate_sample_images()

        try:
            # Encode product image into CLIP vector space
            vector = clip_service.encode_image(img_full_path)
            image_vectors.append(vector)
            processed_products.append(product)
        except Exception as e:
            print(f"  [X] Error encoding image for {product_id}: {str(e)}")

    if not image_vectors:
        raise RuntimeError("No product images could be successfully encoded.")

    # Upsert all vectors & payload metadata into Qdrant
    qdrant_service.upsert_products(
        products_data=processed_products,
        vectors=image_vectors
    )

    print("Products indexed successfully.\n")
    return {
        "message": "Products indexed successfully",
        "count": len(processed_products)
    }

if __name__ == "__main__":
    index_all_products()
