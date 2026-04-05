from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse
from typing import Optional
from twilio.request_validator import RequestValidator
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta
import config
from database import SessionLocal, Order
from api.services import store_notify

router = APIRouter()

_twilio_validator = RequestValidator(config.TWILIO_AUTH_TOKEN)

# Delay in minutes for each retry attempt, indexed by current retry_count
RETRY_DELAYS = [30, 60]
MAX_RETRIES = 2

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


def _compute_next_retry_at(store, retry_count: int) -> datetime:
    """Calculate next_retry_at in UTC, clamped to the store's calling window.

    If the candidate time falls outside the store's window, it is pushed
    forward to the next window open (same day or next day).
    Always returns a timezone-aware UTC datetime.
    """
    delay_minutes = RETRY_DELAYS[retry_count]
    tz = ZoneInfo(store.timezone)

    now_utc = datetime.now(timezone.utc)
    candidate_utc = now_utc + timedelta(minutes=delay_minutes)
    candidate_local = candidate_utc.astimezone(tz)
    candidate_time = candidate_local.time()

    window_start = store.call_window_start
    window_end = store.call_window_end

    if window_start <= candidate_time <= window_end:
        return candidate_utc

    # Clamp to next window open
    if candidate_time < window_start:
        next_open = candidate_local.replace(
            hour=window_start.hour, minute=window_start.minute, second=0, microsecond=0
        )
    else:  # past window_end
        next_day = candidate_local + timedelta(days=1)
        next_open = next_day.replace(
            hour=window_start.hour, minute=window_start.minute, second=0, microsecond=0
        )

    return next_open.astimezone(timezone.utc)


def _schedule_retry_or_close(order, db, background_tasks: BackgroundTasks) -> None:
    """After a failed call attempt, either schedule the next retry or close the order."""
    if order.retry_count >= MAX_RETRIES:
        order.status = "no_response"
        order.next_retry_at = None
        db.commit()
        _maybe_notify(order, background_tasks)
    else:
        order.next_retry_at = _compute_next_retry_at(order.store, order.retry_count)
        order.retry_count += 1
        db.commit()


def _maybe_notify(order, background_tasks: BackgroundTasks) -> None:
    """Fire store callback if a webhook_url is registered."""
    if order.store.webhook_url:
        background_tasks.add_task(
            store_notify.notify,
            webhook_url=order.store.webhook_url,
            order_id=order.id,
            order_number=order.order_number,
            status=order.status,
            customer_name=order.customer_name,
            phone=order.phone,
            order_amount=float(order.order_amount),
        )


def _twiml(audio_url: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""


def _get_order_language(order_id: int, db) -> str:
    order = db.query(Order).filter(Order.id == order_id).first()
    return order.store.language if order else "english"


@router.post("/keypress/{order_id}", response_class=PlainTextResponse)
async def handle_keypress(request: Request, background_tasks: BackgroundTasks, order_id: int, Digits: Optional[str] = Form(default=None)):
    """Handle customer keypress after the call audio plays.

    1 → confirmed
    2 → cancelled
    no input / other → schedule retry or close
    """
    await _validate_twilio_request(request)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        language = order.store.language if order else "english"

        if Digits == "1":
            if order:
                order.status = "confirmed"
                order.next_retry_at = None
                db.commit()
                _maybe_notify(order, background_tasks)
            audio_key = "confirmed"
        elif Digits == "2":
            if order:
                order.status = "cancelled"
                order.next_retry_at = None
                db.commit()
                _maybe_notify(order, background_tasks)
            audio_key = "cancelled"
        else:
            if order:
                _schedule_retry_or_close(order, db, background_tasks)
            audio_key = "no_response"
    finally:
        db.close()

    audio_url = f"{config.API_URL}/audio/static/{language}/{audio_key}.mp3"
    return Response(content=_twiml(audio_url), media_type="application/xml")


@router.post("/call-status/{order_id}")
async def handle_call_status(
    request: Request,
    background_tasks: BackgroundTasks,
    order_id: int,
    CallStatus: Optional[str] = Form(default=None),
):
    """Handle Twilio call status callbacks.

    If the call never connected (busy, failed, no-answer), schedule a retry
    or close the order if max retries exhausted.
    """
    await _validate_twilio_request(request)

    if CallStatus in ("busy", "failed", "no-answer", "canceled"):
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order and order.status == "pending":
                _schedule_retry_or_close(order, db, background_tasks)
        finally:
            db.close()

    return {"received": True}
