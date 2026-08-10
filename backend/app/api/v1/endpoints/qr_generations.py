from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUser, get_dashboard_service, get_qr_generator_service
from app.services.dashboard_service import DashboardService
from app.models.qr_generation import QrGeneration
from app.schemas.qr_generation import (
    QrGenerationListResponse,
    QrGenerationRequest,
    QrGenerationResponse,
    QrGenerationUpdateRequest,
    QrDesignRequest,
)
from app.services.qr.generator_service import QrGeneratorService


router = APIRouter()
MEDIA_TYPES = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}


def _response(generation: QrGeneration) -> QrGenerationResponse:
    downloads = {
        file_format: f"/api/v1/qr/generations/{generation.id}/files/{file_format}"
        for file_format in generation.files
    }
    return QrGenerationResponse(
        id=generation.id,
        type=generation.payload_type,
        label=generation.label,
        payload_preview=generation.payload_preview,
        slug=generation.slug,
        dynamic_url=generation.dynamic_url,
        destination_url=generation.destination_url,
        access_mode=generation.access_mode,
        allowed_emails=generation.allowed_emails,
        is_encrypted=generation.encrypted_destination is not None,
        status=generation.status,
        is_active=generation.is_active,
        is_favorite=generation.is_favorite,
        expires_at=generation.expires_at,
        max_scans=generation.max_scans,
        scan_count=generation.scan_count,
        design=QrDesignRequest(**generation.design),
        has_logo=generation.logo_file is not None,
        downloads=downloads,
        created_at=generation.created_at,
        updated_at=generation.updated_at,
    )


@router.post("", response_model=QrGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_qr(
    payload: QrGenerationRequest,
    current_user: CurrentUser,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
) -> QrGenerationResponse:
    return _response(await service.generate(current_user.id, payload))


@router.get("", response_model=QrGenerationListResponse)
async def list_qr_generations(
    current_user: CurrentUser,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
    search: Annotated[str | None, Query(max_length=100)] = None,
    type: Annotated[Literal["url", "text", "email", "phone", "wifi", "contact", "location"] | None, Query()] = None,
    status_filter: Annotated[Literal["active", "paused", "expired", "scan_limit_reached"] | None, Query(alias="status")] = None,
    favorite: Annotated[bool | None, Query()] = None,
) -> QrGenerationListResponse:
    items, total = await service.list_owned(
        current_user.id, limit, offset, search, type, status_filter, favorite
    )
    return QrGenerationListResponse(
        items=[_response(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(items) < total,
    )


@router.get("/{generation_id}", response_model=QrGenerationResponse)
async def get_qr_generation(
    generation_id: str,
    current_user: CurrentUser,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
) -> QrGenerationResponse:
    return _response(await service.get_owned(generation_id, current_user.id))


@router.patch("/{generation_id}", response_model=QrGenerationResponse)
async def update_qr_generation(
    generation_id: str,
    payload: QrGenerationUpdateRequest,
    current_user: CurrentUser,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
) -> QrGenerationResponse:
    return _response(await service.update_owned(generation_id, current_user.id, payload))


@router.delete("/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qr_generation(
    generation_id: str,
    current_user: CurrentUser,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
) -> Response:
    await service.delete_owned(generation_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{generation_id}/files/{file_format}", response_class=FileResponse)
async def download_qr_generation(
    generation_id: str,
    file_format: Literal["png", "svg", "pdf"],
    current_user: CurrentUser,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
    background_tasks: BackgroundTasks,
    dashboard: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> FileResponse:
    path, filename = await service.resolve_download(generation_id, current_user.id, file_format)
    background_tasks.add_task(dashboard.record_download, current_user.id, "qr", generation_id, filename, file_format)
    return FileResponse(path, media_type=MEDIA_TYPES[file_format], filename=filename, background=background_tasks)
