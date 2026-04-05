"""Fire-and-forget outgoing webhook to a store's registered callback URL."""

import httpx


def notify(webhook_url: str, order_id: int, status: str,
           customer_name: str, phone: str, order_amount: float) -> None:
    """POST order status update to the store's callback URL.

    Runs as a FastAPI BackgroundTask — failures are logged but never
    propagated back to Twilio or the caller.
    """
    try:
        httpx.post(
            webhook_url,
            json={
                "order_id": order_id,
                "status": status,
                "customer_name": customer_name,
                "phone": phone,
                "order_amount": order_amount,
            },
            timeout=10.0,
        )
    except Exception as e:
        print(f"[store_notify] Failed to notify store for order {order_id}: {e}")
