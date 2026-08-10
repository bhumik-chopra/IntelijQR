from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.models.bulk_job import BulkJob


class BulkJobRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.bulk_jobs

    async def create(self, user_id: str, filename: str, total_rows: int, formats: list[str]) -> BulkJob:
        now = datetime.now(timezone.utc)
        document = {"user_id": user_id, "filename": filename, "status": "queued", "total_rows": total_rows,
                    "processed_rows": 0, "succeeded_rows": 0, "failed_rows": 0, "formats": formats,
                    "errors": [], "zip_path": None, "created_at": now, "updated_at": now, "completed_at": None}
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_domain(document)

    async def update(self, job_id: str, changes: dict) -> BulkJob | None:
        object_id = self._object_id(job_id)
        if object_id is None: return None
        changes["updated_at"] = datetime.now(timezone.utc)
        document = await self._collection.find_one_and_update({"_id": object_id}, {"$set": changes}, return_document=ReturnDocument.AFTER)
        return self._to_domain(document) if document else None

    async def find_owned(self, job_id: str, user_id: str) -> BulkJob | None:
        object_id = self._object_id(job_id)
        if object_id is None: return None
        document = await self._collection.find_one({"_id": object_id, "user_id": user_id})
        return self._to_domain(document) if document else None

    async def list_owned(self, user_id: str, limit: int, offset: int = 0) -> tuple[list[BulkJob], int]:
        query = {"user_id": user_id}
        total = await self._collection.count_documents(query)
        documents = await self._collection.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [self._to_domain(item) for item in documents], total

    async def delete_owned(self, job_id: str, user_id: str) -> BulkJob | None:
        object_id = self._object_id(job_id)
        if object_id is None: return None
        document = await self._collection.find_one_and_delete({"_id": object_id, "user_id": user_id})
        return self._to_domain(document) if document else None

    @staticmethod
    def _object_id(value: str) -> ObjectId | None:
        try: return ObjectId(value)
        except InvalidId: return None

    @staticmethod
    def _to_domain(document: dict) -> BulkJob:
        return BulkJob(id=str(document["_id"]), user_id=document["user_id"], filename=document["filename"],
                       status=document["status"], total_rows=document["total_rows"], processed_rows=document.get("processed_rows", 0),
                       succeeded_rows=document.get("succeeded_rows", 0), failed_rows=document.get("failed_rows", 0),
                       formats=document.get("formats", ["png"]), errors=document.get("errors", []), zip_path=document.get("zip_path"),
                       created_at=document["created_at"], updated_at=document.get("updated_at", document["created_at"]),
                       completed_at=document.get("completed_at"))
