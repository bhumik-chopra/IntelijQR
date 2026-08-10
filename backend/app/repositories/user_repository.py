from datetime import datetime, timezone

from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import ConflictError
from app.models.user import User


class UserRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.users

    async def create(self, name: str, email: str, password_hash: str, role: str = "user", locale: str = "en") -> User:
        now = datetime.now(timezone.utc)
        document = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "status": "active",
            "token_version": 1,
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
            "locale": locale,
        }
        try:
            result = await self._collection.insert_one(document)
        except DuplicateKeyError as exc:
            raise ConflictError("An account with this email already exists") from exc
        document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def find_by_email(self, email: str) -> User | None:
        document = await self._collection.find_one({"email": email})
        return self._to_domain(document) if document else None

    async def find_by_id(self, user_id: str) -> User | None:
        from bson import ObjectId
        from bson.errors import InvalidId

        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            return None
        document = await self._collection.find_one({"_id": object_id})
        return self._to_domain(document) if document else None

    async def record_login(self, user_id: str) -> None:
        from bson import ObjectId

        now = datetime.now(timezone.utc)
        await self._collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"last_login_at": now, "updated_at": now}}
        )

    async def update_name(self, user_id: str, name: str) -> User | None:
        from bson import ObjectId
        from pymongo import ReturnDocument
        document = await self._collection.find_one_and_update(
            {"_id": ObjectId(user_id), "status": "active"},
            {"$set": {"name": name, "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    async def change_password(self, user_id: str, password_hash: str) -> User | None:
        from bson import ObjectId
        from pymongo import ReturnDocument
        document = await self._collection.find_one_and_update(
            {"_id": ObjectId(user_id), "status": "active"},
            {"$set": {"password_hash": password_hash, "updated_at": datetime.now(timezone.utc)}, "$inc": {"token_version": 1}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    async def set_role(self, user_id: str, role: str) -> User | None:
        from bson import ObjectId
        from pymongo import ReturnDocument
        document = await self._collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}, "$inc": {"token_version": 1}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    async def update_locale(self, user_id: str, locale: str) -> User | None:
        from bson import ObjectId
        from pymongo import ReturnDocument
        document = await self._collection.find_one_and_update(
            {"_id": ObjectId(user_id), "status": "active"},
            {"$set": {"locale": locale, "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    @staticmethod
    def _to_domain(document: dict) -> User:
        return User(
            id=str(document["_id"]),
            name=document.get("name", document.get("username", "IntelliQR User")),
            email=document["email"],
            password_hash=document["password_hash"],
            role=document.get("role", "user"),
            status=document.get("status", "active"),
            token_version=document.get("token_version", 1),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            last_login_at=document.get("last_login_at"),
            locale=document.get("locale", "en"),
        )
