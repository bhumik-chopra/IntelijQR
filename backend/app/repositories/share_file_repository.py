from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.models.share_file import ShareFile


class ShareFileRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.share_files

    async def create(self, **values) -> ShareFile:
        now = datetime.now(timezone.utc)
        document = {**values, "download_count": 0, "is_active": True, "created_at": now, "updated_at": now}
        result = await self._collection.insert_one(document); document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def slug_exists(self, slug: str) -> bool:
        return await self._collection.find_one({"slug": slug}, {"_id": 1}) is not None

    async def find_by_slug(self, slug: str) -> ShareFile | None:
        document = await self._collection.find_one({"slug": slug})
        return self._to_domain(document) if document else None

    async def find_owned(self, share_id: str, user_id: str) -> ShareFile | None:
        object_id = self._object_id(share_id)
        if object_id is None: return None
        document = await self._collection.find_one({"_id": object_id, "user_id": user_id})
        return self._to_domain(document) if document else None

    async def list_owned(self, user_id: str, limit: int, offset: int = 0) -> tuple[list[ShareFile], int]:
        query = {"user_id": user_id}; total = await self._collection.count_documents(query)
        documents = await self._collection.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [self._to_domain(item) for item in documents], total

    async def update_owned(self, share_id: str, user_id: str, changes: dict) -> ShareFile | None:
        object_id = self._object_id(share_id)
        if object_id is None: return None
        changes["updated_at"] = datetime.now(timezone.utc)
        document = await self._collection.find_one_and_update({"_id": object_id, "user_id": user_id}, {"$set": changes}, return_document=ReturnDocument.AFTER)
        return self._to_domain(document) if document else None

    async def consume_download(self, slug: str) -> ShareFile | None:
        now = datetime.now(timezone.utc)
        document = await self._collection.find_one_and_update({"slug": slug, "is_active": {"$ne": False}, "$and": [
            {"$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}]},
            {"$or": [{"max_downloads": None}, {"$expr": {"$lt": [{"$ifNull": ["$download_count", 0]}, "$max_downloads"]}}]},
        ]}, {"$inc": {"download_count": 1}, "$set": {"updated_at": now}}, return_document=ReturnDocument.AFTER)
        return self._to_domain(document) if document else None

    async def delete_owned(self, share_id: str, user_id: str) -> ShareFile | None:
        object_id = self._object_id(share_id)
        if object_id is None: return None
        document = await self._collection.find_one_and_delete({"_id": object_id, "user_id": user_id})
        return self._to_domain(document) if document else None

    @staticmethod
    def _object_id(value: str) -> ObjectId | None:
        try: return ObjectId(value)
        except InvalidId: return None

    @staticmethod
    def _to_domain(document: dict) -> ShareFile:
        return ShareFile(id=str(document["_id"]), user_id=document["user_id"], slug=document["slug"], filename=document["filename"],
                         media_type=document["media_type"], size=document["size"], content_hash=document["content_hash"], stored_path=document["stored_path"],
                         qr_generation_id=document["qr_generation_id"], access_mode=document.get("access_mode", "public"),
                         access_password_hash=document.get("access_password_hash"), allowed_emails=document.get("allowed_emails", []),
                         expires_at=document.get("expires_at"), max_downloads=document.get("max_downloads"), download_count=document.get("download_count", 0),
                         is_active=document.get("is_active", True), created_at=document["created_at"], updated_at=document.get("updated_at", document["created_at"]))
