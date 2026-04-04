"""API key management endpoints.

All endpoints require the internal API key (X-Api-Key header).
Per-store keys generated here are intended for the future public /v1/ API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import database
from api.dependencies import require_internal_key
from api.services import api_key as api_key_service

router = APIRouter()


class GenerateKeyRequest(BaseModel):
    store_id: int


class RevokeKeyRequest(BaseModel):
    store_id: int


@router.post("/generate-key", dependencies=[Depends(require_internal_key)])
def generate_key(payload: GenerateKeyRequest, db: Session = Depends(database.get_db)):
    """Generate a new API key for a store.

    The raw key is returned exactly once — it cannot be recovered afterward.
    """
    store = db.query(database.Store).filter(database.Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found.")

    raw, hashed = api_key_service.generate()
    store.api_key_hash = hashed
    db.commit()

    return {
        "store_id": store.id,
        "api_key": raw,
        "warning": "Save this key — it will not be shown again.",
    }


@router.post("/revoke-key", dependencies=[Depends(require_internal_key)])
def revoke_key(payload: RevokeKeyRequest, db: Session = Depends(database.get_db)):
    """Revoke the API key for a store."""
    store = db.query(database.Store).filter(database.Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found.")

    store.api_key_hash = None
    db.commit()

    return {"store_id": store.id, "status": "revoked"}
