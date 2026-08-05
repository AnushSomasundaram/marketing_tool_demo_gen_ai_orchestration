from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from app.config import get_settings
from app.prompts import campaign_planner, caption_generator, chat_router, revision_merger
from app.schemas.plan import CampaignPlan, ChatActionPlan, GeneratedCaption, MergedPrompt
from app.services.exceptions import (
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderSafetyError,
    ProviderTaskFailedError,
    ProviderTimeoutError,
)

REQUEST_TIMEOUT_SECONDS = 60.0


class OpenAITextProvider:
    """Uses the OpenAI Responses API with structured outputs for every text task."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderNotConfiguredError("OpenAI", provider="openai")
        self._model = settings.openai_text_model
        self._client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    async def _parse(self, *, instructions: str, input_, text_format: type):
        try:
            response = await self._client.responses.parse(
                model=self._model,
                instructions=instructions,
                input=input_,
                text_format=text_format,
            )
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc), provider="openai") from exc
        except APIConnectionError as exc:
            raise ProviderTimeoutError(str(exc), provider="openai") from exc
        except APIStatusError as exc:
            if exc.status_code == 401:
                raise ProviderAuthenticationError(str(exc), provider="openai") from exc
            if exc.status_code in (400, 422) and "safety" in str(exc).lower():
                raise ProviderSafetyError(str(exc), provider="openai") from exc
            # Any other rejection must still become a ProviderError — callers
            # only catch that hierarchy, so re-raising the raw SDK exception
            # here left campaigns stuck mid-generation instead of failing
            # cleanly with a reportable message.
            raise ProviderTaskFailedError(str(exc), provider="openai") from exc
        parsed = response.output_parsed
        if parsed is None:
            raise ProviderSafetyError("Model declined to produce structured output.", provider="openai")
        return parsed

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
        user_prompt = campaign_planner.build_user_prompt(
            product_name=product_name,
            product_description=product_description,
            target_audience=target_audience,
            tone=tone,
            price=price,
            website_url=website_url,
        )
        input_ = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ]
        return await self._parse(
            instructions=campaign_planner.SYSTEM_PROMPT, input_=input_, text_format=CampaignPlan
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
        user_prompt = caption_generator.build_user_prompt(
            campaign_title=campaign_title,
            asset_title=asset_title,
            asset_type=asset_type,
            key_messages=plan.caption_brief.key_messages,
            tone_descriptors=plan.caption_brief.tone_descriptors,
            hashtag_themes=plan.caption_brief.hashtag_themes,
            call_to_action_options=plan.caption_brief.call_to_action_options,
            verified_product_facts=plan.verified_product_facts,
            prohibited_or_unverified_claims=plan.prohibited_or_unverified_claims,
            revision_instruction=revision_instruction,
            tone_override=tone_override,
        )
        return await self._parse(
            instructions=caption_generator.SYSTEM_PROMPT, input_=user_prompt, text_format=GeneratedCaption
        )

    async def interpret_chat(
        self,
        *,
        message: str,
        scope: str,
        selected_asset_id: str | None,
        campaign_summary: str,
        selected_asset_summary: str | None,
    ) -> ChatActionPlan:
        user_prompt = chat_router.build_user_prompt(
            message=message,
            scope=scope,
            selected_asset_id=selected_asset_id,
            campaign_summary=campaign_summary,
            selected_asset_summary=selected_asset_summary,
        )
        return await self._parse(
            instructions=chat_router.SYSTEM_PROMPT, input_=user_prompt, text_format=ChatActionPlan
        )

    async def merge_revision(self, *, previous_prompt: str, instruction: str) -> MergedPrompt:
        user_prompt = revision_merger.build_user_prompt(
            previous_prompt=previous_prompt, instruction=instruction
        )
        return await self._parse(
            instructions=revision_merger.SYSTEM_PROMPT, input_=user_prompt, text_format=MergedPrompt
        )
