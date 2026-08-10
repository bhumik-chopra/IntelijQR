from datetime import datetime, timezone
from pymongo.asynchronous.database import AsyncDatabase
from app.models.share_file import ShareFile
from app.services.analytics.scan_context import ScanContext


class ShareDownloadRepository:
    def __init__(self, database: AsyncDatabase) -> None: self._collection = database.share_download_events
    async def record(self, share: ShareFile, context: ScanContext, accessor_user_id: str | None) -> None:
        await self._collection.insert_one({"share_id": share.id, "owner_user_id": share.user_id, "accessor_user_id": accessor_user_id,
            "visitor_hash": context.visitor_hash, "device_type": context.device_type, "browser": context.browser,
            "operating_system": context.operating_system, "country": context.country, "city": context.city, "downloaded_at": datetime.now(timezone.utc)})

    async def list_owned(self, share_id: str, owner_user_id: str, limit: int, offset: int = 0) -> tuple[list[dict], int]:
        query = {"share_id": share_id, "owner_user_id": owner_user_id}
        total = await self._collection.count_documents(query)
        documents = await self._collection.find(query, {"visitor_hash": 0, "accessor_user_id": 0, "owner_user_id": 0}).sort("downloaded_at", -1).skip(offset).limit(limit).to_list(length=limit)
        for document in documents: document["id"] = str(document.pop("_id"))
        return documents, total

    async def delete_for_share(self, share_id: str, owner_user_id: str) -> None:
        await self._collection.delete_many({"share_id": share_id, "owner_user_id": owner_user_id})
