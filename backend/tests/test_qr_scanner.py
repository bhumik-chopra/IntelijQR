import asyncio
from io import BytesIO

import qrcode
import pytest

from app.infrastructure.qr.decoder import QrImageDecoder
from app.services.qr.classifier import SmartClassifier
from app.services.qr.safe_scan import SafeScanService
from app.services.qr.scanner_service import QrScannerService


def test_decoder_reads_generated_qr_image() -> None:
    image = qrcode.make("https://example.com/safe")
    output = BytesIO()
    image.save(output, format="PNG")

    assert QrImageDecoder().decode(output.getvalue()) == ["https://example.com/safe"]


@pytest.mark.parametrize("content", ["नमस्ते दुनिया", "નમસ્તે વિશ્વ", "مرحبا بالعالم", "こんにちは世界"])
def test_decoder_preserves_multilingual_utf8_content(content: str) -> None:
    image = qrcode.make(content)
    output = BytesIO()
    image.save(output, format="PNG")

    assert QrImageDecoder().decode(output.getvalue()) == [content]


def test_classifier_recognizes_structured_and_web_content() -> None:
    classifier = SmartClassifier()

    assert classifier.classify("WIFI:T:WPA;S:Office;P:secret;;").content_type == "wifi"
    assert classifier.classify("BEGIN:VCARD\nFN:Ada Lovelace\nEND:VCARD").content_type == "contact"
    assert classifier.classify("mailto:hello@example.com").content_type == "email"
    assert classifier.classify("https://example.com/report.pdf").content_type == "pdf"
    assert classifier.classify("https://instagram.com/intelliqr").content_type == "social_media"
    assert classifier.classify("ordinary text").content_type == "text"


def test_wifi_classification_does_not_expose_password() -> None:
    result = SmartClassifier().classify("WIFI:T:WPA;S:Office;P:super-secret;;")

    assert result.metadata == {"ssid": "Office", "security": "WPA"}
    assert "super-secret" not in str(result.metadata)


def test_safe_scan_scores_https_and_suspicious_links() -> None:
    scanner = SafeScanService()
    safe = scanner.assess("https://example.com/about")
    risky = scanner.assess("http://bit.ly/urgent-login-account")

    assert safe["score"] == 0
    assert safe["is_safe"] is True
    assert risky["score"] >= 50
    assert risky["is_safe"] is False
    assert risky["warnings"]


def test_scanner_service_persists_classification_and_safety() -> None:
    class FakeRepository:
        values = None

        async def create(self, **values):
            self.values = values
            return values

    repository = FakeRepository()
    service = QrScannerService(repository, SmartClassifier(), SafeScanService())

    result = asyncio.run(service.analyze("user-id", "https://example.com", "upload"))

    assert result["content_type"] == "website"
    assert result["security"]["is_safe"] is True
    assert len(result["content_hash"]) == 64
