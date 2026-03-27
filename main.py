from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
from routers import orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Robocall Order Confirmation System", lifespan=lifespan)

app.include_router(orders.router)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(database.get_db)):
    stores = db.query(database.Store).all()
    return templates.TemplateResponse(request=request, name="index.html", context={"stores": stores})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@app.get("/api/orders")
def get_orders(db: Session = Depends(database.get_db)):
    orders = db.query(database.Order).order_by(database.Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "phone": o.phone,
            "store_name": o.store.business_name,
            "order_amount": float(o.order_amount),
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]
