import random
import time
import uuid

from app.services.providers.video.base import VideoTaskHandle, VideoTaskStatus

# The mock output URL is a sentinel, not a real remote URL: the caller (asset
# generation service) recognizes the "mock://" scheme and reads the bundled
# placeholder video from disk instead of downloading anything.
MOCK_OUTPUT_URL = "mock://placeholder_video.mp4"

# Module-level (not instance-level) so task state survives regardless of how
# many MockVideoProvider instances the provider factory creates over time.
_TASKS: dict[str, dict] = {}


class MockVideoProvider:
    """Offline stand-in for Runway. Simulates the same async task lifecycle
    (queued task id, polled progress, eventual completion or failure) purely
    in memory, so the rest of the system exercises the exact same polling
    path it would use against the real provider."""

    async def generate(
        self, *, prompt: str, reference_image_url: str, ratio: str, duration_seconds: int
    ) -> VideoTaskHandle:
        del prompt, reference_image_url, ratio, duration_seconds
        task_id = f"mock_task_{uuid.uuid4().hex[:10]}"
        _TASKS[task_id] = {
            "start": time.monotonic(),
            "total": random.uniform(4.0, 7.0),
            "will_fail": random.random() < 0.15,
        }
        return VideoTaskHandle(external_task_id=task_id)

    async def get_status(self, external_task_id: str) -> VideoTaskStatus:
        task = _TASKS.get(external_task_id)
        if task is None:
            return VideoTaskStatus(
                state="failed", progress=None, output_url=None, error_message="Unknown task id."
            )

        elapsed = time.monotonic() - task["start"]
        if elapsed < task["total"]:
            progress = min(96, int((elapsed / task["total"]) * 100))
            return VideoTaskStatus(state="processing", progress=progress, output_url=None, error_message=None)

        if task["will_fail"]:
            return VideoTaskStatus(
                state="failed",
                progress=None,
                output_url=None,
                error_message="Video rendering failed unexpectedly. This is usually recoverable — try again.",
            )
        return VideoTaskStatus(
            state="completed", progress=100, output_url=MOCK_OUTPUT_URL, error_message=None
        )
