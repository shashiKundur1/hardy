from email.message import EmailMessage

import aiosmtplib

from src.config import settings
from src.observability import get_logger

SMTP_TIMEOUT_SECONDS = 30

logger = get_logger("mailer")


def configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user)


def compose(to: str, subject: str, text: str, html: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_user or "hardy@localhost"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


async def send(message: EmailMessage) -> bool:
    if not configured():
        logger.info("smtp unconfigured, holding message for %s", message["To"])
        return False
    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=True,
        timeout=SMTP_TIMEOUT_SECONDS,
    )
    logger.info("sent %s to %s", message["Subject"], message["To"])
    return True
