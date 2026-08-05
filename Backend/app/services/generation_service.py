"""Orchestrates the full campaign generation workflow: planning, then image,
video, and caption generation. Every entrypoint here is designed to be called
from a FastAPI BackgroundTask, so each opens its own DB session rather than
reusing a request-scoped one.
"""

import asyncio
from pathlib import Path

import httpx

from app.config import get_settings
from app.database import SessionLocal
from app.logging_config import get_logger
from app.models.asset import Asset
from app.models.campaign import Campaign, CampaignPlanRecord
from app.models.caption import Caption
from app.models.enums import AssetStatus, AssetType, CampaignStatus, GenerationJobType
from app.schemas.plan import CampaignPlan
from app.services import job_service
from app.services.campaign_service import recompute_campaign_status
from app.services.exceptions import ProviderError
from app.services.providers.factory import get_image_provider, get_text_provider, get_video_provider
from app.services.providers.video.mock_video import MOCK_OUTPUT_URL
from app.services.storage import get_storage_provider
from app.utils.files import safe_filename

logger = get_logger(__name__)

MOCK_PLACEHOLDER_VIDEO = Path(__file__).resolve().parents[1] / "mock_assets" / "placeholder_video.mp4"
VIDEO_POLL_INTERVAL_SECONDS = 2.5
VIDEO_POLL_MAX_ATTEMPTS = 240  # ~10 minutes


async def _fetch_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def run_campaign_generation(campaign_id: str) -> None:
    """Entrypoint for POST /campaigns/{id}/generate. Plans the campaign, then
    kicks off image, video, and caption generation."""
    db = SessionLocal()
    try:
        campaign = db.get(Campaign, campaign_id)
        if campaign is None:
            return

        campaign.status = CampaignStatus.PLANNING
        db.commit()

        plan_job = job_service.create_job(
            db, campaign_id=campaign_id, job_type=GenerationJobType.CAMPAIGN_PLAN
        )
        job_service.mark_processing(db, plan_job)

        text_provider = get_text_provider()
        try:
            plan = await text_provider.create_campaign_plan(
                product_name=campaign.product_name,
                product_description=campaign.product_description,
                target_audience=campaign.target_audience,
                tone=campaign.tone,
                price=campaign.price,
                website_url=campaign.website_url,
                image_url=campaign.product_image_url or "",
            )
        except ProviderError as exc:
            job_service.mark_failed(db, plan_job, error_code=type(exc).__name__, error_message=exc.message)
            campaign.status = CampaignStatus.FAILED
            db.commit()
            return

        job_service.mark_completed(db, plan_job, result={"campaignTitle": plan.campaign_title})
        campaign.title = plan.campaign_title
        campaign.plan_json = plan.model_dump_json()
        db.add(
            CampaignPlanRecord(
                campaign_id=campaign_id,
                plan_json=plan.model_dump_json(),
                model_used=text_provider.__class__.__name__,
            )
        )
        campaign.status = CampaignStatus.GENERATING
        db.commit()

        assets = _create_initial_assets(db, campaign, plan)
        await _generate_captions_for_assets(db, campaign, plan, assets)

        image_assets = [a for a in assets if a.asset_type == AssetType.IMAGE]
        video_asset = next((a for a in assets if a.asset_type == AssetType.VIDEO), None)

        await asyncio.gather(*(_generate_image_asset(db, asset) for asset in image_assets))
        recompute_campaign_status(db, campaign_id)

        if video_asset is not None:
            await _start_and_poll_video(db, video_asset)
        recompute_campaign_status(db, campaign_id)
    finally:
        db.close()


def _create_initial_assets(db, campaign: Campaign, plan: CampaignPlan) -> list[Asset]:
    assets: list[Asset] = []
    for index, concept in enumerate(plan.image_concepts):
        asset = Asset(
            campaign_id=campaign.id,
            title=concept.concept_name,
            asset_type=AssetType.IMAGE,
            status=AssetStatus.QUEUED,
            aspect_ratio=concept.aspect_ratio,
            generation_prompt=concept.prompt,
            sort_order=index,
        )
        db.add(asset)
        assets.append(asset)

    video_asset = Asset(
        campaign_id=campaign.id,
        title=plan.video_concept.concept_name,
        asset_type=AssetType.VIDEO,
        status=AssetStatus.QUEUED,
        aspect_ratio="9:16",
        duration_seconds=float(plan.video_concept.duration_seconds),
        generation_prompt=plan.video_concept.prompt,
        sort_order=len(plan.image_concepts),
    )
    db.add(video_asset)
    assets.append(video_asset)

    db.commit()
    for asset in assets:
        db.refresh(asset)
    return assets


async def _generate_captions_for_assets(
    db, campaign: Campaign, plan: CampaignPlan, assets: list[Asset]
) -> None:
    text_provider = get_text_provider()
    for asset in assets:
        job = job_service.create_job(
            db, campaign_id=campaign.id, job_type=GenerationJobType.CAPTION, asset_id=asset.id
        )
        job_service.mark_processing(db, job)
        try:
            generated = await text_provider.generate_caption(
                plan=plan,
                campaign_title=campaign.title,
                asset_title=asset.title,
                asset_type=asset.asset_type,
            )
        except ProviderError as exc:
            job_service.mark_failed(db, job, error_code=type(exc).__name__, error_message=exc.message)
            continue

        caption = Caption(
            campaign_id=campaign.id,
            asset_id=asset.id,
            version=1,
            text=generated.text,
            call_to_action=generated.call_to_action,
            tone=campaign.tone,
            is_current=True,
        )
        caption.hashtags = generated.hashtags
        db.add(caption)
        job_service.mark_completed(db, job, result={"captionId": None})
    db.commit()


async def _generate_image_asset(db, asset: Asset) -> None:
    campaign = db.get(Campaign, asset.campaign_id)
    job = job_service.create_job(
        db, campaign_id=asset.campaign_id, job_type=GenerationJobType.IMAGE, asset_id=asset.id
    )
    job_service.mark_processing(db, job)
    asset.status = AssetStatus.PROCESSING
    asset.progress = 10
    db.commit()

    image_provider = get_image_provider()
    storage = get_storage_provider()
    try:
        reference_bytes = (
            await _fetch_bytes(campaign.product_image_url) if campaign and campaign.product_image_url else b""
        )
        result_bytes = await image_provider.generate(
            prompt=asset.generation_prompt or "",
            reference_image_bytes=reference_bytes,
            aspect_ratio=asset.aspect_ratio,
        )
        filename = safe_filename(None, "image/png")
        stored = await storage.upload_bytes(
            result_bytes, folder="generated", filename=filename, resource_type="image"
        )
        asset.preview_url = stored.url
        asset.download_url = stored.url
        asset.storage_public_id = stored.public_id
        asset.status = AssetStatus.COMPLETED
        asset.progress = 100
        asset.error_code = None
        asset.error_message = None
        job_service.mark_completed(db, job, result={"url": stored.url})
    except ProviderError as exc:
        asset.status = AssetStatus.FAILED
        asset.progress = None
        asset.error_code = type(exc).__name__
        asset.error_message = exc.message
        job_service.mark_failed(db, job, error_code=type(exc).__name__, error_message=exc.message)
    db.commit()


async def _start_and_poll_video(db, asset: Asset) -> None:
    settings = get_settings()
    job = job_service.create_job(
        db, campaign_id=asset.campaign_id, job_type=GenerationJobType.VIDEO, asset_id=asset.id
    )
    job_service.mark_processing(db, job)
    asset.status = AssetStatus.PROCESSING
    asset.progress = 5
    db.commit()

    campaign = db.get(Campaign, asset.campaign_id)
    video_provider = get_video_provider()
    try:
        handle = await video_provider.generate(
            prompt=asset.generation_prompt or "",
            reference_image_url=campaign.product_image_url if campaign else "",
            ratio=settings.runway_video_ratio,
            duration_seconds=int(asset.duration_seconds or settings.runway_video_duration_seconds),
        )
    except ProviderError as exc:
        asset.status = AssetStatus.FAILED
        asset.progress = None
        asset.error_code = type(exc).__name__
        asset.error_message = exc.message
        job_service.mark_failed(db, job, error_code=type(exc).__name__, error_message=exc.message)
        db.commit()
        return

    asset.external_task_id = handle.external_task_id
    asset.external_provider = video_provider.__class__.__name__
    job.external_task_id = handle.external_task_id
    db.commit()

    await _poll_video_task(db, asset, job)


async def _poll_video_task(db, asset: Asset, job) -> None:
    video_provider = get_video_provider()
    storage = get_storage_provider()

    for _ in range(VIDEO_POLL_MAX_ATTEMPTS):
        status = await video_provider.get_status(asset.external_task_id)

        if status.state in ("queued", "processing"):
            asset.progress = status.progress if status.progress is not None else asset.progress
            db.commit()
            await asyncio.sleep(VIDEO_POLL_INTERVAL_SECONDS)
            continue

        if status.state == "failed":
            asset.status = AssetStatus.FAILED
            asset.progress = None
            asset.error_code = "task_failed"
            asset.error_message = status.error_message or "Video generation failed."
            job_service.mark_failed(db, job, error_code="task_failed", error_message=asset.error_message)
            db.commit()
            return

        # completed
        if status.output_url == MOCK_OUTPUT_URL:
            video_bytes = MOCK_PLACEHOLDER_VIDEO.read_bytes()
        else:
            video_bytes = await _fetch_bytes(status.output_url) if status.output_url else b""

        from app.services.composition_service import extract_thumbnail

        thumbnail_bytes = await extract_thumbnail(video_bytes)

        video_stored = await storage.upload_bytes(
            video_bytes, folder="generated", filename=safe_filename(None, "video/mp4"), resource_type="video"
        )
        thumb_stored = await storage.upload_bytes(
            thumbnail_bytes,
            folder="generated",
            filename=safe_filename(None, "image/jpeg"),
            resource_type="image",
        )

        asset.preview_url = thumb_stored.url
        asset.download_url = video_stored.url
        asset.storage_public_id = video_stored.public_id
        asset.raw_video_url = video_stored.url
        asset.raw_video_storage_public_id = video_stored.public_id
        asset.status = AssetStatus.COMPLETED
        asset.progress = 100
        asset.error_code = None
        asset.error_message = None
        job_service.mark_completed(db, job, result={"url": video_stored.url})
        db.commit()
        return

    asset.status = AssetStatus.FAILED
    asset.progress = None
    asset.error_code = "timeout"
    asset.error_message = "Video generation timed out."
    job_service.mark_failed(db, job, error_code="timeout", error_message=asset.error_message)
    db.commit()


async def regenerate_all_images(campaign_id: str) -> None:
    from app.services.asset_service import revise_image_asset_by_id

    db = SessionLocal()
    try:
        from app.services.serializers import get_current_assets

        assets = [a for a in get_current_assets(db, campaign_id) if a.asset_type == AssetType.IMAGE]
        asset_ids = [a.id for a in assets]
    finally:
        db.close()

    await asyncio.gather(*(revise_image_asset_by_id(asset_id, instruction=None) for asset_id in asset_ids))


async def regenerate_video(campaign_id: str) -> None:
    from app.services.asset_service import revise_video_asset_by_id

    db = SessionLocal()
    try:
        from app.services.serializers import get_current_assets

        video = next(
            (a for a in get_current_assets(db, campaign_id) if a.asset_type == AssetType.VIDEO), None
        )
        asset_id = video.id if video else None
    finally:
        db.close()

    if asset_id:
        await revise_video_asset_by_id(asset_id, instruction=None)


def create_additional_image_asset(db, campaign: Campaign) -> Asset:
    """Adds one more image asset to the campaign, reusing the plan's first
    image concept as a starting point (or a generic prompt if there's no
    plan yet)."""
    from app.services.plan_utils import load_campaign_plan
    from app.services.serializers import get_current_assets

    plan = load_campaign_plan(campaign)
    concept = plan.image_concepts[0] if plan and plan.image_concepts else None
    current = get_current_assets(db, campaign.id)
    image_count = sum(1 for a in current if a.asset_type == AssetType.IMAGE)
    sort_order = max((a.sort_order for a in current), default=-1) + 1

    asset = Asset(
        campaign_id=campaign.id,
        title=f"{concept.concept_name if concept else 'Feed Post'} {image_count + 1}",
        asset_type=AssetType.IMAGE,
        status=AssetStatus.QUEUED,
        aspect_ratio=concept.aspect_ratio if concept else "1:1",
        generation_prompt=concept.prompt
        if concept
        else f"Studio product photo of {campaign.product_name}, {campaign.product_description}",
        sort_order=sort_order,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


async def generate_additional_image_asset(asset_id: str) -> None:
    db = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is not None:
            await _generate_image_asset(db, asset)
            recompute_campaign_status(db, asset.campaign_id)
    finally:
        db.close()


def create_additional_video_asset(db, campaign: Campaign) -> Asset:
    from app.services.plan_utils import load_campaign_plan
    from app.services.serializers import get_current_assets

    settings = get_settings()
    plan = load_campaign_plan(campaign)
    concept = plan.video_concept if plan else None
    current = get_current_assets(db, campaign.id)
    sort_order = max((a.sort_order for a in current), default=-1) + 1

    asset = Asset(
        campaign_id=campaign.id,
        title=concept.concept_name if concept else "Reel",
        asset_type=AssetType.VIDEO,
        status=AssetStatus.QUEUED,
        aspect_ratio="9:16",
        duration_seconds=float(
            concept.duration_seconds if concept else settings.runway_video_duration_seconds
        ),
        generation_prompt=concept.prompt
        if concept
        else f"Slow rotating hero shot of {campaign.product_name}, clean product-focused motion.",
        sort_order=sort_order,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


async def generate_additional_video_asset(asset_id: str) -> None:
    db = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return
        job = job_service.create_job(
            db, campaign_id=asset.campaign_id, job_type=GenerationJobType.VIDEO, asset_id=asset.id
        )
        job_service.mark_processing(db, job)
        asset.status = AssetStatus.PROCESSING
        asset.progress = 5
        db.commit()

        settings = get_settings()
        campaign = db.get(Campaign, asset.campaign_id)
        video_provider = get_video_provider()
        try:
            handle = await video_provider.generate(
                prompt=asset.generation_prompt or "",
                reference_image_url=campaign.product_image_url if campaign else "",
                ratio=settings.runway_video_ratio,
                duration_seconds=int(asset.duration_seconds or settings.runway_video_duration_seconds),
            )
        except ProviderError as exc:
            asset.status = AssetStatus.FAILED
            asset.error_code = type(exc).__name__
            asset.error_message = exc.message
            job_service.mark_failed(db, job, error_code=type(exc).__name__, error_message=exc.message)
            db.commit()
            recompute_campaign_status(db, asset.campaign_id)
            return

        asset.external_task_id = handle.external_task_id
        asset.external_provider = video_provider.__class__.__name__
        job.external_task_id = handle.external_task_id
        db.commit()

        await _poll_video_task(db, asset, job)
        recompute_campaign_status(db, asset.campaign_id)
    finally:
        db.close()
