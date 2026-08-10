from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.database import AsyncDatabase

from app.models.qr_scan import QrContentType, QrScan, QrScanSource


class QrScanRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.qr_scans

    async def create(
        self,
        *,
        user_id: str,
        content: str,
        content_hash: str,
        content_type: QrContentType,
        source: QrScanSource,
        metadata: dict,
        security: dict | None,
    ) -> QrScan:
        document = {
            "user_id": user_id,
            "content": content,
            "content_hash": content_hash,
            "content_type": content_type,
            "source": source,
            "metadata": metadata,
            "security": security,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def list_owned(self, user_id: str, limit: int, offset: int = 0) -> tuple[list[QrScan], int]:
        query = {"user_id": user_id}
        total = await self._collection.count_documents(query)
        documents = await self._collection.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [self._to_domain(document) for document in documents], total

    async def delete_owned(self, scan_id: str, user_id: str) -> bool:
        try:
            object_id = ObjectId(scan_id)
        except InvalidId:
            return False
        result = await self._collection.delete_one({"_id": object_id, "user_id": user_id})
        return result.deleted_count == 1

    @staticmethod
    def _to_domain(document: dict) -> QrScan:
        return QrScan(
            id=str(document["_id"]),
            user_id=document["user_id"],
            content=document["content"],
            content_hash=document["content_hash"],
            content_type=document["content_type"],
            source=document["source"],
            metadata=document.get("metadata", {}),
            security=document.get("security"),
            created_at=document["created_at"],
        )
