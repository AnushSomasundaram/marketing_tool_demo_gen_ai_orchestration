from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import CampaignStatus
from app.models.user import DEV_USER_ID

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.caption import Caption
    from app.models.chat_message import ChatMessage
    from app.models.generation_job import GenerationJob
    from app.models.publish_job import PublishJob
    from app.models.user import User


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), default=DEV_USER_ID, nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    product_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    product_image_storage_id: Mapped[str | None] = mapped_column(String, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String, nullable=True)
    tone: Mapped[str] = mapped_column(String, nullable=False, default="professional")
    price: Mapped[str | None] = mapped_column(String, nullable=True)
    website_url: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, default=CampaignStatus.DRAFT, nullable=False)
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    plans: Mapped[list["CampaignPlanRecord"]] = relationship(
        "CampaignPlanRecord", back_populates="campaign", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", back_populates="campaign", cascade="all, delete-orphan"
    )
    captions: Mapped[list["Caption"]] = relationship(
        "Caption", back_populates="campaign", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    jobs: Mapped[list["GenerationJob"]] = relationship(
        "GenerationJob", back_populates="campaign", cascade="all, delete-orphan"
    )
    publish_jobs: Mapped[list["PublishJob"]] = relationship(
        "PublishJob", back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignPlanRecord(Base, TimestampMixin):
    __tablename__ = "campaign_plan_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="plans")
