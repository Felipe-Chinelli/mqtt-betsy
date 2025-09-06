import aiosmtplib
from email.message import EmailMessage
import logging

from .config import settings

logger = logging.getLogger(__name__)

async def send_notification_email(subject: str, body: str, recipient_email: str):
    msg = EmailMessage()
    msg['From'] = settings.EMAIL_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        async with aiosmtplib.SMTP(hostname=settings.EMAIL_HOST, port=settings.EMAIL_PORT, use_tls=True) as smtp:
            await smtp.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            await smtp.send_message(msg)
        logger.info(f"Email sent successfully to {recipient_email} with subject: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)