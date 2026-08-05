from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.models.publish_job import PublishJob
from app.models.social_account import SocialAccount
from app.models.user import DEV_USER_ID, User
from app.schemas.instagram import (
    InstagramAccountOut,
    InstagramConnectResponse,
    PublishJobOut,
    PublishRequest,
)
from app.services import instagram_publisher
from app.services.exceptions import ProviderError, to_http_exception

router = APIRouter(prefix="/instagram", tags=["instagram"])


@router.get("/connect", response_model=InstagramConnectResponse)
def connect(user: User = Depends(get_current_user)) -> InstagramConnectResponse:
    del user
    try:
        url, demo_mode = instagram_publisher.build_connect_response()
    except ProviderError as exc:
        raise to_http_exception(exc) from exc
    return InstagramConnectResponse(authorization_url=url, demo_mode=demo_mode)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    db: Session = Depends(get_db),
) -> InstagramAccountOut:
    try:
        account = await instagram_publisher.handle_oauth_callback(db, code=code)
    except ProviderError as exc:
        raise to_http_exception(exc) from exc
    return InstagramAccountOut(
        id=account.id,
        platform=account.platform,
        instagram_business_account_id=account.instagram_business_account_id,
        connected=bool(account.access_token),
    )


@router.get("/accounts", response_model=list[InstagramAccountOut])
def list_accounts(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[InstagramAccountOut]:
    del user
    accounts = db.query(SocialAccount).filter_by(user_id=DEV_USER_ID, platform="instagram").all()
    return [
        InstagramAccountOut(
            id=a.id,
            platform=a.platform,
            instagram_business_account_id=a.instagram_business_account_id,
            connected=bool(a.access_token),
        )
        for a in accounts
    ]


@router.post("/publish", response_model=PublishJobOut, status_code=202)
def publish(
    request: PublishRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PublishJobOut:
    campaign = db.get(Campaign, request.campaign_id)
    if campaign is None or campaign.user_id != user.id:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    asset = db.get(Asset, request.asset_id)
    if asset is None or asset.campaign_id != campaign.id:
        raise HTTPException(status_code=404, detail="Asset not found in this campaign.")
    if asset.status != "completed":
        raise HTTPException(status_code=409, detail="Asset must be completed before publishing.")

    caption = None
    if request.caption_id:
        caption = db.get(Caption, request.caption_id)
        if caption is None or caption.campaign_id != campaign.id:
            raise HTTPException(status_code=404, detail="Caption not found in this campaign.")

    job = instagram_publisher.create_publish_job(
        db, campaign=campaign, asset=asset, caption=caption, is_ai_generated=request.is_ai_generated
    )
    background_tasks.add_task(instagram_publisher.run_publish_job, job.id)
    return PublishJobOut.model_validate(job)


@router.get("/publish/{publish_job_id}", response_model=PublishJobOut)
def get_publish_status(
    publish_job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> PublishJobOut:
    job = db.get(PublishJob, publish_job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Publish job not found.")
    campaign = db.get(Campaign, job.campaign_id)
    if campaign is None or campaign.user_id != user.id:
        raise HTTPException(status_code=404, detail="Publish job not found.")
    return PublishJobOut.model_validate(job)
