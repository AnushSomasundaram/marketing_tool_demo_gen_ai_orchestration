from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.models.user import DEV_USER_ID, User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Single development user, standing in for real authentication (per spec:
    not worth building full auth for this demo). Ownership checks still run
    against this user id so the query patterns are the same as they'd be with
    real auth."""
    user = db.get(User, DEV_USER_ID)
    if user is None:
        user = User(id=DEV_USER_ID, email="dev@campaignstudio.local", display_name="Dev User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_owned_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None or campaign.user_id != user.id:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign


def get_owned_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    campaign = db.get(Campaign, asset.campaign_id)
    if campaign is None or campaign.user_id != user.id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    return asset


def get_owned_caption(
    caption_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Caption:
    caption = db.get(Caption, caption_id)
    if caption is None:
        raise HTTPException(status_code=404, detail="Caption not found.")
    campaign = db.get(Campaign, caption.campaign_id)
    if campaign is None or campaign.user_id != user.id:
        raise HTTPException(status_code=404, detail="Caption not found.")
    return caption


__all__ = [
    "get_db",
    "get_current_user",
    "get_owned_campaign",
    "get_owned_asset",
    "get_owned_caption",
]
