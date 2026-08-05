from runwayml import (
    APIConnectionError,
    APIStatusError,
    AsyncRunwayML,
    RateLimitError,
)

from app.config import get_settings
from app.services.exceptions import (
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderTaskFailedError,
    ProviderTimeoutError,
)
from app.services.providers.video.base import VideoTaskHandle, VideoTaskStatus

REQUEST_TIMEOUT_SECONDS = 30.0

_STATE_MAP = {
    "PENDING": "queued",
    "RUNNING": "processing",
    "THROTTLED": "processing",
    "SUCCEEDED": "completed",
    "FAILED": "failed",
    "CANCELLED": "failed",
}


class RunwayVideoProvider:
    """Image-to-video generation via Runway. Tasks are asynchronous: `generate` only
    creates the task, and the caller polls `get_status` (see background job recovery)."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.runwayml_api_secret:
            raise ProviderNotConfiguredError("Runway", provider="runway")
        self._client = AsyncRunwayML(api_key=settings.runwayml_api_secret, timeout=REQUEST_TIMEOUT_SECONDS)
        self._model = settings.runway_video_model

    async def generate(
        self, *, prompt: str, reference_image_url: str, ratio: str, duration_seconds: int
    ) -> VideoTaskHandle:
        try:
            task = await self._client.image_to_video.create(
                model=self._model,
                prompt_image=reference_image_url,
                prompt_text=prompt,
                ratio=ratio,
                duration=duration_seconds,
            )
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc), provider="runway") from exc
        except APIConnectionError as exc:
            raise ProviderTimeoutError(str(exc), provider="runway") from exc
        except APIStatusError as exc:
            if exc.status_code == 401:
                raise ProviderAuthenticationError(str(exc), provider="runway") from exc
            # Any other rejection (e.g. 400 invalid parameter) must still
            # become a ProviderError — callers only catch that hierarchy, so
            # re-raising the raw SDK exception here left assets stuck at
            # 'processing' forever instead of being marked failed.
            raise ProviderTaskFailedError(str(exc), provider="runway") from exc
        return VideoTaskHandle(external_task_id=task.id)

    async def get_status(self, external_task_id: str) -> VideoTaskStatus:
        try:
            task = await self._client.tasks.retrieve(external_task_id)
        except APIConnectionError as exc:
            raise ProviderTimeoutError(str(exc), provider="runway") from exc
        except APIStatusError as exc:
            if exc.status_code == 401:
                raise ProviderAuthenticationError(str(exc), provider="runway") from exc
            raise ProviderTaskFailedError(str(exc), provider="runway") from exc

        state = _STATE_MAP.get(task.status, "processing")
        progress = int(task.progress * 100) if task.progress is not None else None
        output_url = task.output[0] if task.output else None
        error_message = task.failure if state == "failed" else None
        return VideoTaskStatus(
            state=state, progress=progress, output_url=output_url, error_message=error_message
        )
