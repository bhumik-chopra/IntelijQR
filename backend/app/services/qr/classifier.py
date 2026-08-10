import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

from app.models.qr_scan import QrContentType


@dataclass(frozen=True, slots=True)
class Classification:
    content_type: QrContentType
    metadata: dict
    url: str | None = None


class SmartClassifier:
    _social_hosts = {
        "facebook.com", "instagram.com", "linkedin.com", "tiktok.com",
        "twitter.com", "x.com", "youtube.com", "youtu.be",
    }
    _image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

    def classify(self, content: str) -> Classification:
        value = content.strip()
        upper = value.upper()
        lower = value.lower()

        if upper.startswith("WIFI:"):
            return Classification("wifi", self._wifi_metadata(value))
        if upper.startswith("BEGIN:VCARD"):
            return Classification("contact", self._card_metadata(value))
        if upper.startswith("BEGIN:VEVENT"):
            return Classification("event", self._event_metadata(value))
        if lower.startswith("mailto:") or re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            address = value[7:].split("?", 1)[0] if lower.startswith("mailto:") else value
            return Classification("email", {"email": unquote(address)})
        if lower.startswith("tel:"):
            return Classification("phone", {"phone": value[4:]})
        if lower.startswith("geo:"):
            coordinates = value[4:].split("?", 1)[0]
            return Classification("location", {"coordinates": coordinates})
        if lower.startswith(("upi://", "bitcoin:", "ethereum:", "paytmmp://")):
            return Classification("payment", {"scheme": value.split(":", 1)[0].lower()})

        url = self._as_url(value)
        if url:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower().removeprefix("www.")
            path = parsed.path.lower()
            metadata = {"host": host, "scheme": parsed.scheme.lower()}
            if path.endswith(".pdf"):
                return Classification("pdf", metadata, url)
            if path.endswith(self._image_extensions):
                return Classification("image", metadata, url)
            if any(host == social or host.endswith(f".{social}") for social in self._social_hosts):
                return Classification("social_media", metadata, url)
            return Classification("website", metadata, url)
        return Classification("text", {"length": len(value)})

    @staticmethod
    def _as_url(value: str) -> str | None:
        candidate = value if "://" in value else f"https://{value}"
        parsed = urlparse(candidate)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        if "://" not in value and (" " in value or "." not in (parsed.hostname or "")):
            return None
        return candidate

    @staticmethod
    def _fields(value: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for line in value.replace(";", "\n").splitlines():
            if ":" in line:
                key, raw = line.split(":", 1)
                fields[key.upper().split(";", 1)[0]] = raw.replace("\\;", ";")
        return fields

    def _wifi_metadata(self, value: str) -> dict:
        fields = self._fields(value[5:])
        return {"ssid": fields.get("S", "Unknown network"), "security": fields.get("T", "unknown")}

    def _card_metadata(self, value: str) -> dict:
        fields = self._fields(value)
        return {key: fields[key] for key in ("FN", "ORG", "TITLE") if fields.get(key)}

    def _event_metadata(self, value: str) -> dict:
        fields = self._fields(value)
        return {key.lower(): fields[key] for key in ("SUMMARY", "DTSTART", "DTEND", "LOCATION") if fields.get(key)}
