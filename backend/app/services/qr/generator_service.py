import asyncio
import hashlib
import logging
import secrets
import uuid
from dataclasses import replace
from pathlib import Path

from app.core.exceptions import ApplicationError, GoneError, NotFoundError
from app.core.security import PasswordService
from app.core.vault import VaultCipher, VaultGrantService
from app.infrastructure.qr.renderer import QrRenderer
from app.infrastructure.storage.local_qr_storage import LocalQrStorage
from app.models.qr_generation import QrDesign, QrFileFormat, QrGeneration, QrPayloadType
from app.repositories.qr_generation_repository import QrGenerationRepository
from app.schemas.qr_generation import QrGenerationRequest, QrGenerationUpdateRequest
from app.services.qr.payload_builder import QrPayloadBuilder


logger = logging.getLogger(__name__)


class QrGeneratorService:
    def __init__(
        self,
        repository: QrGenerationRepository,
        renderer: QrRenderer,
        storage: LocalQrStorage,
        payload_builder: QrPayloadBuilder,
        redirect_base_url: str,
        frontend_base_url: str,
        cipher: VaultCipher,
        grants: VaultGrantService,
        passwords: PasswordService,
    ) -> None:
        self._repository = repository
        self._renderer = renderer
        self._storage = storage
        self._payload_builder = payload_builder
        self._redirect_base_url = redirect_base_url.rstrip("/")
        self._frontend_base_url = frontend_base_url.rstrip("/")
        self._cipher = cipher
        self._grants = grants
        self._passwords = passwords

    async def generate(self, user_id: str, request: QrGenerationRequest) -> QrGeneration:
        destination_payload = self._payload_builder.build(request)
        if request.type != "url" and request.access_mode != "public":
            raise ApplicationError("SecureVault protection is available for dynamic URL QR codes")
        slug = await self._new_slug()
        dynamic_url = f"{self._redirect_base_url}/r/{slug}" if request.type == "url" else None
        rendered_payload = dynamic_url or destination_payload
        design = QrDesign(**request.design.model_dump())
        logo = await asyncio.to_thread(self._renderer.normalize_logo, request.logo_data_url)
        rendered = await asyncio.to_thread(self._renderer.render_all, rendered_payload, design, logo)
        storage_key = uuid.uuid4().hex
        stored_files = await asyncio.to_thread(self._storage.save, storage_key, rendered, logo)
        try:
            protected = request.type == "url" and request.access_mode != "public"
            password_hash = self._passwords.hash(request.access_password) if request.access_password else None
            generation = await self._repository.create(
                user_id=user_id,
                payload_type=request.type,
                label=request.label,
                payload_preview=("Protected SecureVault destination" if protected else self._payload_builder.preview(request, destination_payload)),
                payload_hash=hashlib.sha256(destination_payload.encode("utf-8")).hexdigest(),
                payload_details=({"protected": True} if protected else self._payload_builder.safe_details(request)),
                files=stored_files,
                slug=slug,
                dynamic_url=dynamic_url,
                destination_url=destination_payload if request.type == "url" and not protected else None,
                encrypted_destination=self._cipher.encrypt(destination_payload) if protected else None,
                access_mode=request.access_mode,
                access_password_hash=password_hash,
                allowed_emails=[str(email).lower() for email in request.allowed_emails],
                expires_at=request.expires_at,
                max_scans=request.max_scans,
                design=request.design.model_dump(),
                logo_file=f"{storage_key}/logo.png" if logo else None,
            )
        except Exception:
            await asyncio.to_thread(self._storage.delete, storage_key)
            raise
        logger.info("QR code generated", extra={"user_id": user_id, "qr_id": generation.id})
        return self._hydrate_destination(generation)

    async def get_owned(self, generation_id: str, user_id: str) -> QrGeneration:
        generation = await self._repository.find_owned(generation_id, user_id)
        if generation is None:
            raise NotFoundError("QR generation was not found")
        return self._hydrate_destination(generation)

    async def list_owned(
        self,
        user_id: str,
        limit: int,
        offset: int = 0,
        search: str | None = None,
        payload_type: QrPayloadType | None = None,
        status: str | None = None,
        favorite: bool | None = None,
    ) -> tuple[list[QrGeneration], int]:
        items, total = await self._repository.list_owned(
            user_id, limit, offset, search, payload_type, status, favorite
        )
        return [self._hydrate_destination(item) for item in items], total

    async def update_owned(
        self,
        generation_id: str,
        user_id: str,
        request: QrGenerationUpdateRequest,
    ) -> QrGeneration:
        current = await self.get_owned(generation_id, user_id)
        changes: dict = {}
        provided = request.model_fields_set
        for field in ("label", "is_active", "is_favorite", "expires_at", "max_scans"):
            if field in provided:
                changes[field] = getattr(request, field)
        policy_requested = bool(provided.intersection({"access_mode", "access_password", "allowed_emails"}))
        destination_requested = "destination_url" in provided
        if policy_requested or destination_requested:
            if current.payload_type != "url" or not current.dynamic_url:
                raise ApplicationError("SecureVault controls are available only for dynamic URL QR codes")
            destination = str(request.destination_url) if request.destination_url is not None else current.destination_url
            if not destination:
                raise ApplicationError("The QR destination is unavailable")
            access_mode = request.access_mode or current.access_mode
            allowed_emails = (
                [str(email).lower() for email in request.allowed_emails]
                if request.allowed_emails is not None else current.allowed_emails
            )
            password_hash = current.access_password_hash
            if request.access_password:
                password_hash = self._passwords.hash(request.access_password)
            if access_mode == "password" and not password_hash:
                raise ApplicationError("Set a password before enabling password protection")
            if access_mode == "private" and not allowed_emails:
                raise ApplicationError("Add at least one allowed email for private sharing")
            if access_mode != "password":
                password_hash = None
            if access_mode != "private":
                allowed_emails = []
            protected = access_mode != "public"
            changes.update(
                access_mode=access_mode,
                access_password_hash=password_hash,
                allowed_emails=allowed_emails,
                destination_url=None if protected else destination,
                encrypted_destination=self._cipher.encrypt(destination) if protected else None,
                payload_preview=("Protected SecureVault destination" if protected else destination[:160]),
                payload_hash=hashlib.sha256(destination.encode("utf-8")).hexdigest(),
                payload_details=({"protected": True} if protected else {**current.payload_details, "url": destination, "protected": False}),
            )
        design_requested = "design" in provided and request.design is not None
        logo_requested = "logo_data_url" in provided and request.logo_data_url is not None
        remove_logo = "remove_logo" in provided and request.remove_logo is True
        replacement_storage_key: str | None = None
        old_storage_key: str | None = None
        if design_requested or logo_requested or remove_logo:
            if not current.dynamic_url:
                raise ApplicationError("Saved design updates are available for dynamic URL QR codes")
            selected_design = QrDesign(**(
                request.design.model_dump()
                if request.design is not None
                else current.design
            ))
            if logo_requested:
                logo = await asyncio.to_thread(self._renderer.normalize_logo, request.logo_data_url)
            elif remove_logo:
                logo = None
            elif current.logo_file:
                logo = await asyncio.to_thread(self._storage.read, current.logo_file)
            else:
                logo = None
            rendered = await asyncio.to_thread(self._renderer.render_all, current.dynamic_url, selected_design, logo)
            replacement_storage_key = uuid.uuid4().hex
            replacement_files = await asyncio.to_thread(self._storage.save, replacement_storage_key, rendered, logo)
            changes.update(
                files=replacement_files,
                design={
                    "foreground_color": selected_design.foreground_color,
                    "background_color": selected_design.background_color,
                    "gradient_enabled": selected_design.gradient_enabled,
                    "gradient_color": selected_design.gradient_color,
                    "gradient_direction": selected_design.gradient_direction,
                    "module_style": selected_design.module_style,
                    "frame_style": selected_design.frame_style,
                    "frame_text": selected_design.frame_text,
                    "error_correction": selected_design.error_correction,
                    "size": selected_design.size,
                    "margin": selected_design.margin,
                },
                logo_file=f"{replacement_storage_key}/logo.png" if logo else None,
            )
            first_old_file = next(iter(current.files.values()), None)
            old_storage_key = first_old_file.split("/", 1)[0] if first_old_file else None
        try:
            updated = await self._repository.update_owned(generation_id, user_id, changes)
        except Exception:
            if replacement_storage_key:
                await asyncio.to_thread(self._storage.delete, replacement_storage_key)
            raise
        if updated is None:
            if replacement_storage_key:
                await asyncio.to_thread(self._storage.delete, replacement_storage_key)
            raise NotFoundError("QR generation was not found")
        if old_storage_key and old_storage_key != replacement_storage_key:
            await asyncio.to_thread(self._storage.delete, old_storage_key)
        logger.info("QR code updated", extra={"user_id": user_id, "qr_id": generation_id})
        return self._hydrate_destination(updated)

    async def delete_owned(self, generation_id: str, user_id: str) -> None:
        generation = await self._repository.delete_owned(generation_id, user_id)
        if generation is None:
            raise NotFoundError("QR generation was not found")
        first_file = next(iter(generation.files.values()), None)
        if first_file:
            await asyncio.to_thread(self._storage.delete, first_file.split("/", 1)[0])
        logger.info("QR code deleted", extra={"user_id": user_id, "qr_id": generation_id})

    async def resolve_redirect(self, slug: str, grant: str | None = None) -> tuple[str, QrGeneration | None]:
        candidate = await self._repository.find_by_slug(slug)
        if candidate is None or candidate.status != "active":
            raise GoneError("This QR code is inactive, expired, or has reached its scan limit")
        if candidate.access_mode != "public" and not grant:
            return f"{self._frontend_base_url}/access/{slug}", None
        if candidate.access_mode != "public":
            self._grants.validate(grant or "", slug)
        generation = await self._repository.consume_dynamic_scan(slug)
        if generation is None:
            raise GoneError("This QR code is inactive, expired, or has reached its scan limit")
        hydrated = self._hydrate_destination(generation)
        if not hydrated.destination_url:
            raise GoneError("This QR destination is unavailable")
        logger.info("Dynamic QR redirected", extra={"qr_id": generation.id})
        return hydrated.destination_url, hydrated

    async def resolve_download(
        self, generation_id: str, user_id: str, file_format: QrFileFormat
    ) -> tuple[Path, str]:
        generation = await self.get_owned(generation_id, user_id)
        relative_path = generation.files.get(file_format)
        if relative_path is None:
            raise NotFoundError("Requested QR file was not found")
        try:
            path = await asyncio.to_thread(self._storage.resolve, relative_path)
        except FileNotFoundError as exc:
            raise NotFoundError("Requested QR file was not found") from exc
        return path, f"intelliqr-{generation.id}.{file_format}"

    async def _new_slug(self) -> str:
        for _ in range(5):
            slug = secrets.token_urlsafe(8).rstrip("=")
            if not await self._repository.slug_exists(slug):
                return slug
        raise ApplicationError("Could not allocate a unique QR link")

    def _hydrate_destination(self, generation: QrGeneration) -> QrGeneration:
        if generation.encrypted_destination:
            return replace(generation, destination_url=self._cipher.decrypt(generation.encrypted_destination))
        return generation
