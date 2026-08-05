from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.services.exceptions import StaleVersionError
from app.services.plan_utils import load_campaign_plan as _load_plan
from app.services.providers.factory import get_text_provider


async def create_caption(db: Session, campaign: Campaign, asset: Asset, *, tone: str | None) -> Caption:
    plan = _load_plan(campaign)
    if plan is not None:
        generated = await get_text_provider().generate_caption(
            plan=plan,
            campaign_title=campaign.title,
            asset_title=asset.title,
            asset_type=asset.asset_type,
            tone_override=tone,
        )
        text, hashtags, cta = generated.text, generated.hashtags, generated.call_to_action
    else:
        text, hashtags, cta = f"{campaign.product_name} — {campaign.product_description[:120]}", [], None

    caption = Caption(
        campaign_id=campaign.id,
        asset_id=asset.id,
        version=1,
        text=text,
        call_to_action=cta,
        tone=tone or campaign.tone,
        is_current=True,
    )
    caption.hashtags = hashtags
    db.add(caption)
    db.commit()
    db.refresh(caption)
    return caption


def _spawn_next_version(
    db: Session,
    old_caption: Caption,
    *,
    text: str,
    hashtags: list[str],
    call_to_action: str | None,
    tone: str | None,
    revision_instruction: str | None,
) -> Caption:
    if not old_caption.is_current:
        raise StaleVersionError("This caption version is no longer current. Refresh and try again.")

    new_caption = Caption(
        campaign_id=old_caption.campaign_id,
        asset_id=old_caption.asset_id,
        parent_caption_id=old_caption.id,
        root_caption_id=old_caption.root_caption_id or old_caption.id,
        version=old_caption.version + 1,
        text=text,
        call_to_action=call_to_action,
        tone=tone or old_caption.tone,
        revision_instruction=revision_instruction,
        is_current=True,
    )
    new_caption.hashtags = hashtags
    old_caption.is_current = False
    db.add(new_caption)
    db.commit()
    db.refresh(new_caption)
    return new_caption


def update_caption(
    db: Session,
    caption: Caption,
    *,
    text: str | None,
    hashtags: list[str] | None,
    call_to_action: str | None,
) -> Caption:
    """A manual (non-AI) edit still creates a new version, so caption history
    captures every change, not just AI revisions."""
    return _spawn_next_version(
        db,
        caption,
        text=text if text is not None else caption.text,
        hashtags=hashtags if hashtags is not None else caption.hashtags,
        call_to_action=call_to_action if call_to_action is not None else caption.call_to_action,
        tone=caption.tone,
        revision_instruction=None,
    )


async def revise_caption(db: Session, caption: Caption, *, instruction: str) -> Caption:
    campaign = db.get(Campaign, caption.campaign_id)
    asset = db.get(Asset, caption.asset_id)
    plan = _load_plan(campaign) if campaign else None
    if campaign is None or asset is None or plan is None:
        return update_caption(
            db, caption, text=f"{caption.text} ({instruction})", hashtags=None, call_to_action=None
        )

    generated = await get_text_provider().generate_caption(
        plan=plan,
        campaign_title=campaign.title,
        asset_title=asset.title,
        asset_type=asset.asset_type,
        revision_instruction=instruction,
    )
    return _spawn_next_version(
        db,
        caption,
        text=generated.text,
        hashtags=generated.hashtags,
        call_to_action=generated.call_to_action,
        tone=caption.tone,
        revision_instruction=instruction,
    )


async def generate_alternative_caption(db: Session, caption: Caption, *, tone: str | None) -> Caption:
    campaign = db.get(Campaign, caption.campaign_id)
    asset = db.get(Asset, caption.asset_id)
    plan = _load_plan(campaign) if campaign else None
    if campaign is None or asset is None or plan is None:
        return update_caption(
            db, caption, text=caption.text, hashtags=caption.hashtags, call_to_action=caption.call_to_action
        )

    generated = await get_text_provider().generate_caption(
        plan=plan,
        campaign_title=campaign.title,
        asset_title=asset.title,
        asset_type=asset.asset_type,
        tone_override=tone,
    )
    return _spawn_next_version(
        db,
        caption,
        text=generated.text,
        hashtags=generated.hashtags,
        call_to_action=generated.call_to_action,
        tone=tone or caption.tone,
        revision_instruction=None,
    )


def list_caption_versions(db: Session, caption_id: str) -> list[Caption]:
    caption = db.get(Caption, caption_id)
    if caption is None:
        return []
    root_id = caption.root_caption_id or caption.id
    return (
        db.query(Caption)
        .filter((Caption.id == root_id) | (Caption.root_caption_id == root_id))
        .order_by(Caption.version)
        .all()
    )


def restore_caption_version(db: Session, current_caption: Caption, version_caption: Caption) -> Caption:
    return _spawn_next_version(
        db,
        current_caption,
        text=version_caption.text,
        hashtags=version_caption.hashtags,
        call_to_action=version_caption.call_to_action,
        tone=version_caption.tone,
        revision_instruction=f"Restored from version {version_caption.version}",
    )
