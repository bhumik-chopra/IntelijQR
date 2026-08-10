import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest


def test_registration_normalizes_name_whitespace() -> None:
    payload = RegisterRequest(
        name="  IntelliQR   User  ",
        email="USER@example.com",
        password="password123",
    )

    assert str(payload.email) == "USER@example.com"
    assert payload.name == "IntelliQR User"


def test_registration_rejects_oversized_bcrypt_password() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="IntelliQR User",
            email="user@example.com",
            password="é" * 40,
        )


def test_registration_accepts_supported_locale_and_rejects_unknown_locale() -> None:
    assert RegisterRequest(name="User Name", email="user@example.com", password="password123", locale="hi").locale == "hi"
    with pytest.raises(ValidationError):
        RegisterRequest(name="User Name", email="user@example.com", password="password123", locale="fr")
