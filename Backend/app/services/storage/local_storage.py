import shutil
from pathlib import Path

from app.config import get_settings
from app.services.exceptions import StorageError
from app.services.storage.base import ResourceType, StoredFile
from app.utils.files import is_safe_storage_segment

STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage"


class LocalStorageProvider:
    """Stores files under storage/{folder}/ and serves them via FastAPI StaticFiles."""

    def __init__(self) -> None:
        self._settings = get_settings()
        for sub in ("uploads", "generated", "composed"):
            (STORAGE_ROOT / sub).mkdir(parents=True, exist_ok=True)

    def _resolve(self, folder: str, filename: str) -> Path:
        if not is_safe_storage_segment(folder) or not is_safe_storage_segment(filename):
            raise StorageError("Invalid storage path.")
        return STORAGE_ROOT / folder / filename

    def _public_url(self, folder: str, filename: str) -> str:
        base = self._settings.public_base_url.rstrip("/")
        return f"{base}/storage/{folder}/{filename}"

    async def upload_bytes(
        self, data: bytes, *, folder: str, filename: str, resource_type: ResourceType
    ) -> StoredFile:
        destination = self._resolve(folder, filename)
        destination.write_bytes(data)
        public_id = f"{folder}/{filename}"
        return StoredFile(
            url=self._public_url(folder, filename), public_id=public_id, resource_type=resource_type
        )

    async def upload_file(
        self, path: Path, *, folder: str, filename: str, resource_type: ResourceType
    ) -> StoredFile:
        destination = self._resolve(folder, filename)
        if path.resolve() != destination.resolve():
            shutil.copyfile(path, destination)
        public_id = f"{folder}/{filename}"
        return StoredFile(
            url=self._public_url(folder, filename), public_id=public_id, resource_type=resource_type
        )

    async def delete(self, public_id: str, *, resource_type: ResourceType) -> None:
        del resource_type
        target = STORAGE_ROOT / public_id
        try:
            target.relative_to(STORAGE_ROOT)
        except ValueError as exc:
            raise StorageError("Refusing to delete outside storage root.") from exc
        target.unlink(missing_ok=True)
