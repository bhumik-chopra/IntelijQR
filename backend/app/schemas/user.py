from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import User


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    role: str
    status: str
    created_at: datetime
    last_login_at: datetime | None
    locale: str = "en"

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls.model_validate(user)
