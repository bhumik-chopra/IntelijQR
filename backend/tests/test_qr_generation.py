import asyncio
import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image
from pydantic import ValidationError

from app.infrastructure.qr.renderer import QrRenderer
from app.infrastructure.storage.local_qr_storage import LocalQrStorage
from app.infrastructure.storage.vercel_blob_qr_storage import VercelBlobQrStorage
from app.models.qr_generation import QrDesign, QrGeneration
from app.schemas.qr_generation import (
    ContactQrRequest,
    EmailQrRequest,
    LocationQrRequest,
    PhoneQrRequest,
    TextQrRequest,
    UrlQrRequest,
    WifiQrRequest,
    QrDesignRequest,
)
from app.services.qr.payload_builder import QrPayloadBuilder
from app.services.qr.generator_service import QrGeneratorService
from app.core.config import Settings
from app.core.security import PasswordService
from app.core.vault import VaultCipher, VaultGrantService


def test_builds_all_supported_payload_types() -> None:
    builder = QrPayloadBuilder()
    requests = [
        UrlQrRequest(type="url", url="https://example.com"),
        TextQrRequest(type="text", text="Hello IntelliQR"),
        EmailQrRequest(type="email", email="hello@example.com", subject="Hello"),
        PhoneQrRequest(type="phone", phone="+1 555 0100"),
        WifiQrRequest(type="wifi", ssid="Local Network", password="secret"),
        ContactQrRequest(
            type="contact",
            full_name="IntelliQR User",
            email="user@example.com",
        ),
        LocationQrRequest(type="location", latitude=19.076, longitude=72.8777, name="Mumbai"),
    ]

    payloads = [builder.build(request) for request in requests]

    assert payloads[0].startswith("https://example.com")
    assert payloads[1] == "Hello IntelliQR"
    assert payloads[2].startswith("mailto:hello@example.com")
    assert payloads[3] == "tel:+15550100"
    assert payloads[4].startswith("WIFI:T:WPA;")
    assert "BEGIN:VCARD" in payloads[5]
    assert payloads[6].startswith("geo:19.076000,72.877700")
    assert builder.safe_details(requests[4])["password"] == "***"


def test_renders_png_svg_and_pdf() -> None:
    rendered = QrRenderer().render_all("https://example.com/intelliqr")

    assert rendered["png"].startswith(b"\x89PNG\r\n\x1a\n")
    assert b"<svg" in rendered["svg"][:500]
    assert rendered["pdf"].startswith(b"%PDF")


def test_local_storage_round_trip(tmp_path: Path) -> None:
    storage = LocalQrStorage(tmp_path)
    paths = storage.save("safe-storage-key", {"png": b"png", "svg": b"svg", "pdf": b"pdf"})

    assert storage.resolve(paths["png"]).read_bytes() == b"png"
    assert storage.resolve(paths["svg"]).read_bytes() == b"svg"
    assert storage.resolve(paths["pdf"]).read_bytes() == b"pdf"


def test_vercel_blob_qr_storage_round_trip() -> None:
    objects = {}

    class Result:
        def __init__(self, pathname, content=b"", status_code=200):
            self.pathname, self.content, self.status_code = pathname, content, status_code

    class Client:
        def __init__(self, token=None): self.token = token
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def put(self, pathname, content, **_kwargs): objects[pathname] = content; return Result(pathname)
        def get(self, pathname, **_kwargs): return Result(pathname, objects[pathname])
        def delete(self, paths):
            for path in ([paths] if isinstance(paths, str) else paths): objects.pop(path, None)

    storage = VercelBlobQrStorage("token", Client)
    paths = storage.save("key", {"png": b"png", "svg": b"svg", "pdf": b"pdf"}, b"logo")

    assert storage.read(paths["png"]) == b"png"
    assert objects["key/logo.png"] == b"logo"
    storage.delete("key")
    assert objects == {}


def test_dynamic_url_generation_renders_stable_redirect(tmp_path: Path) -> None:
    class FakeRenderer:
        payload = ""

        @staticmethod
        def normalize_logo(_: str | None) -> None:
            return None

        def render_all(self, payload: str, *_args) -> dict[str, bytes]:
            self.payload = payload
            return {"png": b"png", "svg": b"svg", "pdf": b"pdf"}

    class FakeRepository:
        async def slug_exists(self, _: str) -> bool:
            return False

        async def create(self, **values) -> QrGeneration:
            now = datetime.now(timezone.utc)
            return QrGeneration(
                id="generation-id",
                user_id=values["user_id"],
                payload_type=values["payload_type"],
                label=values["label"],
                payload_preview=values["payload_preview"],
                payload_hash=values["payload_hash"],
                payload_details=values["payload_details"],
                files=values["files"],
                slug=values["slug"],
                dynamic_url=values["dynamic_url"],
                destination_url=values["destination_url"],
                encrypted_destination=values["encrypted_destination"],
                access_mode=values["access_mode"],
                access_password_hash=values["access_password_hash"],
                allowed_emails=values["allowed_emails"],
                is_active=True,
                is_favorite=False,
                expires_at=values["expires_at"],
                max_scans=values["max_scans"],
                scan_count=0,
                design=values["design"],
                logo_file=values["logo_file"],
                created_at=now,
                updated_at=now,
            )

    renderer = FakeRenderer()
    vault_settings = Settings(_env_file=None, jwt_secret="x" * 32)
    service = QrGeneratorService(
        repository=FakeRepository(),
        renderer=renderer,
        storage=LocalQrStorage(tmp_path),
        payload_builder=QrPayloadBuilder(),
        redirect_base_url="http://192.168.1.10:8000",
        frontend_base_url="http://127.0.0.1:5173",
        cipher=VaultCipher("x" * 32),
        grants=VaultGrantService(vault_settings),
        passwords=PasswordService(),
    )

    generation = asyncio.run(
        service.generate(
            "user-id",
            UrlQrRequest(type="url", url="https://example.com/destination", max_scans=5),
        )
    )

    assert generation.destination_url == "https://example.com/destination"
    assert generation.dynamic_url is not None
    assert generation.dynamic_url.startswith("http://192.168.1.10:8000/r/")
    assert renderer.payload == generation.dynamic_url
    assert generation.max_scans == 5

    direct_generation = asyncio.run(
        service.generate(
            "user-id",
            UrlQrRequest(type="url", url="https://example.com/direct", dynamic=False),
        )
    )

    assert direct_generation.destination_url == "https://example.com/direct"
    assert direct_generation.dynamic_url is None
    assert renderer.payload == "https://example.com/direct"


def test_qr_status_reflects_pause_expiry_and_scan_limit() -> None:
    now = datetime.now(timezone.utc)
    base = dict(
        id="id",
        user_id="user",
        payload_type="url",
        label=None,
        payload_preview="https://example.com",
        payload_hash="hash",
        payload_details={},
        files={},
        slug="slug",
        dynamic_url="http://localhost:8000/r/slug",
        destination_url="https://example.com",
        encrypted_destination=None,
        access_mode="public",
        access_password_hash=None,
        allowed_emails=[],
        is_favorite=False,
        design={},
        logo_file=None,
        created_at=now,
        updated_at=now,
    )

    assert QrGeneration(**base, is_active=False, expires_at=None, max_scans=None, scan_count=0).status == "paused"
    assert QrGeneration(**base, is_active=True, expires_at=now - timedelta(seconds=1), max_scans=None, scan_count=0).status == "expired"
    assert QrGeneration(**base, is_active=True, expires_at=None, max_scans=2, scan_count=2).status == "scan_limit_reached"
    assert QrGeneration(**base, is_active=True, expires_at=None, max_scans=2, scan_count=1).status == "active"


def test_brandcraft_renders_persistable_design_and_validated_logo() -> None:
    logo_image = Image.new("RGBA", (80, 80), "#7C3AED")
    logo_buffer = BytesIO()
    logo_image.save(logo_buffer, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(logo_buffer.getvalue()).decode("ascii")
    logo = QrRenderer.normalize_logo(data_url)
    design = QrDesign(
        foreground_color="#111827",
        background_color="#FFFFFF",
        gradient_enabled=True,
        gradient_color="#7C3AED",
        gradient_direction="diagonal",
        module_style="dots",
        frame_style="rounded",
        frame_text="SCAN ME",
        error_correction="H",
        size=512,
        margin=4,
    )

    rendered = QrRenderer().render_all("https://example.com/brandcraft", design, logo)

    with Image.open(BytesIO(rendered["png"])) as png:
        assert png.size == (512, 512)
    assert b"<circle" in rendered["svg"]
    assert b"SCAN ME" in rendered["svg"]
    assert b"data:image/png;base64" in rendered["svg"]
    assert rendered["pdf"].startswith(b"%PDF")


def test_brandcraft_rejects_unscannable_low_contrast_colors() -> None:
    try:
        QrDesignRequest(foreground_color="#FFFFFF", background_color="#FFFFFF")
    except ValidationError:
        return
    raise AssertionError("Low contrast design should be rejected")
