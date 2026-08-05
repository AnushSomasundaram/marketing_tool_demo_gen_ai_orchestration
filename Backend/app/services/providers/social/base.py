from typing import Literal, Protocol

ContainerStatus = Literal["in_progress", "finished", "error"]


class SocialPublisher(Protocol):
    """Low-level Instagram Graph API container-publishing steps. A higher-level
    InstagramPublisher service (app/services/instagram_publisher.py) drives these
    into a full publish flow and persists PublishJob state along the way."""

    async def create_container(
        self, *, ig_user_id: str, access_token: str, media_url: str, caption: str, is_video: bool
    ) -> str:
        """Returns the new container (creation) id."""
        ...

    async def get_container_status(self, *, container_id: str, access_token: str) -> ContainerStatus: ...

    async def publish_container(self, *, ig_user_id: str, access_token: str, container_id: str) -> str:
        """Returns the published media id."""
        ...

    async def get_permalink(self, *, media_id: str, access_token: str) -> str | None: ...
