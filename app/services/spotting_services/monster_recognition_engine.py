from abc import ABC, abstractmethod
from typing import Optional
import random

from app.models.pg.monster_drink import MonsterDrink
from app.init.logger_setup import LoggerSetup


class RecognitionResult:
    """Value object representing the result of a monster drink recognition attempt."""

    def __init__(
        self,
        is_match: bool,
        matched_monster_drink: Optional[MonsterDrink] = None,
        confidence: float = 0.0,
        rejection_reason: Optional[str] = None,
    ):
        self.is_match = is_match
        self.matched_monster_drink = matched_monster_drink
        self.confidence = confidence
        self.rejection_reason = rejection_reason


class RecognitionStrategy(ABC):
    """Abstract strategy interface for Monster drink image recognition."""

    @abstractmethod
    def identify(self, image_data: bytes) -> RecognitionResult:
        """Attempts to identify a Monster drink from the provided image data."""
        pass


class StubRecognitionStrategy(RecognitionStrategy):
    """Stub that randomly selects a Monster drink. For development and testing only."""

    def identify(self, image_data: bytes) -> RecognitionResult:
        """Simulates image recognition by randomly selecting a Monster drink."""
        logger = LoggerSetup.get_logger("general")

        all_monsters = list(MonsterDrink.select())

        if not all_monsters:
            logger.warning("No Monster drinks in database — recognition cannot match.")
            return RecognitionResult(
                is_match=False,
                rejection_reason="No Monster drinks registered in the system.",
            )

        matched_monster = random.choice(all_monsters)
        logger.info(
            f"Stub recognition matched: {matched_monster.name} "
            f"(flavour: {matched_monster.flavour})"
        )

        return RecognitionResult(
            is_match=True,
            matched_monster_drink=matched_monster,
            confidence=round(random.uniform(0.7, 1.0), 2),
        )


class MonsterRecognitionEngine:
    """Facade that delegates image recognition to a pluggable strategy."""

    def __init__(self, strategy: Optional[RecognitionStrategy] = None):
        self._strategy = strategy or self._create_default_strategy()

    def identify(self, image_data: bytes) -> RecognitionResult:
        """Delegates identification to the configured recognition strategy."""
        return self._strategy.identify(image_data)

    @staticmethod
    def _create_default_strategy() -> RecognitionStrategy:
        """Selects the recognition strategy based on configured vision provider."""
        from config.app_config import AppConfig

        logger = LoggerSetup.get_logger("general")
        provider_name = AppConfig.VISION_PROVIDER

        if provider_name == "mistral" and AppConfig.MISTRAL_API_KEY:
            from app.services.spotting_services.mistral_vision_provider import MistralVisionProvider
            from app.services.spotting_services.vision_llm_strategy import VisionLLMRecognitionStrategy
            logger.info("Using Mistral Pixtral vision provider for recognition.")
            return VisionLLMRecognitionStrategy(MistralVisionProvider())

        logger.warning("No vision provider configured — falling back to stub recognition.")
        return StubRecognitionStrategy()
