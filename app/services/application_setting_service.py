from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.settings import ApplicationSetting
from app.models.user import User
from app.services.audit_service import AuditService

LOGIN_RECAPTCHA_ENABLED = "login_recaptcha_enabled"


class ApplicationSettingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def get(self, key: str) -> ApplicationSetting | None:
        return self.db.scalar(select(ApplicationSetting).where(ApplicationSetting.key == key))

    def get_bool(self, key: str, *, default: bool = False) -> bool:
        setting = self.get(key)
        if setting is None:
            return default
        return setting.value.strip().lower() in {"1", "true", "yes", "on"}

    def recaptcha_enabled(self) -> bool:
        return self.get_bool(LOGIN_RECAPTCHA_ENABLED, default=False)

    def set_recaptcha_enabled(self, enabled: bool, *, actor: User) -> ApplicationSetting:
        settings = get_settings()
        if enabled and not settings.recaptcha_configured:
            raise ValueError(
                "Google reCAPTCHA cannot be enabled until both the site key and secret key "
                "are configured in the application environment."
            )

        setting = self.get(LOGIN_RECAPTCHA_ENABLED)
        before_enabled = self.recaptcha_enabled()
        if setting is None:
            setting = ApplicationSetting(
                key=LOGIN_RECAPTCHA_ENABLED,
                value="true" if enabled else "false",
                updated_by_user_id=actor.id,
            )
            self.db.add(setting)
        else:
            setting.value = "true" if enabled else "false"
            setting.updated_by_user_id = actor.id

        self.audit.record(
            action="ApplicationSettingUpdated",
            entity_type="application_setting",
            entity_id=LOGIN_RECAPTCHA_ENABLED,
            actor=actor,
            before={"enabled": before_enabled},
            after={"enabled": enabled},
            source="Administration",
        )
        self.db.commit()
        self.db.refresh(setting)
        return setting
