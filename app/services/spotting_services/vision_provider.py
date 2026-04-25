from abc import ABC, abstractmethod


class VisionProvider(ABC):
    """Abstract interface for vision LLM providers (Anthropic, OpenAI, Mistral, etc.)."""

    @abstractmethod
    def analyze_image(self, image_data: bytes, prompt: str, media_type: str) -> str:
        """Sends an image with a text prompt to a vision model and returns the response text.

        Args:
            image_data: Raw image bytes.
            prompt: Instructional prompt describing what to analyze.
            media_type: MIME type of the image (e.g. 'image/jpeg').

        Returns:
            The model's text response.
        """
        pass
