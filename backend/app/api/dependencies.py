from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import PasswordService, TokenService, TokenValidationError
from app.db.mongodb import mongo
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_user_repository() -> UserRepository:
    return UserRepository(mongo.database)


def get_session_repository() -> SessionRepository:
    return SessionRepository(mongo.database)


def get_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> TokenService:
    return TokenService(settings)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(users, sessions, PasswordService(), tokens, settings)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    try:
        payload = tokens.decode(token, "access")
    except TokenValidationError as exc:
        raise AuthenticationError("Could not validate credentials") from exc
    user = await users.find_by_id(payload.subject)
    if user is None or user.status != "active" or user.token_version != payload.token_version:
        raise AuthenticationError("Could not validate credentials")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

