from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import ScheduledJobSetting
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.job_service import JobService


class ScheduledJobService:
    METRICS_KEY = JobService.METRICS_JOB
    FINDINGS_KEY = JobService.FINDINGS_JOB

    ALLOWED_INTERVALS: tuple[int, ...] = (15, 30, 60, 120, 240, 360, 720, 1440)
    DEFAULTS: dict[str, dict[str, Any]] = {
        METRICS_KEY: {
            "label": "Analytics & Metrics",
            "description": (
                "Recalculate persisted architecture metrics so date-dependent and repository-derived "
                "scores remain current even when the repository is otherwise idle."
            ),
            "interval_minutes": 360,
        },
        FINDINGS_KEY: {
            "label": "Findings Evaluation",
            "description": (
                "Evaluate built-in and custom finding rules periodically so time-based findings can "
                "appear or resolve even when no repository write occurs."
            ),
            "interval_minutes": 60,
        },
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    def ensure_defaults(self, *, now: datetime | None = None) -> None:
        current = now or self.now()
        existing = set(self.db.scalars(select(ScheduledJobSetting.job_key)).all())
        changed = False
        for job_key, definition in self.DEFAULTS.items():
            if job_key in existing:
                continue
            interval = int(definition["interval_minutes"])
            self.db.add(
                ScheduledJobSetting(
                    job_key=job_key,
                    enabled=True,
                    interval_minutes=interval,
                    next_run_at=current + timedelta(minutes=interval),
                    last_status="Never run",
                )
            )
            changed = True
        if changed:
            self.db.commit()

    def list_settings(self) -> list[ScheduledJobSetting]:
        self.ensure_defaults()
        rows = list(self.db.scalars(select(ScheduledJobSetting)).all())
        order = {key: idx for idx, key in enumerate(self.DEFAULTS)}
        rows.sort(key=lambda row: order.get(row.job_key, 999))
        return rows

    def get(self, job_key: str) -> ScheduledJobSetting | None:
        self.ensure_defaults()
        return self.db.get(ScheduledJobSetting, job_key)

    def update(
        self,
        job_key: str,
        *,
        enabled: bool,
        interval_minutes: int,
        actor: User,
    ) -> ScheduledJobSetting:
        if interval_minutes not in self.ALLOWED_INTERVALS:
            raise ValueError("Select a supported background-processing interval")
        setting = self.get(job_key)
        if setting is None or job_key not in self.DEFAULTS:
            raise ValueError("Unknown scheduled process")

        before = self._state(setting)
        now = self.now()
        setting.enabled = enabled
        setting.interval_minutes = interval_minutes
        setting.next_run_at = now + timedelta(minutes=interval_minutes) if enabled else None
        setting.updated_by_user_id = actor.id
        setting.updated_at = now
        AuditService(self.db).record(
            action="ScheduledJobUpdated",
            entity_type="scheduled_job_setting",
            entity_id=job_key,
            actor=actor,
            before=before,
            after=self._state(setting),
            source="Administration",
        )
        self.db.commit()
        return setting

    def run_now(self, job_key: str, *, actor: User) -> ScheduledJobSetting:
        setting = self.get(job_key)
        if setting is None or job_key not in self.DEFAULTS:
            raise ValueError("Unknown scheduled process")
        now = self.now()
        self._enqueue(job_key, correlation_id=f"manual:{job_key}:{actor.id}")
        setting.last_enqueued_at = now
        setting.last_status = "Queued"
        setting.last_error = None
        setting.updated_by_user_id = actor.id
        setting.updated_at = now
        AuditService(self.db).record(
            action="ScheduledJobRunRequested",
            entity_type="scheduled_job_setting",
            entity_id=job_key,
            actor=actor,
            after={"job_key": job_key, "requested_at": now.isoformat()},
            source="Administration",
        )
        self.db.commit()
        return setting

    def enqueue_due(self, *, now: datetime | None = None) -> int:
        self.ensure_defaults(now=now)
        current = now or self.now()
        stmt = (
            select(ScheduledJobSetting)
            .where(
                ScheduledJobSetting.enabled.is_(True),
                ScheduledJobSetting.next_run_at.is_not(None),
                ScheduledJobSetting.next_run_at <= current,
            )
            .order_by(ScheduledJobSetting.next_run_at, ScheduledJobSetting.job_key)
        )
        if self.db.bind is not None and self.db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)
        settings = list(self.db.scalars(stmt).all())
        if not settings:
            return 0

        for setting in settings:
            self._enqueue(
                setting.job_key,
                correlation_id=f"schedule:{setting.job_key}:{current.isoformat()}",
            )
            setting.last_enqueued_at = current
            setting.last_status = "Queued"
            setting.last_error = None
            # If the platform was offline, run the overdue process once and resume from now.
            setting.next_run_at = current + timedelta(minutes=setting.interval_minutes)
            setting.updated_at = current
        self.db.commit()
        return len(settings)

    def record_started(
        self,
        job_key: str,
        *,
        enqueued_at: datetime | None = None,
        started_at: datetime | None = None,
    ) -> None:
        setting = self.db.get(ScheduledJobSetting, job_key)
        if setting is None:
            return
        if enqueued_at is not None:
            setting.last_enqueued_at = enqueued_at
        setting.last_started_at = started_at or self.now()
        setting.last_status = "Running"
        setting.updated_at = setting.last_started_at
        self.db.flush()

    def record_completed(
        self,
        job_key: str,
        *,
        result_count: int,
        completed_at: datetime | None = None,
    ) -> None:
        setting = self.db.get(ScheduledJobSetting, job_key)
        if setting is None:
            return
        setting.last_completed_at = completed_at or self.now()
        setting.last_status = "Successful"
        setting.last_result_count = result_count
        setting.last_error = None
        setting.updated_at = setting.last_completed_at
        self.db.flush()

    def record_failed(
        self,
        job_key: str,
        *,
        error: str,
        failed_at: datetime | None = None,
    ) -> None:
        setting = self.db.get(ScheduledJobSetting, job_key)
        if setting is None:
            return
        setting.last_completed_at = failed_at or self.now()
        setting.last_status = "Failed"
        setting.last_error = error[:4000]
        setting.updated_at = setting.last_completed_at
        self.db.flush()

    def view(self, setting: ScheduledJobSetting) -> dict[str, Any]:
        definition = self.DEFAULTS[setting.job_key]
        return {
            "job_key": setting.job_key,
            "label": definition["label"],
            "description": definition["description"],
            "enabled": setting.enabled,
            "interval_minutes": setting.interval_minutes,
            "interval_label": self.interval_label(setting.interval_minutes),
            "last_enqueued_at": setting.last_enqueued_at,
            "last_started_at": setting.last_started_at,
            "last_completed_at": setting.last_completed_at,
            "next_run_at": setting.next_run_at,
            "last_status": setting.last_status,
            "last_result_count": setting.last_result_count,
            "last_error": setting.last_error,
        }

    @classmethod
    def interval_options(cls) -> list[dict[str, int | str]]:
        return [
            {"minutes": minutes, "label": cls.interval_label(minutes)}
            for minutes in cls.ALLOWED_INTERVALS
        ]

    @staticmethod
    def interval_label(minutes: int) -> str:
        if minutes < 60:
            return f"Every {minutes} minutes"
        hours = minutes // 60
        if hours == 1:
            return "Every 1 hour"
        if hours == 24:
            return "Every 24 hours"
        return f"Every {hours} hours"

    def _enqueue(self, job_key: str, *, correlation_id: str) -> None:
        jobs = JobService(self.db)
        if job_key == self.METRICS_KEY:
            jobs.enqueue_metrics_recalculation(correlation_id=correlation_id)
            return
        if job_key == self.FINDINGS_KEY:
            jobs.enqueue_findings_evaluation(correlation_id=correlation_id)
            return
        raise ValueError("Unknown scheduled process")

    @staticmethod
    def _state(setting: ScheduledJobSetting) -> dict[str, Any]:
        return {
            "job_key": setting.job_key,
            "enabled": setting.enabled,
            "interval_minutes": setting.interval_minutes,
            "next_run_at": setting.next_run_at.isoformat() if setting.next_run_at else None,
            "last_status": setting.last_status,
        }
