from fastapi import APIRouter, Form, Response
from fastapi.responses import PlainTextResponse
from typing import Optional
import config
from database import SessionLocal, Order

router = APIRouter()


def _twiml(audio_url: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""


def _get_order_language(order_id: int, db) -> str:
    order = db.query(Order).filter(Order.id == order_id).first()
    return order.store.language if order else "english"


def _update_order_status(order_id: int, status: str) -> None:
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
    finally:
        db.close()


@router.post("/keypress/{order_id}", response_class=PlainTextResponse)
def handle_keypress(order_id: int, Digits: Optional[str] = Form(default=None)):
    """Handle customer keypress after the call audio plays.

    1 → confirmed
    2 → cancelled
    anything else / no input → no_response
    """
    if Digits == "1":
        status = "confirmed"
        audio_key = "confirmed"
    elif Digits == "2":
        status = "cancelled"
        audio_key = "cancelled"
    else:
        status = "no_response"
        audio_key = "no_response"

    db = SessionLocal()
    try:
        language = _get_order_language(order_id, db)
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
    finally:
        db.close()

    audio_url = f"{config.API_URL}/audio/static/{language}/{audio_key}.mp3"
    return Response(content=_twiml(audio_url), media_type="application/xml")


@router.post("/call-status/{order_id}")
def handle_call_status(
    order_id: int,
    CallStatus: Optional[str] = Form(default=None),
):
    """Handle Twilio call status callbacks.

    If the call never connected (busy, failed, no-answer), mark order as no_response.
    """
    if CallStatus in ("busy", "failed", "no-answer", "canceled"):
        _update_order_status(order_id, "no_response")

    return {"received": True}
