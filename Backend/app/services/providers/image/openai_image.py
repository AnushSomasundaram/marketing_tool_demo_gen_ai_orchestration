import base64
import io

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from app.config import get_settings
from app.services.exceptions import (
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderSafetyError,
    ProviderTaskFailedError,
    ProviderTimeoutError,
)
from app.services.providers.image.base import size_for_aspect
from app.utils.images import crop_to_aspect_ratio

REQUEST_TIMEOUT_SECONDS = 120.0


class OpenAIImageProvider:
    """Uses GPT Image (edit endpoint) for both generation and revision — generation is
    always conditioned on the product reference photo, and revision is conditioned on the
    previously generated image, so product identity is preserved in both cases."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderNotConfiguredError("OpenAI", provider="openai")
        self._model = settings.openai_image_model
        self._client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    async def _edit(self, *, prompt: str, base_image_bytes: bytes, aspect_ratio: str) -> bytes:
        try:
            response = await self._client.images.edit(
                model=self._model,
                image=("reference.png", io.BytesIO(base_image_bytes), "image/png"),
                prompt=prompt,
                size=size_for_aspect(aspect_ratio),
            )
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc), provider="openai") from exc
        except APIConnectionError as exc:
            raise ProviderTimeoutError(str(exc), provider="openai") from exc
        except APIStatusError as exc:
            if exc.status_code == 401:
                raise ProviderAuthenticationError(str(exc), provider="openai") from exc
            if exc.status_code in (400, 422):
                raise ProviderSafetyError(str(exc), provider="openai") from exc
            # Any other rejection must still become a ProviderError — callers
            # only catch that hierarchy, so re-raising the raw SDK exception
            # here left assets stuck at 'processing' instead of failing
            # cleanly with a reportable message.
            raise ProviderTaskFailedError(str(exc), provider="openai") from exc

        data = response.data
        if not data or not data[0].b64_json:
            raise ProviderSafetyError("Image model returned no output.", provider="openai")
        raw = base64.b64decode(data[0].b64_json)
        return crop_to_aspect_ratio(raw, aspect_ratio)

    async def generate(self, *, prompt: str, reference_image_bytes: bytes, aspect_ratio: str) -> bytes:
        return await self._edit(
            prompt=prompt, base_image_bytes=reference_image_bytes, aspect_ratio=aspect_ratio
        )

    async def revise(self, *, prompt: str, base_image_bytes: bytes, aspect_ratio: str) -> bytes:
        return await self._edit(prompt=prompt, base_image_bytes=base_image_bytes, aspect_ratio=aspect_ratio)
