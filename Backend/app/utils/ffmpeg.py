import shutil

from app.config import get_settings


def ffmpeg_available() -> bool:
    settings = get_settings()
    return shutil.which(settings.ffmpeg_binary) is not None


def ffmpeg_path() -> str | None:
    settings = get_settings()
    return shutil.which(settings.ffmpeg_binary)
