import asyncio
from pathlib import Path

import cloudinary
import cloudinary.uploader

from app.config import get_settings
from app.services.exceptions import StorageError
from app.services.storage.base import ResourceType, StoredFile


class CloudinaryStorageProvider:
    def __init__(self) -> None:
        settings = get_settings()
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    async def upload_bytes(
        self, data: bytes, *, folder: str, filename: str, resource_type: ResourceType
    ) -> StoredFile:
        try:
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                data,
                folder=folder,
                public_id=Path(filename).stem,
                resource_type=resource_type,
                overwrite=True,
            )
        except Exception as exc:  # cloudinary raises its own generic Error type
            raise StorageError(f"Cloudinary upload failed: {exc}") from exc
        return StoredFile(
            url=result["secure_url"], public_id=result["public_id"], resource_type=resource_type
        )

    async def upload_file(
        self, path: Path, *, folder: str, filename: str, resource_type: ResourceType
    ) -> StoredFile:
        try:
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                str(path),
                folder=folder,
                public_id=Path(filename).stem,
                resource_type=resource_type,
                overwrite=True,
            )
        except Exception as exc:
            raise StorageError(f"Cloudinary upload failed: {exc}") from exc
        return StoredFile(
            url=result["secure_url"], public_id=result["public_id"], resource_type=resource_type
        )

    async def delete(self, public_id: str, *, resource_type: ResourceType) -> None:
        try:
            await asyncio.to_thread(cloudinary.uploader.destroy, public_id, resource_type=resource_type)
        except Exception as exc:
            raise StorageError(f"Cloudinary delete failed: {exc}") from exc
