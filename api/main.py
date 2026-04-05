from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import database
from api.routers import orders, webhooks, auth
from api.routers.v1 import orders as v1_orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Robocall API", lifespan=lifespan)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

app.include_router(orders.router, prefix="/orders")
app.include_router(webhooks.router, prefix="/webhook")
app.include_router(auth.router, prefix="/auth")
app.include_router(v1_orders.router, prefix="/v1/orders", tags=["v1"])
