"""
Sample Data and Placeholder Image Generator Script
==================================================
This script generates a sample product dataset (data/products.json) containing
15+ realistic interior products across various categories:
- bed
- sofa
- curtain
- wallpaper
- lighting
- decor

It also generates synthetic product image files in the `products/` directory using Python Pillow (PIL).
This ensures that OpenCLIP can encode real image files out of the box.
"""

import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Define base project directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PRODUCTS_DIR = BASE_DIR / "products"

# 15+ Realistic Sample Products
SAMPLE_PRODUCTS = [
    {
        "product_id": "BED001",
        "name": "Luxury Walnut King Bed",
        "category": "bed",
        "color": "walnut brown",
        "material": "solid wood",
        "style": ["luxury", "modern"],
        "price": 45000,
        "image_path": "products/beds/bed_01.jpg"
    },
    {
        "product_id": "BED002",
        "name": "Minimalist Velvet Upholstered Platform Bed",
        "category": "bed",
        "color": "beige",
        "material": "velvet fabric",
        "style": ["minimalist", "modern"],
        "price": 38000,
        "image_path": "products/beds/bed_02.jpg"
    },
    {
        "product_id": "BED003",
        "name": "Royal Emerald Tufted Storage Bed",
        "category": "bed",
        "color": "emerald green",
        "material": "velvet",
        "style": ["luxury", "classic"],
        "price": 52000,
        "image_path": "products/beds/bed_03.jpg"
    },
    {
        "product_id": "SOFA001",
        "name": "Scandinavian Chesterfield Leather Sofa",
        "category": "sofa",
        "color": "cognac brown",
        "material": "genuine leather",
        "style": ["scandinavian", "luxury"],
        "price": 65000,
        "image_path": "products/sofas/sofa_01.jpg"
    },
    {
        "product_id": "SOFA002",
        "name": "Modern Boucle Sectional Sofa",
        "category": "sofa",
        "color": "off-white",
        "material": "boucle fabric",
        "style": ["modern", "minimalist"],
        "price": 72000,
        "image_path": "products/sofas/sofa_02.jpg"
    },
    {
        "product_id": "SOFA003",
        "name": "Velvet Accent Loveseat",
        "category": "sofa",
        "color": "navy blue",
        "material": "velvet",
        "style": ["modern", "chic"],
        "price": 28000,
        "image_path": "products/sofas/sofa_03.jpg"
    },
    {
        "product_id": "CURTAIN001",
        "name": "Heavy Blackout Linen Curtains",
        "category": "curtain",
        "color": "beige",
        "material": "natural linen",
        "style": ["modern", "minimalist"],
        "price": 4500,
        "image_path": "products/curtains/curtain_01.jpg"
    },
    {
        "product_id": "CURTAIN002",
        "name": "Luxury Silk Sheer Drapes",
        "category": "curtain",
        "color": "warm ivory",
        "material": "silk blend",
        "style": ["luxury", "classic"],
        "price": 8500,
        "image_path": "products/curtains/curtain_02.jpg"
    },
    {
        "product_id": "WALLPAPER001",
        "name": "Textured Warm Wood Slat Wallpaper",
        "category": "wallpaper",
        "color": "brown",
        "material": "vinyl wallpaper",
        "style": ["modern", "natural"],
        "price": 3200,
        "image_path": "products/wallpapers/wallpaper_01.jpg"
    },
    {
        "product_id": "WALLPAPER002",
        "name": "Gold Leaf Geometric Accent Wallpaper",
        "category": "wallpaper",
        "color": "gold and cream",
        "material": "metallic paper",
        "style": ["luxury", "art deco"],
        "price": 5500,
        "image_path": "products/wallpapers/wallpaper_02.jpg"
    },
    {
        "product_id": "LIGHTING001",
        "name": "Brushed Brass Warm LED Chandelier",
        "category": "lighting",
        "color": "gold brass",
        "material": "brass and glass",
        "style": ["luxury", "modern"],
        "price": 18500,
        "image_path": "products/lighting/lighting_01.jpg"
    },
    {
        "product_id": "LIGHTING002",
        "name": "Nordic Ceramic Warm Bedside Table Lamp",
        "category": "lighting",
        "color": "terracotta",
        "material": "ceramic",
        "style": ["minimalist", "nordic"],
        "price": 6200,
        "image_path": "products/lighting/lighting_02.jpg"
    },
    {
        "product_id": "LIGHTING003",
        "name": "Minimalist Matte Black Arc Floor Lamp",
        "category": "lighting",
        "color": "matte black",
        "material": "steel",
        "style": ["modern", "industrial"],
        "price": 9500,
        "image_path": "products/lighting/lighting_03.jpg"
    },
    {
        "product_id": "DECOR001",
        "name": "Abstract Bronze Table Sculpture",
        "category": "decor",
        "color": "bronze",
        "material": "metal",
        "style": ["luxury", "contemporary"],
        "price": 7500,
        "image_path": "products/decor/decor_01.jpg"
    },
    {
        "product_id": "DECOR002",
        "name": "Organic Ceramic Flower Vase",
        "category": "decor",
        "color": "off-white",
        "material": "ceramic",
        "style": ["minimalist", "wabi-sabi"],
        "price": 2800,
        "image_path": "products/decor/decor_02.jpg"
    },
    {
        "product_id": "DECOR003",
        "name": "Large Framed Canvas Abstract Wall Art",
        "category": "decor",
        "color": "beige and charcoal",
        "material": "canvas wood frame",
        "style": ["modern", "abstract"],
        "price": 12000,
        "image_path": "products/decor/decor_03.jpg"
    }
]

# Color map for sample synthetic image generation
COLOR_MAP = {
    "walnut brown": (101, 67, 33),
    "beige": (245, 245, 220),
    "emerald green": (8, 143, 143),
    "cognac brown": (154, 70, 61),
    "off-white": (250, 249, 246),
    "navy blue": (0, 0, 128),
    "warm ivory": (255, 253, 208),
    "brown": (139, 69, 19),
    "gold and cream": (212, 175, 55),
    "gold brass": (205, 127, 50),
    "terracotta": (226, 114, 91),
    "matte black": (30, 30, 30),
    "bronze": (205, 127, 50),
    "beige and charcoal": (180, 170, 160)
}

def generate_sample_images():
    """Generates synthetic product image placeholders with distinct colors and labels."""
    print("Generating sample product images...")
    for product in SAMPLE_PRODUCTS:
        rel_path = product["image_path"]
        full_path = BASE_DIR / rel_path
        
        # Ensure category directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not full_path.exists():
            # Get background color or default
            color_name = product.get("color", "")
            bg_color = COLOR_MAP.get(color_name, (200, 200, 200))
            
            # Create a 400x400 synthetic image
            img = Image.new("RGB", (400, 400), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # Draw decorative inner border
            draw.rectangle([20, 20, 380, 380], outline=(255, 255, 255), width=4)
            
            # Save image
            img.save(full_path, "JPEG")
            print(f"  [+] Created placeholder image: {rel_path}")

def generate_products_json():
    """Writes the SAMPLE_PRODUCTS array to data/products.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DATA_DIR / "products.json"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_PRODUCTS, f, indent=4)
    print(f"[✓] Created catalog file: {json_path}")

if __name__ == "__main__":
    generate_sample_images()
    generate_products_json()
    print("\nSample dataset creation complete!")
