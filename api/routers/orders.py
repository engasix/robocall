from fastapi import APIRouter
from pydantic import BaseModel
from api.services.audio_stitcher import build_call_audio

router = APIRouter()


class ProcessOrderRequest(BaseModel):
    order_id: int
    customer_name: str
    store_id: int
    store_name: str
    order_amount: float
    language: str
    phone: str


@router.post("/process")
def process_order(payload: ProcessOrderRequest):
    build_call_audio(
        order_id=payload.order_id,
        customer_name=payload.customer_name,
        store_id=payload.store_id,
        store_name=payload.store_name,
        order_amount=payload.order_amount,
        language=payload.language,
    )
    # TODO: trigger Twilio call (Phase 5)
    return {"status": "processing"}
