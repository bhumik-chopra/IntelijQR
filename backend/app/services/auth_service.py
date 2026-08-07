import hmac
import logging
import secrets
from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import PasswordService, TokenService, TokenValidationError
from app.models.user import User
from app.services.ports import SessionStore, UserStore


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    user: User
    access_token: str
    refresh_token: str
    access_expires_in: int


class AuthService:
    def __init__(
        self,
        users: UserStore,
        sessions: SessionStore,
        passwords: PasswordService,
        tokens: TokenService,
        settings: Settings,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._passwords = passwords
        self._tokens = tokens
        self._settings = settings

    async def register(self, name: str, email: str, password: str) -> AuthenticationResult:
        normalized_email = email.strip().lower()
        if await self._users.find_by_email(normalized_email):
            raise ConflictError("An account with this email already exists")
        user = await self._users.create(
            name.strip(), normalized_email, self._passwords.hash(password)
        )
        logger.info("User registered", extra={"user_id": user.id})
        return await self._issue_session(user)

    async def login(self, email: str, password: str) -> AuthenticationResult:
        user = await self._users.find_by_email(email.strip().lower())
        if user is None:
            self._passwords.verify(password, self._passwords.dummy_hash)
            raise AuthenticationError("Incorrect email or password")
        if not self._passwords.verify(password, user.password_hash):
            raise AuthenticationError("Incorrect email or password")
        if user.status != "active":
            raise AuthenticationError("Account is not active")
        await self._users.record_login(user.id)
        logger.info("User authenticated", extra={"user_id": user.id})
        return await self._issue_session(user)

    async def refresh(self, refresh_token: str) -> AuthenticationResult:
        try:
            payload = self._tokens.decode(refresh_token, "refresh")
        except TokenValidationError as exc:
            raise AuthenticationError("Invalid refresh token") from exc
        token_hash = self._tokens.digest(refresh_token)
        session = await self._sessions.consume(payload.jti, token_hash)
        if session is None:
            previous_session = await self._sessions.find_by_jti(payload.jti)
            if previous_session is not None:
                await self._sessions.revoke_family(previous_session.token_family_id)
                logger.warning(
                    "Refresh token reuse detected; token family revoked",
                    extra={"user_id": payload.subject},
                )
            raise AuthenticationError("Refresh session is invalid")
        if not hmac.compare_digest(session.refresh_token_hash, token_hash):
            await self._sessions.revoke_family(session.token_family_id)
            raise AuthenticationError("Refresh session is invalid")
        user = await self._users.find_by_id(payload.subject)
        if user is None or user.status != "active" or user.token_version != payload.token_version:
            raise AuthenticationError("Refresh session is invalid")
        replacement = await self._issue_session(user, family_id=session.token_family_id)
        new_payload = self._tokens.decode(replacement.refresh_token, "refresh")
        new_session = await self._sessions.find_by_jti(new_payload.jti)
        if new_session is not None:
            await self._sessions.mark_replacement(session.id, new_session.id)
        logger.info("Refresh token rotated", extra={"user_id": user.id})
        return replacement

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = self._tokens.decode(refresh_token, "refresh")
        except TokenValidationError:
            return
        await self._sessions.revoke_by_jti(payload.jti)
        logger.info("User session revoked", extra={"user_id": payload.subject})

    async def _issue_session(
        self, user: User, family_id: str | None = None
    ) -> AuthenticationResult:
        access_token, _ = self._tokens.create_access_token(
            user.id, user.role, user.token_version
        )
        refresh_token, refresh_jti, refresh_expires_at = self._tokens.create_refresh_token(
            user.id, user.role, user.token_version
        )
        await self._sessions.create(
            user_id=user.id,
            token_hash=self._tokens.digest(refresh_token),
            refresh_jti=refresh_jti,
            family_id=family_id or secrets.token_urlsafe(24),
            expires_at=refresh_expires_at,
        )
        return AuthenticationResult(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_in=self._settings.access_token_expire_minutes * 60,
        )
