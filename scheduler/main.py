"""
Scheduler — Retry failed calls within each store's calling window.

Polls the orders table every 60 seconds and retries any pending order
whose next_retry_at has passed.

Usage:
    uv run -m scheduler.main
"""

import time
import logging
from datetime import datetime, timezone
from database import SessionLocal, Order
from api.services.call_service import trigger_call

logging.basicConfig(level=logging.INFO, format="[scheduler] %(message)s")
log = logging.getLogger(__name__)

POLL_INTERVAL = 60  # seconds
BATCH_SIZE = 20     # max calls per poll cycle — adjust based on telephony provider limits


def _process_retries() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        orders = (
            db.query(Order)
            .filter(
                Order.status == "pending",
                Order.next_retry_at.isnot(None),
                Order.next_retry_at <= now,
            )
            .limit(BATCH_SIZE)
            .all()
        )

        if not orders:
            return

        log.info(f"{len(orders)} order(s) ready for retry.")

        for order in orders:
            try:
                # Increment call_attempts and clear next_retry_at before triggering
                # to prevent double-firing if scheduler polls again before webhook updates.
                order.call_attempts += 1
                order.next_retry_at = None
                db.commit()

                trigger_call(order_id=order.id, phone=order.phone)
                log.info(f"Call triggered for order {order.id} (attempt {order.call_attempts})")
            except Exception as e:
                log.error(f"Failed to trigger retry for order {order.id}: {e}")

    finally:
        db.close()


def run() -> None:
    log.info("Starting. Polling every 60 seconds.")
    while True:
        try:
            _process_retries()
        except Exception as e:
            log.error(f"Unexpected error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
