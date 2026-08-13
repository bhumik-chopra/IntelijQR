import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.exceptions import ApplicationError, AuthorizationError
from app.core.security import PasswordService, TokenValidationError
from app.core.vault import VaultCipher, VaultGrantService
from app.infrastructure.storage.encrypted_share_storage import EncryptedShareStorage
from app.infrastructure.storage.vercel_blob_share_storage import VercelBlobShareStorage
from app.models.share_file import ShareFile
from app.services.analytics.scan_context import ScanContextService
from app.services.share.share_service import ShareVaultService


def test_encrypted_share_storage_never_writes_plaintext(tmp_path: Path) -> None:
    storage = EncryptedShareStorage(tmp_path, VaultCipher("share-secret-that-is-at-least-32-characters"))
    relative = storage.save("file-key", b"confidential document content")

    assert b"confidential" not in (tmp_path / relative).read_bytes()
    assert storage.read(relative) == b"confidential document content"


def test_vercel_blob_share_storage_encrypts_round_trip() -> None:
    objects = {}

    class Result:
        def __init__(self, pathname, content=b"", status_code=200):
            self.pathname = pathname
            self.content = content
            self.status_code = status_code

    class Client:
        def __init__(self, token=None): self.token = token
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def put(self, pathname, content, **_):
            objects[pathname] = content
            return Result(pathname)
        def get(self, pathname, **_): return Result(pathname, objects[pathname])
        def delete(self, pathname): objects.pop(pathname, None)

    storage = VercelBlobShareStorage(
        "test-token",
        VaultCipher("share-secret-that-is-at-least-32-characters"),
        Client,
    )
    pathname = storage.save("file-key", b"confidential document content")

    assert pathname == "sharevault/file-key.vault"
    assert b"confidential" not in objects[pathname]
    assert storage.read(pathname) == b"confidential document content"
    storage.delete(pathname)
    assert pathname not in objects


def test_share_grants_cannot_be_used_as_qr_grants() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32)
    grants = VaultGrantService(settings)
    token, _ = grants.create("share-slug", "visitor", purpose="share")

    assert grants.validate(token, "share-slug", purpose="share")["purpose"] == "share"
    with pytest.raises(TokenValidationError):
        grants.validate(token, "share-slug", purpose="qr")


def test_share_status_reflects_expiry_and_download_limits() -> None:
    now = datetime.now(timezone.utc)
    base = dict(id="id", user_id="user", slug="slug", filename="file.pdf", media_type="application/pdf", size=10,
                content_hash="hash", stored_path="file.vault", qr_generation_id="qr", access_mode="public",
                access_password_hash=None, allowed_emails=[], is_active=True, created_at=now, updated_at=now)
    assert ShareFile(**base, expires_at=now - timedelta(seconds=1), max_downloads=None, download_count=0).status == "expired"
    assert ShareFile(**base, expires_at=None, max_downloads=2, download_count=2).status == "download_limit_reached"


def test_share_service_rejects_disguised_files_and_enforces_password() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32)
    passwords = PasswordService()
    share = SimpleNamespace(status="active", access_mode="password", access_password_hash=passwords.hash("correct-password"), allowed_emails=[])

    class Repository:
        async def find_by_slug(self, _slug): return share

    service = ShareVaultService(Repository(), None, None, None, passwords, VaultGrantService(settings), ScanContextService("x" * 32),
                                "http://127.0.0.1:5173", "http://127.0.0.1:8000", 1024 * 1024)
    with pytest.raises(ApplicationError): service._validate_file("malware.pdf", "application/pdf", b"MZ executable")
    with pytest.raises(AuthorizationError): asyncio.run(service.grant("slug", "wrong-password", None))
    url, _ = asyncio.run(service.grant("slug", "correct-password", None))
    assert "/shares/access/slug/download?grant=" in url


def test_share_qr_opens_frontend_access_page_directly() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32)

    class Repository:
        async def slug_exists(self, _slug): return False
        async def create(self, **values): return SimpleNamespace(**values)

    class Storage:
        def save(self, key, _content): return f"{key}.vault"
        def delete(self, _path): pass

    class Generator:
        request = None
        async def generate(self, _user_id, request):
            self.request = request
            return SimpleNamespace(id="qr-id")

    generator = Generator()
    service = ShareVaultService(
        Repository(), None, Storage(), generator, PasswordService(), VaultGrantService(settings),
        ScanContextService("x" * 32), "https://intelij-qr.vercel.app", "https://api.example.com", 1024 * 1024,
    )

    asyncio.run(service.create("user", "note.txt", "text/plain", b"hello", "public", None, "", None, None))

    assert str(generator.request.url).startswith("https://intelij-qr.vercel.app/share/")
    assert generator.request.dynamic is False
