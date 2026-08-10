from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.database import AsyncDatabase

from app.models.notification import Notification


DEFAULT_PREFERENCES = {
    "in_app_enabled": True,
    "email_enabled": False,
    "security_alerts": True,
    "qr_activity": True,
    "share_activity": True,
    "bulk_activity": True,
}


class NotificationRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._database = database
        self._collection = database.notifications

    async def create(self, **values) -> Notification:
        document = {**values, "is_read": False, "created_at": datetime.now(timezone.utc)}
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def list_owned(self, user_id: str, limit: int, offset: int, unread_only: bool) -> tuple[list[Notification], int]:
        query: dict = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        total = await self._collection.count_documents(query)
        documents = await self._collection.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [self._to_domain(item) for item in documents], total

    async def unread_count(self, user_id: str) -> int:
        return await self._collection.count_documents({"user_id": user_id, "is_read": False})

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        object_id = self._object_id(notification_id)
        if object_id is None:
            return False
        result = await self._collection.update_one({"_id": object_id, "user_id": user_id}, {"$set": {"is_read": True}})
        return result.matched_count == 1

    async def mark_all_read(self, user_id: str) -> None:
        await self._collection.update_many({"user_id": user_id, "is_read": False}, {"$set": {"is_read": True}})

    async def delete_owned(self, notification_id: str, user_id: str) -> bool:
        object_id = self._object_id(notification_id)
        if object_id is None:
            return False
        result = await self._collection.delete_one({"_id": object_id, "user_id": user_id})
        return result.deleted_count == 1

    async def preferences(self, user_id: str) -> dict:
        document = await self._database.users.find_one({"_id": ObjectId(user_id)}, {"notification_preferences": 1})
        return {**DEFAULT_PREFERENCES, **((document or {}).get("notification_preferences") or {})}

    async def update_preferences(self, user_id: str, preferences: dict) -> dict:
        await self._database.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"notification_preferences": preferences, "updated_at": datetime.now(timezone.utc)}})
        return {**DEFAULT_PREFERENCES, **preferences}

    @staticmethod
    def _object_id(value: str) -> ObjectId | None:
        try:
            return ObjectId(value)
        except InvalidId:
            return None

    @staticmethod
    def _to_domain(document: dict) -> Notification:
        return Notification(id=str(document["_id"]), user_id=document["user_id"], event_type=document["event_type"],
            category=document["category"], severity=document["severity"], title=document["title"], message=document["message"],
            action_url=document.get("action_url"), metadata=document.get("metadata", {}), is_read=document.get("is_read", False),
            created_at=document["created_at"])
