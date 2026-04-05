"""API key management endpoints — admin only.

Protected by ADMIN_KEY from config (.env).
Used to generate and revoke per-store API keys for the public /v1/ API.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import config
import database
from api.services import api_key as api_key_service

router = APIRouter()


def require_admin_key(x_api_key: str = Header(...)) -> None:
    if not config.ADMIN_KEY:
        raise HTTPException(status_code=500, detail="Server misconfiguration: ADMIN_KEY not set.")
    if x_api_key != config.ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key.")


class GenerateKeyRequest(BaseModel):
    store_id: int


class RevokeKeyRequest(BaseModel):
    store_id: int


@router.post("/generate-key", dependencies=[Depends(require_admin_key)])
def generate_key(payload: GenerateKeyRequest, db: Session = Depends(database.get_db)):
    store = db.query(database.Store).filter(database.Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found.")

    raw, hashed = api_key_service.generate()
    store.api_key_hash = hashed
    db.commit()

    return {
        "status": True,
        "data": {
            "store_id": store.id,
            "api_key": raw,
            "warning": "Save this key — it will not be shown again.",
        }
    }


@router.post("/revoke-key", dependencies=[Depends(require_admin_key)])
def revoke_key(payload: RevokeKeyRequest, db: Session = Depends(database.get_db)):
    store = db.query(database.Store).filter(database.Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found.")

    store.api_key_hash = None
    db.commit()

    return {"status": True, "data": {"store_id": store.id, "revoked": True}}
