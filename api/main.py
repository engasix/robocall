from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
import database
from api.routers import webhooks, auth
from api.routers.v1 import orders as v1_orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Robocall API", lifespan=lifespan)


# ── Standardize all error responses ──────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # If already in our format, pass through; otherwise wrap it
    if isinstance(exc.detail, dict) and "reason" in exc.detail:
        content = exc.detail
    else:
        content = {"status": False, "reason": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Surface the first meaningful error message
    reason = errors[0].get("msg", "Invalid request.") if errors else "Invalid request."
    return JSONResponse(status_code=422, content={"status": False, "reason": reason})


# ── Routers ───────────────────────────────────────────────────────────────────

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

app.include_router(webhooks.router, prefix="/webhook")
app.include_router(auth.router, prefix="/v1/auth", tags=["v1"])
app.include_router(v1_orders.router, prefix="/v1/orders", tags=["v1"])
