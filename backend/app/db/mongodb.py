import logging

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
        await self.database.qr_scans.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)], name="ix_scans_user_created"
        )


mongo = MongoDatabase()
