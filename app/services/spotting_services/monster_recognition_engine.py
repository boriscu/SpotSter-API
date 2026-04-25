from abc import ABC, abstractmethod
from typing import Optional
import random

from app.models.pg.monster_drink import MonsterDrink
from app.init.logger_setup import LoggerSetup


class RecognitionResult:
    """
    Value object representing the result of a monster drink recognition attempt.
    """

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
    """
    Abstract strategy interface for Monster drink image recognition.
    Implementations can range from stub/mock to ML model-based recognisers.
    """

    @abstractmethod
    def identify(self, image_data: bytes) -> RecognitionResult:
        """
        Attempts to identify a Monster drink from the provided image data.

        Args:
            image_data: The raw image bytes to analyse.

        Returns:
            RecognitionResult: The recognition outcome.
        """
        pass


class StubRecognitionStrategy(RecognitionStrategy):
    """
    Stub implementation of the recognition strategy.
    Randomly selects a known Monster drink from the database to simulate a match.
    Intended for development and testing until a real recognition model is integrated.
    """

    def identify(self, image_data: bytes) -> RecognitionResult:
        """
        Simulates image recognition by randomly selecting a Monster drink.

        Args:
            image_data: The raw image bytes (not actually analysed in stub mode).

        Returns:
            RecognitionResult: A simulated match result.
        """
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
    """
    Facade that delegates image recognition to a pluggable strategy.
    Defaults to StubRecognitionStrategy if no strategy is explicitly provided.
    """

    def __init__(self, strategy: Optional[RecognitionStrategy] = None):
        self._strategy = strategy or StubRecognitionStrategy()

    def identify(self, image_data: bytes) -> RecognitionResult:
        """
        Delegates identification to the configured recognition strategy.

        Args:
            image_data: The raw image bytes to identify.

        Returns:
            RecognitionResult: The recognition outcome from the chosen strategy.
        """
        return self._strategy.identify(image_data)
