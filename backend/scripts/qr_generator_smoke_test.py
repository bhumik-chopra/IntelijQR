"""Exercise all QR payloads and downloads against disposable local storage and MongoDB."""

import os
import shutil
import tempfile
from pathlib import Path


TEST_DATABASE = "intelliqr_qr_generator_smoke_test"
TEST_STORAGE = Path(tempfile.gettempdir()) / "intelliqr_qr_generator_smoke_test"
os.environ["INTELLIQR_MONGODB_DATABASE"] = TEST_DATABASE
os.environ["INTELLIQR_MONGODB_REQUIRED_ON_STARTUP"] = "true"
os.environ["INTELLIQR_QR_STORAGE_DIRECTORY"] = str(TEST_STORAGE)

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.core.config import get_settings
from app.main import app


PAYLOADS = [
    {"type": "url", "label": "Website", "url": "https://example.com"},
    {"type": "text", "label": "Message", "text": "Hello from IntelliQR"},
    {
        "type": "email",
        "email": "hello@example.com",
        "subject": "IntelliQR",
        "body": "Generated locally",
    },
    {"type": "phone", "phone": "+91 98765 43210"},
    {
        "type": "wifi",
        "ssid": "IntelliQR Local",
        "password": "local-secret",
        "security": "WPA",
    },
    {
        "type": "contact",
        "full_name": "IntelliQR User",
        "organization": "IntelliQR",
        "phone": "+91 98765 43210",
        "email": "user@example.com",
        "url": "https://example.com",
    },
    {"type": "location", "latitude": 19.076, "longitude": 72.8777, "name": "Mumbai"},
]


def main() -> None:
    settings = get_settings()
    if settings.mongodb_database != TEST_DATABASE or settings.qr_storage_directory != TEST_STORAGE:
        raise RuntimeError("Refusing to run QR smoke test outside disposable resources")

    try:
        with TestClient(app) as client:
            registration = client.post(
                "/api/v1/auth/register",
                json={
                    "name": "QR Smoke User",
                    "email": "qr-smoke@example.com",
                    "password": "local-smoke-password",
                },
            )
            assert registration.status_code == 201, registration.text
            authorization = {"Authorization": f"Bearer {registration.json()['access_token']}"}

            generations = []
            for payload in PAYLOADS:
                response = client.post(
                    "/api/v1/qr/generations",
                    json=payload,
                    headers=authorization,
                )
                assert response.status_code == 201, response.text
                generations.append(response.json())

            first_id = generations[0]["id"]
            signatures = {"png": b"\x89PNG", "svg": b"<svg", "pdf": b"%PDF"}
            media_types = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}
            for file_format in ("png", "svg", "pdf"):
                download = client.get(
                    f"/api/v1/qr/generations/{first_id}/files/{file_format}",
                    headers=authorization,
                )
                assert download.status_code == 200, download.text
                assert download.headers["content-type"].startswith(media_types[file_format])
                assert download.content.startswith(signatures[file_format])

            history = client.get("/api/v1/qr/generations", headers=authorization)
            assert history.status_code == 200, history.text
            assert len(history.json()["items"]) == len(PAYLOADS)

            inspection = MongoClient(settings.mongodb_uri)
            collection = inspection[TEST_DATABASE].qr_generations
            assert collection.count_documents({}) == len(PAYLOADS)
            wifi_record = collection.find_one({"payload_type": "wifi"})
            assert wifi_record is not None
            assert wifi_record["payload_details"]["password"] == "***"
            assert set(wifi_record["files"]) == {"png", "svg", "pdf"}
            inspection.close()

        print("QR generator smoke test passed")
    finally:
        cleanup = MongoClient(settings.mongodb_uri)
        cleanup.drop_database(TEST_DATABASE)
        cleanup.close()
        if TEST_STORAGE == Path(tempfile.gettempdir()) / "intelliqr_qr_generator_smoke_test":
            shutil.rmtree(TEST_STORAGE, ignore_errors=True)


if __name__ == "__main__":
    main()
