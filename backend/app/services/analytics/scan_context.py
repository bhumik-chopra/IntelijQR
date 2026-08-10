import hashlib
import hmac
import ipaddress
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScanContext:
    visitor_hash: str
    device_type: str
    browser: str
    operating_system: str
    country: str
    city: str


class ScanContextService:
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def parse(self, client_ip: str, user_agent: str) -> ScanContext:
        normalized_agent = user_agent[:1000]
        visitor_hash = hmac.new(
            self._secret,
            f"{client_ip}|{normalized_agent}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return ScanContext(
            visitor_hash=visitor_hash,
            device_type=self._device(normalized_agent),
            browser=self._browser(normalized_agent),
            operating_system=self._os(normalized_agent),
            country=self._country(client_ip),
            city="Local Network" if self._is_local(client_ip) else "Unknown",
        )

    @staticmethod
    def _device(agent: str) -> str:
        lower = agent.lower()
        if any(value in lower for value in ("bot", "crawler", "spider", "slurp")):
            return "bot"
        if any(value in lower for value in ("ipad", "tablet", "kindle")):
            return "tablet"
        if any(value in lower for value in ("mobile", "iphone", "android")):
            return "mobile"
        return "desktop" if agent else "unknown"

    @staticmethod
    def _browser(agent: str) -> str:
        if "Edg/" in agent:
            return "Edge"
        if "OPR/" in agent or "Opera" in agent:
            return "Opera"
        if "Firefox/" in agent:
            return "Firefox"
        if "Chrome/" in agent or "CriOS/" in agent:
            return "Chrome"
        if "Safari/" in agent:
            return "Safari"
        return "Other"

    @staticmethod
    def _os(agent: str) -> str:
        if "Windows" in agent:
            return "Windows"
        if "Android" in agent:
            return "Android"
        if "iPhone" in agent or "iPad" in agent:
            return "iOS"
        if "Mac OS X" in agent or "Macintosh" in agent:
            return "macOS"
        if "Linux" in agent:
            return "Linux"
        return "Other"

    @classmethod
    def _country(cls, client_ip: str) -> str:
        return "Local" if cls._is_local(client_ip) else "Unknown"

    @staticmethod
    def _is_local(client_ip: str) -> bool:
        try:
            address = ipaddress.ip_address(client_ip)
            return address.is_private or address.is_loopback or address.is_link_local
        except ValueError:
            return client_ip.lower() == "localhost"
