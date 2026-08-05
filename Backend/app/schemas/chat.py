from datetime import datetime

from app.models.enums import ChatActionType
from app.schemas.campaign import CampaignOut
from app.schemas.common import CamelModel


class ChatRequest(CamelModel):
    message: str
    scope: str
    selected_asset_id: str | None = None


class ChatActionOut(CamelModel):
    type: ChatActionType
    asset_id: str | None = None
    caption_id: str | None = None
    instruction: str | None = None


class ChatTurnResponse(CamelModel):
    """Shaped so the top-level fields alone satisfy the frontend's existing
    ChatMessage contract (id/role/content/createdAt), while `actions` and
    `campaign` carry the richer orchestration result for clients that use it.
    """

    id: str
    role: str
    content: str
    created_at: datetime
    assistant_message: str
    actions: list[ChatActionOut]
    campaign: CampaignOut
