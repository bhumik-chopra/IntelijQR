from pydantic import BaseModel


class ApiAuthenticationInfo(BaseModel):
    scheme: str
    header: str
    refresh_transport: str


class ApiLimits(BaseModel):
    list_page_size_max: int
    scan_image_bytes_max: int
    bulk_file_bytes_max: int
    bulk_rows_max: int
    share_file_bytes_max: int


class ApiMetaResponse(BaseModel):
    name: str
    version: str
    status: str
    documentation: dict[str, str]
    authentication: ApiAuthenticationInfo
    resources: dict[str, list[str]]
    limits: ApiLimits
