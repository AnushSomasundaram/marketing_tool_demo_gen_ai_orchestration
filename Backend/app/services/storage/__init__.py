from functools import lru_cache

from app.config import get_settings
from app.services.storage.base import ResourceType, StorageProvider, StoredFile

__all__ = ["ResourceType", "StorageProvider", "StoredFile", "get_storage_provider"]


@lru_cache
def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    if settings.use_local_storage:
        from app.services.storage.local_storage import LocalStorageProvider

        return LocalStorageProvider()

    from app.services.storage.cloudinary_storage import CloudinaryStorageProvider

    return CloudinaryStorageProvider()
