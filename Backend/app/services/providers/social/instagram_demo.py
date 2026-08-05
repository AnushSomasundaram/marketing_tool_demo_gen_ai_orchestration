import asyncio
import time
import uuid

from app.services.providers.social.base import ContainerStatus

# Module-level so simulated container state survives across provider instances.
_CONTAINERS: dict[str, float] = {}

SIMULATED_PROCESSING_SECONDS = 2.0


class DemoInstagramPublisher:
    """Simulates the Instagram container publish lifecycle without ever calling Meta.

    Every result from this publisher is clearly marked as simulated by the caller
    (PublishJob.is_simulated=True) — this class never pretends a publish was real.
    """

    async def create_container(
        self, *, ig_user_id: str, access_token: str, media_url: str, caption: str, is_video: bool
    ) -> str:
        del ig_user_id, access_token, media_url, caption, is_video
        await asyncio.sleep(0.2)
        container_id = f"demo_container_{uuid.uuid4().hex[:10]}"
        _CONTAINERS[container_id] = time.monotonic()
        return container_id

    async def get_container_status(self, *, container_id: str, access_token: str) -> ContainerStatus:
        del access_token
        started = _CONTAINERS.get(container_id)
        if started is None:
            return "error"
        if time.monotonic() - started < SIMULATED_PROCESSING_SECONDS:
            return "in_progress"
        return "finished"

    async def publish_container(self, *, ig_user_id: str, access_token: str, container_id: str) -> str:
        del ig_user_id, access_token
        await asyncio.sleep(0.2)
        return f"demo_media_{uuid.uuid4().hex[:10]}" if container_id in _CONTAINERS else ""

    async def get_permalink(self, *, media_id: str, access_token: str) -> str | None:
        del access_token
        return f"https://www.instagram.com/p/{media_id}-simulated/"
