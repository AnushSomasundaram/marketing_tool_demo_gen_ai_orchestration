import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

ACCEPTED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Broader than ACCEPTED_IMAGE_TYPES: covers every content type this backend ever
# writes to storage (uploads, generated images/thumbnails, generated/composed
# videos), used only for picking a sensible file extension — not for upload
# validation, which stays restricted to ACCEPTED_IMAGE_TYPES.
KNOWN_EXTENSIONS: dict[str, str] = {
    **ACCEPTED_IMAGE_TYPES,
    "video/mp4": ".mp4",
}


def safe_filename(original_name: str | None, content_type: str) -> str:
    """Generate a safe, unpredictable filename. Never trust the browser-supplied name."""
    extension = KNOWN_EXTENSIONS.get(content_type)
    if extension is None and original_name:
        suffix = Path(original_name).suffix.lower()
        if suffix in (".jpg", ".jpeg", ".png", ".webp", ".mp4"):
            extension = suffix if suffix != ".jpeg" else ".jpg"
    extension = extension or ".bin"
    return f"{uuid.uuid4().hex}{extension}"


_SAFE_SEGMENT = re.compile(r"^[a-zA-Z0-9._-]+$")


def is_safe_storage_segment(segment: str) -> bool:
    """Reject path traversal or otherwise unsafe path segments."""
    return bool(segment) and ".." not in segment and _SAFE_SEGMENT.match(segment) is not None


async def validate_and_read_image(file: UploadFile, *, max_bytes: int) -> bytes:
    if file.content_type not in ACCEPTED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Please upload a JPG, PNG, or WebP image.")

    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image must be smaller than {max_bytes // (1024 * 1024)}MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return contents
