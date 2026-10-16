"""
Database package for Decore AI
"""
from app.database.mongodb import (
    get_database,
    get_users_collection,
    get_products_collection,
    get_orders_collection,
    get_cart_collection,
    get_designs_collection,
    init_db,
    close_db
)

__all__ = [
    "get_database",
    "get_users_collection",
    "get_products_collection",
    "get_orders_collection",
    "get_cart_collection",
    "get_designs_collection",
    "init_db",
    "close_db"
]
