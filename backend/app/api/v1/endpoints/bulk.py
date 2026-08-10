from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUser, get_bulk_forge_service, get_dashboard_service, get_notification_service
from app.services.dashboard_service import DashboardService
from app.core.exceptions import ApplicationError
from app.models.bulk_job import BulkJob
from app.schemas.bulk import BulkJobListResponse, BulkJobResponse
from app.services.bulk.bulk_service import BulkForgeService
from app.services.notification_service import NotificationService


router = APIRouter()
MAX_FILE_BYTES = 5 * 1024 * 1024


async def _process_job(service: BulkForgeService, notifications: NotificationService, job: BulkJob, requests, errors) -> None:
    await service.process(job, requests, errors)
    completed = await service.get_owned(job.id, job.user_id)
    severity = "success" if completed.status == "completed" else "warning" if completed.status == "partial" else "critical"
    await notifications.notify(job.user_id, f"bulk.{completed.status}", "bulk", severity,
        "BulkForge job completed" if completed.status in {"completed", "partial"} else "BulkForge job failed",
        f"{completed.succeeded_rows} QR codes succeeded and {completed.failed_rows} rows failed.",
        "/bulk", {"job_id": job.id, "status": completed.status})


def _response(job: BulkJob) -> BulkJobResponse:
    progress = round(job.processed_rows / job.total_rows * 100, 1) if job.total_rows else 0
    return BulkJobResponse(id=job.id, filename=job.filename, status=job.status, total_rows=job.total_rows,
                           processed_rows=job.processed_rows, succeeded_rows=job.succeeded_rows, failed_rows=job.failed_rows,
                           progress_percentage=progress, formats=job.formats, errors=job.errors,
                           download_url=f"/api/v1/bulk/jobs/{job.id}/download" if job.zip_path else None,
                           created_at=job.created_at, updated_at=job.updated_at, completed_at=job.completed_at)


@router.post("/jobs", response_model=BulkJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_bulk_job(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: Annotated[BulkForgeService, Depends(get_bulk_forge_service)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    file: Annotated[UploadFile, File(description="UTF-8 CSV or XLSX import")],
    formats: Annotated[str, Form(pattern=r"^(png|svg|pdf)(,(png|svg|pdf))*$")] = "png",
) -> BulkJobResponse:
    content = await file.read(MAX_FILE_BYTES + 1)
    await file.close()
    if len(content) > MAX_FILE_BYTES: raise ApplicationError("Bulk import files must be 5 MB or smaller")
    selected_formats = list(dict.fromkeys(formats.split(",")))
    safe_filename = Path(file.filename or "bulk-import.csv").name[:120]
    job, requests, errors = await service.create_job(current_user.id, safe_filename, content, selected_formats)
    background_tasks.add_task(_process_job, service, notifications, job, requests, errors)
    return _response(job)


@router.get("/jobs", response_model=BulkJobListResponse)
async def list_bulk_jobs(current_user: CurrentUser, service: Annotated[BulkForgeService, Depends(get_bulk_forge_service)],
                         limit: Annotated[int, Query(ge=1, le=100)] = 50,
                         offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0) -> BulkJobListResponse:
    jobs, total = await service.list_owned(current_user.id, limit, offset)
    return BulkJobListResponse(items=[_response(job) for job in jobs], total=total, limit=limit, offset=offset,
                               has_more=offset + len(jobs) < total)


@router.get("/jobs/{job_id}", response_model=BulkJobResponse)
async def get_bulk_job(job_id: str, current_user: CurrentUser, service: Annotated[BulkForgeService, Depends(get_bulk_forge_service)]) -> BulkJobResponse:
    return _response(await service.get_owned(job_id, current_user.id))


@router.get("/jobs/{job_id}/download", response_class=FileResponse)
async def download_bulk_job(job_id: str, background_tasks: BackgroundTasks, current_user: CurrentUser,
                            service: Annotated[BulkForgeService, Depends(get_bulk_forge_service)], dashboard: Annotated[DashboardService, Depends(get_dashboard_service)]) -> FileResponse:
    path, filename = await service.resolve_download(job_id, current_user.id)
    background_tasks.add_task(dashboard.record_download, current_user.id, "bulk", job_id, filename, "zip")
    return FileResponse(path, media_type="application/zip", filename=filename, background=background_tasks)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_job(job_id: str, current_user: CurrentUser, service: Annotated[BulkForgeService, Depends(get_bulk_forge_service)]) -> Response:
    await service.delete_owned(job_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
