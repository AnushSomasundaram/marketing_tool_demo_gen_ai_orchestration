import json
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.campaign import Campaign


class Caption(Base, TimestampMixin):
    __tablename__ = "captions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=False)
    parent_caption_id: Mapped[str | None] = mapped_column(ForeignKey("captions.id"), nullable=True)
    root_caption_id: Mapped[str | None] = mapped_column(ForeignKey("captions.id"), nullable=True)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    call_to_action: Mapped[str | None] = mapped_column(String, nullable=True)
    tone: Mapped[str | None] = mapped_column(String, nullable=True)
    revision_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Marks the current/active version among a caption's version chain.
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="captions")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="captions", foreign_keys=[asset_id])

    @property
    def hashtags(self) -> list[str]:
        return json.loads(self.hashtags_json) if self.hashtags_json else []

    @hashtags.setter
    def hashtags(self, value: list[str]) -> None:
        self.hashtags_json = json.dumps(value)
