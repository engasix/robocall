from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database

router = APIRouter()


class OrderRequest(BaseModel):
    customer_name: str
    phone: str
    store_id: int
    order_amount: float


@router.post("/place-order")
def place_order(payload: OrderRequest, db: Session = Depends(database.get_db)):
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

    # TODO: trigger call (Phase 5)

    return {"order_id": order.id, "status": order.status}
