import asyncio
from datetime import datetime, timezone
from pymongo.asynchronous.database import AsyncDatabase


class DashboardRepository:
    def __init__(self, database: AsyncDatabase) -> None: self._db = database

    async def record_download(self, user_id: str, resource_type: str, resource_id: str, filename: str, file_format: str) -> None:
        await self._db.download_events.insert_one({"user_id": user_id, "resource_type": resource_type, "resource_id": resource_id,
            "filename": filename, "file_format": file_format, "downloaded_at": datetime.now(timezone.utc)})

    async def summary(self, user_id: str) -> dict:
        qr_count, favourites, scanner_count, shares, bulk, exports = await asyncio.gather(
            self._db.qr_generations.count_documents({"user_id": user_id}), self._db.qr_generations.count_documents({"user_id": user_id, "is_favorite": True}),
            self._db.qr_scans.count_documents({"user_id": user_id}), self._db.share_files.count_documents({"user_id": user_id}),
            self._db.bulk_jobs.count_documents({"user_id": user_id}), self._db.download_events.count_documents({"user_id": user_id}),
        )
        qr_totals = await self._db.qr_generations.aggregate([{"$match": {"user_id": user_id}}, {"$group": {"_id": None, "scans": {"$sum": {"$ifNull": ["$scan_count", 0]}}}}]).to_list(length=1)
        share_totals = await self._db.share_files.aggregate([{"$match": {"user_id": user_id}}, {"$group": {"_id": None, "downloads": {"$sum": {"$ifNull": ["$download_count", 0]}}}}]).to_list(length=1)
        recent_downloads = await self._db.download_events.find({"user_id": user_id}).sort("downloaded_at", -1).limit(20).to_list(length=20)
        activity_sources = await asyncio.gather(
            self._db.qr_generations.find({"user_id": user_id}, {"label": 1, "payload_preview": 1, "payload_type": 1, "created_at": 1}).sort("created_at", -1).limit(5).to_list(length=5),
            self._db.qr_scans.find({"user_id": user_id}, {"content_type": 1, "source": 1, "created_at": 1}).sort("created_at", -1).limit(5).to_list(length=5),
            self._db.share_files.find({"user_id": user_id}, {"filename": 1, "access_mode": 1, "created_at": 1}).sort("created_at", -1).limit(5).to_list(length=5),
            self._db.bulk_jobs.find({"user_id": user_id}, {"filename": 1, "status": 1, "created_at": 1}).sort("created_at", -1).limit(5).to_list(length=5),
        )
        activities = []
        for item in activity_sources[0]: activities.append({"id": str(item["_id"]), "type": "qr_created", "title": item.get("label") or item.get("payload_preview", "QR code"), "detail": f"{item.get('payload_type', 'QR')} code created", "occurred_at": item["created_at"]})
        for item in activity_sources[1]: activities.append({"id": str(item["_id"]), "type": "qr_scanned", "title": f"{item.get('content_type', 'QR')} content scanned", "detail": f"Source: {item.get('source', 'upload')}", "occurred_at": item["created_at"]})
        for item in activity_sources[2]: activities.append({"id": str(item["_id"]), "type": "file_shared", "title": item.get("filename", "Shared file"), "detail": f"{item.get('access_mode', 'public')} ShareVault access", "occurred_at": item["created_at"]})
        for item in activity_sources[3]: activities.append({"id": str(item["_id"]), "type": "bulk_job", "title": item.get("filename", "Bulk job"), "detail": f"BulkForge {item.get('status', 'queued')}", "occurred_at": item["created_at"]})
        activities.sort(key=lambda item: item["occurred_at"], reverse=True)
        return {"qr_codes": qr_count, "favourite_qr_codes": favourites, "total_redirect_scans": (qr_totals or [{}])[0].get("scans", 0),
            "scanner_history": scanner_count, "shared_files": shares, "shared_file_downloads": (share_totals or [{}])[0].get("downloads", 0),
            "bulk_jobs": bulk, "exports": exports, "recent_activity": activities[:12],
            "download_history": [{"id": str(item["_id"]), "resource_type": item["resource_type"], "resource_id": item["resource_id"],
                "filename": item["filename"], "file_format": item["file_format"], "downloaded_at": item["downloaded_at"]} for item in recent_downloads]}
