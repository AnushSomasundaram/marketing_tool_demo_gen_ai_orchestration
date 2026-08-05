import asyncio
import io
from pathlib import Path

from PIL import Image, ImageDraw

from app.utils.images import crop_to_aspect_ratio

PLACEHOLDER_PATH = Path(__file__).resolve().parents[3] / "mock_assets" / "placeholder_image.png"


class MockImageProvider:
    """Offline stand-in for GPT Image: copies the bundled placeholder image, lightly
    stamped with a version marker so successive revisions are visibly distinct."""

    async def _placeholder(self, *, aspect_ratio: str, label: str) -> bytes:
        await asyncio.sleep(0.4)
        with Image.open(PLACEHOLDER_PATH) as base:
            img = base.convert("RGB").copy()
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, img.height - 60, img.width, img.height], fill=(27, 27, 24))
        draw.text((24, img.height - 44), label[:60], fill=(247, 247, 246))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return crop_to_aspect_ratio(buffer.getvalue(), aspect_ratio)

    async def generate(self, *, prompt: str, reference_image_bytes: bytes, aspect_ratio: str) -> bytes:
        del reference_image_bytes
        return await self._placeholder(aspect_ratio=aspect_ratio, label=prompt)

    async def revise(self, *, prompt: str, base_image_bytes: bytes, aspect_ratio: str) -> bytes:
        del base_image_bytes
        return await self._placeholder(aspect_ratio=aspect_ratio, label=f"Revised: {prompt}")
