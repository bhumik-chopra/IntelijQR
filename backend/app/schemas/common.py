from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class PaginationFields(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool
