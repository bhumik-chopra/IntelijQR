import logging
from datetime import datetime, timezone

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings


logger = logging.getLogger(__name__)


class MongoDatabase:
    def __init__(self) -> None:
        self._client: AsyncMongoClient | None = None
        self._database: AsyncDatabase | None = None

    @property
    def database(self) -> AsyncDatabase:
        if self._database is None:
            raise RuntimeError("MongoDB has not been initialized")
        return self._database

    async def connect(self, settings: Settings) -> None:
        self._client = AsyncMongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
            tz_aware=True,
        )
        self._database = self._client[settings.mongodb_database]
        try:
            await self._client.admin.command("ping")
            await self._create_indexes()
            logger.info("MongoDB connection established")
        except Exception:
            logger.exception("MongoDB is unavailable during startup")
            if settings.mongodb_required_on_startup:
                await self.close()
                raise

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
        self._client = None
        self._database = None

    async def _create_indexes(self) -> None:
        user_indexes = await self.database.users.index_information()
        if "uq_users_username" in user_indexes:
            await self.database.users.drop_index("uq_users_username")
        await self.database.users.create_indexes(
            [
                IndexModel([("email", ASCENDING)], unique=True, name="uq_users_email"),
            ]
        )
        await self.database.sessions.create_indexes(
            [
                IndexModel([("refresh_jti", ASCENDING)], unique=True, name="uq_sessions_jti"),
                IndexModel([("user_id", ASCENDING), ("revoked_at", ASCENDING)], name="ix_sessions_user_active"),
                IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_sessions_expiry"),
            ]
        )
        await self.database.qr_generations.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_generations_user_created"
        )
        await self.database.qr_generations.create_indexes(
            [
                IndexModel([("slug", ASCENDING)], unique=True, sparse=True, name="uq_generations_slug"),
                IndexModel([("user_id", ASCENDING), ("is_favorite", ASCENDING)], name="ix_generations_user_favorite"),
                IndexModel([("user_id", ASCENDING), ("is_active", ASCENDING)], name="ix_generations_user_active"),
            ]
        )
        await self.database.qr_scans.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_scans_user_created"
        )
        await self.database.qr_scan_events.create_indexes(
            [
                IndexModel([("user_id", ASCENDING), ("scanned_at", DESCENDING)], name="ix_scan_events_user_time"),
                IndexModel([("generation_id", ASCENDING), ("scanned_at", DESCENDING)], name="ix_scan_events_qr_time"),
                IndexModel([("user_id", ASCENDING), ("visitor_hash", ASCENDING), ("scanned_at", DESCENDING)], name="ix_scan_events_visitor_time"),
            ]
        )
        await self.database.bulk_jobs.create_indexes(
            [
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_bulk_jobs_user_created"),
                IndexModel([("user_id", ASCENDING), ("status", ASCENDING)], name="ix_bulk_jobs_user_status"),
            ]
        )
        now = datetime.now(timezone.utc)
        await self.database.bulk_jobs.update_many(
            {"status": {"$in": ["queued", "processing"]}},
            {"$set": {
                "status": "failed",
                "completed_at": now,
                "updated_at": now,
                "errors": [{"row": 0, "message": "Job interrupted by a backend restart; upload the source file again"}],
            }},
        )
        await self.database.share_files.create_indexes(
            [
                IndexModel([("slug", ASCENDING)], unique=True, name="uq_share_files_slug"),
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_share_files_user_created"),
                IndexModel([("user_id", ASCENDING), ("is_active", ASCENDING)], name="ix_share_files_user_active"),
            ]
        )
        await self.database.share_download_events.create_indexes(
            [
                IndexModel([("owner_user_id", ASCENDING), ("downloaded_at", DESCENDING)], name="ix_share_downloads_owner_time"),
                IndexModel([("share_id", ASCENDING), ("downloaded_at", DESCENDING)], name="ix_share_downloads_share_time"),
            ]
        )
        await self.database.download_events.create_index(
            [("user_id", ASCENDING), ("downloaded_at", DESCENDING)], name="ix_download_events_user_time"
        )
        await self.database.qr_scans.create_index(
            [("user_id", ASCENDING), ("content_hash", ASCENDING)], name="ix_scans_user_content"
        )
        await self.database.admin_audit_events.create_indexes(
            [
                IndexModel([("created_at", DESCENDING)], name="ix_admin_audit_time"),
                IndexModel([("admin_user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_admin_audit_actor_time"),
                IndexModel([("target_id", ASCENDING), ("created_at", DESCENDING)], name="ix_admin_audit_target_time"),
            ]
        )
        await self.database.notifications.create_indexes(
            [
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_notifications_user_time"),
                IndexModel([("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", DESCENDING)], name="ix_notifications_user_unread"),
            ]
        )


mongo = MongoDatabase()
