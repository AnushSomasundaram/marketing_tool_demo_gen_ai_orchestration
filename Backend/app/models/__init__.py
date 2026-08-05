"""Import every model module so all classes register on Base's mapper registry
before any relationship() string targets or Alembic autogenerate need them."""

from app.models.asset import Asset
from app.models.campaign import Campaign, CampaignPlanRecord
from app.models.caption import Caption
from app.models.chat_message import ChatMessage
from app.models.generation_job import GenerationJob
from app.models.publish_job import PublishJob
from app.models.social_account import SocialAccount
from app.models.user import DEV_USER_ID, User

__all__ = [
    "Asset",
    "Campaign",
    "CampaignPlanRecord",
    "Caption",
    "ChatMessage",
    "GenerationJob",
    "PublishJob",
    "SocialAccount",
    "User",
    "DEV_USER_ID",
]
