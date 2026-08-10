import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.models.qr_generation import QrGeneration, QrFileFormat, QrPayloadType


class QrGenerationRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.qr_generations

    async def create(
        self,
        user_id: str,
        payload_type: QrPayloadType,
        label: str | None,
        payload_preview: str,
        payload_hash: str,
        payload_details: dict,
        files: dict[QrFileFormat, str],
        slug: str,
        dynamic_url: str | None,
        destination_url: str | None,
        encrypted_destination: str | None,
        access_mode: str,
        access_password_hash: str | None,
        allowed_emails: list[str],
        expires_at: datetime | None,
        max_scans: int | None,
        design: dict,
        logo_file: str | None,
    ) -> QrGeneration:
        now = datetime.now(timezone.utc)
        document = {
            "user_id": user_id,
            "payload_type": payload_type,
            "label": label,
            "payload_preview": payload_preview,
            "payload_hash": payload_hash,
            "payload_details": payload_details,
            "files": files,
            "slug": slug,
            "dynamic_url": dynamic_url,
            "destination_url": destination_url,
            "encrypted_destination": encrypted_destination,
            "access_mode": access_mode,
            "access_password_hash": access_password_hash,
            "allowed_emails": allowed_emails,
            "is_active": True,
            "is_favorite": False,
            "expires_at": expires_at,
            "max_scans": max_scans,
            "scan_count": 0,
            "design": design,
            "logo_file": logo_file,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def find_owned(self, generation_id: str, user_id: str) -> QrGeneration | None:
        object_id = self._object_id(generation_id)
        if object_id is None:
            return None
        document = await self._collection.find_one({"_id": object_id, "user_id": user_id})
        return self._to_domain(document) if document else None

    async def find_by_slug(self, slug: str) -> QrGeneration | None:
        document = await self._collection.find_one({"slug": slug, "payload_type": "url"})
        return self._to_domain(document) if document else None

    async def list_owned(
        self,
        user_id: str,
        limit: int,
        offset: int = 0,
        search: str | None = None,
        payload_type: QrPayloadType | None = None,
        status: str | None = None,
        favorite: bool | None = None,
    ) -> tuple[list[QrGeneration], int]:
        now = datetime.now(timezone.utc)
        clauses: list[dict] = [{"user_id": user_id}]
        if search:
            pattern = re.escape(search.strip())
            clauses.append({"$or": [{"label": {"$regex": pattern, "$options": "i"}}, {"payload_preview": {"$regex": pattern, "$options": "i"}}]})
        if payload_type:
            clauses.append({"payload_type": payload_type})
        if favorite is not None:
            clauses.append({"is_favorite": favorite})
        if status == "paused":
            clauses.append({"is_active": False})
        elif status == "expired":
            clauses.extend([{"is_active": {"$ne": False}}, {"expires_at": {"$lte": now}}])
        elif status == "scan_limit_reached":
            clauses.extend([
                {"is_active": {"$ne": False}},
                {"max_scans": {"$ne": None}},
                {"$expr": {"$gte": [{"$ifNull": ["$scan_count", 0]}, "$max_scans"]}},
            ])
        elif status == "active":
            clauses.extend([
                {"is_active": {"$ne": False}},
                {"$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}]},
                {"$or": [{"max_scans": None}, {"$expr": {"$lt": [{"$ifNull": ["$scan_count", 0]}, "$max_scans"]}}]},
            ])
        query = clauses[0] if len(clauses) == 1 else {"$and": clauses}
        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [self._to_domain(document) for document in documents], total

    async def update_owned(self, generation_id: str, user_id: str, changes: dict) -> QrGeneration | None:
        object_id = self._object_id(generation_id)
        if object_id is None:
            return None
        changes["updated_at"] = datetime.now(timezone.utc)
        document = await self._collection.find_one_and_update(
            {"_id": object_id, "user_id": user_id},
            {"$set": changes},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    async def delete_owned(self, generation_id: str, user_id: str) -> QrGeneration | None:
        object_id = self._object_id(generation_id)
        if object_id is None:
            return None
        document = await self._collection.find_one_and_delete({"_id": object_id, "user_id": user_id})
        return self._to_domain(document) if document else None

    async def consume_dynamic_scan(self, slug: str) -> QrGeneration | None:
        now = datetime.now(timezone.utc)
        document = await self._collection.find_one_and_update(
            {
                "slug": slug,
                "payload_type": "url",
                "is_active": {"$ne": False},
                "$and": [
                    {"$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}]},
                    {"$or": [{"max_scans": None}, {"$expr": {"$lt": [{"$ifNull": ["$scan_count", 0]}, "$max_scans"]}}]},
                ],
            },
            {"$inc": {"scan_count": 1}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_domain(document) if document else None

    async def slug_exists(self, slug: str) -> bool:
        return await self._collection.find_one({"slug": slug}, {"_id": 1}) is not None

    @staticmethod
    def _object_id(value: str) -> ObjectId | None:
        try:
            return ObjectId(value)
        except InvalidId:
            return None

    @staticmethod
    def _to_domain(document: dict) -> QrGeneration:
        identifier = str(document["_id"])
        created_at = document["created_at"]
        return QrGeneration(
            id=identifier,
            user_id=document["user_id"],
            payload_type=document["payload_type"],
            label=document.get("label"),
            payload_preview=document["payload_preview"],
            payload_hash=document["payload_hash"],
            payload_details=document.get("payload_details", {}),
            files=document["files"],
            slug=document.get("slug", identifier),
            dynamic_url=document.get("dynamic_url"),
            destination_url=document.get("destination_url"),
            encrypted_destination=document.get("encrypted_destination"),
            access_mode=document.get("access_mode", "public"),
            access_password_hash=document.get("access_password_hash"),
            allowed_emails=document.get("allowed_emails", []),
            is_active=document.get("is_active", True),
            is_favorite=document.get("is_favorite", False),
            expires_at=document.get("expires_at"),
            max_scans=document.get("max_scans"),
            scan_count=document.get("scan_count", 0),
            design=document.get("design", {}),
            logo_file=document.get("logo_file"),
            created_at=created_at,
            updated_at=document.get("updated_at", created_at),
        )
