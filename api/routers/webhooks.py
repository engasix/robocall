from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse
from typing import Optional
from twilio.request_validator import RequestValidator
import config
from database import SessionLocal, Order

router = APIRouter()

_twilio_validator = RequestValidator(config.TWILIO_AUTH_TOKEN)


async def _validate_twilio_request(request: Request) -> None:
    """Raise 403 if the request did not come from Twilio.

    Uses config.API_URL as the base — Nginx rewrites the host so request.url
    reflects the internal address, not the public URL Twilio signed against.
    Reads all form fields so the signature covers the full POST body.
    """
    signature = request.headers.get("X-Twilio-Signature", "")
    url = config.API_URL.rstrip("/") + str(request.url.path)
    form_data = dict(await request.form())
    if not _twilio_validator.validate(url, form_data, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature.",
        )


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
async def handle_keypress(request: Request, order_id: int, Digits: Optional[str] = Form(default=None)):
    """Handle customer keypress after the call audio plays.

    1 → confirmed
    2 → cancelled
    anything else / no input → no_response
    """
    await _validate_twilio_request(request)

    if Digits == "1":
        order_status = "confirmed"
        audio_key = "confirmed"
    elif Digits == "2":
        order_status = "cancelled"
        audio_key = "cancelled"
    else:
        order_status = "no_response"
        audio_key = "no_response"

    db = SessionLocal()
    try:
        language = _get_order_language(order_id, db)
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = order_status
            db.commit()
    finally:
        db.close()

    audio_url = f"{config.API_URL}/audio/static/{language}/{audio_key}.mp3"
    return Response(content=_twiml(audio_url), media_type="application/xml")


@router.post("/call-status/{order_id}")
async def handle_call_status(
    request: Request,
    order_id: int,
    CallStatus: Optional[str] = Form(default=None),
):
    """Handle Twilio call status callbacks.

    If the call never connected (busy, failed, no-answer), mark order as no_response.
    """
    await _validate_twilio_request(request)

    if CallStatus in ("busy", "failed", "no-answer", "canceled"):
        _update_order_status(order_id, "no_response")

    return {"received": True}
