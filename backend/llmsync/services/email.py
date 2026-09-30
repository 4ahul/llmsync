import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from llmsync.config import settings
import logging

logger = logging.getLogger(__name__)

async def send_magic_link_email(email: str, token: str):
    """Send magic link verification email."""
    magic_link = f"http://localhost:8000/api/auth/verify?token={token}"

    message = MIMEMultipart("alternative")
    message["Subject"] = "LLMSync Login Link"
    message["From"] = settings.from_email
    message["To"] = email

    text = f"""
Click the link below to log in to LLMSync:

{magic_link}

This link expires in 30 minutes.
    """

    html = f"""
<html>
  <body>
    <p>Click the link below to log in to LLMSync:</p>
    <p><a href="{magic_link}">Log in to LLMSync</a></p>
    <p>This link expires in 30 minutes.</p>
  </body>
</html>
    """

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        if settings.smtp_user and settings.smtp_password:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=True
            )
        else:
            # Dev mode: just log
            logger.info(f"Magic link for {email}: {magic_link}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise
