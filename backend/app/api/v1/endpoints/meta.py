from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.api_meta import ApiAuthenticationInfo, ApiLimits, ApiMetaResponse


router = APIRouter()


@router.get("", response_model=ApiMetaResponse, summary="Discover the IntelliQR REST API")
async def api_metadata(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ApiMetaResponse:
    return ApiMetaResponse(
        name=settings.app_name,
        version=settings.api_version,
        status="available",
        documentation={"openapi": "/openapi.json", "swagger": "/docs", "redoc": "/redoc"},
        authentication=ApiAuthenticationInfo(
            scheme="Bearer JWT",
            header="Authorization: Bearer <access_token>",
            refresh_transport=f"HttpOnly cookie ({settings.refresh_cookie_name})",
        ),
        resources={
            "authentication": ["register", "login", "refresh", "logout", "current-user"],
            "qr": ["generate", "list", "read", "update", "delete", "download"],
            "scanning": ["decode-image", "analyze-content", "history", "delete-history"],
            "analytics": ["overview"],
            "files": ["upload", "list", "read", "update", "delete", "download-history"],
            "bulk": ["create-job", "list-jobs", "read-job", "download-zip", "delete-job"],
            "administration": ["overview", "list-users", "update-user-access", "audit-history"],
            "notifications": ["list", "unread-count", "mark-read", "preferences", "local-email"],
        },
        limits=ApiLimits(
            list_page_size_max=100,
            scan_image_bytes_max=10 * 1024 * 1024,
            bulk_file_bytes_max=5 * 1024 * 1024,
            bulk_rows_max=settings.bulk_max_rows,
            share_file_bytes_max=settings.share_max_file_bytes,
        ),
    )
