"""Internal planning / orchestration contracts.

These are OpenAI structured-output schemas used between the backend and the
LLM. They are never returned to the frontend directly — they get persisted
as JSON and consumed by the generation services.
"""

from pydantic import BaseModel, Field

from app.models.enums import ChatActionType


class VisualDirection(BaseModel):
    color_palette: list[str] = Field(description="3-5 hex or named colors that define the visual identity")
    lighting: str
    composition_notes: str
    mood: str


class ImageConcept(BaseModel):
    concept_name: str
    aspect_ratio: str = Field(description='Either "1:1" or "4:5"')
    scene_description: str
    prompt: str = Field(description="The full image-generation prompt for this concept")


class VideoConcept(BaseModel):
    concept_name: str
    motion_description: str
    prompt: str = Field(description="The full image-to-video motion prompt")
    duration_seconds: int = 5


class CaptionBrief(BaseModel):
    key_messages: list[str]
    tone_descriptors: list[str]
    hashtag_themes: list[str]
    call_to_action_options: list[str]


class CampaignPlan(BaseModel):
    campaign_title: str
    summary: str
    target_audience: str
    tone: str
    visual_direction: VisualDirection
    image_concepts: list[ImageConcept]
    video_concept: VideoConcept
    caption_brief: CaptionBrief
    verified_product_facts: list[str] = Field(
        description="Facts explicitly supplied by the user or visibly supported by the product image"
    )
    prohibited_or_unverified_claims: list[str] = Field(
        description="Claims that must NOT be made because they are not supported by the input"
    )


class GeneratedCaption(BaseModel):
    text: str
    hashtags: list[str]
    call_to_action: str | None = None


class ChatActionPlanItem(BaseModel):
    type: ChatActionType
    asset_id: str | None = None
    caption_id: str | None = None
    instruction: str | None = None


class ChatActionPlan(BaseModel):
    assistant_message: str
    actions: list[ChatActionPlanItem]


class MergedPrompt(BaseModel):
    """Result of merging a prior generation prompt with a new revision instruction."""

    prompt: str
