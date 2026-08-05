from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_owned_campaign, get_owned_caption
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.schemas.caption import (
    AlternativeCaptionRequest,
    CaptionOut,
    CreateCaptionRequest,
    UpdateCaptionRequest,
)
from app.schemas.common import ReviseRequest
from app.services import caption_service
from app.services.exceptions import ProviderError, StaleVersionError, to_http_exception
from app.services.serializers import serialize_caption

router = APIRouter(tags=["captions"])


@router.post("/campaigns/{campaign_id}/captions", response_model=CaptionOut, status_code=201)
async def create_caption(
    request: CreateCaptionRequest,
    campaign: Campaign = Depends(get_owned_campaign),
    db: Session = Depends(get_db),
) -> CaptionOut:
    asset = db.get(Asset, request.asset_id)
    if asset is None or asset.campaign_id != campaign.id:
        raise HTTPException(status_code=404, detail="Asset not found in this campaign.")
    try:
        caption = await caption_service.create_caption(db, campaign, asset, tone=request.tone)
    except ProviderError as exc:
        raise to_http_exception(exc) from exc
    return serialize_caption(caption)


@router.patch("/captions/{caption_id}", response_model=CaptionOut)
def update_caption(
    request: UpdateCaptionRequest,
    caption: Caption = Depends(get_owned_caption),
    db: Session = Depends(get_db),
) -> CaptionOut:
    try:
        updated = caption_service.update_caption(
            db, caption, text=request.text, hashtags=request.hashtags, call_to_action=request.call_to_action
        )
    except StaleVersionError as exc:
        raise to_http_exception(exc) from exc
    return serialize_caption(updated)


@router.post("/captions/{caption_id}/revise", response_model=CaptionOut)
async def revise_caption(
    request: ReviseRequest,
    caption: Caption = Depends(get_owned_caption),
    db: Session = Depends(get_db),
) -> CaptionOut:
    try:
        updated = await caption_service.revise_caption(db, caption, instruction=request.instruction)
    except (ProviderError, StaleVersionError) as exc:
        raise to_http_exception(exc) from exc
    return serialize_caption(updated)


@router.post("/captions/{caption_id}/alternatives", response_model=CaptionOut)
async def generate_alternative(
    request: AlternativeCaptionRequest,
    caption: Caption = Depends(get_owned_caption),
    db: Session = Depends(get_db),
) -> CaptionOut:
    try:
        updated = await caption_service.generate_alternative_caption(db, caption, tone=request.tone)
    except (ProviderError, StaleVersionError) as exc:
        raise to_http_exception(exc) from exc
    return serialize_caption(updated)


@router.get("/captions/{caption_id}/versions", response_model=list[CaptionOut])
def list_versions(
    caption: Caption = Depends(get_owned_caption), db: Session = Depends(get_db)
) -> list[CaptionOut]:
    versions = caption_service.list_caption_versions(db, caption.id)
    return [serialize_caption(v) for v in versions]


@router.post("/captions/{caption_id}/restore/{version_id}", response_model=CaptionOut)
def restore_version(
    version_id: str,
    caption: Caption = Depends(get_owned_caption),
    db: Session = Depends(get_db),
) -> CaptionOut:
    version = db.get(Caption, version_id)
    if version is None or version.campaign_id != caption.campaign_id:
        raise HTTPException(status_code=404, detail="Version not found.")
    try:
        restored = caption_service.restore_caption_version(db, caption, version)
    except StaleVersionError as exc:
        raise to_http_exception(exc) from exc
    return serialize_caption(restored)
