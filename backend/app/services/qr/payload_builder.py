from urllib.parse import urlencode

from app.schemas.qr_generation import (
    ContactQrRequest,
    EmailQrRequest,
    LocationQrRequest,
    PhoneQrRequest,
    QrGenerationRequest,
    TextQrRequest,
    UrlQrRequest,
    WifiQrRequest,
)


def _escape_wifi(value: str) -> str:
    for character in ("\\", ";", ",", ":", '"'):
        value = value.replace(character, f"\\{character}")
    return value


def _escape_vcard(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


class QrPayloadBuilder:
    def build(self, request: QrGenerationRequest) -> str:
        if isinstance(request, UrlQrRequest):
            return str(request.url)
        if isinstance(request, TextQrRequest):
            return request.text
        if isinstance(request, EmailQrRequest):
            query = urlencode(
                {key: value for key, value in {"subject": request.subject, "body": request.body}.items() if value}
            )
            return f"mailto:{request.email}" + (f"?{query}" if query else "")
        if isinstance(request, PhoneQrRequest):
            return f"tel:{request.phone.replace(' ', '')}"
        if isinstance(request, WifiQrRequest):
            return (
                f"WIFI:T:{request.security};S:{_escape_wifi(request.ssid)};"
                f"P:{_escape_wifi(request.password)};H:{str(request.hidden).lower()};;"
            )
        if isinstance(request, ContactQrRequest):
            lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{_escape_vcard(request.full_name)}"]
            optional = (
                ("ORG", request.organization),
                ("TITLE", request.title),
                ("TEL", request.phone),
                ("EMAIL", str(request.email) if request.email else None),
                ("URL", str(request.url) if request.url else None),
                ("ADR", request.address),
            )
            lines.extend(f"{key}:{_escape_vcard(value)}" for key, value in optional if value)
            return "\r\n".join([*lines, "END:VCARD"])
        if isinstance(request, LocationQrRequest):
            base = f"geo:{request.latitude:.6f},{request.longitude:.6f}"
            if request.name:
                return f"{base}?{urlencode({'q': f'{request.latitude:.6f},{request.longitude:.6f}({request.name})'})}"
            return base
        raise TypeError("Unsupported QR payload type")

    def safe_details(self, request: QrGenerationRequest) -> dict:
        details = request.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"design", "logo_data_url", "expires_at", "max_scans", "label"},
        )
        if isinstance(request, WifiQrRequest) and "password" in details:
            details["password"] = "***" if request.password else ""
        return details

    def preview(self, request: QrGenerationRequest, payload: str) -> str:
        if isinstance(request, WifiQrRequest):
            return f"WiFi: {request.ssid}"
        if isinstance(request, ContactQrRequest):
            return f"Contact: {request.full_name}"
        if isinstance(request, LocationQrRequest):
            return request.name or f"{request.latitude:.6f}, {request.longitude:.6f}"
        return payload[:160]
