from fastapi import APIRouter

from app.api.v1.endpoints import admin, analytics, auth, bulk, dashboard, health, meta, notifications, qr_generations, qr_scans, shares, users, vault


api_router = APIRouter()
api_router.include_router(meta.router, prefix="/meta", tags=["API discovery"])
api_router.include_router(admin.router, prefix="/admin", tags=["administration"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    qr_generations.router,
    prefix="/qr/generations",
    tags=["QR generation"],
)
api_router.include_router(qr_scans.router, prefix="/qr/scans", tags=["QR scanning"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(vault.router, prefix="/qr/access", tags=["SecureVault access"])
api_router.include_router(bulk.router, prefix="/bulk", tags=["BulkForge"])
api_router.include_router(shares.router, prefix="/shares", tags=["ShareVault"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["personal dashboard"])
