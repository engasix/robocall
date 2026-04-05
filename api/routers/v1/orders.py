"""Public API — store-facing order endpoints.

Authentication: X-Api-Key header (per-store key generated via /auth/generate-key).
All endpoints automatically scope to the authenticated store.

Response format:
    { "status": true, "data": ... }
    { "status": false, "reason": "..." }
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import database
from api.dependencies import require_store_api_key
from api.services.order_processor import build_and_schedule

router = APIRouter()


def ok(data):
    return {"status": True, "data": data}


def err(reason: str, http_status: int = 400):
    return JSONResponse(
        status_code=http_status,
        content={"status": False, "reason": reason},
    )


class PlaceOrderRequest(BaseModel):
    customer_name: str
    phone: str
    order_amount: float
    order_number: str | None = None



@router.post("", status_code=status.HTTP_201_CREATED)
def place_order(
    payload: PlaceOrderRequest,
    background_tasks: BackgroundTasks,
    store: database.Store = Depends(require_store_api_key),
    db: Session = Depends(database.get_db),
):
    # Check for duplicate order_number within this store
    if payload.order_number:
        existing = db.query(database.Order).filter(
            database.Order.store_id == store.id,
            database.Order.order_number == payload.order_number,
        ).first()
        if existing:
            return err(f"Order number '{payload.order_number}' already exists.", http_status=409)

    order = database.Order(
        store_id=store.id,
        order_number=payload.order_number,
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

    return ok({"order_id": order.id, "order_number": order.order_number, "status": order.status})


@router.get("/{identifier}")
def get_order(
    identifier: str,
    store: database.Store = Depends(require_store_api_key),
    db: Session = Depends(database.get_db),
):
    # Accept both internal order_id (integer) and external order_number (string)
    query = db.query(database.Order).filter(database.Order.store_id == store.id)
    if identifier.isdigit():
        order = query.filter(database.Order.id == int(identifier)).first()
    else:
        order = query.filter(database.Order.order_number == identifier).first()

    if not order:
        return err("Order not found.", http_status=404)
    return ok({
        "order_id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "order_amount": float(order.order_amount),
        "status": order.status,
        "call_attempts": order.call_attempts,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    })


@router.get("")
def list_orders(
    store: database.Store = Depends(require_store_api_key),
    db: Session = Depends(database.get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    total = db.query(database.Order).filter(database.Order.store_id == store.id).count()
    orders = (
        db.query(database.Order)
        .filter(database.Order.store_id == store.id)
        .order_by(database.Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return ok({
        "page": page,
        "page_size": page_size,
        "total": total,
        "orders": [
            {
                "order_id": o.id,
                "order_number": o.order_number,
                "customer_name": o.customer_name,
                "phone": o.phone,
                "order_amount": float(o.order_amount),
                "status": o.status,
                "retry_count": o.retry_count,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
    })
