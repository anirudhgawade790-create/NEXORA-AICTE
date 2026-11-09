import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def send_notification_email(recipient: str, message: str, action_link: str | None) -> None:
    sender = settings.SMTP_FROM or settings.SMTP_USER
    if not settings.SMTP_HOST or not sender:
        return
    try:
        port = int(settings.SMTP_PORT or "587")
    except ValueError as exc:
        raise ValueError("SMTP_PORT must be a valid port number") from exc
    if not 1 <= port <= 65535:
        raise ValueError("SMTP_PORT must be between 1 and 65535")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must both be set when SMTP authentication is used")

    email = EmailMessage()
    email["Subject"] = f"NEXORA alert: {message[:120]}"
    email["From"] = sender
    email["To"] = recipient
    content = f"{message}\n\nSign in to NEXORA to review this item."
    if action_link:
        content += f"\nWorkspace route: {action_link}"
    email.set_content(content)

    if port == 465:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            port,
            timeout=10,
            context=ssl.create_default_context(),
        ) as server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(email)
        return

    with smtplib.SMTP(settings.SMTP_HOST, port, timeout=10) as server:
        server.starttls(context=ssl.create_default_context())
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(email)
