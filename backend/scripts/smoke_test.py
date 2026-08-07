"""Run a disposable end-to-end authentication smoke test against local MongoDB."""

import os


TEST_DATABASE = "intelliqr_backend_smoke_test"
os.environ["INTELLIQR_MONGODB_DATABASE"] = TEST_DATABASE
os.environ["INTELLIQR_MONGODB_REQUIRED_ON_STARTUP"] = "true"

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.core.config import get_settings
from app.main import app


def main() -> None:
    settings = get_settings()
    if settings.mongodb_database != TEST_DATABASE:
        raise RuntimeError("Refusing to run against a non-test database")

    try:
        migration_client = MongoClient(settings.mongodb_uri)
        migration_client[TEST_DATABASE].users.create_index(
            "username", unique=True, name="uq_users_username"
        )
        migration_client.close()

        with TestClient(app) as client:
            index_client = MongoClient(settings.mongodb_uri)
            user_indexes = index_client[TEST_DATABASE].users.index_information()
            index_client.close()
            assert "uq_users_username" not in user_indexes

            registration = client.post(
                "/api/v1/auth/register",
                json={
                    "name": "Smoke Test User",
                    "email": "smoke-test@example.com",
                    "password": "local-smoke-password",
                },
            )
            assert registration.status_code == 201, registration.text
            access_token = registration.json()["access_token"]

            inspection_client = MongoClient(settings.mongodb_uri)
            stored_user = inspection_client[TEST_DATABASE].users.find_one(
                {"email": "smoke-test@example.com"}
            )
            inspection_client.close()
            assert stored_user is not None
            assert stored_user["name"] == "Smoke Test User"
            assert stored_user["password_hash"].startswith("$2b$")
            assert stored_user["created_at"] is not None
            assert stored_user["updated_at"] is not None
            assert "password" not in stored_user

            profile = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert profile.status_code == 200, profile.text

            refreshed = client.post("/api/v1/auth/refresh")
            assert refreshed.status_code == 200, refreshed.text
            rotated_refresh_token = client.cookies.get(settings.refresh_cookie_name)
            assert rotated_refresh_token

            logout = client.post("/api/v1/auth/logout")
            assert logout.status_code == 200, logout.text

            rejected = client.post(
                "/api/v1/auth/refresh",
                headers={"Cookie": f"{settings.refresh_cookie_name}={rotated_refresh_token}"},
            )
            assert rejected.status_code == 401, rejected.text

            login = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "SMOKE-TEST@example.com",
                    "password": "local-smoke-password",
                },
            )
            assert login.status_code == 200, login.text

            invalid_login = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "smoke-test@example.com",
                    "password": "incorrect-password",
                },
            )
            assert invalid_login.status_code == 401, invalid_login.text

        print("Authentication smoke test passed")
    finally:
        cleanup_client = MongoClient(settings.mongodb_uri)
        cleanup_client.drop_database(TEST_DATABASE)
        cleanup_client.close()


if __name__ == "__main__":
    main()
