import argparse
import getpass

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticationService
from app.services.demo_service import DemoDataService
from app.services.findings_service import FindingsService
from app.services.job_service import JobService
from app.services.seed_service import SystemSeedService


def create_admin(username: str, display_name: str) -> int:
    password = getpass.getpass("Password (minimum 12 characters): ")
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Passwords do not match.")
        return 1
    with get_session_factory()() as db:
        try:
            user = AuthenticationService(db).create_initial_admin(username, display_name, password)
        except ValueError as exc:
            print(f"Unable to create administrator: {exc}")
            return 1
    print(f"Created initial Platform Administrator: {user.username}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenEA Community administration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    admin = subparsers.add_parser("create-admin", help="Create the initial Platform Administrator")
    admin.add_argument("--username", required=True)
    admin.add_argument("--display-name", required=True)
    subparsers.add_parser("seed-system", help="Seed the standard OpenEA Community metamodel and reference data")
    subparsers.add_parser("recalculate-metrics", help="Queue analytics and risk metric recalculation")
    subparsers.add_parser("recalculate-metrics-now", help="Recalculate analytics synchronously for administration/testing")
    subparsers.add_parser("evaluate-findings", help="Queue finding rule evaluation")
    subparsers.add_parser("evaluate-findings-now", help="Evaluate finding rules synchronously for administration/testing")
    subparsers.add_parser("seed-demo", help="Seed the fictional Northstar Financial demo repository")
    subparsers.add_parser("remove-demo", help="Archive the Northstar Financial demo repository")
    args = parser.parse_args()
    if args.command == "create-admin":
        return create_admin(args.username, args.display_name)
    if args.command == "recalculate-metrics":
        with get_session_factory()() as db:
            job = JobService(db).enqueue_metrics_recalculation()
            db.commit()
        print(f"Queued metrics recalculation job: {job.id}")
        return 0
    if args.command == "evaluate-findings":
        with get_session_factory()() as db:
            job = JobService(db).enqueue_findings_evaluation()
            db.commit()
        print(f"Queued findings evaluation job: {job.id}")
        return 0
    if args.command == "evaluate-findings-now":
        with get_session_factory()() as db:
            count = FindingsService(db).evaluate_all()
        print(f"Findings evaluation complete: active_findings={count}")
        return 0
    if args.command == "recalculate-metrics-now":
        with get_session_factory()() as db:
            count = AnalyticsService(db).calculate_all()
        print(f"Metrics recalculation complete: metrics={count}")
        return 0
    if args.command in {"seed-demo", "remove-demo"}:
        with get_session_factory()() as db:
            actor = db.scalar(select(User).where(User.is_active.is_(True)).order_by(User.created_at))
            if actor is None:
                print("Create an administrator before managing demo data.")
                return 1
            service = DemoDataService(db)
            counts = service.seed(actor) if args.command == "seed-demo" else service.remove(actor)
        action = "seeded" if args.command == "seed-demo" else "archived"
        print(f"Demo data {action}: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
        return 0
    if args.command == "seed-system":
        with get_session_factory()() as db:
            counts = SystemSeedService(db).seed()
        print("System seed complete: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
