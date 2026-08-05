"""Per-asset operations: revision (creates a new version), deletion, download,
version history, and overlay updates.

Revision is split into two phases so a router can respond immediately with
the new asset id instead of blocking on generation:
  1. create_*_revision(db, ...)   -- fast, synchronous: spawns the new version row
  2. generate_*_revision(asset_id) -- slow, async, meant for BackgroundTasks

revise_*_asset_by_id combines both phases for callers (like chat) that only
need the end result queued in the background, not the new id back immediately.
"""

import contextlib

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.asset import Asset
from app.models.campaign import Campaign
from app.models.caption import Caption
from app.models.enums import AssetStatus, AssetType, GenerationJobType
from app.services import job_service
from app.services.campaign_service import recompute_campaign_status
from app.services.exceptions import ProviderError, StaleVersionError
from app.services.providers.factory import get_image_provider, get_text_provider, get_video_provider
from app.services.storage import get_storage_provider
from app.utils.files import safe_filename


def _repoint_captions(db: Session, *, from_asset_id: str, to_asset_id: str) -> None:
    db.query(Caption).filter(Caption.asset_id == from_asset_id).update({Caption.asset_id: to_asset_id})
    db.commit()


async def _merge_prompt(previous_prompt: str, instruction: str | None) -> tuple[str, str | None]:
    if not instruction:
        return previous_prompt, None
    try:
        merged = await get_text_provider().merge_revision(
            previous_prompt=previous_prompt, instruction=instruction
        )
        return merged.prompt, instruction
    except ProviderError:
        return f"{previous_prompt} Additionally: {instruction}", instruction


def _spawn_next_version(db: Session, old_asset: Asset, *, new_prompt: str, instruction: str | None) -> Asset:
    if not old_asset.is_current:
        raise StaleVersionError("This asset version is no longer current. Refresh and try again.")

    new_asset = Asset(
        campaign_id=old_asset.campaign_id,
        parent_asset_id=old_asset.id,
        root_asset_id=old_asset.root_asset_id or old_asset.id,
        title=old_asset.title,
        version=old_asset.version + 1,
        asset_type=old_asset.asset_type,
        status=AssetStatus.QUEUED,
        aspect_ratio=old_asset.aspect_ratio,
        duration_seconds=old_asset.duration_seconds,
        generation_prompt=new_prompt,
        revision_instruction=instruction,
        sort_order=old_asset.sort_order,
        is_current=True,
    )
    old_asset.is_current = False
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    _repoint_captions(db, from_asset_id=old_asset.id, to_asset_id=new_asset.id)
    # Recompute synchronously (not just at generation completion) so a caller
    # that immediately re-fetches the campaign right after this call returns
    # already sees status=GENERATING and knows to start polling, rather than
    # racing the background generation task that hasn't started yet.
    recompute_campaign_status(db, new_asset.campaign_id)
    return new_asset


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


async def create_image_revision(db: Session, old_asset: Asset, *, instruction: str | None) -> Asset:
    new_prompt, resolved_instruction = await _merge_prompt(old_asset.generation_prompt or "", instruction)
    return _spawn_next_version(db, old_asset, new_prompt=new_prompt, instruction=resolved_instruction)


async def generate_image_revision(asset_id: str) -> None:
    db = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return

        job = job_service.create_job(
            db, campaign_id=asset.campaign_id, job_type=GenerationJobType.IMAGE, asset_id=asset.id
        )
        job_service.mark_processing(db, job)
        asset.status = AssetStatus.PROCESSING
        asset.progress = 10
        db.commit()

        campaign = db.get(Campaign, asset.campaign_id)
        image_provider = get_image_provider()
        storage = get_storage_provider()

        try:
            base_bytes = b""
            if campaign and campaign.product_image_url:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.get(campaign.product_image_url)
                    resp.raise_for_status()
                    base_bytes = resp.content

            result_bytes = await image_provider.revise(
                prompt=asset.generation_prompt or "",
                base_image_bytes=base_bytes,
                aspect_ratio=asset.aspect_ratio,
            )
            stored = await storage.upload_bytes(
                result_bytes,
                folder="generated",
                filename=safe_filename(None, "image/png"),
                resource_type="image",
            )
            asset.preview_url = stored.url
            asset.download_url = stored.url
            asset.storage_public_id = stored.public_id
            asset.status = AssetStatus.COMPLETED
            asset.progress = 100
            job_service.mark_completed(db, job, result={"url": stored.url})
        except ProviderError as exc:
            asset.status = AssetStatus.FAILED
            asset.progress = None
            asset.error_code = type(exc).__name__
            asset.error_message = exc.message
            job_service.mark_failed(db, job, error_code=type(exc).__name__, error_message=exc.message)

        db.commit()
        recompute_campaign_status(db, asset.campaign_id)
    finally:
        db.close()


async def revise_image_asset_by_id(asset_id: str, *, instruction: str | None) -> Asset | None:
    db = SessionLocal()
    try:
        old_asset = db.get(Asset, asset_id)
        if old_asset is None:
            return None
        new_asset = await create_image_revision(db, old_asset, instruction=instruction)
        new_id = new_asset.id
    finally:
        db.close()

    await generate_image_revision(new_id)

    db = SessionLocal()
    try:
        return db.get(Asset, new_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------


async def create_video_revision(db: Session, old_asset: Asset, *, instruction: str | None) -> Asset:
    new_prompt, resolved_instruction = await _merge_prompt(old_asset.generation_prompt or "", instruction)
    return _spawn_next_version(db, old_asset, new_prompt=new_prompt, instruction=resolved_instruction)


async def generate_video_revision(asset_id: str) -> None:
    from app.services.generation_service import _poll_video_task

    db = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return

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


async def revise_video_asset_by_id(asset_id: str, *, instruction: str | None) -> Asset | None:
    db = SessionLocal()
    try:
        old_asset = db.get(Asset, asset_id)
        if old_asset is None:
            return None
        new_asset = await create_video_revision(db, old_asset, instruction=instruction)
        new_id = new_asset.id
    finally:
        db.close()

    await generate_video_revision(new_id)

    db = SessionLocal()
    try:
        return db.get(Asset, new_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Versions, deletion, download, overlays
# ---------------------------------------------------------------------------


def list_asset_versions(db: Session, root_or_asset_id: str) -> list[Asset]:
    asset = db.get(Asset, root_or_asset_id)
    if asset is None:
        return []
    root_id = asset.root_asset_id or asset.id
    return (
        db.query(Asset)
        .filter((Asset.id == root_id) | (Asset.root_asset_id == root_id))
        .order_by(Asset.version)
        .all()
    )


def restore_asset_version(db: Session, current_asset: Asset, version_asset: Asset) -> Asset:
    """Creates a new current version that copies the content of an older version,
    rather than mutating history — consistent with 'do not overwrite earlier results'."""
    if not current_asset.is_current:
        raise StaleVersionError("This asset version is no longer current. Refresh and try again.")

    new_asset = Asset(
        campaign_id=current_asset.campaign_id,
        parent_asset_id=current_asset.id,
        root_asset_id=current_asset.root_asset_id or current_asset.id,
        title=version_asset.title,
        version=current_asset.version + 1,
        asset_type=version_asset.asset_type,
        status=version_asset.status,
        preview_url=version_asset.preview_url,
        download_url=version_asset.download_url,
        storage_public_id=version_asset.storage_public_id,
        raw_video_url=version_asset.raw_video_url,
        raw_video_storage_public_id=version_asset.raw_video_storage_public_id,
        generation_prompt=version_asset.generation_prompt,
        revision_instruction=f"Restored from version {version_asset.version}",
        aspect_ratio=version_asset.aspect_ratio,
        duration_seconds=version_asset.duration_seconds,
        progress=version_asset.progress,
        sort_order=current_asset.sort_order,
        is_current=True,
    )
    current_asset.is_current = False
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    _repoint_captions(db, from_asset_id=current_asset.id, to_asset_id=new_asset.id)
    return new_asset


async def delete_asset(db: Session, asset: Asset) -> None:
    storage = get_storage_provider()
    if asset.storage_public_id:
        resource_type = "video" if asset.asset_type == AssetType.VIDEO else "image"
        # Storage cleanup is best-effort; don't block the delete on it.
        with contextlib.suppress(Exception):
            await storage.delete(asset.storage_public_id, resource_type=resource_type)
    asset.status = AssetStatus.DELETED
    asset.is_current = False
    db.commit()
    recompute_campaign_status(db, asset.campaign_id)


class OverlayError(Exception):
    pass


async def update_asset_overlays(
    db: Session,
    asset: Asset,
    *,
    headline: str | None,
    product_name: str | None,
    price: str | None,
    website: str | None,
    call_to_action: str | None,
    fade_in: bool,
    fade_out: bool,
) -> Asset:
    """Re-composes the video's text overlay deterministically via FFmpeg — no
    AI regeneration. Always composes from the untouched raw AI output so
    repeated overlay edits never compound on top of each other."""
    if asset.asset_type != AssetType.VIDEO:
        raise OverlayError("Overlays only apply to video assets.")
    if not asset.raw_video_url:
        raise OverlayError("This video has no generated output yet.")

    from app.services.composition_service import apply_overlays

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(asset.raw_video_url)
        response.raise_for_status()
        raw_bytes = response.content

    composed_bytes = await apply_overlays(
        raw_bytes,
        headline=headline,
        product_name=product_name,
        price=price,
        website=website,
        call_to_action=call_to_action,
        fade_in=fade_in,
        fade_out=fade_out,
        duration_seconds=asset.duration_seconds or 5.0,
    )

    storage = get_storage_provider()
    stored = await storage.upload_bytes(
        composed_bytes, folder="composed", filename=safe_filename(None, "video/mp4"), resource_type="video"
    )
    asset.download_url = stored.url
    asset.overlay = {
        "headline": headline,
        "productName": product_name,
        "price": price,
        "website": website,
        "callToAction": call_to_action,
        "fadeIn": fade_in,
        "fadeOut": fade_out,
    }
    db.commit()
    return asset


def download_asset(asset: Asset) -> tuple[str, str]:
    url = asset.download_url or asset.preview_url or ""
    extension = "mp4" if asset.asset_type == AssetType.VIDEO else "png"
    filename = f"{asset.title.replace(' ', '-').lower()}.{extension}"
    return url, filename


async def update_asset_overlays_by_id(
    asset_id: str,
    *,
    headline: str | None,
    product_name: str | None,
    price: str | None,
    website: str | None,
    call_to_action: str | None,
    fade_in: bool,
    fade_out: bool,
) -> None:
    """Self-contained variant of update_asset_overlays for use from
    BackgroundTasks (e.g. the chat flow), which must not reuse a
    request-scoped session."""
    db = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return
        with contextlib.suppress(OverlayError):
            await update_asset_overlays(
                db,
                asset,
                headline=headline,
                product_name=product_name,
                price=price,
                website=website,
                call_to_action=call_to_action,
                fade_in=fade_in,
                fade_out=fade_out,
            )
    finally:
        db.close()
