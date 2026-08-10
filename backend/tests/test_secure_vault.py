import asyncio
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import PasswordService, TokenValidationError
from app.core.vault import VaultCipher, VaultGrantService
from app.schemas.qr_generation import UrlQrRequest
from app.models.qr_generation import QrGeneration
from app.infrastructure.storage.local_qr_storage import LocalQrStorage
from app.services.qr.generator_service import QrGeneratorService
from app.services.qr.payload_builder import QrPayloadBuilder
from app.services.qr.vault_access_service import VaultAccessService


def test_aes_gcm_round_trip_uses_random_authenticated_ciphertext() -> None:
    cipher = VaultCipher("vault-secret-that-is-at-least-32-characters")
    first = cipher.encrypt("https://example.com/private")
    second = cipher.encrypt("https://example.com/private")

    assert first != second
    assert "example.com" not in first
    assert cipher.decrypt(first) == "https://example.com/private"
    with pytest.raises((InvalidTag, ValueError)):
        cipher.decrypt(first[:-2] + "AA")


def test_vault_grant_is_short_lived_and_slug_bound() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32, vault_grant_expire_minutes=5)
    grants = VaultGrantService(settings)
    token, expires_at = grants.create("allowed-slug", "user-id")

    assert grants.validate(token, "allowed-slug")["sub"] == "user-id"
    assert expires_at is not None
    with pytest.raises(TokenValidationError):
        grants.validate(token, "different-slug")


def test_secure_policy_schema_requires_password_or_allowlist() -> None:
    with pytest.raises(ValidationError):
        UrlQrRequest(type="url", url="https://example.com", access_mode="password")
    with pytest.raises(ValidationError):
        UrlQrRequest(type="url", url="https://example.com", access_mode="private")


def test_password_and_private_access_are_enforced() -> None:
    passwords = PasswordService()
    settings = Settings(_env_file=None, jwt_secret="x" * 32)
    protected = SimpleNamespace(
        id="qr-id", slug="slug", label="Protected", status="active", access_mode="password",
        access_password_hash=passwords.hash("correct-password"), allowed_emails=[],
    )

    class Repository:
        async def find_by_slug(self, _slug):
            return protected

    service = VaultAccessService(Repository(), passwords, VaultGrantService(settings), "http://127.0.0.1:8000")
    with pytest.raises(AuthorizationError):
        asyncio.run(service.unlock("slug", "wrong-password", None))
    redirect, _ = asyncio.run(service.unlock("slug", "correct-password", None))
    assert redirect.startswith("http://127.0.0.1:8000/r/slug?grant=")

    protected.access_mode = "private"
    protected.allowed_emails = ["allowed@example.com"]
    with pytest.raises(AuthenticationError):
        asyncio.run(service.unlock("slug", None, None))
    with pytest.raises(AuthorizationError):
        asyncio.run(service.unlock("slug", None, SimpleNamespace(id="2", email="blocked@example.com")))
    redirect, _ = asyncio.run(service.unlock("slug", None, SimpleNamespace(id="1", email="allowed@example.com")))
    assert "grant=" in redirect


def test_secure_generation_persists_only_encrypted_destination(tmp_path: Path) -> None:
    class Renderer:
        @staticmethod
        def normalize_logo(_value): return None
        @staticmethod
        def render_all(_payload, _design, _logo): return {"png": b"png", "svg": b"svg", "pdf": b"pdf"}

    class Repository:
        values = None
        async def slug_exists(self, _slug): return False
        async def create(self, **values):
            self.values = values
            now = datetime.now(timezone.utc)
            return QrGeneration(
                id="qr-id", user_id=values["user_id"], payload_type=values["payload_type"], label=values["label"],
                payload_preview=values["payload_preview"], payload_hash=values["payload_hash"], payload_details=values["payload_details"],
                files=values["files"], slug=values["slug"], dynamic_url=values["dynamic_url"], destination_url=values["destination_url"],
                encrypted_destination=values["encrypted_destination"], access_mode=values["access_mode"],
                access_password_hash=values["access_password_hash"], allowed_emails=values["allowed_emails"],
                is_active=True, is_favorite=False, expires_at=values["expires_at"], max_scans=values["max_scans"], scan_count=0,
                design=values["design"], logo_file=values["logo_file"], created_at=now, updated_at=now,
            )

    settings = Settings(_env_file=None, jwt_secret="x" * 32)
    repository = Repository()
    service = QrGeneratorService(
        repository, Renderer(), LocalQrStorage(tmp_path), QrPayloadBuilder(), "http://127.0.0.1:8000",
        "http://127.0.0.1:5173", VaultCipher("vault-secret-that-is-at-least-32-characters"),
        VaultGrantService(settings), PasswordService(),
    )
    result = asyncio.run(service.generate("user-id", UrlQrRequest(
        type="url", url="https://secret.example/private", access_mode="password", access_password="correct-password",
    )))

    assert repository.values["destination_url"] is None
    assert "secret.example" not in repository.values["encrypted_destination"]
    assert repository.values["payload_preview"] == "Protected SecureVault destination"
    assert result.destination_url == "https://secret.example/private"
