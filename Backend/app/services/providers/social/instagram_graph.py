import httpx

from app.config import get_settings
from app.services.exceptions import (
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
)
from app.services.providers.social.base import ContainerStatus

REQUEST_TIMEOUT_SECONDS = 30.0

_STATUS_MAP: dict[str, ContainerStatus] = {
    "IN_PROGRESS": "in_progress",
    "PUBLISHED": "finished",
    "FINISHED": "finished",
    "ERROR": "error",
    "EXPIRED": "error",
}


def build_authorization_url(*, state: str) -> str:
    settings = get_settings()
    if not settings.meta_app_id:
        raise ProviderNotConfiguredError("Instagram", provider="instagram")
    scopes = "instagram_basic,instagram_content_publish,pages_show_list,business_management"
    return (
        "https://www.facebook.com/"
        f"{settings.instagram_api_version}/dialog/oauth"
        f"?client_id={settings.meta_app_id}"
        f"&redirect_uri={settings.meta_redirect_uri}"
        f"&state={state}"
        f"&scope={scopes}"
    )


async def exchange_code_for_token(*, code: str) -> dict:
    settings = get_settings()
    if not (settings.meta_app_id and settings.meta_app_secret):
        raise ProviderNotConfiguredError("Instagram", provider="instagram")

    url = f"https://graph.facebook.com/{settings.instagram_api_version}/oauth/access_token"
    params = {
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "redirect_uri": settings.meta_redirect_uri,
        "code": code,
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(url, params=params)
    if response.status_code == 401:
        raise ProviderAuthenticationError("Meta rejected the OAuth code.", provider="instagram")
    response.raise_for_status()
    return response.json()


async def fetch_instagram_business_account(*, access_token: str) -> dict | None:
    """Walks /me/accounts to find the first Facebook Page with a connected
    Instagram professional account, per the standard Graph API onboarding flow."""
    settings = get_settings()
    url = f"https://graph.facebook.com/{settings.instagram_api_version}/me/accounts"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(
            url, params={"access_token": access_token, "fields": "id,instagram_business_account"}
        )
    response.raise_for_status()
    for page in response.json().get("data", []):
        ig_account = page.get("instagram_business_account")
        if ig_account:
            return {"page_id": page["id"], "instagram_business_account_id": ig_account["id"]}
    return None


class InstagramGraphPublisher:
    """Real Instagram Graph API publisher. Requires INSTAGRAM_DEMO_MODE=false and a
    connected SocialAccount with a valid access token."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_version = settings.instagram_api_version
        self._base_url = f"https://graph.facebook.com/{self._api_version}"

    async def create_container(
        self, *, ig_user_id: str, access_token: str, media_url: str, caption: str, is_video: bool
    ) -> str:
        payload: dict = {"caption": caption, "access_token": access_token}
        if is_video:
            payload["media_type"] = "REELS"
            payload["video_url"] = media_url
        else:
            payload["image_url"] = media_url

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(f"{self._base_url}/{ig_user_id}/media", data=payload)
            except httpx.TimeoutException as exc:
                raise ProviderTimeoutError(str(exc), provider="instagram") from exc
        if response.status_code == 401:
            raise ProviderAuthenticationError("Instagram rejected the access token.", provider="instagram")
        response.raise_for_status()
        return response.json()["id"]

    async def get_container_status(self, *, container_id: str, access_token: str) -> ContainerStatus:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{self._base_url}/{container_id}",
                params={"fields": "status_code", "access_token": access_token},
            )
        response.raise_for_status()
        return _STATUS_MAP.get(response.json().get("status_code", ""), "in_progress")

    async def publish_container(self, *, ig_user_id: str, access_token: str, container_id: str) -> str:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self._base_url}/{ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": access_token},
            )
        if response.status_code == 401:
            raise ProviderAuthenticationError("Instagram rejected the access token.", provider="instagram")
        response.raise_for_status()
        return response.json()["id"]

    async def get_permalink(self, *, media_id: str, access_token: str) -> str | None:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{self._base_url}/{media_id}", params={"fields": "permalink", "access_token": access_token}
            )
        if response.status_code != 200:
            return None
        return response.json().get("permalink")
