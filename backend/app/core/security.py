import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import Settings


class TokenValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TokenPayload:
    subject: str
    token_type: Literal["access", "refresh"]
    jti: str
    expires_at: datetime
    token_version: int
    role: str


class PasswordService:
    def __init__(self) -> None:
        self._hasher = PasswordHash((BcryptHasher(rounds=12),))
        self.dummy_hash = self._hasher.hash("intelliqr-dummy-password")

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._hasher.verify(password, password_hash)


class TokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_access_token(self, subject: str, role: str, token_version: int) -> tuple[str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self._settings.access_token_expire_minutes
        )
        return self._encode(subject, role, token_version, "access", expires_at), expires_at

    def create_refresh_token(
        self, subject: str, role: str, token_version: int
    ) -> tuple[str, str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._settings.refresh_token_expire_days
        )
        jti = secrets.token_urlsafe(24)
        token = self._encode(subject, role, token_version, "refresh", expires_at, jti)
        return token, jti, expires_at

    def decode(self, token: str, expected_type: Literal["access", "refresh"]) -> TokenPayload:
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
                options={"require": ["sub", "type", "jti", "exp", "iat", "ver"]},
            )
            if payload["type"] != expected_type:
                raise TokenValidationError("Unexpected token type")
            return TokenPayload(
                subject=str(payload["sub"]),
                token_type=expected_type,
                jti=str(payload["jti"]),
                expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc),
                token_version=int(payload["ver"]),
                role=str(payload.get("role", "user")),
            )
        except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise TokenValidationError("Invalid or expired token") from exc

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _encode(
        self,
        subject: str,
        role: str,
        token_version: int,
        token_type: Literal["access", "refresh"],
        expires_at: datetime,
        jti: str | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "role": role,
            "ver": token_version,
            "type": token_type,
            "jti": jti or secrets.token_urlsafe(16),
            "iat": now,
            "exp": expires_at,
            "iss": self._settings.jwt_issuer,
            "aud": self._settings.jwt_audience,
        }
        return jwt.encode(payload, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm)
