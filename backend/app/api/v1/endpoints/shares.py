from datetime import datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Request, Response, UploadFile, status

from app.api.dependencies import CurrentUser, OptionalCurrentUser, get_notification_service, get_share_vault_service
from app.core.config import Settings, get_settings
from app.models.share_file import ShareFile
from app.schemas.share import (ShareAccessPolicyResponse, ShareDownloadListResponse, ShareFileListResponse,
    ShareFileResponse, ShareGrantRequest, ShareGrantResponse, ShareUpdateRequest)
from app.services.share.share_service import ShareVaultService
from app.services.notification_service import NotificationService


router = APIRouter()


def _response(share: ShareFile, frontend_base_url: str) -> ShareFileResponse:
    return ShareFileResponse(id=share.id, slug=share.slug, filename=share.filename, media_type=share.media_type, size=share.size,
        qr_generation_id=share.qr_generation_id, access_mode=share.access_mode, allowed_emails=share.allowed_emails,
        expires_at=share.expires_at, max_downloads=share.max_downloads, download_count=share.download_count,
        is_active=share.is_active, status=share.status, share_url=f"{frontend_base_url.rstrip('/')}/share/{share.slug}",
        qr_downloads={fmt: f"/api/v1/qr/generations/{share.qr_generation_id}/files/{fmt}" for fmt in ("png", "svg", "pdf")},
        created_at=share.created_at, updated_at=share.updated_at)


@router.post("", response_model=ShareFileResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    current_user: CurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)],
    settings: Annotated[Settings, Depends(get_settings)], file: Annotated[UploadFile, File()],
    access_mode: Annotated[str, Form(pattern="^(public|password|authenticated|private)$")] = "public",
    access_password: Annotated[str | None, Form(max_length=72)] = None,
    allowed_emails: Annotated[str, Form(max_length=2000)] = "",
    expires_at: Annotated[datetime | None, Form()] = None,
    max_downloads: Annotated[int | None, Form(ge=1, le=1_000_000)] = None,
) -> ShareFileResponse:
    content = await file.read(settings.share_max_file_bytes + 1); await file.close()
    share = await service.create(current_user.id, file.filename or "shared-file", file.content_type or "application/octet-stream", content,
                                 access_mode, access_password, allowed_emails, expires_at, max_downloads)
    return _response(share, settings.frontend_base_url)


@router.get("", response_model=ShareFileListResponse)
async def list_shares(current_user: CurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)],
                      settings: Annotated[Settings, Depends(get_settings)], limit: Annotated[int, Query(ge=1, le=100)] = 50,
                      offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0) -> ShareFileListResponse:
    shares, total = await service.list_owned(current_user.id, limit, offset)
    return ShareFileListResponse(items=[_response(item, settings.frontend_base_url) for item in shares], total=total,
                                 limit=limit, offset=offset, has_more=offset + len(shares) < total)


@router.get("/{share_id}", response_model=ShareFileResponse)
async def get_share(share_id: str, current_user: CurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)], settings: Annotated[Settings, Depends(get_settings)]) -> ShareFileResponse:
    return _response(await service.get_owned(share_id, current_user.id), settings.frontend_base_url)


@router.patch("/{share_id}", response_model=ShareFileResponse)
async def update_share(share_id: str, payload: ShareUpdateRequest, current_user: CurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)], settings: Annotated[Settings, Depends(get_settings)]) -> ShareFileResponse:
    return _response(await service.update_owned(share_id, current_user.id, payload), settings.frontend_base_url)


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share(share_id: str, current_user: CurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)]) -> Response:
    await service.delete_owned(share_id, current_user.id); return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{share_id}/downloads", response_model=ShareDownloadListResponse)
async def share_download_history(share_id: str, current_user: CurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)],
                                 limit: Annotated[int, Query(ge=1, le=100)] = 50,
                                 offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0) -> ShareDownloadListResponse:
    items, total = await service.list_downloads(share_id, current_user.id, limit, offset)
    return ShareDownloadListResponse(items=items, total=total, limit=limit, offset=offset,
                                     has_more=offset + len(items) < total)


@router.get("/access/{slug}/policy", response_model=ShareAccessPolicyResponse)
async def share_access_policy(slug: str, service: Annotated[ShareVaultService, Depends(get_share_vault_service)]) -> ShareAccessPolicyResponse:
    share = await service.policy(slug)
    return ShareAccessPolicyResponse(slug=slug, filename=share.filename, media_type=share.media_type, size=share.size,
        access_mode=share.access_mode, requires_authentication=share.access_mode in {"authenticated", "private"}, status=share.status)


@router.post("/access/{slug}/grant", response_model=ShareGrantResponse)
async def grant_share_access(slug: str, payload: ShareGrantRequest, current_user: OptionalCurrentUser, service: Annotated[ShareVaultService, Depends(get_share_vault_service)]) -> ShareGrantResponse:
    url, expires = await service.grant(slug, payload.password, current_user)
    return ShareGrantResponse(download_url=url, expires_at=expires)


@router.get("/access/{slug}/download")
async def download_shared_file(slug: str, grant: Annotated[str, Query(max_length=2048)], request: Request,
                               background_tasks: BackgroundTasks, current_user: OptionalCurrentUser,
                               service: Annotated[ShareVaultService, Depends(get_share_vault_service)],
                               notifications: Annotated[NotificationService, Depends(get_notification_service)]) -> Response:
    content, share = await service.download(slug, grant, current_user, request.client.host if request.client else "unknown", request.headers.get("user-agent", ""))
    reached_limit = share.max_downloads is not None and share.download_count >= share.max_downloads
    background_tasks.add_task(notifications.notify, share.user_id,
        "share.download_limit_reached" if reached_limit else "share.downloaded", "share", "warning" if reached_limit else "info",
        "Share download limit reached" if reached_limit else "Shared file downloaded",
        "A shared file reached its download limit and is now unavailable." if reached_limit else "A recipient downloaded one of your shared files.",
        "/share-vault", {"share_id": share.id, "download_count": share.download_count})
    disposition = f"attachment; filename*=UTF-8''{quote(share.filename)}"
    return Response(content=content, media_type=share.media_type, background=background_tasks,
        headers={"Content-Disposition": disposition, "Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"})
