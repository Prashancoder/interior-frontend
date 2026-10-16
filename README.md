# Decore AI - Multi-Vendor AI Interior Design Platform (`decore-ai`)

> **A production-grade Python + FastAPI + MongoDB + OpenCLIP + Qdrant multi-vendor backend** powering an AI Interior Design platform connecting **Customers** and **Sellers/Vendors**.

---

## 🎯 Platform Vision & Overview

**Decore AI** transforms interior design into a seamless commerce experience:
1. **Customers**: Upload room images, define preferences (room type, style, budget), receive photorealistic AI redesigned spaces featuring **catalog-only vendor products**, view matched items, and order directly.
2. **Sellers / Vendors**: Manage their own storefronts, upload real product images with rich metadata, track inventory, view analytics, and fulfill orders.
3. **AI Multi-Modal Pipeline**:
   - **Vision AI (Groq Vision)** analyzes room photos into structured JSON.
   - **OpenCLIP** embeds visual traits and product images into a joint vector space.
   - **Qdrant Vector Database** performs high-speed semantic search constrained by metadata filters.
   - **Catalog-Only Recommendation** ensures the generative AI receives real catalog product references.

---

## 🏗️ Architecture & Source of Truth

```
[ FRONTEND CLIENT ] (React + TypeScript)
        ↓
[ FASTAPI BACKEND ] (app/main.py)
   ├── Auth & Role Security (JWT + Bcrypt)
   ├── Seller Product Management & Safe Image Uploads
   └── AI Multi-Modal Engine
        ├── MongoDB (Source of Truth for Users, Sellers, Products, Orders, Cart, Designs)
        ├── Qdrant Vector Database (Vector Similarity Index + Searchable Payloads)
        ├── OpenCLIP (ViT-B-32 Joint Text/Image Embeddings)
        └── Groq Vision AI (Room Photo Structural Analysis)
```

### 💡 Database Responsibilities
- **MongoDB**: Primary transactional database & source of truth for all business entities (`users`, `products`, `orders`, `cart`, `designs`).
- **Qdrant**: Dedicated vector similarity index storing image vectors and searchable payload metadata (`product_id`, `seller_id`, `category`, `price`, `style`, `color`, `material`, `stock`, `is_active`).

---

## 📁 Repository Structure

```
interior-ai/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application, lifespan & static upload mounting
│   ├── config.py                  # Settings (MongoDB, JWT, Qdrant, CLIP, Groq)
│   │
│   ├── database/                  # Database management
│   │   ├── __init__.py
│   │   └── mongodb.py             # Async Motor MongoDB connection & index setup
│   │
│   ├── models/                    # Pydantic data schemas
│   │   ├── __init__.py
│   │   ├── user.py                # User, Seller, JWT & Role schemas
│   │   ├── product.py             # Product, Search Result, Seller CRUD & Stats schemas
│   │   └── room.py                # Room Analysis & Legacy API schemas
│   │
│   ├── services/                  # Core business & AI services
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Password hashing (bcrypt) & JWT role-based guard
│   │   ├── storage_service.py     # Safe image upload, MIME validation & path sanitization
│   │   ├── clip_service.py        # OpenCLIP image & text encoder module
│   │   ├── qdrant_service.py      # Qdrant vector database client & query_points retrieval
│   │   ├── product_service.py     # Query builder & category-wise retrieval logic
│   │   └── prompt_service.py      # Generative prompt builder & design synthesis
│   │
│   ├── ingestion/                 # Batch catalog ingestion
│   │   ├── __init__.py
│   │   └── index_products.py      # Product image embedding & Qdrant indexer
│   │
│   └── routes/                    # API Endpoints
│       ├── __init__.py
│       ├── auth.py                # POST /api/auth/register, POST /api/auth/login, GET /api/auth/me
│       ├── seller.py              # Seller CRUD: /api/seller/products, /api/seller/stats
│       ├── products.py            # POST /products/index & POST /products/search
│       └── design.py              # POST /design/prepare
│
├── uploads/                       # Secure seller-uploaded product images
│   └── sellers/{seller_id}/products/{product_id}/
│
├── products/                      # Sample synthetic images subdirectories
│   ├── beds/
│   ├── sofas/
│   ├── curtains/
│   ├── wallpapers/
│   ├── lighting/
│   └── decor/
│
├── data/
│   └── products.json              # Sample catalog dataset
│
├── scripts/
│   ├── create_sample_products.py  # Generates products.json & sample synthetic images
│   └── test_phase1.py             # Phase 1 automated integration test suite
│
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python package dependencies
└── README.md                      # Project documentation & setup guide
```

---

## 🛠️ Step-by-Step Installation & Setup Guide

### 1. Activate Python Virtual Environment (`venv`)

#### 🪟 Windows (PowerShell):
```powershell
# Navigate into project directory
cd "interior-ai"

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

#### 🍎 macOS / 🐧 Linux:
```bash
source venv/bin/activate
```

---

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 3. Setup Environment Variables (`.env`)
Copy `.env.example` to create `.env`:
```bash
cp .env.example .env
```

Key environment variables:
```ini
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=decore_ai

# JWT Auth
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# File Storage
UPLOAD_DIR=uploads

# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=interior_products

# CLIP / OpenCLIP Model
CLIP_MODEL=ViT-B-32
CLIP_PRETRAINED=laion2b_s34b_b79k

# Groq Vision AI (Backend Only)
GROQ_API_KEY=your_groq_api_key_here
GROQ_VISION_MODEL=llama-3.2-11b-vision-preview
```

---

### 4. Start MongoDB & Qdrant Services

#### Start MongoDB:
- **Local MongoDB**: `net start MongoDB` or run MongoDB Community Edition on port `27017`.
- **Docker**: `docker run -d -p 27017:27017 --name decore_mongo mongo:latest`

#### Start Qdrant:
- **Docker**: `docker run -d -p 6333:6333 -p 6334:6334 --name qdrant_interior qdrant/qdrant`
- **Dashboard**: Open [http://localhost:6333/dashboard](http://localhost:6333/dashboard) in your browser.

---

### 5. Start FastAPI Backend Server
```bash
uvicorn app.main:app --reload
```
Server starts on: **`http://127.0.0.1:8000`**
Interactive Swagger UI: **`http://127.0.0.1:8000/docs`**

---

## 📡 API Reference & Endpoints

### 🔐 Authentication Module (`/api/auth`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Register customer or seller (`role: "customer"` or `"seller"`). |
| `POST` | `/api/auth/login` | Public | Login with email & password, returns JWT token. |
| `GET` | `/api/auth/me` | Authenticated | Get current authenticated user profile. |

#### Sample Registration Request:
```json
POST /api/auth/register
{
  "name": "Luxury Home Living",
  "email": "seller@decore.ai",
  "password": "SecurePassword123!",
  "role": "seller",
  "business_name": "Luxury Home Decor LLC",
  "phone": "+919876543210"
}
```

---

### 🏬 Seller Dashboard Module (`/api/seller`)
*(Requires Bearer JWT token with `role: "seller"`)*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/seller/products` | Upload product with image (`multipart/form-data`) and metadata. |
| `GET` | `/api/seller/products` | List seller's products with optional filtering (category, stock, status). |
| `GET` | `/api/seller/products/{id}` | Get full details of a specific seller product. |
| `PUT` | `/api/seller/products/{id}` | Update product metadata and optionally replace the image. |
| `DELETE`| `/api/seller/products/{id}` | Delete product from database and cleanup uploaded image. |
| `GET` | `/api/seller/stats` | Retrieve dashboard stats (total products, active, out of stock, recent). |

#### Sample Product Upload (`multipart/form-data`):
- `file`: `[image file: lamp.jpg]`
- `name`: `Modern Brass Floor Lamp`
- `category`: `lighting`
- `subcategory`: `floor lamp`
- `description`: `Brushed brass arc lamp with warm ambient LED light.`
- `price`: `8500`
- `color`: `gold brass`
- `material`: `brass and metal`
- `style`: `modern, luxury`
- `stock`: `10`
- `is_active`: `true`

---

### 🔍 Vector Search & Design Pipeline (Legacy Compatible)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/products/index` | Batch indexes catalog images into Qdrant. |
| `POST` | `/products/search` | Performs category-wise CLIP vector search in Qdrant with budget filters. |
| `POST` | `/design/prepare` | Synthesizes final prompt and selects reference images from catalog. |

---

---

## ⚡ Phase 2 - Automatic Product Embeddings & Qdrant Sync

Phase 2 connects the seller catalog management pipeline with the OpenCLIP neural vision encoder and Qdrant vector database for automated real-time multi-modal indexing.

### 🔄 Automatic Upload & Indexing Pipeline Flow

```
Seller Uploads Product (POST /api/seller/products)
        ↓
FastAPI Backend
        ↓
1. Validate & Save Image (uploads/sellers/{seller_id}/products/{product_id}/)
        ↓
2. Save Product Document in MongoDB (Primary Source of Truth)
        ↓
3. OpenCLIP Image Embedding (ViT-B-32 / laion2b_s34b_b79k)
        ↓
4. Generate 512-Dimensional Normalized Vector
        ↓
5. Upsert Vector + Payload into Qdrant ('interior_products')
   Point ID: Deterministic UUID5(NAMESPACE_DNS, product_id)
        ↓
Product Immediately Available for AI Semantic Vector Search
```

### 🏷️ Qdrant Vector Payload Schema
Every indexed product stores a rich multi-vendor payload enabling combined vector similarity with hard metadata filtering:

```json
{
  "product_id": "SOFA_CB875D",
  "seller_id": "SELLER_E3486385",
  "name": "Emerald Velvet Accent Armchair",
  "category": "sofa",
  "subcategory": "armchair",
  "description": "Luxurious emerald green velvet accent armchair with gold legs.",
  "price": 24999.0,
  "currency": "INR",
  "color": "emerald green",
  "material": "velvet and brass",
  "style": ["luxury", "modern", "contemporary"],
  "dimensions": "85x80x90 cm",
  "stock": 8,
  "image_path": "uploads/sellers/SELLER_E3486385/products/SOFA_CB875D/product_9974ea43.jpg",
  "is_active": true
}
```

### 🔁 Update & Delete Synchronization Rules

1. **Deterministic Point ID (`UUID5`)**:
   - Every product vector in Qdrant uses a stable `uuid5(NAMESPACE_DNS, product_id)` point ID.
   - Updates target the exact same point without creating duplicate vectors.

2. **Metadata-Only Updates (`PUT /api/seller/products/{id}`)**:
   - When only metadata (name, price, stock, active status, etc.) changes, Qdrant payload is updated using `set_payload`.
   - The CLIP image vector is **not** unnecessarily recomputed, maximizing server throughput.

3. **Image Replacement (`PUT /api/seller/products/{id}` with new file)**:
   - Old image file is safely unlinked from disk.
   - New image is saved and encoded into a new 512-d OpenCLIP vector.
   - Qdrant vector point is overwritten with the new vector and updated payload under the same point ID.

4. **Product Deletion (`DELETE /api/seller/products/{id}`)**:
   - **Layer 1 (MongoDB)**: Document is removed from database.
   - **Layer 2 (Qdrant)**: Vector point is deleted using point selector (zero orphan vectors).
   - **Layer 3 (Filesystem)**: Product image file and directory are cleaned up from `uploads/`.

5. **Multi-Vendor Isolation & Security**:
   - Every vector payload includes `seller_id` and `product_id`.
   - Seller ownership is strictly enforced on updates and deletions (HTTP 403 Forbidden for unauthorized sellers).

---

## 🧪 Automated Testing

### Run Phase 1 Test Suite
```powershell
.\venv\Scripts\python.exe scripts/test_phase1.py
```

### Run Phase 2 Test Suite
```powershell
.\venv\Scripts\python.exe scripts/test_phase2.py
```

All integration suites test real local MongoDB and Qdrant instances across the full lifecycle:
- Seller Auth & Registration
- Multipart Product Image Upload
- OpenCLIP 512-d Vector Generation
- Deterministic UUID5 Point Verification in Qdrant
- Complete Payload Validation
- Semantic Vector Search (`POST /products/search`)
- Selective Metadata Update vs Image Vector Regeneration
- Cross-Seller Ownership Protection
- Active Status Filter Synchronization (`is_active: false` exclusion)
- Synchronized Multi-Layer Deletion (MongoDB + Qdrant + Filesystem)

"# interior-frontend" 
