import ipaddress
import re
from urllib.parse import urlparse


class SafeScanService:
    _shorteners = {
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
        "buff.ly", "cutt.ly", "rebrand.ly", "shorturl.at",
    }
    _suspicious_terms = {"verify", "urgent", "password", "wallet", "gift", "login", "account", "secure-update"}

    def assess(self, url: str) -> dict:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        warnings: list[str] = []
        checks: list[str] = []
        score = 0

        if parsed.scheme == "https":
            checks.append("Uses HTTPS encryption")
        else:
            score += 25
            warnings.append("Connection does not use HTTPS")
        if host in self._shorteners:
            score += 25
            warnings.append("URL shortening service hides the final destination")
        if "xn--" in host:
            score += 25
            warnings.append("Internationalized hostname may imitate another domain")
        if "@" in parsed.netloc:
            score += 30
            warnings.append("URL contains misleading user information")
        if len(url) > 180:
            score += 10
            warnings.append("Unusually long URL")
        if host.count(".") >= 4:
            score += 10
            warnings.append("Hostname contains many subdomains")
        try:
            port = parsed.port
        except ValueError:
            port = -1
        if port not in (None, 80, 443):
            score += 10
            warnings.append("URL uses a non-standard network port")
        if any(term in url.lower() for term in self._suspicious_terms):
            score += 15
            warnings.append("URL contains wording commonly used in phishing links")
        if self._is_private_or_ip(host):
            score += 20
            warnings.append("Destination uses a local or direct IP address")
        if re.search(r"[^a-z0-9.-]", host):
            score += 10
            warnings.append("Hostname contains unusual characters")

        score = min(score, 100)
        level = "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
        if not warnings:
            checks.append("No common phishing URL patterns detected")
        return {
            "checked": True,
            "is_safe": score < 50,
            "score": score,
            "level": level,
            "normalized_url": url,
            "checks": checks,
            "warnings": warnings,
        }

    @staticmethod
    def _is_private_or_ip(host: str) -> bool:
        if host in {"localhost", "localhost.localdomain"}:
            return True
        try:
            address = ipaddress.ip_address(host)
            return address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
        except ValueError:
            return False
