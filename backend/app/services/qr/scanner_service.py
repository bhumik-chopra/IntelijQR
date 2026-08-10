import hashlib

from app.core.exceptions import NotFoundError
from app.models.qr_scan import QrScan, QrScanSource
from app.repositories.qr_scan_repository import QrScanRepository
from app.services.qr.classifier import SmartClassifier
from app.services.qr.safe_scan import SafeScanService


class QrScannerService:
    def __init__(self, repository: QrScanRepository, classifier: SmartClassifier, safe_scan: SafeScanService) -> None:
        self._repository = repository
        self._classifier = classifier
        self._safe_scan = safe_scan

    async def analyze(self, user_id: str, content: str, source: QrScanSource) -> QrScan:
        normalized = content.strip()
        classification = self._classifier.classify(normalized)
        security = self._safe_scan.assess(classification.url) if classification.url else None
        return await self._repository.create(
            user_id=user_id,
            content=normalized,
            content_hash=hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            content_type=classification.content_type,
            source=source,
            metadata=classification.metadata,
            security=security,
        )

    async def list_owned(self, user_id: str, limit: int, offset: int = 0) -> tuple[list[QrScan], int]:
        return await self._repository.list_owned(user_id, limit, offset)

    async def delete_owned(self, scan_id: str, user_id: str) -> None:
        if not await self._repository.delete_owned(scan_id, user_id):
            raise NotFoundError("Scan history item was not found")
