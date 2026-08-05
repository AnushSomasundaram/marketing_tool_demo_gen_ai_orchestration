from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class CaptionVersionOut(CamelModel):
    """Matches the frontend's CaptionVersion interface exactly."""

    id: str
    text: str = Field(alias="caption")
    hashtags: list[str]
    call_to_action: str | None = None
    tone: str | None = None
    created_at: datetime


class CaptionOut(CamelModel):
    """The fuller Caption resource, for the dedicated /captions endpoints."""

    id: str
    campaign_id: str
    asset_id: str
    parent_caption_id: str | None = None
    root_caption_id: str | None = None
    version: int
    text: str = Field(alias="caption")
    hashtags: list[str]
    call_to_action: str | None = None
    tone: str | None = None
    revision_instruction: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateCaptionRequest(CamelModel):
    asset_id: str
    tone: str | None = None


class UpdateCaptionRequest(CamelModel):
    text: str | None = Field(default=None, alias="caption")
    hashtags: list[str] | None = None
    call_to_action: str | None = None


class AlternativeCaptionRequest(CamelModel):
    tone: str | None = None
