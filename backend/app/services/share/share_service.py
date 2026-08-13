import asyncio
import hashlib
import re
import secrets
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.exceptions import ApplicationError, AuthenticationError, AuthorizationError, GoneError, NotFoundError
from app.core.security import PasswordService
from app.core.vault import VaultGrantService
from app.infrastructure.storage.encrypted_share_storage import EncryptedShareStorage
from app.models.share_file import ShareFile
from app.models.user import User
from app.repositories.share_download_repository import ShareDownloadRepository
from app.repositories.share_file_repository import ShareFileRepository
from app.schemas.qr_generation import UrlQrRequest
from app.schemas.share import ShareUpdateRequest
from app.services.analytics.scan_context import ScanContextService
from app.services.qr.generator_service import QrGeneratorService


logger = logging.getLogger(__name__)


class ShareVaultService:
    _extensions = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mov", ".txt", ".csv", ".docx", ".xlsx", ".pptx", ".odt"}
    _media_types = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif", ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
        ".txt": "text/plain", ".csv": "text/csv", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation", ".odt": "application/vnd.oasis.opendocument.text"}
    _email = TypeAdapter(EmailStr)

    def __init__(self, repository: ShareFileRepository, downloads: ShareDownloadRepository, storage: EncryptedShareStorage,
                 generator: QrGeneratorService, passwords: PasswordService, grants: VaultGrantService,
                 context: ScanContextService, frontend_base_url: str, api_base_url: str, max_file_bytes: int) -> None:
        self._repository = repository; self._downloads = downloads; self._storage = storage; self._generator = generator
        self._passwords = passwords; self._grants = grants; self._context = context
        self._frontend_base_url = frontend_base_url.rstrip("/"); self._api_base_url = api_base_url.rstrip("/"); self._max_file_bytes = max_file_bytes

    async def create(self, user_id: str, filename: str, media_type: str, content: bytes, access_mode: str, access_password: str | None,
                     allowed_emails: str, expires_at: datetime | None, max_downloads: int | None) -> ShareFile:
        safe_name, canonical_media_type = self._validate_file(filename, media_type, content)
        if expires_at is not None and expires_at <= datetime.now(expires_at.tzinfo): raise ApplicationError("Expiry must be in the future")
        emails = self._parse_emails(allowed_emails)
        if access_mode != "private" and emails: raise ApplicationError("Allowed emails can only be used with private sharing")
        if access_mode != "password" and access_password: raise ApplicationError("A password can only be used with password protection")
        password_hash = self._validate_policy(access_mode, access_password, emails, None)
        slug = await self._new_slug(); storage_key = secrets.token_hex(24)
        stored_path = await asyncio.to_thread(self._storage.save, storage_key, content)
        generation = None
        try:
            # ShareVault records its own download analytics, so its QR should open
            # the public frontend access page directly instead of depending on a
            # second dynamic redirect through the API host.
            generation = await self._generator.generate(user_id, UrlQrRequest(
                type="url",
                url=f"{self._frontend_base_url}/share/{slug}",
                label=f"Share: {safe_name}",
                dynamic=False,
            ))
            return await self._repository.create(user_id=user_id, slug=slug, filename=safe_name, media_type=canonical_media_type,
                size=len(content), content_hash=hashlib.sha256(content).hexdigest(), stored_path=stored_path, qr_generation_id=generation.id,
                access_mode=access_mode, access_password_hash=password_hash, allowed_emails=emails if access_mode == "private" else [], expires_at=expires_at, max_downloads=max_downloads)
        except Exception:
            await asyncio.to_thread(self._storage.delete, stored_path)
            if generation:
                try: await self._generator.delete_owned(generation.id, user_id)
                except Exception: pass
            raise

    async def list_owned(self, user_id: str, limit: int, offset: int = 0): return await self._repository.list_owned(user_id, limit, offset)
    async def list_downloads(self, share_id: str, user_id: str, limit: int, offset: int = 0):
        await self.get_owned(share_id, user_id)
        return await self._downloads.list_owned(share_id, user_id, limit, offset)
    async def get_owned(self, share_id: str, user_id: str) -> ShareFile:
        share = await self._repository.find_owned(share_id, user_id)
        if share is None: raise NotFoundError("Shared file was not found")
        return share
    async def policy(self, slug: str) -> ShareFile:
        share = await self._repository.find_by_slug(slug)
        if share is None: raise NotFoundError("Shared file was not found")
        return share

    async def grant(self, slug: str, password: str | None, user: User | None) -> tuple[str, datetime]:
        share = await self.policy(slug)
        if share.status != "active": raise GoneError("This shared file is unavailable")
        if share.access_mode == "password":
            if not password or not share.access_password_hash or not self._passwords.verify(password, share.access_password_hash):
                raise AuthorizationError("The ShareVault password is incorrect")
        elif share.access_mode in {"authenticated", "private"}:
            if user is None: raise AuthenticationError("Sign in to access this shared file")
            if share.access_mode == "private" and user.email.lower() not in share.allowed_emails:
                raise AuthorizationError("Your account is not allowed to access this file")
        token, expires = self._grants.create(slug, user.id if user else "share-visitor", purpose="share")
        return f"/shares/access/{slug}/download?grant={token}", expires

    async def download(self, slug: str, grant: str, user: User | None, client_ip: str, user_agent: str) -> tuple[bytes, ShareFile]:
        grant_payload = self._grants.validate(grant, slug, purpose="share")
        candidate = await self.policy(slug)
        if candidate.status != "active": raise GoneError("This shared file is unavailable")
        if candidate.access_mode in {"authenticated", "private"}:
            if user is None or grant_payload.get("sub") != user.id:
                raise AuthenticationError("Sign in with the account that authorized this download")
        try: content = await asyncio.to_thread(self._storage.read, candidate.stored_path)
        except FileNotFoundError as exc: raise NotFoundError("The encrypted file was not found") from exc
        share = await self._repository.consume_download(slug)
        if share is None: raise GoneError("This shared file is unavailable")
        try: await self._downloads.record(share, self._context.parse(client_ip, user_agent), user.id if user else None)
        except Exception: logger.exception("ShareVault download event could not be recorded", extra={"share_id": share.id})
        return content, share

    async def update_owned(self, share_id: str, user_id: str, request: ShareUpdateRequest) -> ShareFile:
        current = await self.get_owned(share_id, user_id); provided = request.model_fields_set; changes = {}
        mode = request.access_mode or current.access_mode
        emails = [str(item).lower() for item in request.allowed_emails] if request.allowed_emails is not None else current.allowed_emails
        if mode != "private": emails = []
        password_hash = self._validate_policy(mode, request.access_password, emails, current.access_password_hash)
        if provided.intersection({"access_mode", "access_password", "allowed_emails"}):
            changes.update(access_mode=mode, access_password_hash=password_hash, allowed_emails=emails if mode == "private" else [])
        for field in ("expires_at", "max_downloads", "is_active"):
            if field in provided: changes[field] = getattr(request, field)
        updated = await self._repository.update_owned(share_id, user_id, changes)
        if updated is None: raise NotFoundError("Shared file was not found")
        return updated

    async def delete_owned(self, share_id: str, user_id: str) -> None:
        share = await self._repository.delete_owned(share_id, user_id)
        if share is None: raise NotFoundError("Shared file was not found")
        await asyncio.to_thread(self._storage.delete, share.stored_path)
        await self._downloads.delete_for_share(share.id, user_id)
        try: await self._generator.delete_owned(share.qr_generation_id, user_id)
        except NotFoundError: pass

    def _validate_file(self, filename: str, media_type: str, content: bytes) -> tuple[str, str]:
        if not content: raise ApplicationError("The uploaded file is empty")
        if len(content) > self._max_file_bytes: raise ApplicationError(f"Files must be {self._max_file_bytes // (1024 * 1024)} MB or smaller")
        safe_name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "-", Path(filename or "shared-file").name).strip(" .")[:140]
        extension = Path(safe_name).suffix.lower()
        if extension not in self._extensions: raise ApplicationError("This file type is not allowed in ShareVault")
        if extension == ".pdf" and not content.startswith(b"%PDF"): raise ApplicationError("The PDF signature is invalid")
        if extension in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            try:
                with Image.open(BytesIO(content)) as image:
                    if image.width * image.height > 25_000_000: raise ApplicationError("Image dimensions are too large")
                    image.verify()
            except ApplicationError: raise
            except (UnidentifiedImageError, OSError) as exc: raise ApplicationError("The image file is invalid") from exc
        if extension in {".docx", ".xlsx", ".pptx", ".odt"} and not content.startswith(b"PK"):
            raise ApplicationError("The document container is invalid")
        if extension in {".mp4", ".mov"} and b"ftyp" not in content[:16]: raise ApplicationError("The video signature is invalid")
        if extension == ".webm" and not content.startswith(b"\x1aE\xdf\xa3"): raise ApplicationError("The WebM signature is invalid")
        if extension in {".txt", ".csv"}:
            try: content.decode("utf-8")
            except UnicodeDecodeError as exc: raise ApplicationError("Text files must use UTF-8 encoding") from exc
        return safe_name or f"shared-file{extension}", self._media_types[extension]

    def _parse_emails(self, value: str) -> list[str]:
        emails = []
        for raw in re.split(r"[,\n]", value or ""):
            if not raw.strip(): continue
            try: emails.append(str(self._email.validate_python(raw.strip())).lower())
            except ValidationError as exc: raise ApplicationError(f"Invalid allowed email: {raw.strip()}") from exc
        return list(dict.fromkeys(emails))

    def _validate_policy(self, mode: str, password: str | None, emails: list[str], current_hash: str | None) -> str | None:
        if mode not in {"public", "password", "authenticated", "private"}: raise ApplicationError("Invalid share access mode")
        if mode != "password" and password: raise ApplicationError("A password can only be used with password protection")
        if password and len(password.encode()) > 72: raise ApplicationError("Password must not exceed 72 UTF-8 bytes")
        if mode == "password":
            if not password and not current_hash: raise ApplicationError("A password of at least 8 characters is required")
            if password and len(password) < 8: raise ApplicationError("A password of at least 8 characters is required")
            return self._passwords.hash(password) if password else current_hash
        if mode == "private" and not emails: raise ApplicationError("At least one allowed email is required")
        if len(emails) > 25: raise ApplicationError("Private shares support up to 25 email addresses")
        return None

    async def _new_slug(self) -> str:
        for _ in range(5):
            slug = secrets.token_urlsafe(12).rstrip("=")
            if not await self._repository.slug_exists(slug): return slug
        raise ApplicationError("Could not allocate a unique share link")
