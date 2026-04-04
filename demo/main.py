from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import config
import database
from demo.routers import orders, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Robocall Demo", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

app.mount("/static", StaticFiles(directory="demo/static"), name="static")

app.include_router(auth.router)
app.include_router(orders.router)

templates = Jinja2Templates(directory="demo/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if request.session.get("store"):
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session_store=Depends(auth.require_auth)):
    if isinstance(session_store, RedirectResponse):
        return session_store
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"store": session_store},
    )


@app.get("/place-order", response_class=HTMLResponse)
def place_order_page(request: Request, session_store=Depends(auth.require_auth)):
    if isinstance(session_store, RedirectResponse):
        return session_store
    db = next(database.get_db())
    stores = db.query(database.Store).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"stores": stores, "store": session_store},
    )


@app.get("/api/orders")
def get_orders(
    request: Request,
    store_id: Optional[int] = None,
    session_store=Depends(auth.require_auth),
    db: Session = Depends(database.get_db),
):
    if isinstance(session_store, RedirectResponse):
        return session_store

    query = db.query(database.Order)
    # Future: uncomment to filter by store
    # if store_id:
    #     query = query.filter(database.Order.store_id == store_id)

    result = query.order_by(database.Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "phone": o.phone,
            "store_name": o.store.business_name,
            "order_amount": float(o.order_amount),
            "status": o.status,
            "retry_count": o.retry_count,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in result
    ]
