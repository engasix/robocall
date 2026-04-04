from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.services.audio_stitcher import build_call_audio
from api.services.call_service import trigger_call
from api.dependencies import require_internal_key

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
def process_order(payload: ProcessOrderRequest):
    build_call_audio(
        order_id=payload.order_id,
        customer_name=payload.customer_name,
        store_id=payload.store_id,
        store_name=payload.store_name,
        order_amount=payload.order_amount,
        language=payload.language,
    )
    call_sid = trigger_call(order_id=payload.order_id, phone=payload.phone)
    return {"status": "calling", "call_sid": call_sid}
