from datetime import datetime, timezone

from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import ConflictError
from app.models.user import User


class UserRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.users

    async def create(self, name: str, email: str, password_hash: str) -> User:
        now = datetime.now(timezone.utc)
        document = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": "user",
            "status": "active",
            "token_version": 1,
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
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

    @staticmethod
    def _to_domain(document: dict) -> User:
        return User(
            id=str(document["_id"]),
            name=document.get("name", document.get("username", "IntelliQR User")),
            email=document["email"],
            password_hash=document["password_hash"],
            role=document["role"],
            status=document["status"],
            token_version=document["token_version"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            last_login_at=document.get("last_login_at"),
        )
