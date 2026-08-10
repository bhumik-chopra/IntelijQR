from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import OptionalCurrentUser, get_vault_access_service
from app.schemas.vault import VaultGrantResponse, VaultPolicyResponse, VaultUnlockRequest
from app.services.qr.vault_access_service import VaultAccessService


router = APIRouter()


@router.get("/{slug}", response_model=VaultPolicyResponse)
async def vault_policy(
    slug: str,
    service: Annotated[VaultAccessService, Depends(get_vault_access_service)],
) -> VaultPolicyResponse:
    generation = await service.policy(slug)
    return VaultPolicyResponse(
        slug=slug,
        label=generation.label or "Protected QR destination",
        access_mode=generation.access_mode,
        requires_authentication=generation.access_mode in {"authenticated", "private"},
        status=generation.status,
    )


@router.post("/{slug}/unlock", response_model=VaultGrantResponse)
async def unlock_vault(
    slug: str,
    payload: VaultUnlockRequest,
    current_user: OptionalCurrentUser,
    service: Annotated[VaultAccessService, Depends(get_vault_access_service)],
) -> VaultGrantResponse:
    redirect_url, expires_at = await service.unlock(slug, payload.password, current_user)
    return VaultGrantResponse(redirect_url=redirect_url, expires_at=expires_at)
