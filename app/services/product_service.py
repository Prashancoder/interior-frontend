"""
Product Search & Query Builder Service
======================================
This service converts raw Vision AI output + user preferences into a rich text query
and handles category-wise retrieval from Qdrant with budget-aware ranking.
"""

from itertools import product as cartesian_product
from typing import List, Dict, Any, Tuple, Optional
from app.models.room import RoomAnalysis
from app.models.product import ProductSearchResult
from app.services.clip_service import clip_service
from app.services.qdrant_service import qdrant_service

def build_search_query(
    room_analysis: RoomAnalysis,
    style: str,
    budget: float,
    categories: Optional[List[str]] = None
) -> str:
    """
    Builds a semantic CLIP text query from room analysis, style, and categories.
    Accurately represents room occupancy (empty vs furnished) and visible attributes
    without polluting search embeddings with hallucinated furniture.
    """
    _ = budget  # kept for API compatibility with existing callers

    # 1. Room state: empty vs furnished
    is_empty = (
        not room_analysis.existing_furniture or
        (room_analysis.room_condition and "empty" in room_analysis.room_condition.lower()) or
        (room_analysis.room_condition and "unfinished" in room_analysis.room_condition.lower())
    )
    if is_empty:
        room_clause = f"empty {room_analysis.room_type.strip()}"
    else:
        furn_items = [f for f in room_analysis.existing_furniture if f.lower() not in ("none", "unknown", "—", "")]
        if furn_items:
            room_clause = f"{room_analysis.room_type.strip()} with existing {', '.join(furn_items[:2])}"
        else:
            room_clause = f"{room_analysis.room_type.strip()}"

    # 2. Wall & flooring
    wall = (room_analysis.wall_color_finish or room_analysis.wall_color or "").strip()
    if wall.lower() in ("unknown", "undetermined", "none", "—", ""):
        wall = "neutral walls"
    elif not any(w in wall.lower() for w in ("wall", "walls")):
        wall = f"{wall} walls"

    floor = (room_analysis.flooring_material or room_analysis.floor or "").strip()
    if floor.lower() in ("unknown", "undetermined", "none", "—", ""):
        floor = "neutral floor"
    elif not any(f in floor.lower() for f in ("floor", "flooring", "tile", "hardwood", "carpet", "marble")):
        floor = f"{floor} floor"

    # 3. Dominant colors
    colors = [c for c in room_analysis.dominant_colors if c.lower() not in ("unknown", "undetermined", "none", "—", "")]
    colors_str = f"{', '.join(colors[:3])} palette" if colors else "neutral palette"

    # 4. Architectural highlights (balcony, sliding door, windows, etc.)
    arch_items = room_analysis.architectural_features or room_analysis.room_features or []
    arch_highlight = ""
    for feat in arch_items:
        feat_lower = feat.lower()
        if any(w in feat_lower for w in ("balcony", "sliding", "window", "terrace", "patio", "ceiling")):
            arch_highlight = feat.strip()
            break

    # 5. Target style and requested categories
    style_str = style.strip() if style and style.lower() not in ("none", "undetermined") else "Modern"
    
    parts = [room_clause, wall, floor, colors_str]
    if arch_highlight:
        parts.append(arch_highlight)

    if categories:
        cat_str = ", ".join(categories)
        parts.append(f"{style_str} furniture: {cat_str}")
    else:
        parts.append(f"{style_str} furniture")

    query = ", ".join(parts) + "."
    return query

def _budget_status(budget: float, estimated_total: float) -> Tuple[float, str]:
    remaining = round(budget - estimated_total, 2)
    if remaining >= 0:
        return remaining, "within_budget"
    if abs(remaining) <= (budget * 0.20):
        return remaining, "slightly_over_budget"
    return remaining, "exceeds_budget"

def _pick_budget_aware_combination(
    category_candidates: Dict[str, List[ProductSearchResult]],
    budget: float
) -> Tuple[List[ProductSearchResult], float]:
    """
    Prefer a combination of one product per category that:
    1) stays within budget when possible
    2) maximizes semantic relevance
    3) avoids unnecessary overspending
    """
    category_lists = list(category_candidates.values())
    if not category_lists:
        return [], 0.0

    # Cap combinatorial explosion (top candidates already limited by caller)
    best_within: Optional[Tuple[float, float, List[ProductSearchResult]]] = None
    best_overall: Optional[Tuple[float, float, List[ProductSearchResult]]] = None

    for combo in cartesian_product(*category_lists):
        items = list(combo)
        total_price = sum(item.price for item in items)
        total_score = sum(item.score for item in items)
        # Prefer higher score; among equals prefer lower spend
        rank_key = (total_score, -total_price)

        if best_overall is None or rank_key > (best_overall[0], -best_overall[1]):
            best_overall = (total_score, total_price, items)

        if total_price <= budget:
            if best_within is None or rank_key > (best_within[0], -best_within[1]):
                best_within = (total_score, total_price, items)

    if best_within is not None:
        return best_within[2], best_within[1]

    # Soft fallback: best semantic combo even if slightly over budget
    if best_overall is not None:
        return best_overall[2], best_overall[1]

    return [], 0.0

def search_products_by_category(
    room_analysis: RoomAnalysis,
    style: str,
    budget: float,
    categories: List[str],
    limit_per_category: int = 2
) -> Tuple[str, List[ProductSearchResult]]:
    """
    Performs category-wise vector search in Qdrant:
    1. Builds search query string (style/room semantics only).
    2. Encodes search text query into CLIP vector space.
    3. Iterates over requested categories.
    4. For each category, queries Qdrant with category + price + stock + active filters.
    5. Returns the search query text and matched ProductSearchResult items.
    """
    query_text = build_search_query(room_analysis, style, budget, categories=categories)
    print(f"[ProductService] Search Query: '{query_text}'")

    query_vector = clip_service.encode_text(query_text)

    all_matched_products: List[ProductSearchResult] = []

    for cat in categories:
        clean_cat = cat.lower().strip()
        print(f"[ProductService] Querying Qdrant for category '{clean_cat}'...")

        raw_results = qdrant_service.search_products(
            query_vector=query_vector,
            category=clean_cat,
            max_price=budget,
            filter_active=True,
            min_stock=1,
            top_k=limit_per_category
        )

        for item in raw_results:
            all_matched_products.append(ProductSearchResult(**item))

    return query_text, all_matched_products

def recommend_products_budget_aware(
    room_analysis: RoomAnalysis,
    style: str,
    budget: float,
    categories: List[str],
    top_candidates_per_category: int = 3
) -> Tuple[str, List[ProductSearchResult], float, float, str, List[str]]:
    """
    Budget-Aware Product Recommendation Engine
    ==========================================
    1. Encodes semantic search query (no budget in CLIP text).
    2. Retrieves top semantically similar in-stock active products per category.
    3. Uses product prices to select a useful combination across categories.
    4. Prefers combinations within budget; otherwise best available with status flag.
    """
    query_text = build_search_query(room_analysis, style, budget, categories=categories)
    print(f"[ProductService] Budget-aware search query: '{query_text}'")

    query_vector = clip_service.encode_text(query_text)

    category_candidates: Dict[str, List[ProductSearchResult]] = {}
    categories_covered: List[str] = []
    n_cats = max(len(categories), 1)
    # Soft per-item ceiling keeps expensive outliers from eating the whole budget alone
    per_item_ceiling = max(budget * 0.85, budget / n_cats)

    for cat in categories:
        clean_cat = cat.lower().strip()
        raw_results = qdrant_service.search_products(
            query_vector=query_vector,
            category=clean_cat,
            max_price=per_item_ceiling,
            filter_active=True,
            min_stock=1,
            top_k=top_candidates_per_category
        )

        # If too strict, relax price filter to full budget for that category
        if not raw_results:
            raw_results = qdrant_service.search_products(
                query_vector=query_vector,
                category=clean_cat,
                max_price=budget,
                filter_active=True,
                min_stock=1,
                top_k=top_candidates_per_category
            )

        candidates = [ProductSearchResult(**item) for item in raw_results]
        if candidates:
            category_candidates[clean_cat] = candidates
            categories_covered.append(clean_cat)
        else:
            print(f"[ProductService] Notice: No products found for category '{clean_cat}'.")

    selected_primary, current_total = _pick_budget_aware_combination(category_candidates, budget)

    estimated_total = round(current_total, 2)
    budget_remaining, budget_status = _budget_status(budget, estimated_total)

    print(
        f"[ProductService] Recommendation total=INR {estimated_total}, "
        f"remaining=INR {budget_remaining}, status={budget_status}"
    )

    return (
        query_text,
        selected_primary,
        estimated_total,
        budget_remaining,
        budget_status,
        categories_covered
    )
