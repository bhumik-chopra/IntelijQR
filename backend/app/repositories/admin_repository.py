import asyncio
import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.models.user import User
from app.repositories.user_repository import UserRepository


class AdminRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._database = database
        self._users = UserRepository(database)

    async def overview(self) -> dict[str, int]:
        values = await asyncio.gather(
            self._database.users.count_documents({}),
            self._database.users.count_documents({"status": {"$ne": "disabled"}}),
            self._database.users.count_documents({"role": "admin", "status": {"$ne": "disabled"}}),
            self._database.qr_generations.count_documents({}),
            self._database.qr_scan_events.count_documents({}),
            self._database.qr_scans.count_documents({}),
            self._database.share_files.count_documents({}),
            self._database.share_download_events.count_documents({}),
            self._database.bulk_jobs.count_documents({}),
        )
        keys = ("users", "active_users", "active_admins", "qr_codes", "dynamic_scans", "decoded_scans",
                "shared_files", "share_downloads", "bulk_jobs")
        return dict(zip(keys, values, strict=True))

    async def list_users(
        self, limit: int, offset: int, search: str | None, role: str | None, status: str | None
    ) -> tuple[list[User], int]:
        query: dict = {}
        if search and search.strip():
            pattern = re.escape(search.strip())
            query["$or"] = [
                {"name": {"$regex": pattern, "$options": "i"}},
                {"email": {"$regex": pattern, "$options": "i"}},
            ]
        if role:
            query["role"] = role
        if status:
            query["status"] = status
        total = await self._database.users.count_documents(query)
        documents = await self._database.users.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [self._users._to_domain(document) for document in documents], total

    async def count_active_admins(self) -> int:
        return await self._database.users.count_documents({"role": "admin", "status": {"$ne": "disabled"}})

    async def find_user(self, user_id: str) -> User | None:
        return await self._users.find_by_id(user_id)

    async def update_user(self, user_id: str, changes: dict) -> User | None:
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            return None
        document = await self._database.users.find_one_and_update(
            {"_id": object_id},
            {"$set": {**changes, "updated_at": datetime.now(timezone.utc)}, "$inc": {"token_version": 1}},
            return_document=ReturnDocument.AFTER,
        )
        return self._users._to_domain(document) if document else None

    async def record_audit(self, admin_user_id: str, action: str, target_user_id: str, details: dict) -> None:
        await self._database.admin_audit_events.insert_one({
            "admin_user_id": admin_user_id,
            "action": action,
            "target_type": "user",
            "target_id": target_user_id,
            "details": details,
            "created_at": datetime.now(timezone.utc),
        })

    async def list_audit(self, limit: int = 20) -> list[dict]:
        documents = await self._database.admin_audit_events.find({}).sort("created_at", -1).limit(limit).to_list(length=limit)
        results = []
        for document in documents:
            identifier = str(document.pop("_id"))
            results.append({**document, "id": identifier})
        return results
