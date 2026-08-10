from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.models.session import Session


class SessionRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.sessions

    async def create(
        self,
        user_id: str,
        token_hash: str,
        refresh_jti: str,
        family_id: str,
        expires_at: datetime,
    ) -> Session:
        now = datetime.now(timezone.utc)
        document = {
            "user_id": user_id,
            "refresh_token_hash": token_hash,
            "refresh_jti": refresh_jti,
            "token_family_id": family_id,
            "created_at": now,
            "expires_at": expires_at,
            "revoked_at": None,
            "replaced_by_session_id": None,
        }
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def find_by_jti(self, refresh_jti: str) -> Session | None:
        document = await self._collection.find_one({"refresh_jti": refresh_jti})
        return self._to_domain(document) if document else None

    async def consume(self, refresh_jti: str, token_hash: str) -> Session | None:
        document = await self._collection.find_one_and_update(
            {
                "refresh_jti": refresh_jti,
                "refresh_token_hash": token_hash,
                "revoked_at": None,
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            },
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    async def mark_replacement(self, session_id: str, replacement_id: str) -> None:
        from bson import ObjectId

        await self._collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"replaced_by_session_id": replacement_id}},
        )

    async def revoke(self, session_id: str, replacement_id: str | None = None) -> None:
        from bson import ObjectId

        await self._collection.update_one(
            {"_id": ObjectId(session_id), "revoked_at": None},
            {
                "$set": {
                    "revoked_at": datetime.now(timezone.utc),
                    "replaced_by_session_id": replacement_id,
                }
            },
        )

    async def revoke_by_jti(self, refresh_jti: str) -> None:
        await self._collection.update_one(
            {"refresh_jti": refresh_jti, "revoked_at": None},
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
        )

    async def revoke_family(self, family_id: str) -> None:
        await self._collection.update_many(
            {"token_family_id": family_id, "revoked_at": None},
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
        )

    async def revoke_user(self, user_id: str) -> None:
        await self._collection.update_many(
            {"user_id": user_id, "revoked_at": None},
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
        )

    @staticmethod
    def _to_domain(document: dict) -> Session:
        return Session(
            id=str(document["_id"]),
            user_id=document["user_id"],
            refresh_token_hash=document["refresh_token_hash"],
            refresh_jti=document["refresh_jti"],
            token_family_id=document["token_family_id"],
            created_at=document["created_at"],
            expires_at=document["expires_at"],
            revoked_at=document.get("revoked_at"),
            replaced_by_session_id=document.get("replaced_by_session_id"),
        )
