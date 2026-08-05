from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.user import DEV_USER_ID

if TYPE_CHECKING:
    from app.models.user import User


class SocialAccount(Base, TimestampMixin):
    __tablename__ = "social_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), default=DEV_USER_ID, nullable=False)
    platform: Mapped[str] = mapped_column(String, default="instagram", nullable=False)

    # Demo-scoped storage. In production this token would be encrypted at rest.
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    instagram_business_account_id: Mapped[str | None] = mapped_column(String, nullable=True)
    page_id: Mapped[str | None] = mapped_column(String, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="social_accounts")
