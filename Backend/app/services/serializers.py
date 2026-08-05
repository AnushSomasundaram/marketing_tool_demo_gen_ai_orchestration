from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.models.enums import AssetStatus
from app.models.generation_job import GenerationJob
from app.schemas.campaign import CampaignAssetOut, CampaignOut, GenerationJobOut
from app.schemas.caption import CaptionOut, CaptionVersionOut


def get_current_caption(db: Session, asset_id: str) -> Caption | None:
    stmt = select(Caption).where(Caption.asset_id == asset_id, Caption.is_current.is_(True))
    return db.execute(stmt).scalar_one_or_none()


def get_caption_history(db: Session, asset_id: str) -> list[Caption]:
    stmt = (
        select(Caption)
        .where(Caption.asset_id == asset_id, Caption.is_current.is_(False))
        .order_by(Caption.version)
    )
    return list(db.execute(stmt).scalars().all())


def get_current_assets(db: Session, campaign_id: str) -> list[Asset]:
    stmt = (
        select(Asset)
        .where(
            Asset.campaign_id == campaign_id,
            Asset.is_current.is_(True),
            Asset.status != AssetStatus.DELETED,
        )
        .order_by(Asset.sort_order)
    )
    return list(db.execute(stmt).scalars().all())


def serialize_caption_version(caption: Caption) -> CaptionVersionOut:
    return CaptionVersionOut.model_validate(caption)


def serialize_caption(caption: Caption) -> CaptionOut:
    return CaptionOut.model_validate(caption)


def serialize_asset(db: Session, asset: Asset) -> CampaignAssetOut:
    current = get_current_caption(db, asset.id)
    history = get_caption_history(db, asset.id)
    return CampaignAssetOut(
        id=asset.id,
        asset_type=asset.asset_type,
        title=asset.title,
        preview_url=asset.preview_url,
        download_url=asset.download_url,
        caption=current.text if current else "",
        hashtags=current.hashtags if current else [],
        call_to_action=current.call_to_action if current else None,
        aspect_ratio=asset.aspect_ratio,
        duration_seconds=asset.duration_seconds,
        version=asset.version,
        status=asset.status,
        progress=asset.progress,
        error_message=asset.error_message,
        caption_history=[serialize_caption_version(c) for c in history],
    )


def serialize_campaign(db: Session, campaign: Campaign) -> CampaignOut:
    assets = get_current_assets(db, campaign.id)
    return CampaignOut(
        id=campaign.id,
        title=campaign.title,
        product_name=campaign.product_name,
        product_description=campaign.product_description,
        target_audience=campaign.target_audience,
        tone=campaign.tone,
        status=campaign.status,
        product_image_url=campaign.product_image_url,
        assets=[serialize_asset(db, asset) for asset in assets],
        created_at=campaign.created_at,
    )


def serialize_job(job: GenerationJob) -> GenerationJobOut:
    return GenerationJobOut.model_validate(job)
