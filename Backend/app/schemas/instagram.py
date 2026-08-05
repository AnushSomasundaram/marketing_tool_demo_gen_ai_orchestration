from datetime import datetime

from app.schemas.common import CamelModel


class InstagramConnectResponse(CamelModel):
    authorization_url: str
    demo_mode: bool


class InstagramAccountOut(CamelModel):
    id: str
    platform: str
    instagram_business_account_id: str | None = None
    connected: bool


class PublishRequest(CamelModel):
    campaign_id: str
    asset_id: str
    caption_id: str | None = None
    is_ai_generated: bool = True


class PublishJobOut(CamelModel):
    id: str
    campaign_id: str
    asset_id: str
    caption_id: str | None = None
    status: str
    is_ai_generated: bool
    is_simulated: bool
    instagram_media_id: str | None = None
    permalink: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
