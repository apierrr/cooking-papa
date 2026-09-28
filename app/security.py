import hmac
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException, status

from .config import CSRF_SECRET

_serializer = URLSafeTimedSerializer(CSRF_SECRET, salt="csrf")
CSRF_COOKIE = "csrf_token"
CSRF_MAX_AGE = 60 * 60 * 8  # 8h


def issue_csrf_token() -> str:
    return _serializer.dumps(secrets.token_urlsafe(16))


def verify_csrf(request: Request, form_token: str | None) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    if not cookie_token or not form_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token missing")
    if not hmac.compare_digest(cookie_token, form_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token mismatch")
    try:
        _serializer.loads(cookie_token, max_age=CSRF_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token expired")
    except BadSignature:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token invalid")


SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}
