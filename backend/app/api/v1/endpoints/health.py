from fastapi import APIRouter, HTTPException, status

from app.db.mongodb import mongo


router = APIRouter()


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> dict[str, str]:
    if not await mongo.ping():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is unavailable",
        )
    return {"status": "ready", "database": "connected"}

