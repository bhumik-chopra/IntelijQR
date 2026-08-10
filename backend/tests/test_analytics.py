import asyncio
from datetime import datetime, timezone

from app.services.analytics.analytics_service import AnalyticsService
from app.services.analytics.scan_context import ScanContextService


def test_scan_context_parses_device_browser_os_and_hashes_identity() -> None:
    service = ScanContextService("test-secret")
    user_agent = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/125.0 Safari/537.36"

    context = service.parse("127.0.0.1", user_agent)
    same_context = service.parse("127.0.0.1", user_agent)

    assert context.device_type == "mobile"
    assert context.browser == "Chrome"
    assert context.operating_system == "Android"
    assert context.country == "Local"
    assert context.visitor_hash == same_context.visitor_hash
    assert "127.0.0.1" not in context.visitor_hash


def test_scan_context_detects_bots_and_desktop_clients() -> None:
    service = ScanContextService("test-secret")

    assert service.parse("8.8.8.8", "ExampleBot/1.0 crawler").device_type == "bot"
    desktop = service.parse("8.8.8.8", "Mozilla/5.0 (Windows NT 10.0) Firefox/120.0")
    assert desktop.device_type == "desktop"
    assert desktop.browser == "Firefox"
    assert desktop.operating_system == "Windows"
    assert desktop.country == "Unknown"


def test_analytics_overview_calculates_real_metrics_and_percentages() -> None:
    now = datetime.now(timezone.utc)

    class FakeRepository:
        async def overview(self, **_values):
            return {
                "summary": [{"total": 4, "visitors": ["a", "b", "c"]}],
                "previous": [{"total": 2}],
                "series": [{"_id": now.date().isoformat(), "scans": 4, "visitors": ["a", "b", "c"]}],
                "devices": [{"_id": "mobile", "value": 3}, {"_id": "desktop", "value": 1}],
                "browsers": [], "operating_systems": [], "countries": [], "cities": [],
                "top_qr_codes": [{"_id": "qr-1", "label": "Campaign", "scans": 4, "visitors": ["a", "b", "c"]}],
                "recent_scans": [],
            }

    service = AnalyticsService(FakeRepository(), ScanContextService("test-secret"))
    overview = asyncio.run(service.overview("user-1", "7d"))

    assert overview["total_scans"] == 4
    assert overview["unique_visitors"] == 3
    assert overview["scan_change_percentage"] == 100.0
    assert overview["devices"][0]["percentage"] == 75.0
    assert overview["top_qr_codes"][0]["unique_visitors"] == 3
    assert overview["series"][-1]["scans"] == 4


def test_analytics_handles_empty_period_without_fake_data() -> None:
    class FakeRepository:
        async def overview(self, **_values):
            return {}

    service = AnalyticsService(FakeRepository(), ScanContextService("test-secret"))
    overview = asyncio.run(service.overview("user-1", "30d"))

    assert overview["total_scans"] == 0
    assert overview["unique_visitors"] == 0
    assert overview["scan_change_percentage"] is None
    assert all(point["scans"] == 0 for point in overview["series"])
