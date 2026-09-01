import re
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.permissions import PLATFORM_ADMIN, VIEWER
from app.models.analytics import Job, ScheduledJobSetting
from app.services.auth_service import AuthenticationService
from app.services.job_service import JobService
from app.services.scheduled_job_service import ScheduledJobService

PASSWORD = "ValidPassword123!"


def create_user(db: Session, username: str, role: str):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {role})


def csrf_from(text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', text)
    assert match
    return match.group(1)


def login(client: TestClient, username: str) -> None:
    page = client.get("/login")
    token = csrf_from(page.text)
    response = client.post(
        "/login",
        data={
            "username": username,
            "password": PASSWORD,
            "csrf_token": token,
            "next": "/admin/background-processing",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_scheduler_defaults_are_created_with_documented_intervals(db: Session) -> None:
    service = ScheduledJobService(db)
    settings = {item.job_key: item for item in service.list_settings()}

    assert settings[JobService.METRICS_JOB].enabled is True
    assert settings[JobService.METRICS_JOB].interval_minutes == 360
    assert settings[JobService.FINDINGS_JOB].enabled is True
    assert settings[JobService.FINDINGS_JOB].interval_minutes == 60
    assert settings[JobService.METRICS_JOB].next_run_at is not None
    assert settings[JobService.FINDINGS_JOB].next_run_at is not None


def test_due_schedule_queues_once_and_resumes_interval_from_now(db: Session) -> None:
    service = ScheduledJobService(db)
    settings = {item.job_key: item for item in service.list_settings()}
    metrics = settings[JobService.METRICS_JOB]
    findings = settings[JobService.FINDINGS_JOB]
    due = datetime.now(timezone.utc) - timedelta(hours=12)
    metrics.next_run_at = due
    findings.enabled = False
    findings.next_run_at = None
    db.commit()

    now = datetime.now(timezone.utc)
    assert service.enqueue_due(now=now) == 1

    db.refresh(metrics)
    assert metrics.last_status == "Queued"
    assert metrics.last_enqueued_at is not None
    assert metrics.next_run_at is not None
    expected = now + timedelta(hours=6)
    next_run = metrics.next_run_at
    if next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=timezone.utc)
    assert abs((next_run - expected).total_seconds()) < 2
    assert service.enqueue_due(now=now + timedelta(minutes=1)) == 0

    jobs = list(db.scalars(select(Job).where(Job.status == "queued")).all())
    assert {job.job_type for job in jobs} == {
        JobService.METRICS_JOB,
        JobService.FINDINGS_JOB,
    }


def test_scheduler_interval_validation_and_disable(db: Session) -> None:
    actor = create_user(db, "scheduler_admin", PLATFORM_ADMIN)
    service = ScheduledJobService(db)
    service.list_settings()

    try:
        service.update(
            JobService.METRICS_JOB,
            enabled=True,
            interval_minutes=17,
            actor=actor,
        )
    except ValueError as exc:
        assert "supported" in str(exc)
    else:
        raise AssertionError("Unsupported interval accepted")

    setting = service.update(
        JobService.METRICS_JOB,
        enabled=False,
        interval_minutes=360,
        actor=actor,
    )
    assert setting.enabled is False
    assert setting.next_run_at is None


def test_platform_admin_can_manage_background_processing(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    login(client, "admin")

    page = client.get("/admin/background-processing")
    assert page.status_code == 200
    assert "Background Processing" in page.text
    assert "Analytics &amp; Metrics" in page.text or "Analytics & Metrics" in page.text
    assert "Findings Evaluation" in page.text
    assert "Every 6 hours" in page.text
    assert "Every 1 hour" in page.text
    token = csrf_from(page.text)

    response = client.post(
        f"/admin/background-processing/{JobService.METRICS_JOB}",
        data={
            "interval_minutes": "720",
            "enabled": "1",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    setting = db.get(ScheduledJobSetting, JobService.METRICS_JOB)
    assert setting is not None
    db.refresh(setting)
    assert setting.interval_minutes == 720
    assert setting.enabled is True


def test_non_platform_admin_cannot_manage_background_processing(client: TestClient, db: Session) -> None:
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    response = client.get("/admin/background-processing")
    assert response.status_code == 403


def test_run_now_queues_normal_worker_job(client: TestClient, db: Session) -> None:
    create_user(db, "run_admin", PLATFORM_ADMIN)
    login(client, "run_admin")
    page = client.get("/admin/background-processing")
    token = csrf_from(page.text)
    db.execute(delete(Job))
    db.commit()

    response = client.post(
        f"/admin/background-processing/{JobService.FINDINGS_JOB}/run",
        data={"csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 303

    job = db.scalar(
        select(Job).where(
            Job.job_type == JobService.FINDINGS_JOB,
            Job.status == "queued",
        )
    )
    assert job is not None
    setting = db.get(ScheduledJobSetting, JobService.FINDINGS_JOB)
    assert setting is not None
    db.refresh(setting)
    assert setting.last_status == "Queued"


def test_worker_records_schedule_execution_status(db: Session) -> None:
    from app.workers.metrics_worker import run_once

    service = ScheduledJobService(db)
    service.list_settings()
    db.execute(delete(Job))
    db.commit()
    JobService(db).enqueue_findings_evaluation(correlation_id="test:schedule-status")
    db.commit()

    assert run_once() is True

    setting = db.get(ScheduledJobSetting, JobService.FINDINGS_JOB)
    assert setting is not None
    db.refresh(setting)
    assert setting.last_status == "Successful"
    assert setting.last_started_at is not None
    assert setting.last_completed_at is not None
    assert setting.last_result_count is not None
