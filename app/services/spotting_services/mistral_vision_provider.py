import base64

from mistralai.client import Mistral

from config.app_config import AppConfig
from app.services.spotting_services.vision_provider import VisionProvider


class MistralVisionProvider(VisionProvider):
    """Vision provider implementation using Mistral's Pixtral API."""

    def __init__(self) -> None:
        self._client = Mistral(api_key=AppConfig.MISTRAL_API_KEY)

    def analyze_image(self, image_data: bytes, prompt: str, media_type: str) -> str:
        """Sends the image and prompt together in the user message for stronger instruction following."""
        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = self._client.chat.complete(
            model=AppConfig.VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:{media_type};base64,{base64_image}",
                        },
                        {
                            "type": "text",
                            "text": (
                                "Does this image show a real Monster Energy drink can or bottle? "
                                "If it does NOT, you MUST reject it. Respond with the JSON only."
                            ),
                        },
                    ],
                },
            ],
        )

        return response.choices[0].message.content
