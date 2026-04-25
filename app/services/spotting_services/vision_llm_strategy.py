import json
from typing import List

from app.models.pg.monster_drink import MonsterDrink
from app.services.spotting_services.monster_recognition_engine import (
    RecognitionStrategy,
    RecognitionResult,
)
from app.services.spotting_services.vision_provider import VisionProvider
from app.init.logger_setup import LoggerSetup
from config.app_config import AppConfig


class VisionLLMRecognitionStrategy(RecognitionStrategy):
    """Recognition strategy that delegates image analysis to a pluggable vision LLM provider."""

    def __init__(self, provider: VisionProvider) -> None:
        self._provider = provider

    def identify(self, image_data: bytes) -> RecognitionResult:
        """Builds a prompt from all known monsters, sends the image to the vision provider, and parses the result."""
        logger = LoggerSetup.get_logger("general")

        monsters = list(MonsterDrink.select())
        if not monsters:
            return RecognitionResult(
                is_match=False,
                rejection_reason="No Monster drinks registered in the system.",
            )

        prompt = self._build_prompt(monsters)
        media_type = self._detect_media_type(image_data)

        try:
            response_text = self._provider.analyze_image(image_data, prompt, media_type)
        except Exception as e:
            logger.error(f"Vision provider request failed: {e}")
            return RecognitionResult(
                is_match=False,
                rejection_reason="Image recognition service temporarily unavailable.",
            )

        return self._parse_response(response_text, monsters)

    @staticmethod
    def _build_prompt(monsters: List[MonsterDrink]) -> str:
        """Constructs the system prompt with all known monsters and the expected JSON response format."""
        monster_list = "\n".join(
            f'- slug: "{m.slug}", name: "{m.name}", flavour: "{m.flavour}"'
            for m in monsters
        )
        return (
            "You are a strict Monster Energy drink identification system. "
            "Your job is to determine whether the image shows a real, physical Monster Energy drink can or bottle. "
            "Most images you receive will NOT contain a Monster Energy drink — reject them.\n\n"
            "CRITICAL RULES:\n"
            "- ONLY set identified to true if a Monster Energy branded can or bottle is clearly and unambiguously visible in the image.\n"
            "- If the image shows anything other than a Monster Energy drink (screenshots, text, other beverages, random objects, people, food, etc.), you MUST return identified as false.\n"
            "- If it shows a Monster Energy drink but it does not clearly match any slug from the known list below, return identified as false.\n"
            "- Do NOT guess. Do NOT force a match. When in doubt, reject.\n"
            "- confidence must be a float between 0.0 and 1.0.\n\n"
            f"Known Monster Energy drinks:\n{monster_list}\n\n"
            "Respond ONLY with a JSON object, no markdown, no extra text:\n"
            '{"identified": true, "slug": "the-matching-slug", "confidence": 0.95, "reasoning": "brief explanation"}\n\n'
            "Example rejection responses:\n"
            '{"identified": false, "slug": null, "confidence": 0.0, "reasoning": "Image is a chat screenshot, not a photo of a drink."}\n'
            '{"identified": false, "slug": null, "confidence": 0.0, "reasoning": "Image shows a Red Bull, not a Monster Energy drink."}\n'
            '{"identified": false, "slug": null, "confidence": 0.0, "reasoning": "Shows a Monster Energy drink but not a recognized variant from the known list."}'
        )

    @staticmethod
    def _detect_media_type(image_data: bytes) -> str:
        """Detects the MIME type from image file magic bytes."""
        if image_data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if image_data[:2] == b"\xff\xd8":
            return "image/jpeg"
        if image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
            return "image/webp"
        return "image/jpeg"

    @staticmethod
    def _parse_response(
        response_text: str, monsters: List[MonsterDrink]
    ) -> RecognitionResult:
        """Parses the vision LLM JSON response into a RecognitionResult, matching against known monsters."""
        logger = LoggerSetup.get_logger("general")

        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            result = json.loads(cleaned.strip())
        except (json.JSONDecodeError, IndexError):
            logger.warning(f"Failed to parse vision LLM response: {response_text}")
            return RecognitionResult(
                is_match=False,
                rejection_reason="Could not interpret recognition result.",
            )

        if not result.get("identified"):
            return RecognitionResult(
                is_match=False,
                confidence=result.get("confidence", 0.0),
                rejection_reason=result.get(
                    "reasoning", "Not identified as a known Monster drink."
                ),
            )

        confidence = result.get("confidence", 0.0)
        if confidence < AppConfig.VISION_MIN_CONFIDENCE:
            logger.info(
                f"Vision LLM confidence {confidence} below threshold {AppConfig.VISION_MIN_CONFIDENCE}"
            )
            return RecognitionResult(
                is_match=False,
                confidence=confidence,
                rejection_reason="Confidence too low for reliable identification.",
            )

        slug = result.get("slug")
        matched = next((m for m in monsters if m.slug == slug), None)

        if not matched:
            logger.warning(f"Vision LLM returned unknown slug: {slug}")
            return RecognitionResult(
                is_match=False,
                rejection_reason=f"Identified slug '{slug}' not found in database.",
            )

        logger.info(f"Vision LLM matched: {matched.name} (confidence: {confidence})")

        return RecognitionResult(
            is_match=True,
            matched_monster_drink=matched,
            confidence=confidence,
        )
