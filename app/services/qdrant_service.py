"""
Qdrant Vector Database Service
==============================
Why Combine Vector Similarity with Payload Metadata Filters?
------------------------------------------------------------
Vector similarity (e.g. CLIP cosine distance) measures semantic & visual style match:
"Does this product look like a luxury modern beige velvet item?"

However, vector embeddings CANNOT enforce strict hard business rules such as:
1. "Only return products in the category 'bed'" (Vector similarity alone might return a matching sofa or lamp if it shares the same color/vibe!)
2. "Only return products under 50,000 INR budget" (A $500,000 luxury bed and a $40,000 luxury bed look visually identical to CLIP, so their vector embeddings are almost identical!)

Therefore, Qdrant allows us to perform HYBRID RETRIEVAL:
- Qdrant Payload Filter: Hard filtering (e.g., category == "bed", price <= budget, is_active != False)
- Qdrant Vector Search: Ranks the filtered items by visual & semantic style match.
"""
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings


import os

class QdrantService:
    def __init__(self):
        self.client: Optional[QdrantClient] = None

    def connect_qdrant(self, force_reconnect: bool = False) -> QdrantClient:
        """
        Establishes connection to the local Qdrant Vector Database instance.
        If force_reconnect is True, re-creates the client connection.
        """
        if self.client is None or force_reconnect:
            try:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    timeout=10
                )
                # Quick health check
                self.client.get_collections()
            except Exception as e:
                if os.getenv("USE_MOCK_QDRANT", "") == "1":
                    print(f"[QdrantService] Using in-memory Qdrant instance (USE_MOCK_QDRANT=1)")
                    self.client = QdrantClient(":memory:")
                else:
                    raise ConnectionError(
                        f"Unable to connect to Qdrant at "
                        f"{settings.QDRANT_URL}. "
                        "Make sure Qdrant is running via Docker or set USE_MOCK_QDRANT=1. "
                        f"Error details: {str(e)}"
                    )

        return self.client

    def _execute_with_retry(self, operation):
        """
        Executes a Qdrant client operation with automatic single retry on stale connection.
        """
        try:
            return operation(self.connect_qdrant())
        except Exception as e:
            if self.client is not None and getattr(self.client, "_location", None) == ":memory:":
                return operation(self.client)
            # Reconnect and retry once
            client = self.connect_qdrant(force_reconnect=True)
            return operation(client)

    def create_collection(
        self,
        vector_size: int,
        collection_name: Optional[str] = None
    ):
        """
        Creates a Qdrant collection if it does not already exist.
        Uses Cosine similarity for vector search.
        """
        coll_name = (
            collection_name
            or settings.QDRANT_COLLECTION
        )

        def _op(client: QdrantClient):
            exists = client.collection_exists(
                collection_name=coll_name
            )

            if not exists:
                print(
                    f"[QdrantService] Creating collection "
                    f"'{coll_name}' with vector size "
                    f"{vector_size} (Cosine Distance)..."
                )

                client.create_collection(
                    collection_name=coll_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )

                print(
                    f"[QdrantService] Collection "
                    f"'{coll_name}' created successfully."
                )
            else:
                print(
                    f"[QdrantService] Collection "
                    f"'{coll_name}' already exists."
                )

        try:
            self._execute_with_retry(_op)
        except Exception as e:
            raise RuntimeError(
                f"Error creating Qdrant collection '{coll_name}': {str(e)}"
            )

    @staticmethod
    def get_point_id(product_id: str) -> str:
        """
        Generates a deterministic/stable UUID5 point ID derived from product_id.
        Ensures consistent point ID across product creation, updates, and deletion.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(product_id).strip()))

    def build_payload(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs a standardized Qdrant payload dictionary matching Phase 2 specifications.
        """
        styles = product_data.get("style", [])
        if isinstance(styles, str):
            cleaned = styles.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
            styles = [s.strip().lower() for s in cleaned.split(",") if s.strip()]
        elif isinstance(styles, list):
            styles = [str(s).strip().lower() for s in styles if str(s).strip()]
        else:
            styles = []

        return {
            "product_id": str(product_data.get("product_id", "")),
            "seller_id": str(product_data.get("seller_id", "SYSTEM")),
            "name": str(product_data.get("name", "")),
            "category": str(product_data.get("category", "")).lower().strip(),
            "subcategory": product_data.get("subcategory"),
            "description": str(product_data.get("description", "") or ""),
            "price": float(product_data.get("price", 0.0)),
            "currency": str(product_data.get("currency", "INR")).upper(),
            "color": str(product_data.get("color", "")).lower().strip(),
            "material": str(product_data.get("material", "")).lower().strip(),
            "style": styles,
            "dimensions": product_data.get("dimensions"),
            "stock": int(product_data.get("stock", 1)),
            "image_path": str(product_data.get("image_path", "")),
            "is_active": bool(product_data.get("is_active", True))
        }

    def upsert_product_vector(
        self,
        product_data: Dict[str, Any],
        vector: List[float],
        collection_name: Optional[str] = None
    ) -> str:
        """
        Upserts a single product vector with complete payload metadata into Qdrant.
        Uses deterministic UUID5 point ID derived from product_id.
        """
        coll_name = collection_name or settings.QDRANT_COLLECTION

        product_id = product_data["product_id"]
        point_id = self.get_point_id(product_id)
        payload = self.build_payload(product_data)

        point = qmodels.PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )

        def _op(client: QdrantClient):
            client.upsert(
                collection_name=coll_name,
                points=[point],
                wait=True
            )

        self._execute_with_retry(_op)
        print(f"[QdrantService] Successfully indexed vector for product '{product_id}' (Point ID: {point_id})")
        return point_id

    def upsert_products(
        self,
        products_data: List[Dict[str, Any]],
        vectors: List[List[float]],
        collection_name: Optional[str] = None
    ):
        """
        Stores/updates multiple products and their CLIP embeddings into Qdrant.
        """
        coll_name = collection_name or settings.QDRANT_COLLECTION

        points = []
        for product, vector in zip(products_data, vectors):
            point_id = self.get_point_id(product["product_id"])
            payload = self.build_payload(product)

            point = qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            points.append(point)

        print(f"[QdrantService] Upserting {len(points)} points into '{coll_name}'...")
        def _op(client: QdrantClient):
            client.upsert(
                collection_name=coll_name,
                points=points,
                wait=True
            )
        self._execute_with_retry(_op)
        print(f"[QdrantService] Successfully indexed {len(points)} products.")

    def update_product_payload(
        self,
        product_id: str,
        payload_updates: Dict[str, Any],
        collection_name: Optional[str] = None
    ):
        """
        Updates Qdrant metadata payload for a product without re-generating or changing the vector embedding.
        """
        coll_name = collection_name or settings.QDRANT_COLLECTION
        point_id = self.get_point_id(product_id)

        # Normalize any nested fields in payload updates if present
        clean_updates: Dict[str, Any] = {}
        for key, val in payload_updates.items():
            if key == "style":
                if isinstance(val, str):
                    cleaned = val.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
                    clean_updates["style"] = [s.strip().lower() for s in cleaned.split(",") if s.strip()]
                elif isinstance(val, list):
                    clean_updates["style"] = [str(s).strip().lower() for s in val if str(s).strip()]
                else:
                    clean_updates["style"] = val
            elif key == "price" and val is not None:
                clean_updates["price"] = float(val)
            elif key == "stock" and val is not None:
                clean_updates["stock"] = int(val)
            elif key == "is_active" and val is not None:
                clean_updates["is_active"] = bool(val)
            elif key == "category" and val is not None:
                clean_updates["category"] = str(val).lower().strip()
            else:
                clean_updates[key] = val

        def _op(client: QdrantClient):
            client.set_payload(
                collection_name=coll_name,
                payload=clean_updates,
                points=[point_id],
                wait=True
            )
        self._execute_with_retry(_op)
        print(f"[QdrantService] Updated payload for product '{product_id}' (Point ID: {point_id})")

    def delete_product_vector(
        self,
        product_id: str,
        collection_name: Optional[str] = None
    ):
        """
        Deletes a product vector point from Qdrant using deterministic point ID.
        """
        coll_name = collection_name or settings.QDRANT_COLLECTION
        point_id = self.get_point_id(product_id)

        def _op(client: QdrantClient):
            client.delete(
                collection_name=coll_name,
                points_selector=qmodels.PointIdsList(points=[point_id]),
                wait=True
            )
        self._execute_with_retry(_op)
        print(f"[QdrantService] Deleted vector point for product '{product_id}' (Point ID: {point_id})")

    def get_product_point(
        self,
        product_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single product point from Qdrant including payload and vector.
        Returns None if point does not exist.
        """
        coll_name = collection_name or settings.QDRANT_COLLECTION
        point_id = self.get_point_id(product_id)

        def _op(client: QdrantClient):
            return client.retrieve(
                collection_name=coll_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=True
            )

        try:
            records = self._execute_with_retry(_op)
            if records:
                rec = records[0]
                return {
                    "id": str(rec.id),
                    "payload": rec.payload,
                    "vector": rec.vector
                }
        except Exception as e:
            print(f"[QdrantService] Error retrieving point for '{product_id}': {e}")
        return None

    def search_products(
        self,
        query_vector: List[float],
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        filter_active: bool = True,
        min_stock: Optional[int] = 1,
        top_k: int = 3,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search with optional category, price, stock, and active status filters.
        Returns product payloads with similarity scores.
        """
        coll_name = collection_name or settings.QDRANT_COLLECTION

        # -----------------------------------------
        # Build Qdrant filters
        # -----------------------------------------
        must_conditions = []
        must_not_conditions = []

        if category:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="category",
                    match=qmodels.MatchValue(
                        value=category.lower().strip()
                    )
                )
            )

        if max_price is not None and max_price > 0:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="price",
                    range=qmodels.Range(
                        lte=float(max_price)
                    )
                )
            )

        # Exclude deactivated products if filter_active is True
        if filter_active:
            must_not_conditions.append(
                qmodels.FieldCondition(
                    key="is_active",
                    match=qmodels.MatchValue(value=False)
                )
            )

        query_filter = None
        if must_conditions or must_not_conditions:
            query_filter = qmodels.Filter(
                must=must_conditions if must_conditions else None,
                must_not=must_not_conditions if must_not_conditions else None
            )

        # Fetch extra candidates when post-filtering by stock (legacy payloads may omit stock)
        fetch_limit = top_k * 3 if (min_stock is not None and min_stock > 0) else top_k

        def _op(client: QdrantClient):
            return client.query_points(
                collection_name=coll_name,
                query=query_vector,
                query_filter=query_filter,
                limit=fetch_limit
            )

        try:
            search_response = self._execute_with_retry(_op)
            search_results = search_response.points

        except Exception as e:
            raise RuntimeError(
                f"Qdrant vector search failed: {str(e)}"
            )

        results = []
        for hit in search_results:
            result_item = dict(hit.payload or {})
            result_item["score"] = float(hit.score)
            # Soft stock check: missing stock treated as available (legacy catalog points)
            if min_stock is not None and min_stock > 0:
                stock_val = result_item.get("stock", 1)
                try:
                    if int(stock_val) < int(min_stock):
                        continue
                except (TypeError, ValueError):
                    pass
            results.append(result_item)
            if len(results) >= top_k:
                break

        return results


# Global singleton instance
qdrant_service = QdrantService()