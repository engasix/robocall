from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import database
from api.routers import orders, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Robocall API", lifespan=lifespan)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

app.include_router(orders.router, prefix="/orders")
app.include_router(webhooks.router, prefix="/webhook")
