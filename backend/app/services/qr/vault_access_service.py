from app.core.exceptions import AuthenticationError, AuthorizationError, GoneError, NotFoundError
from app.core.security import PasswordService
from app.core.vault import VaultGrantService
from app.models.user import User
from app.repositories.qr_generation_repository import QrGenerationRepository


class VaultAccessService:
    def __init__(self, repository: QrGenerationRepository, passwords: PasswordService, grants: VaultGrantService, redirect_base_url: str) -> None:
        self._repository = repository
        self._passwords = passwords
        self._grants = grants
        self._redirect_base_url = redirect_base_url.rstrip("/")

    async def policy(self, slug: str):
        generation = await self._repository.find_by_slug(slug)
        if generation is None:
            raise NotFoundError("Protected QR code was not found")
        return generation

    async def unlock(self, slug: str, password: str | None, user: User | None) -> tuple[str, object]:
        generation = await self.policy(slug)
        if generation.status != "active":
            raise GoneError("This QR code is inactive, expired, or has reached its scan limit")
        if generation.access_mode == "password":
            if not password or not generation.access_password_hash or not self._passwords.verify(password, generation.access_password_hash):
                raise AuthorizationError("The SecureVault password is incorrect")
        elif generation.access_mode in {"authenticated", "private"}:
            if user is None:
                raise AuthenticationError("Sign in to access this protected QR code")
            if generation.access_mode == "private" and user.email.lower() not in generation.allowed_emails:
                raise AuthorizationError("Your account is not allowed to access this private QR code")
        token, expires_at = self._grants.create(slug, user.id if user else "password-holder")
        return f"{self._redirect_base_url}/r/{slug}?grant={token}", expires_at
