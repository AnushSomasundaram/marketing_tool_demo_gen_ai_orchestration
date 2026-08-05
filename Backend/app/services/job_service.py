import json

from sqlalchemy.orm import Session

from app.models.enums import GenerationJobStatus, GenerationJobType
from app.models.generation_job import GenerationJob


def create_job(
    db: Session,
    *,
    campaign_id: str,
    job_type: GenerationJobType,
    asset_id: str | None = None,
    payload: dict | None = None,
) -> GenerationJob:
    job = GenerationJob(
        campaign_id=campaign_id,
        asset_id=asset_id,
        job_type=job_type,
        status=GenerationJobStatus.QUEUED,
        payload_json=json.dumps(payload) if payload else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def mark_processing(db: Session, job: GenerationJob) -> None:
    job.status = GenerationJobStatus.PROCESSING
    db.commit()


def mark_completed(db: Session, job: GenerationJob, *, result: dict | None = None) -> None:
    job.status = GenerationJobStatus.COMPLETED
    job.progress = 100
    if result is not None:
        job.result_json = json.dumps(result)
    db.commit()


def mark_failed(db: Session, job: GenerationJob, *, error_code: str, error_message: str) -> None:
    job.status = GenerationJobStatus.FAILED
    job.error_code = error_code
    job.error_message = error_message
    db.commit()


def update_progress(db: Session, job: GenerationJob, progress: int) -> None:
    job.progress = progress
    db.commit()


def list_jobs(db: Session, campaign_id: str) -> list[GenerationJob]:
    return (
        db.query(GenerationJob)
        .filter(GenerationJob.campaign_id == campaign_id)
        .order_by(GenerationJob.created_at)
        .all()
    )


def recover_abandoned_jobs(db: Session) -> int:
    """Called on startup: any job/asset still marked 'processing' from a previous
    process lifetime cannot possibly still be running, so mark it failed but
    recoverable (the user can retry via the normal revise/regenerate actions)."""
    from app.models.asset import Asset
    from app.models.enums import AssetStatus

    count = 0
    stuck_jobs = db.query(GenerationJob).filter(GenerationJob.status == GenerationJobStatus.PROCESSING).all()
    for job in stuck_jobs:
        job.status = GenerationJobStatus.FAILED
        job.error_code = "interrupted"
        job.error_message = "Interrupted by a server restart. Retry to attempt again."
        count += 1

    stuck_assets = db.query(Asset).filter(Asset.status == AssetStatus.PROCESSING).all()
    for asset in stuck_assets:
        asset.status = AssetStatus.FAILED
        asset.progress = None
        asset.error_code = "interrupted"
        asset.error_message = "Interrupted by a server restart. Retry to attempt again."
        count += 1

    db.commit()
    return count
