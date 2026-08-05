from typing import Protocol

from app.schemas.plan import CampaignPlan, ChatActionPlan, GeneratedCaption, MergedPrompt


class TextGenerationProvider(Protocol):
    async def create_campaign_plan(
        self,
        *,
        product_name: str,
        product_description: str,
        target_audience: str | None,
        tone: str,
        price: str | None,
        website_url: str | None,
        image_url: str,
    ) -> CampaignPlan: ...

    async def generate_caption(
        self,
        *,
        plan: CampaignPlan,
        campaign_title: str,
        asset_title: str,
        asset_type: str,
        revision_instruction: str | None = None,
        tone_override: str | None = None,
    ) -> GeneratedCaption: ...

    async def interpret_chat(
        self,
        *,
        message: str,
        scope: str,
        selected_asset_id: str | None,
        campaign_summary: str,
        selected_asset_summary: str | None,
    ) -> ChatActionPlan: ...

    async def merge_revision(self, *, previous_prompt: str, instruction: str) -> MergedPrompt: ...
