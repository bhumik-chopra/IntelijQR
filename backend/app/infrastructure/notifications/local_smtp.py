import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import Settings


class LocalSmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._username = settings.smtp_username
        self._password = settings.smtp_password
        self._starttls = settings.smtp_starttls
        self._from_email = settings.notification_from_email

    @property
    def available(self) -> bool:
        return self._host is not None

    async def send(self, recipient: str, subject: str, body: str) -> None:
        if not self._host:
            return
        message = EmailMessage()
        message["From"] = self._from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port, timeout=10) as client:
            if self._starttls:
                client.starttls()
            if self._username and self._password:
                client.login(self._username, self._password)
            client.send_message(message)
