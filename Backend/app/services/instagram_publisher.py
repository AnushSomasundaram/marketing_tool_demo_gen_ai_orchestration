"""Orchestrates the Instagram publish flow (container create -> processing poll ->
publish -> permalink), persisting PublishJob state at every step. Real publishing
requires a connected SocialAccount; demo mode never calls Meta and every
resulting PublishJob is marked is_simulated=True.
"""

import asyncio

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.logging_config import get_logger
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.models.enums import CampaignStatus, PublishJobStatus
from app.models.publish_job import PublishJob
from app.models.social_account import SocialAccount
from app.models.user import DEV_USER_ID
from app.services.exceptions import ProviderError, PublishError
from app.services.providers.factory import get_social_publisher
from app.services.serializers import get_current_caption

logger = get_logger(__name__)

CONTAINER_POLL_INTERVAL_SECONDS = 2.0
CONTAINER_POLL_MAX_ATTEMPTS = 60


def _build_caption_text(caption: Caption | None) -> str:
    if caption is None:
        return ""
    parts = [caption.text]
    if caption.hashtags:
        parts.append(" ".join(caption.hashtags))
    if caption.call_to_action:
        parts.append(caption.call_to_action)
    return "\n\n".join(parts)


def get_or_create_social_account(db: Session) -> SocialAccount:
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.user_id == DEV_USER_ID, SocialAccount.platform == "instagram")
        .first()
    )
    if account is None:
        account = SocialAccount(user_id=DEV_USER_ID, platform="instagram")
        db.add(account)
        db.commit()
        db.refresh(account)
    return account


def build_connect_response() -> tuple[str, bool]:
    """Returns (authorization_url, demo_mode). In demo mode we still return a
    (non-functional) authorization URL shape for UI purposes, clearly flagged."""
    settings = get_settings()
    if settings.instagram_demo_mode:
        return "", True

    from app.services.providers.social.instagram_graph import build_authorization_url

    return build_authorization_url(state=DEV_USER_ID), False


async def handle_oauth_callback(db: Session, *, code: str) -> SocialAccount:
    from app.services.providers.social.instagram_graph import (
        exchange_code_for_token,
        fetch_instagram_business_account,
    )

    token_data = await exchange_code_for_token(code=code)
    access_token = token_data["access_token"]

    account = get_or_create_social_account(db)
    account.access_token = access_token

    ig_info = await fetch_instagram_business_account(access_token=access_token)
    if ig_info:
        account.page_id = ig_info["page_id"]
        account.instagram_business_account_id = ig_info["instagram_business_account_id"]

    db.commit()
    db.refresh(account)
    return account


def create_publish_job(
    db: Session, *, campaign: Campaign, asset: Asset, caption: Caption | None, is_ai_generated: bool
) -> PublishJob:
    settings = get_settings()
    job = PublishJob(
        campaign_id=campaign.id,
        asset_id=asset.id,
        caption_id=caption.id if caption else None,
        status=PublishJobStatus.QUEUED,
        is_ai_generated=is_ai_generated,
        is_simulated=settings.instagram_demo_mode,
    )
    db.add(job)
    campaign.status = CampaignStatus.PUBLISHING
    db.commit()
    db.refresh(job)
    return job


async def run_publish_job(publish_job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(PublishJob, publish_job_id)
        if job is None:
            return
        campaign = db.get(Campaign, job.campaign_id)
        asset = db.get(Asset, job.asset_id)
        if campaign is None or asset is None:
            job.status = PublishJobStatus.FAILED
            job.error_message = "Campaign or asset no longer exists."
            db.commit()
            return

        caption = db.get(Caption, job.caption_id) if job.caption_id else get_current_caption(db, asset.id)
        settings = get_settings()
        publisher = get_social_publisher()

        if settings.instagram_demo_mode:
            ig_user_id, access_token = "demo_ig_user", "demo_token"
        else:
            account = (
                db.query(SocialAccount)
                .filter(SocialAccount.user_id == DEV_USER_ID, SocialAccount.platform == "instagram")
                .first()
            )
            if account is None or not account.access_token or not account.instagram_business_account_id:
                job.status = PublishJobStatus.FAILED
                job.error_code = "not_connected"
                job.error_message = "No connected Instagram account. Connect one first."
                campaign.status = CampaignStatus.READY
                db.commit()
                return
            ig_user_id, access_token = account.instagram_business_account_id, account.access_token

        media_url = asset.download_url or asset.preview_url or ""
        is_video = asset.asset_type == "video"
        caption_text = _build_caption_text(caption)

        try:
            container_id = await publisher.create_container(
                ig_user_id=ig_user_id,
                access_token=access_token,
                media_url=media_url,
                caption=caption_text,
                is_video=is_video,
            )
            job.container_id = container_id
            job.status = PublishJobStatus.CONTAINER_CREATED
            db.commit()

            for _ in range(CONTAINER_POLL_MAX_ATTEMPTS):
                status = await publisher.get_container_status(
                    container_id=container_id, access_token=access_token
                )
                if status == "finished":
                    break
                if status == "error":
                    raise PublishError("Instagram failed to process the media.", code="container_error")
                job.status = PublishJobStatus.PROCESSING
                db.commit()
                await asyncio.sleep(CONTAINER_POLL_INTERVAL_SECONDS)
            else:
                raise PublishError(
                    "Timed out waiting for Instagram to finish processing the media.", code="timeout"
                )

            job.status = PublishJobStatus.PUBLISHING
            db.commit()

            media_id = await publisher.publish_container(
                ig_user_id=ig_user_id, access_token=access_token, container_id=container_id
            )
            permalink = await publisher.get_permalink(media_id=media_id, access_token=access_token)

            job.instagram_media_id = media_id
            job.permalink = permalink
            job.status = PublishJobStatus.COMPLETED
            campaign.status = CampaignStatus.PUBLISHED
            db.commit()
        except (ProviderError, PublishError) as exc:
            job.status = PublishJobStatus.FAILED
            job.error_code = getattr(exc, "code", None) or type(exc).__name__
            job.error_message = getattr(exc, "message", str(exc))
            campaign.status = CampaignStatus.READY
            db.commit()
    finally:
        db.close()
