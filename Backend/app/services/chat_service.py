"""Orchestrates one chat turn: save the user message, ask the OpenAI orchestration
model to translate it into a validated action plan, execute what's allowed, and
return the assistant message + updated campaign state.

Every action is validated against the request's scope before execution — the
model's output is never trusted blindly. See ALLOWED_ACTIONS_BY_SCOPE below.
"""

import json

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.chat_message import ChatMessage
from app.models.enums import AssetType, ChatActionType, ChatRole
from app.schemas.plan import ChatActionPlanItem
from app.services import asset_service, caption_service, generation_service
from app.services.exceptions import ProviderError, StaleVersionError
from app.services.providers.factory import get_text_provider
from app.services.serializers import get_current_assets, get_current_caption, serialize_campaign

ALLOWED_ACTIONS_BY_SCOPE: dict[str, set[ChatActionType]] = {
    "campaign": {
        ChatActionType.REVISE_CAMPAIGN_PLAN,
        ChatActionType.REGENERATE_ALL_IMAGES,
        ChatActionType.REGENERATE_VIDEO,
        ChatActionType.NO_ACTION,
        ChatActionType.REQUEST_CLARIFICATION,
    },
    "selected_asset": {
        ChatActionType.REVISE_IMAGE,
        ChatActionType.REVISE_VIDEO,
        ChatActionType.REVISE_CAPTION,
        ChatActionType.NO_ACTION,
        ChatActionType.REQUEST_CLARIFICATION,
    },
    "caption_only": {
        ChatActionType.REVISE_CAPTION,
        ChatActionType.GENERATE_CAPTION_ALTERNATIVE,
        ChatActionType.NO_ACTION,
        ChatActionType.REQUEST_CLARIFICATION,
    },
    "visual_only": {
        ChatActionType.REVISE_IMAGE,
        ChatActionType.REVISE_VIDEO,
        ChatActionType.UPDATE_VIDEO_OVERLAYS,
        ChatActionType.NO_ACTION,
        ChatActionType.REQUEST_CLARIFICATION,
    },
}

# Actions fast enough to run synchronously within the chat request/response cycle.
SYNCHRONOUS_ACTIONS = {ChatActionType.REVISE_CAPTION, ChatActionType.GENERATE_CAPTION_ALTERNATIVE}


def _validate_actions(
    actions: list[ChatActionPlanItem],
    *,
    scope: str,
    selected_asset_id: str | None,
    campaign_asset_ids: set[str],
) -> list[ChatActionPlanItem]:
    allowed_types = ALLOWED_ACTIONS_BY_SCOPE.get(scope, set())
    validated: list[ChatActionPlanItem] = []

    for action in actions:
        if action.type not in allowed_types:
            continue

        if scope != "campaign":
            if not selected_asset_id:
                continue  # scope requires an asset but none was selected — drop everything
            # Never trust a model-supplied assetId for scoped requests: force it to the
            # one the user actually had selected in the UI.
            action.asset_id = selected_asset_id

        if action.asset_id is not None and action.asset_id not in campaign_asset_ids:
            continue  # asset doesn't belong to this campaign — refuse to touch it

        validated.append(action)

    return validated


async def _execute_action(
    db: Session,
    campaign: Campaign,
    action: ChatActionPlanItem,
    background_tasks: BackgroundTasks,
) -> None:
    if action.type == ChatActionType.NO_ACTION or action.type == ChatActionType.REQUEST_CLARIFICATION:
        return

    if action.type == ChatActionType.REGENERATE_ALL_IMAGES:
        background_tasks.add_task(generation_service.regenerate_all_images, campaign.id)
        return

    if action.type == ChatActionType.REGENERATE_VIDEO:
        background_tasks.add_task(generation_service.regenerate_video, campaign.id)
        return

    if action.type == ChatActionType.REVISE_CAMPAIGN_PLAN:
        # Simplified scope decision (documented in the README): cascades the
        # instruction as a revision across every current asset rather than
        # mutating the structured plan itself.
        background_tasks.add_task(generation_service.regenerate_all_images, campaign.id)
        background_tasks.add_task(generation_service.regenerate_video, campaign.id)
        return

    if action.type in (
        ChatActionType.REVISE_IMAGE,
        ChatActionType.REVISE_VIDEO,
        ChatActionType.UPDATE_VIDEO_OVERLAYS,
    ):
        if not action.asset_id:
            return
        asset = db.get(Asset, action.asset_id)
        if asset is None or asset.campaign_id != campaign.id:
            return

        if action.type == ChatActionType.REVISE_IMAGE and asset.asset_type == AssetType.IMAGE:
            # Create the new (queued) version synchronously, same as the direct
            # "Regenerate" endpoint — this must not be part of the background
            # task, or the chat response returns before the new asset even
            # exists and the frontend's post-chat refresh sees nothing new.
            try:
                new_asset = await asset_service.create_image_revision(db, asset, instruction=action.instruction)
            except StaleVersionError:
                return  # asset changed concurrently; drop this action rather than fail the whole chat turn
            background_tasks.add_task(asset_service.generate_image_revision, new_asset.id)
        elif action.type == ChatActionType.REVISE_VIDEO and asset.asset_type == AssetType.VIDEO:
            try:
                new_asset = await asset_service.create_video_revision(db, asset, instruction=action.instruction)
            except StaleVersionError:
                return
            background_tasks.add_task(asset_service.generate_video_revision, new_asset.id)
        elif action.type == ChatActionType.UPDATE_VIDEO_OVERLAYS and asset.asset_type == AssetType.VIDEO:
            background_tasks.add_task(
                asset_service.update_asset_overlays_by_id,
                asset.id,
                headline=action.instruction,
                product_name=None,
                price=None,
                website=None,
                call_to_action=None,
                fade_in=True,
                fade_out=True,
            )
        return

    if action.type in (ChatActionType.REVISE_CAPTION, ChatActionType.GENERATE_CAPTION_ALTERNATIVE):
        if not action.asset_id:
            return
        caption = get_current_caption(db, action.asset_id)
        if caption is None:
            return
        try:
            if action.type == ChatActionType.REVISE_CAPTION:
                await caption_service.revise_caption(db, caption, instruction=action.instruction or "")
            else:
                await caption_service.generate_alternative_caption(db, caption, tone=None)
        except ProviderError:
            pass  # caption revision failing shouldn't fail the whole chat turn


async def handle_chat_turn(
    db: Session,
    campaign: Campaign,
    *,
    message: str,
    scope: str,
    selected_asset_id: str | None,
    background_tasks: BackgroundTasks,
) -> tuple[ChatMessage, list[ChatActionPlanItem]]:
    db.add(
        ChatMessage(
            campaign_id=campaign.id,
            role=ChatRole.USER,
            content=message,
            scope=scope,
            selected_asset_id=selected_asset_id,
        )
    )
    db.commit()

    current_assets = get_current_assets(db, campaign.id)
    campaign_asset_ids = {a.id for a in current_assets}
    selected_asset = next((a for a in current_assets if a.id == selected_asset_id), None)

    text_provider = get_text_provider()
    try:
        plan = await text_provider.interpret_chat(
            message=message,
            scope=scope,
            selected_asset_id=selected_asset_id,
            campaign_summary=f"{campaign.title}: {campaign.product_description}",
            selected_asset_summary=f"{selected_asset.title} ({selected_asset.asset_type})"
            if selected_asset
            else None,
        )
    except ProviderError as exc:
        assistant = ChatMessage(
            campaign_id=campaign.id,
            role=ChatRole.ASSISTANT,
            content=f"Sorry, I couldn't process that: {exc.message}",
        )
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        return assistant, []

    validated_actions = _validate_actions(
        plan.actions, scope=scope, selected_asset_id=selected_asset_id, campaign_asset_ids=campaign_asset_ids
    )

    assistant = ChatMessage(
        campaign_id=campaign.id,
        role=ChatRole.ASSISTANT,
        content=plan.assistant_message,
        actions_json=json.dumps([a.model_dump(mode="json") for a in validated_actions]),
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)

    for action in validated_actions:
        await _execute_action(db, campaign, action, background_tasks)

    return assistant, validated_actions


def build_response_campaign(db: Session, campaign_id: str):
    campaign = db.get(Campaign, campaign_id)
    return serialize_campaign(db, campaign) if campaign else None
