import json
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import AssetStatus, AssetType

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.caption import Caption


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    parent_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    root_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    asset_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=AssetStatus.QUEUED, nullable=False)

    # Marks the current/active version among an asset's version chain (mirrors
    # Caption.is_current). sort_order is copied across revisions so the asset
    # grid's card order stays stable regardless of which version is current.
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    generation_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)

    preview_url: Mapped[str | None] = mapped_column(String, nullable=True)
    download_url: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_public_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # For video assets: the untouched AI-generated output, kept separate from
    # download_url so the overlays endpoint always composes from the original
    # instead of compounding overlays on top of a previous composition.
    raw_video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_video_storage_public_id: Mapped[str | None] = mapped_column(String, nullable=True)

    external_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    external_task_id: Mapped[str | None] = mapped_column(String, nullable=True)

    aspect_ratio: Mapped[str] = mapped_column(String, nullable=False, default="1:1")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Latest applied overlay configuration (JSON-encoded), used by the
    # overlays endpoint to re-compose a video without a new AI generation.
    overlay_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="assets")
    captions: Mapped[list["Caption"]] = relationship(
        "Caption",
        back_populates="asset",
        cascade="all, delete-orphan",
        foreign_keys="Caption.asset_id",
    )

    @property
    def is_video(self) -> bool:
        return self.asset_type == AssetType.VIDEO

    @property
    def overlay(self) -> dict:
        return json.loads(self.overlay_json) if self.overlay_json else {}

    @overlay.setter
    def overlay(self, value: dict) -> None:
        self.overlay_json = json.dumps(value)
