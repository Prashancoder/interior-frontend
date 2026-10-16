"""
Vision Service for Decore AI
============================
Analyzes uploaded customer room/interior images using Vision AI (Groq Llama 3.2 Vision / OpenAI).
Extracts strictly observed, non-hallucinated structured room characteristics:
- room_type (living room, bedroom, kitchen, bathroom, washroom, dining room, balcony, etc.)
- wall_color_finish / wall_color
- flooring_material / floor
- lighting
- existing_furniture (strictly visible items; empty [] if room is unfurnished)
- visible_objects (fixtures, fans, doors, railings, appliances)
- dominant_colors (actual image palette)
- target_style / design_style (only if evident, otherwise 'undetermined')
- architectural_features / room_features
- room_condition (mostly empty / unfinished / furnished / under renovation)
- confidence scores & uncertain_items

Security & Reliability:
- All Vision API calls execute exclusively on the backend server.
- API keys are NEVER logged or exposed to frontend clients.
- Heuristic fallback operates transparently when API keys are unconfigured and NEVER invents furniture.
"""

import os
import base64
import json
import re
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
from PIL import Image

from app.config import settings
from app.models.room import RoomAnalysis

logger = logging.getLogger("decore_ai.vision")
# Ensure logger outputs to console
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

SYSTEM_VISION_PROMPT = """You are an expert AI Architectural & Interior Design Vision Specialist.
Analyze the provided photo of an interior or residential space with rigorous precision.

You must adhere strictly to these VISUAL INSPECTION RULES:
RULE 1: ONLY describe objects, fixtures, and surfaces that are CLEARLY PHYSICALLY VISIBLE in the uploaded photo.
RULE 2: NEVER ASSUME furniture exists. If no sofa is visible, 'existing_furniture' MUST NOT contain 'sofa'. If no coffee table is visible, 'existing_furniture' MUST NOT contain 'coffee table'. If the room is empty or unfurnished, 'existing_furniture' MUST be an empty array [].
RULE 3: NEVER guess or infer flooring material from generic interior assumptions. If the floor visibly appears to be glossy tile, return "glossy light-colored tile", NEVER "wooden flooring". If unclear, return "unknown" or "undetermined".
RULE 4: DO NOT invent a design style just because the room is a modern apartment. If style cannot be determined with certainty, return "undetermined" or "minimal / unfinished".
RULE 5: Lighting condition must reflect visible sources and ambient light. If the image has cool white tube/LED fixtures or bright daylight, return "cool white artificial lighting with daylight" or "bright natural daylight", NOT "warm ambient".
RULE 6: Strictly distinguish VISIBLE features from INFERRED features. Only report what is directly seen.
RULE 7: If any attribute is uncertain or ambiguous, return "unknown" or "undetermined".
RULE 8: Empty or unfurnished rooms are completely valid. Do NOT automatically populate furniture.
RULE 9: Architectural features must be visible physical elements (e.g. "large sliding glass balcony door", "balcony with railing", "ceiling fans", "wall-mounted light fixture", "open floor plan", "large windows", "columns").
RULE 10: Dominant colors must match the exact pixel colors visible in the photo. Do NOT default to generic beige/brown.

Return a valid JSON object matching this exact schema:
{
  "room_type": "living room | bedroom | kitchen | bathroom | dining room | balcony | hallway | office | other interior space",
  "wall_color_finish": "exact observed wall color and finish (e.g. white / off-white painted walls)",
  "flooring_material": "exact observed flooring material and finish (e.g. glossy light-colored tile, dark hardwood, marble, unknown)",
  "lighting": "exact observed lighting atmosphere and fixtures (e.g. cool white artificial lighting with daylight from balcony)",
  "target_style": "observed interior design style if evident, or 'undetermined' / 'minimal / unfinished' / 'unknown'",
  "existing_furniture": ["only physically visible furniture items, or empty [] if unfurnished"],
  "visible_objects": ["all visible physical objects, fixtures, ceiling fans, doors, railings, buckets, containers, etc."],
  "dominant_colors": ["actual dominant colors visible in the image"],
  "architectural_features": ["visible structural features: sliding glass doors, balcony, railing, ceiling fans, light fixture, etc."],
  "room_condition": "mostly empty / unfinished | furnished | partially furnished | under renovation",
  "confidence": {
    "room_type": 0.95,
    "wall_color_finish": 0.90,
    "flooring_material": 0.90,
    "lighting": 0.85,
    "target_style": 0.20
  },
  "uncertain_items": ["items or attributes that cannot be determined with confidence"],
  "description": "Concise 1-2 sentence visual summary of what is seen in the image."
}
"""

def encode_image_to_base64(image_path: Union[str, Path]) -> tuple[str, str]:
    """
    Reads an image file and returns (base64_string, mime_type).
    """
    path = Path(image_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"Image file not found at: {path}")

    ext = path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".bmp": "image/bmp"
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(path, "rb") as image_file:
        b64_data = base64.b64encode(image_file.read()).decode("utf-8")

    return b64_data, mime_type

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Extracts and parses JSON from Vision LLM response, handling markdown fences and minor syntax issues.
    """
    cleaned = raw_text.strip()

    # Remove markdown ```json ... ``` code blocks
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    # Find JSON object boundaries
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx:end_idx+1]

    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"[VisionService] Direct JSON parse failed: {e}. Attempting sanitized parse...")
        # Clean trailing commas before closing braces/brackets
        cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
        return json.loads(cleaned)

def fallback_heuristic_room_analysis(
    image_path: Union[str, Path],
    preferred_style: Optional[str] = None
) -> RoomAnalysis:
    """
    Accurate local heuristic room analyzer used when Vision API key is not configured or offline.
    Inspects actual image pixels using Pillow.
    CRITICAL RULE: NEVER hallucinate furniture (sofa, coffee table, etc.) or wooden flooring.
    """
    path = Path(image_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path

    room_type = "living room"
    wall_color = "white / off-white painted walls"
    floor = "glossy light-colored tile"
    lighting = "bright cool white lighting with daylight"
    dominant_colors = ["white", "off-white", "light grey"]
    existing_furniture: List[str] = []
    visible_objects = ["open floor area", "wall surfaces", "ceiling area"]
    architectural_features = ["open floor area", "wall layout", "doorway / window opening"]
    style = preferred_style if preferred_style else "undetermined"
    room_condition = "mostly empty / unfinished"
    uncertain_items = ["interior design style", "specific furniture (offline fallback mode)", "exact material specifications"]

    filename_lower = path.name.lower()
    if "bed" in filename_lower:
        room_type = "bedroom"
    elif "kitchen" in filename_lower:
        room_type = "kitchen"
        floor = "tile / stone"
        architectural_features.append("kitchen counter area")
    elif "bath" in filename_lower:
        room_type = "bathroom"
        floor = "ceramic tile"
    elif "dine" in filename_lower or "dining" in filename_lower:
        room_type = "dining room"
    elif "office" in filename_lower or "study" in filename_lower:
        room_type = "study room"
    elif "balcony" in filename_lower:
        room_type = "balcony"
        architectural_features.append("balcony area")

    # Analyze actual image pixels if file exists
    if path.exists():
        try:
            with Image.open(path) as img:
                rgb_img = img.convert("RGB")
                w, h = rgb_img.size
                resized = rgb_img.resize((100, 100))
                pixels = list(resized.getdata())

                avg_r = sum(p[0] for p in pixels) / len(pixels)
                avg_g = sum(p[1] for p in pixels) / len(pixels)
                avg_b = sum(p[2] for p in pixels) / len(pixels)
                brightness = (avg_r + avg_g + avg_b) / 3.0

                # Analyze floor region (bottom 35% of image)
                bottom_pixels = [pixels[i] for i in range(len(pixels)) if (i // 100) >= 65]
                if bottom_pixels:
                    floor_r = sum(p[0] for p in bottom_pixels) / len(bottom_pixels)
                    floor_g = sum(p[1] for p in bottom_pixels) / len(bottom_pixels)
                    floor_b = sum(p[2] for p in bottom_pixels) / len(bottom_pixels)
                    floor_bright = (floor_r + floor_g + floor_b) / 3.0

                    if floor_bright > 150:
                        floor = "glossy light-colored tile"
                    elif floor_r > floor_b + 35 and floor_g > floor_b + 15:
                        floor = "warm hardwood / laminate"
                    elif floor_bright < 80:
                        floor = "dark tile / dark flooring"
                    else:
                        floor = "neutral light tile / flooring"

                # Analyze wall / lighting from top and mid regions
                if brightness > 165:
                    lighting = "bright cool white lighting with daylight"
                    wall_color = "white / off-white painted walls"
                    dominant_colors = ["white", "off-white", "light grey", "neutral accents"]
                elif brightness > 120:
                    if avg_r > avg_b + 20:
                        lighting = "warm natural lighting"
                        wall_color = "light cream / beige painted walls"
                        dominant_colors = ["cream", "warm beige", "off-white"]
                    else:
                        lighting = "neutral ambient lighting with daylight"
                        wall_color = "off-white / pale grey painted walls"
                        dominant_colors = ["off-white", "light grey", "neutral tones"]
                else:
                    lighting = "moody / low ambient lighting"
                    wall_color = "muted neutral walls"
                    dominant_colors = ["grey", "dark neutral", "muted tones"]

        except Exception as e:
            logger.warning(f"[VisionService] Pillow pixel inspection error: {e}")

    logger.info(
        f"[VisionService] Heuristic fallback generated for {room_type}: "
        f"floor='{floor}', wall='{wall_color}', lighting='{lighting}', furniture={existing_furniture}"
    )

    return RoomAnalysis(
        room_type=room_type,
        wall_color=wall_color,
        wall_color_finish=wall_color,
        floor=floor,
        flooring_material=floor,
        lighting=lighting,
        existing_furniture=existing_furniture,
        visible_objects=visible_objects,
        dominant_colors=dominant_colors,
        target_style=style,
        design_style=style,
        architectural_features=architectural_features,
        room_features=architectural_features,
        room_condition=room_condition,
        confidence={
            "room_type": 0.6,
            "wall_color_finish": 0.55,
            "flooring_material": 0.5,
            "lighting": 0.55,
            "target_style": 0.2 if style == "undetermined" else 0.6
        },
        uncertain_items=uncertain_items,
        description=(
            f"Heuristic fallback analysis: A {lighting} {room_type} with {wall_color} and {floor}. "
            f"No furniture detected or assumed."
        ),
        is_fallback=True,
        provider="heuristic_fallback"
    )

class VisionService:
    """
    Vision Service supporting Groq Vision AI (Llama 3.2 Vision) and OpenAI Vision
    with safe debug logging and zero-hallucination heuristic fallback.
    """
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_VISION_MODEL or "llama-3.2-11b-vision-preview"
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_VISION_MODEL or "gpt-4o"

    def is_vision_api_configured(self) -> bool:
        """Returns True if any live vision API key is configured."""
        groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        return bool(groq_key.strip() or openai_key.strip())

    async def analyze_room_image(
        self,
        image_path: Union[str, Path],
        preferred_style: Optional[str] = None
    ) -> RoomAnalysis:
        """
        Analyzes a customer room image using Groq Vision AI (or OpenAI Vision).
        If live API is unconfigured or fails, falls back to honest local heuristic analysis.
        """
        groq_key = (settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")).strip()
        openai_key = (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")).strip()

        logger.info(f"[VisionService] Starting image analysis: {image_path}")

        # Check provider configuration
        if groq_key:
            provider_name = "Groq"
            is_configured = True
        elif openai_key:
            provider_name = "OpenAI"
            is_configured = True
        else:
            provider_name = "None"
            is_configured = False

        logger.info(f"[VisionService] Provider: {provider_name}")
        logger.info(f"[VisionService] Vision API configured: {is_configured}")

        if not is_configured:
            logger.warning("[VisionService] WARNING: Vision API unavailable (GROQ_API_KEY not configured).")
            logger.info("[VisionService] Using development fallback (no hallucinated furniture or styles).")
            return fallback_heuristic_room_analysis(image_path, preferred_style)

        # -------------------------------------------------------------
        # 1. Groq Vision AI Execution
        # -------------------------------------------------------------
        if groq_key:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=groq_key)
                base64_image, mime_type = encode_image_to_base64(image_path)

                user_prompt = (
                    "Inspect this uploaded room photo in detail following the strict visual inspection rules. "
                    "Report ONLY visible objects, exact wall finish, flooring material, lighting sources, "
                    "architectural features, and room condition in strict JSON schema format."
                )
                if preferred_style and preferred_style.lower() not in ("none", "undetermined", "any"):
                    user_prompt += f" Note: Customer is planning a '{preferred_style}' style redesign."

                logger.info(f"[VisionService] Sending image to vision model ({self.groq_model})")
                
                response = await client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_VISION_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"}
                )

                logger.info("[VisionService] Vision response received")
                raw_content = response.choices[0].message.content
                parsed = clean_json_response(raw_content)

                analysis = self._build_room_analysis_from_json(parsed, preferred_style, provider="groq_vision")
                logger.info(
                    f"[VisionService] Parsed structured room analysis successfully: "
                    f"room_type='{analysis.room_type}', floor='{analysis.flooring_material}', "
                    f"furniture={analysis.existing_furniture}, condition='{analysis.room_condition}'"
                )
                return analysis

            except Exception as e:
                logger.warning(f"[VisionService] Groq Vision call failed: {str(e)}.")
                if not openai_key:
                    logger.info("[VisionService] Falling back to intelligent local heuristic analysis.")
                    return fallback_heuristic_room_analysis(image_path, preferred_style)

        # -------------------------------------------------------------
        # 2. OpenAI Vision Execution (Alternative Provider)
        # -------------------------------------------------------------
        if openai_key:
            try:
                import httpx
                base64_image, mime_type = encode_image_to_base64(image_path)
                logger.info(f"[VisionService] Sending image to OpenAI vision model ({self.openai_model})")

                user_prompt = (
                    "Inspect this uploaded room photo in detail following the strict visual inspection rules. "
                    "Report ONLY visible objects, exact wall finish, flooring material, lighting sources, "
                    "architectural features, and room condition in strict JSON schema format."
                )
                if preferred_style and preferred_style.lower() not in ("none", "undetermined", "any"):
                    user_prompt += f" Note: Customer is planning a '{preferred_style}' style redesign."

                async with httpx.AsyncClient(timeout=45.0) as http_client:
                    resp = await http_client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openai_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.openai_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_VISION_PROMPT},
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": user_prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{mime_type};base64,{base64_image}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            "temperature": 0.1,
                            "max_tokens": 1000,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    raw_content = data["choices"][0]["message"]["content"]
                    parsed = clean_json_response(raw_content)

                    logger.info("[VisionService] Vision response received from OpenAI")
                    analysis = self._build_room_analysis_from_json(parsed, preferred_style, provider="openai_vision")
                    logger.info(
                        f"[VisionService] Parsed structured room analysis successfully: "
                        f"room_type='{analysis.room_type}', floor='{analysis.flooring_material}', "
                        f"furniture={analysis.existing_furniture}, condition='{analysis.room_condition}'"
                    )
                    return analysis

            except Exception as e:
                logger.warning(f"[VisionService] OpenAI Vision call failed: {str(e)}.")
                logger.info("[VisionService] Falling back to intelligent local heuristic analysis.")
                return fallback_heuristic_room_analysis(image_path, preferred_style)

        return fallback_heuristic_room_analysis(image_path, preferred_style)

    def _build_room_analysis_from_json(
        self,
        data: Dict[str, Any],
        preferred_style: Optional[str],
        provider: str
    ) -> RoomAnalysis:
        """
        Normalizes and validates raw LLM JSON output into a validated RoomAnalysis model.
        """
        room_type = str(data.get("room_type", "living room")).lower().strip()
        wall_color_finish = str(data.get("wall_color_finish") or data.get("wall_color") or "white / off-white painted walls").strip()
        flooring_material = str(data.get("flooring_material") or data.get("floor") or "glossy light-colored tile").strip()
        lighting = str(data.get("lighting", "bright natural daylight")).strip()

        # Handle furniture list safely
        raw_furn = data.get("existing_furniture", [])
        if isinstance(raw_furn, list):
            existing_furniture = [str(item).strip() for item in raw_furn if str(item).strip()]
        else:
            existing_furniture = []

        # Handle visible objects
        raw_objs = data.get("visible_objects", [])
        if isinstance(raw_objs, list):
            visible_objects = [str(item).strip() for item in raw_objs if str(item).strip()]
        else:
            visible_objects = []

        # Handle dominant colors
        raw_colors = data.get("dominant_colors", [])
        if isinstance(raw_colors, list):
            dominant_colors = [str(c).strip() for c in raw_colors if str(c).strip()]
        else:
            dominant_colors = ["white", "off-white", "light grey"]

        # Handle architectural features
        raw_arch = data.get("architectural_features") or data.get("room_features") or []
        if isinstance(raw_arch, list):
            architectural_features = [str(f).strip() for f in raw_arch if str(f).strip()]
        else:
            architectural_features = []

        target_style = str(data.get("target_style") or data.get("design_style") or "undetermined").strip()
        room_condition = str(data.get("room_condition", "mostly empty / unfinished")).strip()

        # Confidence map
        raw_conf = data.get("confidence", {})
        confidence = {}
        if isinstance(raw_conf, dict):
            for k in ("room_type", "wall_color_finish", "flooring_material", "lighting", "target_style"):
                val = raw_conf.get(k)
                try:
                    confidence[k] = float(val) if val is not None else 0.85
                except (ValueError, TypeError):
                    confidence[k] = 0.85
        else:
            confidence = {
                "room_type": 0.95,
                "wall_color_finish": 0.90,
                "flooring_material": 0.90,
                "lighting": 0.85,
                "target_style": 0.3 if target_style in ("undetermined", "unknown") else 0.85
            }

        # Uncertain items
        raw_unc = data.get("uncertain_items", [])
        if isinstance(raw_unc, list):
            uncertain_items = [str(u).strip() for u in raw_unc if str(u).strip()]
        else:
            uncertain_items = []

        description = str(data.get("description", "")).strip()
        if not description:
            furniture_clause = f"with visible {', '.join(existing_furniture)}" if existing_furniture else "currently empty/unfurnished"
            description = f"A {lighting} {room_type} with {wall_color_finish} and {flooring_material}, {furniture_clause}."

        return RoomAnalysis(
            room_type=room_type,
            wall_color=wall_color_finish,
            wall_color_finish=wall_color_finish,
            floor=flooring_material,
            flooring_material=flooring_material,
            lighting=lighting,
            existing_furniture=existing_furniture,
            visible_objects=visible_objects,
            dominant_colors=dominant_colors,
            target_style=target_style,
            design_style=target_style,
            architectural_features=architectural_features,
            room_features=architectural_features,
            room_condition=room_condition,
            confidence=confidence,
            uncertain_items=uncertain_items,
            description=description,
            is_fallback=False,
            provider=provider
        )

# Global singleton instance
vision_service = VisionService()
