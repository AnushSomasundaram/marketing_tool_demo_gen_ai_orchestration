"""FFmpeg-based video composition: burning deterministic text overlays onto a
completed AI-generated video, and extracting a static thumbnail frame for
previews. All subprocess calls use argument arrays — never shell=True.
"""

import asyncio
import tempfile
from pathlib import Path

from app.utils.ffmpeg import ffmpeg_available, ffmpeg_path

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


class CompositionError(Exception):
    pass


def _resolve_font() -> str | None:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", r"\\\\").replace(":", r"\:").replace("'", r"\'")


async def _run_ffmpeg(args: list[str]) -> None:
    if not ffmpeg_available():
        raise CompositionError("FFmpeg is not installed or not on PATH.")
    binary = ffmpeg_path()
    assert binary is not None
    process = await asyncio.create_subprocess_exec(
        binary,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise CompositionError(f"FFmpeg failed: {stderr.decode(errors='replace')[-500:]}")


async def extract_thumbnail(video_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        video_path = Path(tmp) / "input.mp4"
        thumb_path = Path(tmp) / "thumb.jpg"
        video_path.write_bytes(video_bytes)
        await _run_ffmpeg(
            ["-y", "-i", str(video_path), "-ss", "00:00:00.5", "-vframes", "1", str(thumb_path)]
        )
        return thumb_path.read_bytes()


async def apply_overlays(
    video_bytes: bytes,
    *,
    headline: str | None = None,
    product_name: str | None = None,
    price: str | None = None,
    website: str | None = None,
    call_to_action: str | None = None,
    fade_in: bool = True,
    fade_out: bool = True,
    duration_seconds: float = 5.0,
) -> bytes:
    font = _resolve_font()
    drawtext_filters: list[str] = []

    lines = [line for line in [headline, product_name, price, website, call_to_action] if line]
    for index, line in enumerate(lines):
        y_offset = 60 + index * 50
        font_arg = f"fontfile='{font}':" if font else ""
        drawtext_filters.append(
            f"drawtext={font_arg}text='{_escape_drawtext(line)}':"
            f"fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-{y_offset}:"
            "box=1:boxcolor=black@0.45:boxborderw=12"
        )

    fade_filters: list[str] = []
    if fade_in:
        fade_filters.append("fade=t=in:st=0:d=0.4")
    if fade_out:
        fade_out_start = max(0.0, duration_seconds - 0.4)
        fade_filters.append(f"fade=t=out:st={fade_out_start}:d=0.4")

    filter_chain = ",".join([*drawtext_filters, *fade_filters]) or "null"

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "input.mp4"
        output_path = Path(tmp) / "output.mp4"
        input_path.write_bytes(video_bytes)
        await _run_ffmpeg(
            [
                "-y",
                "-i",
                str(input_path),
                "-vf",
                filter_chain,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        return output_path.read_bytes()
