from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import PasswordService, TokenService, TokenValidationError
from app.core.vault import VaultCipher, VaultGrantService
from app.db.mongodb import mongo
from app.infrastructure.qr.renderer import QrRenderer
from app.infrastructure.qr.decoder import QrImageDecoder
from app.infrastructure.storage.local_qr_storage import LocalQrStorage
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.qr_generation_repository import QrGenerationRepository
from app.repositories.qr_scan_repository import QrScanRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.bulk_job_repository import BulkJobRepository
from app.repositories.share_file_repository import ShareFileRepository
from app.repositories.share_download_repository import ShareDownloadRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.qr.generator_service import QrGeneratorService
from app.services.qr.payload_builder import QrPayloadBuilder
from app.services.qr.classifier import SmartClassifier
from app.services.qr.safe_scan import SafeScanService
from app.services.qr.scanner_service import QrScannerService
from app.services.qr.vault_access_service import VaultAccessService
from app.services.analytics.analytics_service import AnalyticsService
from app.services.analytics.scan_context import ScanContextService
from app.services.bulk.bulk_service import BulkForgeService
from app.infrastructure.bulk.parser import BulkImportParser
from app.infrastructure.bulk.zip_storage import BulkZipStorage
from app.infrastructure.storage.encrypted_share_storage import EncryptedShareStorage
from app.infrastructure.storage.vercel_blob_share_storage import VercelBlobShareStorage
from app.services.share.share_service import ShareVaultService
from app.services.dashboard_service import DashboardService
from app.services.profile_service import ProfileService
from app.services.admin_service import AdminService
from app.services.notification_service import NotificationService
from app.infrastructure.notifications.local_smtp import LocalSmtpEmailSender


bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="JWT access token returned by /api/v1/auth/login or /api/v1/auth/refresh",
    auto_error=False,
)


def get_user_repository() -> UserRepository:
    return UserRepository(mongo.database)


def get_session_repository() -> SessionRepository:
    return SessionRepository(mongo.database)


def get_qr_generation_repository() -> QrGenerationRepository:
    return QrGenerationRepository(mongo.database)


def get_qr_scan_repository() -> QrScanRepository:
    return QrScanRepository(mongo.database)


def get_analytics_repository() -> AnalyticsRepository:
    return AnalyticsRepository(mongo.database)


def get_bulk_job_repository() -> BulkJobRepository:
    return BulkJobRepository(mongo.database)


def get_share_file_repository() -> ShareFileRepository:
    return ShareFileRepository(mongo.database)


def get_share_download_repository() -> ShareDownloadRepository:
    return ShareDownloadRepository(mongo.database)


def get_dashboard_repository() -> DashboardRepository:
    return DashboardRepository(mongo.database)


def get_admin_repository() -> AdminRepository:
    return AdminRepository(mongo.database)


def get_notification_repository() -> NotificationRepository:
    return NotificationRepository(mongo.database)


def get_qr_image_decoder() -> QrImageDecoder:
    return QrImageDecoder()


def get_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> TokenService:
    return TokenService(settings)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(users, sessions, PasswordService(), tokens, settings)


def get_qr_generator_service(
    repository: Annotated[QrGenerationRepository, Depends(get_qr_generation_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> QrGeneratorService:
    return QrGeneratorService(
        repository=repository,
        renderer=QrRenderer(),
        storage=LocalQrStorage(settings.qr_storage_directory),
        payload_builder=QrPayloadBuilder(),
        redirect_base_url=settings.redirect_base_url,
        frontend_base_url=settings.frontend_base_url,
        cipher=VaultCipher(settings.vault_encryption_key or settings.jwt_secret),
        grants=VaultGrantService(settings),
        passwords=PasswordService(),
    )


def get_qr_scanner_service(
    repository: Annotated[QrScanRepository, Depends(get_qr_scan_repository)],
) -> QrScannerService:
    return QrScannerService(repository, SmartClassifier(), SafeScanService())


def get_analytics_service(
    repository: Annotated[AnalyticsRepository, Depends(get_analytics_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalyticsService:
    return AnalyticsService(repository, ScanContextService(settings.jwt_secret))


def get_vault_access_service(
    repository: Annotated[QrGenerationRepository, Depends(get_qr_generation_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> VaultAccessService:
    return VaultAccessService(repository, PasswordService(), VaultGrantService(settings), settings.redirect_base_url)


def get_bulk_forge_service(
    repository: Annotated[BulkJobRepository, Depends(get_bulk_job_repository)],
    generator: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BulkForgeService:
    return BulkForgeService(repository, generator, BulkImportParser(settings.bulk_max_rows), BulkZipStorage(settings.bulk_storage_directory))


def get_share_vault_service(
    repository: Annotated[ShareFileRepository, Depends(get_share_file_repository)],
    downloads: Annotated[ShareDownloadRepository, Depends(get_share_download_repository)],
    generator: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ShareVaultService:
    cipher = VaultCipher(settings.vault_encryption_key or settings.jwt_secret)
    storage = (
        VercelBlobShareStorage(settings.blob_read_write_token, cipher)
        if settings.blob_read_write_token
        else EncryptedShareStorage(settings.share_storage_directory, cipher)
    )
    return ShareVaultService(repository, downloads, storage, generator,
        PasswordService(), VaultGrantService(settings), ScanContextService(settings.jwt_secret), settings.frontend_base_url,
        settings.redirect_base_url, settings.share_max_file_bytes)


def get_dashboard_service(repository: Annotated[DashboardRepository, Depends(get_dashboard_repository)]) -> DashboardService:
    return DashboardService(repository)


def get_profile_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
) -> ProfileService:
    return ProfileService(users, sessions, PasswordService())


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Authentication credentials were not provided")
    try:
        payload = tokens.decode(credentials.credentials, "access")
    except TokenValidationError as exc:
        raise AuthenticationError("Could not validate credentials") from exc
    user = await users.find_by_id(payload.subject)
    if user is None or user.status != "active" or user.token_version != payload.token_version:
        raise AuthenticationError("Could not validate credentials")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise AuthorizationError("Administrator access is required")
    return current_user


AdminUser = Annotated[User, Depends(get_current_admin)]


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = tokens.decode(credentials.credentials, "access")
    except TokenValidationError:
        return None
    user = await users.find_by_id(payload.subject)
    if user is None or user.status != "active" or user.token_version != payload.token_version:
        return None
    return user


OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]


def get_admin_service(
    repository: Annotated[AdminRepository, Depends(get_admin_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
) -> AdminService:
    return AdminService(repository, sessions)


def get_notification_service(
    repository: Annotated[NotificationRepository, Depends(get_notification_repository)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> NotificationService:
    return NotificationService(repository, users, LocalSmtpEmailSender(settings))
