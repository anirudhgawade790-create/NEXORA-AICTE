import hashlib

from fastapi import HTTPException, Request
from limits import parse
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

_password_reset_email_limit = parse("3/hour")


def enforce_password_reset_email_limit(request: Request, email: str) -> None:
    """Keep reset limits separate per normalized email and source IP."""
    normalized_email = email.strip().casefold()
    email_hash = hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
    if not limiter.limiter.hit(
        _password_reset_email_limit,
        "password-reset-email",
        get_remote_address(request),
        email_hash,
    ):
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests for this email. Try again later.",
        )
