from datetime import datetime

from pydantic import Field

from app.schemas.caption import CaptionVersionOut
from app.schemas.common import CamelModel


class CampaignAssetOut(CamelModel):
    """Matches the frontend's CampaignAsset interface exactly.

    Note the two intentional alias overrides: the ORM column is
    `asset_type` (JSON key `type`) and `duration_seconds` (JSON key
    `duration`), so the wire shape matches the frontend's existing
    `AssetType`/`CampaignAsset` model precisely.
    """

    id: str
    asset_type: str = Field(alias="type")
    title: str
    preview_url: str | None = None
    download_url: str | None = None
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str | None = None
    aspect_ratio: str
    duration_seconds: float | None = Field(default=None, alias="duration")
    version: int
    status: str
    progress: int | None = None
    error_message: str | None = None
    caption_history: list[CaptionVersionOut] = Field(default_factory=list)


class CampaignOut(CamelModel):
    """Matches the frontend's Campaign interface, plus productImageUrl."""

    id: str
    title: str
    product_name: str
    product_description: str
    target_audience: str | None = None
    tone: str
    status: str
    product_image_url: str | None = None
    assets: list[CampaignAssetOut] = Field(default_factory=list)
    created_at: datetime


class CampaignSummaryOut(CamelModel):
    id: str
    title: str
    product_name: str
    status: str
    created_at: datetime


class GenerationJobOut(CamelModel):
    id: str
    campaign_id: str
    asset_id: str | None = None
    job_type: str
    status: str
    progress: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
