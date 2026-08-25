from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import Job


class JobService:
    METRICS_JOB = "recalculate_all_metrics"
    FINDINGS_JOB = "evaluate_findings"

    def __init__(self, db: Session) -> None:
        self.db = db

    def enqueue_metrics_recalculation(self, *, correlation_id: str | None = None) -> Job:
        existing = self.db.scalar(
            select(Job).where(Job.job_type == self.METRICS_JOB, Job.status == "queued").limit(1)
        )
        if existing is not None:
            return existing
        job = Job(job_type=self.METRICS_JOB, payload={}, correlation_id=correlation_id)
        self.db.add(job)
        self.db.flush()
        self.enqueue_findings_evaluation(correlation_id=correlation_id)
        return job

    def enqueue_findings_evaluation(self, *, correlation_id: str | None = None) -> Job:
        existing = self.db.scalar(
            select(Job).where(Job.job_type == self.FINDINGS_JOB, Job.status == "queued").limit(1)
        )
        if existing is not None:
            return existing
        job = Job(job_type=self.FINDINGS_JOB, payload={}, correlation_id=correlation_id)
        self.db.add(job)
        self.db.flush()
        return job

    def claim_next(self, worker_id: str) -> Job | None:
        stmt = (
            select(Job)
            .where(Job.status == "queued", Job.available_at <= datetime.now(timezone.utc))
            .order_by(Job.created_at)
            .limit(1)
        )
        if self.db.bind is not None and self.db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)
        job = self.db.scalar(stmt)
        if job is None:
            return None
        job.status = "running"
        job.locked_by = worker_id
        job.locked_at = datetime.now(timezone.utc)
        job.attempts += 1
        self.db.commit()
        return job

    def complete(self, job: Job) -> None:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = job.completed_at
        self.db.commit()

    def fail(self, job: Job, error: str) -> None:
        job.status = "failed"
        job.last_error = error[:4000]
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
