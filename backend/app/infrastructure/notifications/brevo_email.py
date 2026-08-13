import httpx

from app.core.config import Settings


class BrevoEmailSender:
    _endpoint = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.brevo_api_key
        self._from_email = settings.notification_from_email
        self._from_name = settings.notification_from_name

    @property
    def available(self) -> bool:
        return bool(self._api_key and self._from_email and not self._from_email.endswith(".local"))

    async def send(self, recipient: str, subject: str, body: str) -> None:
        if not self.available:
            return
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self._endpoint,
                headers={"api-key": self._api_key, "accept": "application/json"},
                json={
                    "sender": {"name": self._from_name, "email": self._from_email},
                    "to": [{"email": recipient}],
                    "subject": subject,
                    "textContent": body,
                },
            )
            response.raise_for_status()
