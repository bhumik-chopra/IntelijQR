import httpx
from html import escape

from app.core.config import Settings


class BrevoEmailSender:
    _endpoint = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.brevo_api_key
        self._from_email = settings.notification_from_email
        self._from_name = settings.notification_from_name
        self._notification_url = f"{settings.frontend_base_url.rstrip('/')}/notifications"

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
                    "textContent": f"{body}\n\nView notifications: {self._notification_url}",
                    "htmlContent": self._render_html(subject, body),
                },
            )
            response.raise_for_status()

    def _render_html(self, subject: str, body: str) -> str:
        title = subject.removeprefix("IntelliQR:").strip() or "New notification"
        safe_title = escape(title)
        safe_body = escape(body).replace("\n", "<br>")
        safe_url = escape(self._notification_url, quote=True)
        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#080811;font-family:Inter,Arial,sans-serif;color:#f8fafc">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#080811;padding:32px 12px">
    <tr><td align="center">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#121225;border:1px solid #2d2b4f;border-radius:24px;overflow:hidden">
        <tr><td style="height:6px;background:linear-gradient(90deg,#7c3aed,#4f46e5,#3b82f6)"></td></tr>
        <tr><td style="padding:30px 34px 18px">
          <table role="presentation" cellspacing="0" cellpadding="0"><tr>
            <td style="width:44px;height:44px;border-radius:14px;background:#6d4aff;text-align:center;font-size:22px;font-weight:800;color:#fff">IQ</td>
            <td style="padding-left:13px"><div style="font-size:20px;font-weight:800;color:#fff">Intelli<span style="color:#7c8cff">QR</span></div><div style="font-size:12px;color:#8b91aa;margin-top:3px">Smart notification</div></td>
          </tr></table>
        </td></tr>
        <tr><td style="padding:8px 34px 34px">
          <div style="display:inline-block;padding:6px 11px;border-radius:999px;background:#27214a;color:#bca7ff;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase">Activity update</div>
          <h1 style="margin:20px 0 12px;font-size:28px;line-height:1.25;color:#fff">{safe_title}</h1>
          <div style="padding:18px 20px;border:1px solid #292944;border-radius:16px;background:#18182d;color:#c8ccdc;font-size:15px;line-height:1.7">{safe_body}</div>
          <table role="presentation" cellspacing="0" cellpadding="0" style="margin-top:25px"><tr><td style="border-radius:13px;background:#6d4aff">
            <a href="{safe_url}" style="display:inline-block;padding:14px 24px;color:#fff;text-decoration:none;font-size:14px;font-weight:700">Open IntelliQR&nbsp; →</a>
          </td></tr></table>
          <p style="margin:25px 0 0;color:#747b94;font-size:12px;line-height:1.6">This automated message was sent because email notifications are enabled for your IntelliQR account. Never share passwords or access keys by email.</p>
        </td></tr>
        <tr><td style="padding:18px 34px;border-top:1px solid #25253d;color:#646b82;font-size:11px">© IntelliQR · Secure QR management</td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
