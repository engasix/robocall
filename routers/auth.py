from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import bcrypt
import database

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def require_auth(request: Request):
    """Dependency — redirects to /login if not authenticated."""
    if not request.session.get("store"):
        return RedirectResponse(url="/login", status_code=302)
    return request.session["store"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("store"):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db),
):
    store = db.query(database.Store).filter(database.Store.email == email).first()

    if not store or not store.password_hash or not verify_password(password, store.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid email or password."},
            status_code=401,
        )

    request.session["store"] = {
        "id": store.id,
        "business_name": store.business_name,
        "email": store.email,
        "language": store.language,
    }
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
