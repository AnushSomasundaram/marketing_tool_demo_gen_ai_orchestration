"""Startup recovery: on process restart, any job or asset left in 'processing'
belonged to a run that can no longer possibly complete (the process that was
polling it is gone), so we mark it failed-but-recoverable instead of leaving
it stuck forever. The user can retry via the normal revise/regenerate actions.
"""

from app.database import SessionLocal
from app.logging_config import get_logger
from app.services.job_service import recover_abandoned_jobs

logger = get_logger(__name__)


def run_startup_recovery() -> None:
    db = SessionLocal()
    try:
        recovered = recover_abandoned_jobs(db)
        if recovered:
            logger.warning("Startup recovery: marked %d abandoned job/asset row(s) as failed.", recovered)
    finally:
        db.close()
