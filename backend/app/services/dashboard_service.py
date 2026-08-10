import logging
from app.repositories.dashboard_repository import DashboardRepository

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(self, repository: DashboardRepository) -> None: self._repository = repository
    async def summary(self, user_id: str) -> dict: return await self._repository.summary(user_id)
    async def record_download(self, user_id: str, resource_type: str, resource_id: str, filename: str, file_format: str) -> None:
        try: await self._repository.record_download(user_id, resource_type, resource_id, filename, file_format)
        except Exception: logger.exception("Export download event could not be recorded", extra={"user_id": user_id, "resource_id": resource_id})
