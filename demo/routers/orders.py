from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import config
import database

router = APIRouter()


class OrderRequest(BaseModel):
    customer_name: str
    phone: str
    store_id: int
    order_amount: float


def call_api_process_order(order_id: int, customer_name: str, store_id: int,
                           store_name: str, order_amount: float, language: str, phone: str):
    """Call the API to handle audio generation and calling."""
    try:
        httpx.post(
            f"{config.API_URL}/orders/process",
            json={
                "order_id": order_id,
                "customer_name": customer_name,
                "store_id": store_id,
                "store_name": store_name,
                "order_amount": order_amount,
                "language": language,
                "phone": phone,
            },
            headers={"X-Api-Key": config.INTERNAL_API_KEY},
            timeout=300.0,
        )
    except Exception as e:
        print(f"[demo] API call failed for order {order_id}: {e}")


@router.post("/place-order")
def place_order(payload: OrderRequest, background_tasks: BackgroundTasks,
                db: Session = Depends(database.get_db)):
    store = db.query(database.Store).filter(database.Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    order = database.Order(
        store_id=payload.store_id,
        customer_name=payload.customer_name,
        phone=payload.phone,
        order_amount=payload.order_amount,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    background_tasks.add_task(
        call_api_process_order,
        order_id=order.id,
        customer_name=order.customer_name,
        store_id=store.id,
        store_name=store.business_name,
        order_amount=float(order.order_amount),
        language=store.language,
        phone=order.phone,
    )

    return {"order_id": order.id, "status": order.status}
