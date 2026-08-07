from app.core.config import Settings
from app.core.security import PasswordService, TokenService, TokenValidationError


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret="a-test-secret-that-is-longer-than-thirty-two-characters",
    )


def test_password_hash_and_verification() -> None:
    service = PasswordService()
    password_hash = service.hash("strong-password")

    assert password_hash != "strong-password"
    assert password_hash.startswith("$2b$")
    assert service.verify("strong-password", password_hash)
    assert not service.verify("wrong-password", password_hash)


def test_access_token_round_trip() -> None:
    service = TokenService(make_settings())
    token, _ = service.create_access_token("user-id", "user", 1)
    payload = service.decode(token, "access")

    assert payload.subject == "user-id"
    assert payload.token_type == "access"
    assert payload.token_version == 1


def test_rejects_wrong_token_type() -> None:
    service = TokenService(make_settings())
    token, _, _ = service.create_refresh_token("user-id", "user", 1)

    try:
        service.decode(token, "access")
    except TokenValidationError:
        pass
    else:
        raise AssertionError("Refresh token was accepted as an access token")
