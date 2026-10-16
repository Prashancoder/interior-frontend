"""
CLIP Embedding Service (OpenCLIP Integration)
==============================================
How Multi-Modal Vector Embeddings Work:
---------------------------------------
CLIP (Contrastive Language-Image Pre-training) maps both Text and Images into the SAME joint vector space.

PRODUCT SIDE (Image Embedding):
Image File (.jpg)
      ↓
CLIP Image Encoder (Vision Transformer / CNN)
      ↓
Normalized Embedding Vector (e.g. 512-dim Float Array)
      ↓
Stored into Vector Database (Qdrant)

USER SEARCH SIDE (Text Embedding):
"Luxury Modern Bedroom with off-white walls..."
      ↓
CLIP Text Encoder (Transformer Text Model)
      ↓
Normalized Embedding Vector (512-dim Float Array in same vector space!)
      ↓
Qdrant Cosine Similarity Search against stored Image Vectors!

Because both text vectors and image vectors live in the exact same vector space,
the cosine angle between a text prompt vector and an image vector measures how visually
and semantically relevant that product image is to the description!
"""

import os
from typing import Union, List
from pathlib import Path
import numpy as np
import torch
from PIL import Image
import open_clip

from app.config import settings

class CLIPService:
    def __init__(self):
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._embedding_dim = None

    def load_model(self):
        """
        Lazy loads the OpenCLIP model, preprocessing transform, and text tokenizer.
        Uses device CUDA if GPU is available, else CPU.
        """
        if self.model is None:
            print(f"[CLIPService] Loading OpenCLIP model '{settings.CLIP_MODEL}' (pretrained='{settings.CLIP_PRETRAINED}') on {self.device}...")
            try:
                model, _, preprocess = open_clip.create_model_and_transforms(
                    settings.CLIP_MODEL,
                    pretrained=settings.CLIP_PRETRAINED,
                    device=self.device
                )
                tokenizer = open_clip.get_tokenizer(settings.CLIP_MODEL)
                
                self.model = model
                self.preprocess = preprocess
                self.tokenizer = tokenizer
                self.model.eval() # Set model to evaluation mode
                
                # Automatically detect output vector dimension dynamically
                self._detect_embedding_dimension()
                print(f"[CLIPService] Model loaded successfully. Detected Embedding Dimension: {self._embedding_dim}")
            except Exception as e:
                raise RuntimeError(f"Failed to load OpenCLIP model '{settings.CLIP_MODEL}': {str(e)}")

    def _detect_embedding_dimension(self):
        """
        Dynamically detects the image vector dimension from the loaded CLIP model,
        avoiding hardcoded vector size assumptions (e.g. 512 or 768).
        """
        with torch.no_grad():
            dummy_text = self.tokenizer(["dummy text"]).to(self.device)
            dummy_vector = self.model.encode_text(dummy_text)
            self._embedding_dim = int(dummy_vector.shape[-1])

    def get_embedding_dimension(self) -> int:
        """Returns the dynamic vector embedding dimension of the active model."""
        if self.model is None:
            self.load_model()
        return self._embedding_dim

    def encode_image(self, image_input: Union[str, Path, Image.Image]) -> List[float]:
        """
        Encodes an image file path or PIL Image into a normalized float vector.
        
        Workflow:
        Image File -> PIL Image -> Preprocess Transform -> CLIP Image Encoder -> Vector -> L2 Normalization
        """
        if self.model is None:
            self.load_model()

        # Load image if file path is provided
        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            if not img_path.is_absolute():
                img_path = settings.BASE_DIR / img_path
                
            if not img_path.exists():
                raise FileNotFoundError(f"Product image not found at path: {img_path}")
            
            try:
                image = Image.open(img_path).convert("RGB")
            except Exception as e:
                raise ValueError(f"Failed to open or parse image at {img_path}: {str(e)}")
        else:
            image = image_input.convert("RGB")

        with torch.no_grad():
            # Apply preprocessing transform (resizes, crops, normalizes image tensor)
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            # Encode image into vector
            image_features = self.model.encode_image(image_tensor)
            # L2 Normalize vector so cosine similarity equals dot product
            image_features /= image_features.norm(dim=-1, keepdim=True)
            
            vector = image_features.cpu().numpy().squeeze().tolist()
            return vector

    def encode_text(self, text: str) -> List[float]:
        """
        Encodes a text string into a normalized float vector in the same joint vector space.
        
        Workflow:
        Search Text -> Tokenizer -> CLIP Text Encoder -> Vector -> L2 Normalization
        """
        if self.model is None:
            self.load_model()

        if not text or not text.strip():
            raise ValueError("Text prompt for CLIP encoding cannot be empty.")

        with torch.no_grad():
            # Tokenize text input
            text_tokens = self.tokenizer([text]).to(self.device)
            # Encode text into vector
            text_features = self.model.encode_text(text_tokens)
            # L2 Normalize vector
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            vector = text_features.cpu().numpy().squeeze().tolist()
            return vector

# Global singleton instance for easy import across services
clip_service = CLIPService()
