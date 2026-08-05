from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_owned_asset, get_owned_campaign
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.enums import AssetType
from app.schemas.asset import DownloadResponse, OverlayUpdateRequest
from app.schemas.campaign import CampaignAssetOut
from app.schemas.common import ReviseRequest
from app.services import asset_service, generation_service
from app.services.exceptions import StaleVersionError, to_http_exception
from app.services.serializers import serialize_asset

router = APIRouter(tags=["assets"])


@router.post("/campaigns/{campaign_id}/images", response_model=CampaignAssetOut, status_code=202)
def add_image_asset(
    background_tasks: BackgroundTasks,
    campaign: Campaign = Depends(get_owned_campaign),
    db: Session = Depends(get_db),
) -> CampaignAssetOut:
    asset = generation_service.create_additional_image_asset(db, campaign)
    background_tasks.add_task(generation_service.generate_additional_image_asset, asset.id)
    return serialize_asset(db, asset)


@router.post("/campaigns/{campaign_id}/videos", response_model=CampaignAssetOut, status_code=202)
def add_video_asset(
    background_tasks: BackgroundTasks,
    campaign: Campaign = Depends(get_owned_campaign),
    db: Session = Depends(get_db),
) -> CampaignAssetOut:
    asset = generation_service.create_additional_video_asset(db, campaign)
    background_tasks.add_task(generation_service.generate_additional_video_asset, asset.id)
    return serialize_asset(db, asset)


@router.get("/assets/{asset_id}", response_model=CampaignAssetOut)
def get_asset(asset: Asset = Depends(get_owned_asset), db: Session = Depends(get_db)) -> CampaignAssetOut:
    return serialize_asset(db, asset)


@router.get("/assets/{asset_id}/versions", response_model=list[CampaignAssetOut])
def get_asset_versions(
    asset: Asset = Depends(get_owned_asset), db: Session = Depends(get_db)
) -> list[CampaignAssetOut]:
    versions = asset_service.list_asset_versions(db, asset.id)
    return [serialize_asset(db, v) for v in versions]


@router.post("/assets/{asset_id}/revise", response_model=CampaignAssetOut, status_code=202)
async def revise_asset(
    request: ReviseRequest,
    background_tasks: BackgroundTasks,
    asset: Asset = Depends(get_owned_asset),
    db: Session = Depends(get_db),
) -> CampaignAssetOut:
    try:
        if asset.asset_type == AssetType.IMAGE:
            new_asset = await asset_service.create_image_revision(db, asset, instruction=request.instruction)
            background_tasks.add_task(asset_service.generate_image_revision, new_asset.id)
        else:
            new_asset = await asset_service.create_video_revision(db, asset, instruction=request.instruction)
            background_tasks.add_task(asset_service.generate_video_revision, new_asset.id)
    except Exception as exc:  # provider errors during prompt-merge, etc.
        raise to_http_exception(exc) from exc
    return serialize_asset(db, new_asset)


@router.post("/assets/{asset_id}/restore/{version_id}", response_model=CampaignAssetOut)
def restore_asset(
    version_id: str,
    asset: Asset = Depends(get_owned_asset),
    db: Session = Depends(get_db),
) -> CampaignAssetOut:
    version = db.get(Asset, version_id)
    if version is None or version.campaign_id != asset.campaign_id:
        raise HTTPException(status_code=404, detail="Version not found.")
    try:
        restored = asset_service.restore_asset_version(db, asset, version)
    except StaleVersionError as exc:
        raise to_http_exception(exc) from exc
    return serialize_asset(db, restored)


@router.patch("/assets/{asset_id}/overlays", response_model=CampaignAssetOut)
async def update_overlays(
    request: OverlayUpdateRequest,
    asset: Asset = Depends(get_owned_asset),
    db: Session = Depends(get_db),
) -> CampaignAssetOut:
    try:
        updated = await asset_service.update_asset_overlays(
            db,
            asset,
            headline=request.headline,
            product_name=request.product_name,
            price=request.price,
            website=request.website,
            call_to_action=request.call_to_action,
            fade_in=request.fade_in,
            fade_out=request.fade_out,
        )
    except asset_service.OverlayError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return serialize_asset(db, updated)


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(asset: Asset = Depends(get_owned_asset), db: Session = Depends(get_db)) -> None:
    await asset_service.delete_asset(db, asset)


@router.get("/assets/{asset_id}/download", response_model=DownloadResponse)
def download_asset(asset: Asset = Depends(get_owned_asset)) -> DownloadResponse:
    url, filename = asset_service.download_asset(asset)
    if not url:
        raise HTTPException(status_code=409, detail="Asset has no completed output to download yet.")
    return DownloadResponse(url=url, file_name=filename)
