"""
MongoDB Database Connection Module for Decore AI
================================================
Handles async connection management using Motor (AsyncIOMotorClient),
collection accessors, and index initialization for collections:
- users
- products
- orders
- cart
- designs
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo

from app.config import settings

logger = logging.getLogger("decore_ai.mongodb")

class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

db_manager = MongoDBManager()

def get_mongo_client() -> AsyncIOMotorClient:
    """Returns or creates the AsyncIOMotorClient."""
    if db_manager.client is None:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
        db_manager.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000
        )
        db_manager.db = db_manager.client[settings.MONGODB_DATABASE]
    return db_manager.client

def get_database() -> AsyncIOMotorDatabase:
    """Returns the Decore AI database instance."""
    if db_manager.db is None:
        get_mongo_client()
    return db_manager.db

def get_users_collection() -> AsyncIOMotorCollection:
    """Returns the 'users' collection."""
    return get_database()["users"]

def get_products_collection() -> AsyncIOMotorCollection:
    """Returns the 'products' collection."""
    return get_database()["products"]

def get_orders_collection() -> AsyncIOMotorCollection:
    """Returns the 'orders' collection."""
    return get_database()["orders"]

def get_cart_collection() -> AsyncIOMotorCollection:
    """Returns the 'cart' collection."""
    return get_database()["cart"]

def get_designs_collection() -> AsyncIOMotorCollection:
    """Returns the 'designs' collection."""
    return get_database()["designs"]

async def init_db():
    """
    Initializes database connection and creates required indexes.
    Falls back to in-memory mongomock when live MongoDB is unreachable
    (or USE_MOCK_MONGO=1), so local customer-flow demos still work.
    """
    import os

    use_mock = os.getenv("USE_MOCK_MONGO", "").strip() == "1"

    if not use_mock:
        try:
            client = get_mongo_client()
            await client.admin.command("ping")
        except Exception as e:
            logger.warning(f"Live MongoDB unreachable ({e}). Falling back to mongomock.")
            use_mock = True

    if use_mock:
        try:
            from mongomock_motor import AsyncMongoMockClient
            mock_client = AsyncMongoMockClient()
            db_manager.client = mock_client
            db_manager.db = mock_client[settings.MONGODB_DATABASE]
            logger.warning("Using in-memory mongomock MongoDB (data will not persist).")
        except Exception as e:
            logger.warning(f"mongomock fallback unavailable: {e}")
            return

    try:
        db = get_database()
        logger.info(f"Initializing MongoDB indexes for database: {settings.MONGODB_DATABASE}")

        # Users indexes
        users = db["users"]
        await users.create_index([("email", pymongo.ASCENDING)], unique=True)
        await users.create_index([("user_id", pymongo.ASCENDING)], unique=True, sparse=True)
        await users.create_index([("role", pymongo.ASCENDING)])

        # Products indexes
        products = db["products"]
        await products.create_index([("product_id", pymongo.ASCENDING)], unique=True)
        await products.create_index([("seller_id", pymongo.ASCENDING)])
        await products.create_index([("category", pymongo.ASCENDING)])
        await products.create_index([("is_active", pymongo.ASCENDING)])
        await products.create_index([("created_at", pymongo.DESCENDING)])

        # Cart indexes
        cart = db["cart"]
        await cart.create_index([("user_id", pymongo.ASCENDING)])
        await cart.create_index([("user_id", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)], unique=True)

        # Orders indexes
        orders = db["orders"]
        await orders.create_index([("order_id", pymongo.ASCENDING)], unique=True)
        await orders.create_index([("customer_id", pymongo.ASCENDING)])
        await orders.create_index([("items.seller_id", pymongo.ASCENDING)])
        await orders.create_index([("created_at", pymongo.DESCENDING)])

        # Designs indexes
        designs = db["designs"]
        await designs.create_index([("design_id", pymongo.ASCENDING)], unique=True)
        await designs.create_index([("user_id", pymongo.ASCENDING)])
        await designs.create_index([("created_at", pymongo.DESCENDING)])

        logger.info("MongoDB indexes successfully created.")
    except Exception as e:
        logger.warning(f"MongoDB initialization warning: {str(e)}. (Ensure MongoDB is running for full persistence).")

async def close_db():
    """Closes the MongoDB client connection."""
    if db_manager.client is not None:
        logger.info("Closing MongoDB connection...")
        db_manager.client.close()
        db_manager.client = None
        db_manager.db = None
