from datetime import datetime, timezone

from pymongo.asynchronous.database import AsyncDatabase

from app.models.qr_generation import QrGeneration
from app.services.analytics.scan_context import ScanContext


class AnalyticsRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._events = database.qr_scan_events

    async def record(self, generation: QrGeneration, context: ScanContext) -> None:
        await self._events.insert_one({
            "generation_id": generation.id,
            "user_id": generation.user_id,
            "visitor_hash": context.visitor_hash,
            "device_type": context.device_type,
            "browser": context.browser,
            "operating_system": context.operating_system,
            "country": context.country,
            "city": context.city,
            "scanned_at": datetime.now(timezone.utc),
        })

    async def overview(
        self,
        user_id: str,
        starts_at: datetime,
        ends_at: datetime,
        previous_starts_at: datetime,
        generation_id: str | None,
        date_format: str,
    ) -> dict:
        ownership_match: dict = {"user_id": user_id}
        if generation_id:
            ownership_match["generation_id"] = generation_id
        current_match = {**ownership_match, "scanned_at": {"$gte": starts_at, "$lt": ends_at}}
        previous_match = {**ownership_match, "scanned_at": {"$gte": previous_starts_at, "$lt": starts_at}}

        def breakdown(field: str) -> list[dict]:
            return [
                {"$group": {"_id": f"${field}", "value": {"$sum": 1}}},
                {"$sort": {"value": -1, "_id": 1}},
                {"$limit": 8},
            ]

        pipeline = [
            {"$match": {**ownership_match, "scanned_at": {"$gte": previous_starts_at, "$lt": ends_at}}},
            {"$facet": {
                "summary": [
                    {"$match": {"scanned_at": current_match["scanned_at"]}},
                    {"$group": {"_id": None, "total": {"$sum": 1}, "visitors": {"$addToSet": "$visitor_hash"}}},
                ],
                "previous": [{"$match": {"scanned_at": previous_match["scanned_at"]}}, {"$count": "total"}],
                "series": [
                    {"$match": {"scanned_at": current_match["scanned_at"]}},
                    {"$group": {
                        "_id": {"$dateToString": {"format": date_format, "date": "$scanned_at", "timezone": "UTC"}},
                        "scans": {"$sum": 1},
                        "visitors": {"$addToSet": "$visitor_hash"},
                    }},
                    {"$sort": {"_id": 1}},
                ],
                "devices": [{"$match": {"scanned_at": current_match["scanned_at"]}}, *breakdown("device_type")],
                "browsers": [{"$match": {"scanned_at": current_match["scanned_at"]}}, *breakdown("browser")],
                "operating_systems": [{"$match": {"scanned_at": current_match["scanned_at"]}}, *breakdown("operating_system")],
                "countries": [{"$match": {"scanned_at": current_match["scanned_at"]}}, *breakdown("country")],
                "cities": [{"$match": {"scanned_at": current_match["scanned_at"]}}, *breakdown("city")],
                "top_qr_codes": [
                    {"$match": {"scanned_at": current_match["scanned_at"]}},
                    {"$group": {"_id": "$generation_id", "scans": {"$sum": 1}, "visitors": {"$addToSet": "$visitor_hash"}}},
                    {"$sort": {"scans": -1}},
                    {"$limit": 5},
                    {"$addFields": {"generation_object_id": {"$convert": {"input": "$_id", "to": "objectId", "onError": None, "onNull": None}}}},
                    {"$lookup": {"from": "qr_generations", "localField": "generation_object_id", "foreignField": "_id", "as": "generation"}},
                    {"$set": {"label": {"$ifNull": [{"$first": "$generation.label"}, {"$first": "$generation.payload_preview"}]}}},
                ],
                "recent_scans": [
                    {"$match": {"scanned_at": current_match["scanned_at"]}},
                    {"$sort": {"scanned_at": -1}},
                    {"$limit": 10},
                    {"$addFields": {"generation_object_id": {"$convert": {"input": "$generation_id", "to": "objectId", "onError": None, "onNull": None}}}},
                    {"$lookup": {"from": "qr_generations", "localField": "generation_object_id", "foreignField": "_id", "as": "generation"}},
                    {"$set": {"qr_label": {"$ifNull": [{"$first": "$generation.label"}, {"$first": "$generation.payload_preview"}]}}},
                ],
            }},
        ]
        cursor = await self._events.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        return results[0] if results else {}
