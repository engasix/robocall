from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from api.services.audio_stitcher import build_call_audio
from api.dependencies import require_internal_key
import database

router = APIRouter()


class ProcessOrderRequest(BaseModel):
    order_id: int
    customer_name: str
    store_id: int
    store_name: str
    order_amount: float
    language: str
    phone: str


@router.post("/process", dependencies=[Depends(require_internal_key)])
def process_order(payload: ProcessOrderRequest, db: Session = Depends(database.get_db)):
    build_call_audio(
        order_id=payload.order_id,
        customer_name=payload.customer_name,
        store_id=payload.store_id,
        store_name=payload.store_name,
        order_amount=payload.order_amount,
        language=payload.language,
    )

    # Hand off to scheduler — set next_retry_at to now so it gets picked up immediately
    order = db.query(database.Order).filter(database.Order.id == payload.order_id).first()
    if order:
        order.next_retry_at = datetime.now(timezone.utc)
        db.commit()

    return {"status": "scheduled"}
