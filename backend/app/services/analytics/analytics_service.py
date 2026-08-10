import calendar
import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.models.qr_generation import QrGeneration
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics.scan_context import ScanContextService


logger = logging.getLogger(__name__)
AnalyticsPeriod = Literal["7d", "30d", "90d", "12m"]
PERIOD_DAYS: dict[AnalyticsPeriod, int] = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository, context_service: ScanContextService) -> None:
        self._repository = repository
        self._context_service = context_service

    async def record_scan(self, generation: QrGeneration, client_ip: str, user_agent: str) -> None:
        try:
            context = self._context_service.parse(client_ip, user_agent)
            await self._repository.record(generation, context)
        except Exception:
            logger.exception("Analytics event could not be recorded", extra={"qr_id": generation.id})

    async def overview(self, user_id: str, period: AnalyticsPeriod, generation_id: str | None = None) -> dict:
        ends_at = datetime.now(timezone.utc)
        duration = timedelta(days=PERIOD_DAYS[period])
        starts_at = ends_at - duration
        raw = await self._repository.overview(
            user_id=user_id,
            starts_at=starts_at,
            ends_at=ends_at,
            previous_starts_at=starts_at - duration,
            generation_id=generation_id,
            date_format="%Y-%m" if period == "12m" else "%Y-%m-%d",
        )
        summary = (raw.get("summary") or [{}])[0]
        total = summary.get("total", 0)
        unique = len(summary.get("visitors", []))
        previous = (raw.get("previous") or [{}])[0].get("total", 0)
        change = None if previous == 0 else round(((total - previous) / previous) * 100, 1)

        def breakdown(name: str) -> list[dict]:
            return [
                {
                    "label": item.get("_id") or "Unknown",
                    "value": item["value"],
                    "percentage": round(item["value"] / total * 100, 1) if total else 0,
                }
                for item in raw.get(name, [])
            ]

        series_lookup = {
            item["_id"]: {"date": item["_id"], "scans": item["scans"], "unique_visitors": len(item.get("visitors", []))}
            for item in raw.get("series", [])
        }
        series = self._fill_series(series_lookup, starts_at, ends_at, period == "12m")
        return {
            "period": period,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "total_scans": total,
            "unique_visitors": unique,
            "previous_total_scans": previous,
            "scan_change_percentage": change,
            "series": series,
            "devices": breakdown("devices"),
            "browsers": breakdown("browsers"),
            "operating_systems": breakdown("operating_systems"),
            "countries": breakdown("countries"),
            "cities": breakdown("cities"),
            "top_qr_codes": [
                {
                    "id": item["_id"],
                    "label": item.get("label") or "Deleted QR code",
                    "scans": item["scans"],
                    "unique_visitors": len(item.get("visitors", [])),
                }
                for item in raw.get("top_qr_codes", [])
            ],
            "recent_scans": [
                {
                    "id": str(item["_id"]),
                    "generation_id": item["generation_id"],
                    "qr_label": item.get("qr_label") or "Deleted QR code",
                    "device_type": item.get("device_type", "unknown"),
                    "browser": item.get("browser", "Other"),
                    "operating_system": item.get("operating_system", "Other"),
                    "country": item.get("country", "Unknown"),
                    "city": item.get("city", "Unknown"),
                    "scanned_at": item["scanned_at"],
                }
                for item in raw.get("recent_scans", [])
            ],
        }

    @staticmethod
    def _fill_series(points: dict[str, dict], starts_at: datetime, ends_at: datetime, monthly: bool) -> list[dict]:
        values: list[dict] = []
        if monthly:
            cursor = datetime(starts_at.year, starts_at.month, 1, tzinfo=timezone.utc)
            final = datetime(ends_at.year, ends_at.month, 1, tzinfo=timezone.utc)
            while cursor <= final:
                key = cursor.strftime("%Y-%m")
                values.append(points.get(key, {"date": key, "scans": 0, "unique_visitors": 0}))
                days = calendar.monthrange(cursor.year, cursor.month)[1]
                cursor += timedelta(days=days)
            return values
        cursor = starts_at.date()
        while cursor <= ends_at.date():
            key = cursor.isoformat()
            values.append(points.get(key, {"date": key, "scans": 0, "unique_visitors": 0}))
            cursor += timedelta(days=1)
        return values
