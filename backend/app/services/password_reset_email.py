"""SMTP delivery for password reset links."""

import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    sender = settings.SMTP_FROM or settings.SMTP_USER
    if not settings.SMTP_HOST or not sender:
        raise RuntimeError("SMTP_HOST and SMTP_FROM (or SMTP_USER) are required for password recovery")
    try:
        port = int(settings.SMTP_PORT or "587")
    except ValueError as exc:
        raise ValueError("SMTP_PORT must be a valid port number") from exc
    if not 1 <= port <= 65535:
        raise ValueError("SMTP_PORT must be between 1 and 65535")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must both be set when SMTP authentication is used")

    message = EmailMessage()
    message["Subject"] = "Reset your NEXORA password"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your NEXORA password.\n\n"
        f"Use this link within 30 minutes:\n{reset_url}\n\n"
        "If you did not request a reset, you can ignore this email."
    )

    if port == 465:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            port,
            timeout=10,
            context=ssl.create_default_context(),
        ) as server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return

    with smtplib.SMTP(settings.SMTP_HOST, port, timeout=10) as server:
        server.starttls(context=ssl.create_default_context())
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
