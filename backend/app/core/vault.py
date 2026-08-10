import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings
from app.core.security import TokenValidationError


class VaultCipher:
    def __init__(self, secret: str) -> None:
        self._cipher = AESGCM(hashlib.sha256(f"intelliqr-vault:{secret}".encode()).digest())

    def encrypt(self, value: str) -> str:
        nonce = secrets.token_bytes(12)
        encrypted = self._cipher.encrypt(nonce, value.encode("utf-8"), b"intelliqr-destination-v1")
        return base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")

    def decrypt(self, value: str) -> str:
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
        return self._cipher.decrypt(raw[:12], raw[12:], b"intelliqr-destination-v1").decode("utf-8")

    def encrypt_bytes(self, value: bytes) -> bytes:
        nonce = secrets.token_bytes(12)
        return nonce + self._cipher.encrypt(nonce, value, b"intelliqr-file-v1")

    def decrypt_bytes(self, value: bytes) -> bytes:
        return self._cipher.decrypt(value[:12], value[12:], b"intelliqr-file-v1")


class VaultGrantService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self, slug: str, subject: str, purpose: str = "qr") -> tuple[str, datetime]:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self._settings.vault_grant_expire_minutes)
        token = jwt.encode({
            "sub": subject, "slug": slug, "purpose": purpose, "type": "vault_grant", "jti": secrets.token_urlsafe(16),
            "iat": now, "exp": expires, "iss": self._settings.jwt_issuer, "aud": "intelliqr-vault",
        }, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm)
        return token, expires

    def validate(self, token: str, slug: str, purpose: str = "qr") -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._settings.jwt_secret, algorithms=[self._settings.jwt_algorithm], audience="intelliqr-vault", issuer=self._settings.jwt_issuer)
            if payload.get("type") != "vault_grant" or payload.get("slug") != slug or payload.get("purpose") != purpose:
                raise TokenValidationError("Invalid vault grant")
            return payload
        except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise TokenValidationError("Invalid or expired vault grant") from exc
