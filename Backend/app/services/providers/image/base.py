from typing import Protocol

ASPECT_TO_SIZE: dict[str, str] = {
    "1:1": "1024x1024",
    "4:5": "1024x1536",
}


def size_for_aspect(aspect_ratio: str) -> str:
    return ASPECT_TO_SIZE.get(aspect_ratio, "1024x1024")


class ImageGenerationProvider(Protocol):
    async def generate(self, *, prompt: str, reference_image_bytes: bytes, aspect_ratio: str) -> bytes:
        """Generate a new image conditioned on the product reference photo. Returns PNG bytes
        already cropped to the exact requested aspect ratio."""
        ...

    async def revise(self, *, prompt: str, base_image_bytes: bytes, aspect_ratio: str) -> bytes:
        """Edit a previously generated image per a natural-language instruction. Returns PNG
        bytes already cropped to the exact requested aspect ratio."""
        ...
