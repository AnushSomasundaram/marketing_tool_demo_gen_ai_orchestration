from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import AssetStatus, CampaignStatus
from app.models.user import DEV_USER_ID
from app.services.serializers import get_current_assets
from app.services.storage import get_storage_provider
from app.utils.files import safe_filename


async def create_campaign(
    db: Session,
    *,
    product_name: str,
    product_description: str,
    target_audience: str | None,
    tone: str,
    price: str | None,
    website_url: str | None,
    image_bytes: bytes,
    image_content_type: str,
) -> Campaign:
    storage = get_storage_provider()
    filename = safe_filename(None, image_content_type)
    stored = await storage.upload_bytes(
        image_bytes, folder="uploads", filename=filename, resource_type="image"
    )

    campaign = Campaign(
        user_id=DEV_USER_ID,
        title=f"{product_name} Campaign",
        product_name=product_name,
        product_description=product_description,
        target_audience=target_audience,
        tone=tone,
        price=price,
        website_url=website_url,
        product_image_url=stored.url,
        product_image_storage_id=stored.public_id,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def list_campaigns(db: Session) -> list[Campaign]:
    stmt = select(Campaign).where(Campaign.user_id == DEV_USER_ID).order_by(Campaign.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def delete_campaign(db: Session, campaign: Campaign) -> None:
    db.delete(campaign)
    db.commit()


def recompute_campaign_status(db: Session, campaign_id: str) -> None:
    """Re-derive campaign.status from its current assets' statuses. Called after
    every asset transition (image/video completion or failure)."""
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        return
    if campaign.status in (CampaignStatus.PUBLISHING, CampaignStatus.PUBLISHED):
        return  # publishing state is driven by the publish flow, not asset status

    assets = get_current_assets(db, campaign_id)
    if not assets:
        return

    statuses = {a.status for a in assets}
    if statuses <= {AssetStatus.COMPLETED}:
        campaign.status = CampaignStatus.READY
    elif AssetStatus.PROCESSING in statuses or AssetStatus.QUEUED in statuses:
        campaign.status = CampaignStatus.GENERATING
    elif AssetStatus.COMPLETED in statuses and AssetStatus.FAILED in statuses:
        campaign.status = CampaignStatus.PARTIALLY_FAILED
    elif statuses <= {AssetStatus.FAILED}:
        campaign.status = CampaignStatus.FAILED
    db.commit()
