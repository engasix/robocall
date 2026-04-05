"""Shared order processing logic used by both the demo and the public API."""

from datetime import datetime, timezone
import database
from api.services.audio_stitcher import build_call_audio


def build_and_schedule(order_id: int, customer_name: str, store_id: int,
                       store_name: str, order_amount: float, language: str) -> None:
    """Build call audio then hand off to scheduler by setting next_retry_at = now.

    Runs as a FastAPI BackgroundTask — called directly by both the demo and
    the public /v1/orders endpoint, no inter-service HTTP call needed.
    """
    build_call_audio(
        order_id=order_id,
        customer_name=customer_name,
        store_id=store_id,
        store_name=store_name,
        order_amount=order_amount,
        language=language,
    )
    db = database.SessionLocal()
    try:
        order = db.query(database.Order).filter(database.Order.id == order_id).first()
        if order:
            order.next_retry_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
