from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Session:
    id: str
    user_id: str
    refresh_token_hash: str
    refresh_jti: str
    token_family_id: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    replaced_by_session_id: str | None = None

