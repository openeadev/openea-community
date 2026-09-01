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
from app.services.scheduled_job_service import ScheduledJobService

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("openea.worker")

SCHEDULE_CHECK_SECONDS = 60


def run_schedules_once() -> int:
    with get_session_factory()() as db:
        count = ScheduledJobService(db).enqueue_due()
        if count:
            logger.info("scheduled_jobs_enqueued", extra={"schedule_count": count})
        return count


def run_once() -> bool:
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    with get_session_factory()() as db:
        jobs = JobService(db)
        job = jobs.claim_next(worker_id)
        if job is None:
            return False
        scheduler = ScheduledJobService(db)
        try:
            scheduler.record_started(job.job_type, enqueued_at=job.created_at)
            db.commit()
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
            scheduler.record_completed(job.job_type, result_count=count)
            jobs.complete(job)
        except Exception as exc:  # worker boundary must record failures
            logger.exception("job_failed", extra={"job_id": job.id, "job_type": job.job_type})
            scheduler.record_failed(job.job_type, error=str(exc))
            jobs.fail(job, str(exc))
        return True


def main() -> None:
    next_schedule_check = 0.0
    while True:
        try:
            monotonic_now = time.monotonic()
            if monotonic_now >= next_schedule_check:
                try:
                    run_schedules_once()
                finally:
                    next_schedule_check = monotonic_now + SCHEDULE_CHECK_SECONDS
            worked = run_once()
        except Exception:
            # During an in-place upgrade the worker can start before a new migration
            # is applied. Remain available and retry rather than entering a restart loop.
            logger.exception("worker_iteration_failed")
            worked = False
        if not worked:
            time.sleep(2)


if __name__ == "__main__":
    main()
