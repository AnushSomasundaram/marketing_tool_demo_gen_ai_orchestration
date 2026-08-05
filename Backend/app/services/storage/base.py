from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

ResourceType = Literal["image", "video"]


@dataclass
class StoredFile:
    url: str
    public_id: str
    resource_type: ResourceType


class StorageProvider(Protocol):
    async def upload_bytes(
        self, data: bytes, *, folder: str, filename: str, resource_type: ResourceType
    ) -> StoredFile: ...

    async def upload_file(
        self, path: Path, *, folder: str, filename: str, resource_type: ResourceType
    ) -> StoredFile: ...

    async def delete(self, public_id: str, *, resource_type: ResourceType) -> None: ...
