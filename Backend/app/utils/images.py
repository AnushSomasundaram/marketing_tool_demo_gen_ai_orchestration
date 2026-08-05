import io

from PIL import Image

ASPECT_RATIOS: dict[str, tuple[int, int]] = {
    "1:1": (1, 1),
    "4:5": (4, 5),
    "9:16": (9, 16),
}


def crop_to_aspect_ratio(image_bytes: bytes, aspect_ratio: str) -> bytes:
    """Center-crop image bytes to exactly match the given aspect ratio, since the
    image model's native output sizes are only an approximation of some targets (e.g. 4:5)."""
    target = ASPECT_RATIOS.get(aspect_ratio)
    if target is None:
        return image_bytes

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        width, height = img.size
        target_w, target_h = target
        target_ratio = target_w / target_h
        current_ratio = width / height

        if current_ratio > target_ratio:
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            box = (left, 0, left + new_width, height)
        else:
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            box = (0, top, width, top + new_height)

        cropped = img.crop(box)
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG")
        return buffer.getvalue()
