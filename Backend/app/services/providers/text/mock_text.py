import asyncio

from app.models.enums import ChatActionType
from app.schemas.plan import (
    CampaignPlan,
    CaptionBrief,
    ChatActionPlan,
    ChatActionPlanItem,
    GeneratedCaption,
    ImageConcept,
    MergedPrompt,
    VideoConcept,
    VisualDirection,
)

TONE_DESCRIPTORS = {
    "professional": ["polished", "trustworthy", "confident"],
    "playful": ["fun", "casual", "cheeky"],
    "minimal": ["clean", "understated", "quiet"],
    "luxury": ["refined", "premium", "aspirational"],
    "energetic": ["bold", "vibrant", "high-energy"],
}


class MockTextProvider:
    """Deterministic, offline stand-in for the OpenAI text provider."""

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
    ) -> CampaignPlan:
        del image_url
        await asyncio.sleep(0.3)
        descriptors = TONE_DESCRIPTORS.get(tone, TONE_DESCRIPTORS["professional"])
        facts = [f"Product name: {product_name}", f"Description: {product_description}"]
        if price:
            facts.append(f"Price: {price}")

        audience = target_audience or "its target audience"
        return CampaignPlan(
            campaign_title=f"{product_name} Campaign",
            summary=f"A {tone} campaign introducing {product_name} to {audience}.",
            target_audience=target_audience or "General audience",
            tone=tone,
            visual_direction=VisualDirection(
                color_palette=["#1b1b18", "#f7f7f6", "#c9a876"],
                lighting="soft, directional studio lighting",
                composition_notes="product centered with generous negative space",
                mood=", ".join(descriptors),
            ),
            image_concepts=[
                ImageConcept(
                    concept_name="Studio Feed Post",
                    aspect_ratio="1:1",
                    scene_description=f"{product_name} on a clean studio backdrop",
                    prompt=(
                        f"A {', '.join(descriptors)} studio product photo of {product_name}, "
                        f"{product_description}, centered composition, soft shadows."
                    ),
                ),
                ImageConcept(
                    concept_name="Lifestyle Feed Post",
                    aspect_ratio="4:5",
                    scene_description=f"{product_name} in a natural, in-use setting",
                    prompt=(
                        f"A {', '.join(descriptors)} lifestyle photo featuring {product_name} in context, "
                        f"{product_description}, natural lighting."
                    ),
                ),
            ],
            video_concept=VideoConcept(
                concept_name="Product Reveal",
                motion_description=(
                    f"Slow, elegant rotation and gentle push-in on {product_name}, "
                    "clean product-focused motion, no camera shake."
                ),
                prompt=(
                    f"Slow rotating hero shot of {product_name} on a studio backdrop, "
                    f"{', '.join(descriptors)} mood, smooth camera motion."
                ),
                duration_seconds=5,
            ),
            caption_brief=CaptionBrief(
                key_messages=[product_description[:120]],
                tone_descriptors=descriptors,
                hashtag_themes=[product_name.replace(" ", ""), tone, "NewArrival"],
                call_to_action_options=["Shop now", "Learn more", "Discover more"]
                if website_url
                else ["Learn more"],
            ),
            verified_product_facts=facts,
            prohibited_or_unverified_claims=[
                "Any medical, health, or performance claim not stated by the user",
                "Any certification or environmental claim not stated by the user",
            ],
        )

    async def generate_caption(
        self,
        *,
        plan: CampaignPlan,
        campaign_title: str,
        asset_title: str,
        asset_type: str,
        revision_instruction: str | None = None,
        tone_override: str | None = None,
    ) -> GeneratedCaption:
        del campaign_title, asset_type
        await asyncio.sleep(0.2)
        message = plan.caption_brief.key_messages[0] if plan.caption_brief.key_messages else plan.summary
        text = f"{plan.campaign_title.replace(' Campaign', '')} — {message}"
        if tone_override:
            descriptors = TONE_DESCRIPTORS.get(tone_override, [tone_override])
            text = f"{text} ({descriptors[0]} take)"
        if revision_instruction:
            text = f"{text} ({revision_instruction})"
        cta = (
            plan.caption_brief.call_to_action_options[0]
            if plan.caption_brief.call_to_action_options
            else None
        )
        hashtags = [f"#{theme.replace(' ', '')}" for theme in plan.caption_brief.hashtag_themes]
        del asset_title
        return GeneratedCaption(text=text, hashtags=hashtags, call_to_action=cta)

    async def interpret_chat(
        self,
        *,
        message: str,
        scope: str,
        selected_asset_id: str | None,
        campaign_summary: str,
        selected_asset_summary: str | None,
    ) -> ChatActionPlan:
        del campaign_summary, selected_asset_summary
        await asyncio.sleep(0.2)

        if scope == "campaign":
            return ChatActionPlan(
                assistant_message="Got it — I'm reworking the entire campaign now.",
                actions=[ChatActionPlanItem(type=ChatActionType.REGENERATE_ALL_IMAGES, instruction=message)],
            )
        if not selected_asset_id:
            return ChatActionPlan(
                assistant_message="Which post or video should I apply that to?",
                actions=[ChatActionPlanItem(type=ChatActionType.REQUEST_CLARIFICATION)],
            )
        if scope == "caption_only":
            return ChatActionPlan(
                assistant_message="Updating just the caption now.",
                actions=[
                    ChatActionPlanItem(
                        type=ChatActionType.REVISE_CAPTION, asset_id=selected_asset_id, instruction=message
                    )
                ],
            )
        if scope == "visual_only":
            return ChatActionPlan(
                assistant_message="Reworking the visual now, caption stays as-is.",
                actions=[
                    ChatActionPlanItem(
                        type=ChatActionType.REVISE_IMAGE, asset_id=selected_asset_id, instruction=message
                    )
                ],
            )
        return ChatActionPlan(
            assistant_message="Updating that asset now.",
            actions=[
                ChatActionPlanItem(
                    type=ChatActionType.REVISE_IMAGE, asset_id=selected_asset_id, instruction=message
                )
            ],
        )

    async def merge_revision(self, *, previous_prompt: str, instruction: str) -> MergedPrompt:
        await asyncio.sleep(0.1)
        return MergedPrompt(prompt=f"{previous_prompt.strip()} Additionally: {instruction.strip()}")
