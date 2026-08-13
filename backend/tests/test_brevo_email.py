import asyncio

from app.core.config import Settings
from app.infrastructure.notifications.brevo_email import BrevoEmailSender


def test_brevo_sender_posts_transactional_email(monkeypatch) -> None:
    captured = {}

    class Response:
        def raise_for_status(self): return None

    class Client:
        def __init__(self, **_kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def post(self, url, **kwargs):
            captured.update(url=url, **kwargs)
            return Response()

    monkeypatch.setattr("app.infrastructure.notifications.brevo_email.httpx.AsyncClient", Client)
    settings = Settings(_env_file=None, jwt_secret="x" * 32, brevo_api_key="secret",
                        notification_from_email="owner@example.com", notification_from_name="IntelliQR",
                        frontend_base_url="https://intelij-qr.vercel.app")

    asyncio.run(BrevoEmailSender(settings).send("user@example.com", "Test", "It works"))

    assert captured["headers"]["api-key"] == "secret"
    assert captured["json"]["sender"] == {"name": "IntelliQR", "email": "owner@example.com"}
    assert captured["json"]["to"] == [{"email": "user@example.com"}]
    assert "<h1" in captured["json"]["htmlContent"]
    assert "Test" in captured["json"]["htmlContent"]
    assert "https://intelij-qr.vercel.app/notifications" in captured["json"]["htmlContent"]


def test_brevo_email_escapes_notification_content() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32, brevo_api_key="secret",
                        notification_from_email="owner@example.com")
    html = BrevoEmailSender(settings)._render_html("IntelliQR: <Alert>", "<script>bad()</script>")

    assert "<script>" not in html
    assert "&lt;script&gt;bad()&lt;/script&gt;" in html
