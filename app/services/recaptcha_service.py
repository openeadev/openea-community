import json
import logging
from dataclasses import dataclass
from urllib import error, parse, request

from app.core.config import get_settings

logger = logging.getLogger("openea.auth.recaptcha")
VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
VERIFY_TIMEOUT_SECONDS = 5.0


class RecaptchaVerificationUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class RecaptchaVerificationResult:
    success: bool
    error_codes: tuple[str, ...] = ()


class RecaptchaService:
    def verify(self, response_token: str) -> RecaptchaVerificationResult:
        settings = get_settings()
        if not settings.recaptcha_configured:
            raise RecaptchaVerificationUnavailable("reCAPTCHA credentials are not configured")

        payload = parse.urlencode(
            {
                "secret": settings.recaptcha_secret_key,
                "response": response_token,
            }
        ).encode("utf-8")
        verification_request = request.Request(
            VERIFY_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with request.urlopen(verification_request, timeout=VERIFY_TIMEOUT_SECONDS) as response:
                raw = response.read()
        except (error.URLError, TimeoutError, OSError) as exc:
            logger.warning("recaptcha_verification_unavailable", extra={"reason": type(exc).__name__})
            raise RecaptchaVerificationUnavailable(
                "reCAPTCHA verification service is unavailable"
            ) from exc

        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("recaptcha_invalid_verification_response")
            raise RecaptchaVerificationUnavailable(
                "reCAPTCHA verification service returned an invalid response"
            ) from exc

        error_codes = tuple(str(code) for code in result.get("error-codes", []))
        success = bool(result.get("success"))
        if not success:
            logger.info("recaptcha_verification_failed", extra={"error_codes": error_codes})
        return RecaptchaVerificationResult(success=success, error_codes=error_codes)
