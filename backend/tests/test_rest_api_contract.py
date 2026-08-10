import asyncio

from app.api.v1.endpoints.meta import api_metadata
from app.core.config import Settings
from app.main import app


def test_openapi_exposes_versioned_bearer_contract() -> None:
    schema = app.openapi()

    assert schema["info"]["version"] == "1.0.0"
    assert schema["components"]["securitySchemes"]["HTTPBearer"] == {
        "type": "http",
        "description": "JWT access token returned by /api/v1/auth/login or /api/v1/auth/refresh",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    assert schema["paths"]["/api/v1/qr/generations"]["post"]["security"] == [
        {"HTTPBearer": []}
    ]
    assert "security" not in schema["paths"]["/api/v1/meta"]["get"]


def test_openapi_contains_every_milestone_nine_resource() -> None:
    paths = app.openapi()["paths"]
    expected_methods = {
        "/api/v1/auth/register": "post",
        "/api/v1/auth/login": "post",
        "/api/v1/auth/refresh": "post",
        "/api/v1/auth/logout": "post",
        "/api/v1/users/me": "get",
        "/api/v1/users/me/locale": "patch",
        "/api/v1/qr/generations": "post",
        "/api/v1/qr/generations/{generation_id}": "patch",
        "/api/v1/qr/scans/decode": "post",
        "/api/v1/qr/scans/analyze": "post",
        "/api/v1/analytics/overview": "get",
        "/api/v1/shares": "post",
        "/api/v1/bulk/jobs": "post",
        "/api/v1/admin/overview": "get",
        "/api/v1/admin/users": "get",
        "/api/v1/admin/users/{user_id}": "patch",
        "/api/v1/notifications": "get",
        "/api/v1/notifications/preferences": "get",
    }

    for path, method in expected_methods.items():
        assert method in paths[path], f"Missing {method.upper()} {path}"
    assert "delete" in paths["/api/v1/qr/generations/{generation_id}"]


def test_collection_contracts_support_bounded_offset_pagination() -> None:
    schema = app.openapi()
    collection_paths = [
        "/api/v1/qr/generations",
        "/api/v1/qr/scans",
        "/api/v1/bulk/jobs",
        "/api/v1/shares",
        "/api/v1/shares/{share_id}/downloads",
    ]

    for path in collection_paths:
        parameters = {item["name"]: item for item in schema["paths"][path]["get"]["parameters"]}
        assert parameters["limit"]["schema"]["maximum"] == 100
        assert parameters["offset"]["schema"]["minimum"] == 0

    for response_schema in (
        "QrGenerationListResponse",
        "QrScanListResponse",
        "BulkJobListResponse",
        "ShareFileListResponse",
        "ShareDownloadListResponse",
    ):
        required = set(schema["components"]["schemas"][response_schema]["required"])
        assert {"items", "total", "limit", "offset", "has_more"} <= required


def test_api_discovery_reports_local_limits_and_resources() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32, bulk_max_rows=125)
    result = asyncio.run(api_metadata(settings))

    assert result.version == "1.0.0"
    assert result.authentication.scheme == "Bearer JWT"
    assert result.limits.bulk_rows_max == 125
    assert {"authentication", "qr", "scanning", "analytics", "files", "bulk", "administration", "notifications"} == set(result.resources)
