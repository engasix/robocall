from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database
from api.services.order_processor import build_and_schedule

router = APIRouter()


class OrderRequest(BaseModel):
    customer_name: str
    phone: str
    store_id: int
    order_amount: float


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
        build_and_schedule,
        order_id=order.id,
        customer_name=order.customer_name,
        store_id=store.id,
        store_name=store.business_name,
        order_amount=float(order.order_amount),
        language=store.language,
    )

    return {"order_id": order.id, "status": order.status}
