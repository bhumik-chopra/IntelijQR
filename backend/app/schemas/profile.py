from pydantic import BaseModel, Field, field_validator
from typing import Literal


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2 or any(not character.isprintable() for character in cleaned):
            raise ValueError("Enter a valid display name")
        return cleaned


class LocaleUpdateRequest(BaseModel):
    locale: Literal["en", "hi", "gu"]


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("current_password", "new_password")
    @classmethod
    def bcrypt_size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72: raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value
