import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.core.exceptions import ApplicationError, NotFoundError
from app.infrastructure.bulk.parser import BulkImportParser
from app.infrastructure.bulk.zip_storage import BulkZipStorage
from app.models.bulk_job import BulkJob
from app.repositories.bulk_job_repository import BulkJobRepository
from app.services.qr.generator_service import QrGeneratorService


logger = logging.getLogger(__name__)


class BulkForgeService:
    def __init__(self, repository: BulkJobRepository, generator: QrGeneratorService, parser: BulkImportParser, zip_storage: BulkZipStorage) -> None:
        self._repository = repository
        self._generator = generator
        self._parser = parser
        self._zip_storage = zip_storage

    async def create_job(self, user_id: str, filename: str, content: bytes, formats: list[str]):
        requests, errors, total = await asyncio.to_thread(self._parser.parse, filename, content)
        job = await self._repository.create(user_id, filename, total, formats)
        return job, requests, errors

    async def process(self, job: BulkJob, requests: list[tuple[int, object]], validation_errors: list[dict]) -> None:
        errors = validation_errors[:20]
        processed = len(validation_errors)
        succeeded = 0
        failed = len(validation_errors)
        entries: list[tuple[Path, str]] = []
        await self._repository.update(job.id, {"status": "processing", "processed_rows": processed, "failed_rows": failed, "errors": errors})
        for row_number, request in requests:
            try:
                generation = await self._generator.generate(job.user_id, request)
                for file_format in job.formats:
                    path, _ = await self._generator.resolve_download(generation.id, job.user_id, file_format)
                    label = generation.label or f"row-{row_number}"
                    entries.append((path, f"{row_number:04d}-{label}-{generation.id}.{file_format}"))
                succeeded += 1
            except Exception as exc:
                failed += 1
                message = exc.message if isinstance(exc, ApplicationError) else "QR generation failed"
                if len(errors) < 20: errors.append({"row": row_number, "message": message})
                logger.exception("BulkForge row failed", extra={"job_id": job.id, "row": row_number})
            processed += 1
            await self._repository.update(job.id, {"processed_rows": processed, "succeeded_rows": succeeded, "failed_rows": failed, "errors": errors})
        zip_path = None
        if entries:
            try: zip_path = await asyncio.to_thread(self._zip_storage.create, job.id, entries)
            except Exception:
                logger.exception("BulkForge ZIP creation failed", extra={"job_id": job.id})
                errors.append({"row": 0, "message": "ZIP archive creation failed"})
        status = "completed" if failed == 0 and zip_path else "partial" if succeeded > 0 and zip_path else "failed"
        await self._repository.update(job.id, {"status": status, "processed_rows": job.total_rows, "succeeded_rows": succeeded,
                                               "failed_rows": failed, "errors": errors[:20], "zip_path": zip_path,
                                               "completed_at": datetime.now(timezone.utc)})

    async def get_owned(self, job_id: str, user_id: str) -> BulkJob:
        job = await self._repository.find_owned(job_id, user_id)
        if job is None: raise NotFoundError("BulkForge job was not found")
        return job

    async def list_owned(self, user_id: str, limit: int, offset: int = 0) -> tuple[list[BulkJob], int]:
        return await self._repository.list_owned(user_id, limit, offset)

    async def resolve_download(self, job_id: str, user_id: str) -> tuple[Path, str]:
        job = await self.get_owned(job_id, user_id)
        if job.status not in {"completed", "partial"} or not job.zip_path:
            raise ApplicationError("This bulk archive is not ready")
        try: path = await asyncio.to_thread(self._zip_storage.resolve, job.zip_path)
        except FileNotFoundError as exc: raise NotFoundError("Bulk archive was not found") from exc
        return path, f"intelliqr-bulk-{job.id}.zip"

    async def delete_owned(self, job_id: str, user_id: str) -> None:
        current = await self.get_owned(job_id, user_id)
        if current.status in {"queued", "processing"}: raise ApplicationError("Active bulk jobs cannot be deleted")
        job = await self._repository.delete_owned(job_id, user_id)
        if job is None: raise NotFoundError("BulkForge job was not found")
        await asyncio.to_thread(self._zip_storage.delete, job.zip_path)
