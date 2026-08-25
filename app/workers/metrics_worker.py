import logging
import os
import socket
import time

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_session_factory
from app.services.analytics_service import AnalyticsService
from app.services.findings_service import FindingsService
from app.services.job_service import JobService

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("openea.worker")


def run_once() -> bool:
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    with get_session_factory()() as db:
        jobs = JobService(db)
        job = jobs.claim_next(worker_id)
        if job is None:
            return False
        try:
            if job.job_type == JobService.METRICS_JOB:
                count = AnalyticsService(db).calculate_all()
                logger.info(
                    "metrics_recalculated",
                    extra={"job_id": job.id, "job_type": job.job_type, "metric_count": count},
                )
            elif job.job_type == JobService.FINDINGS_JOB:
                count = FindingsService(db).evaluate_all()
                logger.info(
                    "findings_evaluated",
                    extra={"job_id": job.id, "job_type": job.job_type, "finding_count": count},
                )
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")
            jobs.complete(job)
        except Exception as exc:  # worker boundary must record failures
            logger.exception("job_failed", extra={"job_id": job.id, "job_type": job.job_type})
            jobs.fail(job, str(exc))
        return True


def main() -> None:
    while True:
        try:
            worked = run_once()
        except Exception:
            # During an in-place upgrade the worker can start before the new job
            # table migration is applied. Remain available and retry rather than
            # entering a container restart loop.
            logger.exception("worker_iteration_failed")
            worked = False
        if not worked:
            time.sleep(2)


if __name__ == "__main__":
    main()
