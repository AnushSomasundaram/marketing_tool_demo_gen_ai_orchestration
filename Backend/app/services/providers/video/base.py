from dataclasses import dataclass
from typing import Literal, Protocol

VideoTaskState = Literal["queued", "processing", "completed", "failed"]


@dataclass
class VideoTaskHandle:
    external_task_id: str


@dataclass
class VideoTaskStatus:
    state: VideoTaskState
    progress: int | None
    output_url: str | None
    error_message: str | None


class VideoGenerationProvider(Protocol):
    async def generate(
        self, *, prompt: str, reference_image_url: str, ratio: str, duration_seconds: int
    ) -> VideoTaskHandle: ...

    async def get_status(self, external_task_id: str) -> VideoTaskStatus: ...
