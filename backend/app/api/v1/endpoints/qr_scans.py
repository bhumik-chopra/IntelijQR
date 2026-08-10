import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Response, UploadFile, status

from app.api.dependencies import CurrentUser, get_notification_service, get_qr_image_decoder, get_qr_scanner_service
from app.core.exceptions import ApplicationError
from app.infrastructure.qr.decoder import QrImageDecoder
from app.models.qr_scan import QrScan
from app.schemas.qr_scan import QrScanAnalyzeRequest, QrScanListResponse, QrScanResponse
from app.services.qr.scanner_service import QrScannerService
from app.services.notification_service import NotificationService


router = APIRouter()
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


def _response(scan: QrScan) -> QrScanResponse:
    return QrScanResponse(
        id=scan.id,
        content=scan.content,
        content_type=scan.content_type,
        source=scan.source,
        metadata=scan.metadata,
        security=scan.security,
        created_at=scan.created_at,
    )


@router.post("/decode", response_model=QrScanListResponse, status_code=status.HTTP_201_CREATED)
async def decode_qr_image(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: Annotated[QrScannerService, Depends(get_qr_scanner_service)],
    decoder: Annotated[QrImageDecoder, Depends(get_qr_image_decoder)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    file: Annotated[UploadFile, File(description="PNG, JPEG, or WebP image containing QR codes")],
    source: Annotated[str, Form(pattern="^(upload|webcam)$")] = "upload",
) -> QrScanListResponse:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ApplicationError("Only PNG, JPEG, and WebP images are supported")
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ApplicationError("Scan image must be 10 MB or smaller")
    values = await asyncio.to_thread(decoder.decode, image_bytes)
    scans = [await service.analyze(current_user.id, value, source) for value in values]
    for scan in scans:
        if scan.security and not scan.security.get("is_safe", True):
            background_tasks.add_task(notifications.notify, current_user.id, "security.risky_qr_detected", "security", "critical",
                "Risky QR link detected", "SafeScan found warning signs in a decoded QR link. Review the security report before opening it.",
                "/scanner", {"scan_id": scan.id, "risk_score": scan.security.get("score", 0)})
    logger.info("QR image decoded", extra={"user_id": current_user.id, "result_count": len(scans), "source": source})
    return QrScanListResponse(
        items=[_response(scan) for scan in scans],
        total=len(scans),
        limit=len(scans),
        offset=0,
        has_more=False,
    )


@router.post("/analyze", response_model=QrScanResponse, status_code=status.HTTP_201_CREATED)
async def analyze_decoded_content(
    payload: QrScanAnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: Annotated[QrScannerService, Depends(get_qr_scanner_service)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
) -> QrScanResponse:
    scan = await service.analyze(current_user.id, payload.content, payload.source)
    if scan.security and not scan.security.get("is_safe", True):
        background_tasks.add_task(notifications.notify, current_user.id, "security.risky_qr_detected", "security", "critical",
            "Risky QR link detected", "SafeScan found warning signs in a decoded QR link. Review the security report before opening it.",
            "/scanner", {"scan_id": scan.id, "risk_score": scan.security.get("score", 0)})
    return _response(scan)


@router.get("", response_model=QrScanListResponse)
async def list_scan_history(
    current_user: CurrentUser,
    service: Annotated[QrScannerService, Depends(get_qr_scanner_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
) -> QrScanListResponse:
    scans, total = await service.list_owned(current_user.id, limit, offset)
    return QrScanListResponse(
        items=[_response(scan) for scan in scans], total=total, limit=limit, offset=offset,
        has_more=offset + len(scans) < total,
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan_history(
    scan_id: str,
    current_user: CurrentUser,
    service: Annotated[QrScannerService, Depends(get_qr_scanner_service)],
) -> Response:
    await service.delete_owned(scan_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
