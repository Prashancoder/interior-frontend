"""
Image Generation Service Abstraction for Decore AI
==================================================
Provides a clean service abstraction for downstream AI Image Generation.
Supports pluggable providers (mock, SDXL ControlNet, FLUX, etc.).

Currently operates with IMAGE_GENERATION_PROVIDER=mock.
Prepares all inputs (Original Room Image, Reference Product Images, Final Prompt)
so a real generative model can be plugged in without changing customer workflow.
"""

from typing import List, Optional, Dict, Any
from app.config import settings

class ImageGenerationService:
    """
    Service interface for generative interior design rendering.
    """
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.IMAGE_GENERATION_PROVIDER or "mock"

    def generate_design(
        self,
        original_room_image: Optional[str],
        reference_images: List[str],
        final_prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes or prepares the image generation step.
        Returns a structured payload detailing the generation state.
        """
        print(f"[ImageGenerationService] Provider: '{self.provider}'")
        print(f"  [+] Original Room Image: {original_room_image}")
        print(f"  [+] Reference Images Count: {len(reference_images)}")
        print(f"  [+] Prompt Preview: '{final_prompt[:90]}...'")

        if self.provider == "mock":
            return {
                "provider": "mock",
                "status": "ready",
                "message": (
                    "Pipeline execution successful. "
                    "Image generation inputs prepared and ready for ControlNet / SDXL / FLUX provider."
                ),
                "original_room_image": original_room_image,
                "reference_images": reference_images,
                "final_prompt": final_prompt,
                "metadata": metadata or {}
            }
        else:
            # Placeholder for future live provider integrations
            return {
                "provider": self.provider,
                "status": "ready",
                "message": f"Provider '{self.provider}' is ready for rendering pipeline.",
                "original_room_image": original_room_image,
                "reference_images": reference_images,
                "final_prompt": final_prompt,
                "metadata": metadata or {}
            }

# Global singleton instance
image_generation_service = ImageGenerationService()
