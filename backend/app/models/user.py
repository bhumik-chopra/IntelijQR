from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class User:
    id: str
    name: str
    email: str
    password_hash: str
    role: Literal["user", "admin"]
    status: Literal["active", "disabled"]
    token_version: int
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    locale: Literal["en", "hi", "gu"] = "en"
