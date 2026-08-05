from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from src.auth import service
from src.auth.constants import SESSION_USER_KEY
from src.auth.exceptions import InvalidForm
from src.auth.models import User
from src.auth.schemas import Credentials
from src.database import SessionDep
from src.rendering import page

router = APIRouter(tags=["auth"])

EmailField = Annotated[str, Form()]
PasswordField = Annotated[str, Form()]


def validated(email: str, password: str) -> Credentials:
    try:
        return Credentials(email=email, password=password)
    except ValidationError as error:
        raise InvalidForm(error) from error


def start_session(request: Request, user: User) -> RedirectResponse:
    request.session[SESSION_USER_KEY] = user.id
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)


def refused(request: Request, mode: str, email: str, error: HTTPException) -> HTMLResponse:
    return page(
        request, "auth.html", error.status_code, mode=mode, email=email, error=error.detail
    )


@router.get("/signup")
async def signup_form(request: Request) -> HTMLResponse:
    return page(request, "auth.html", mode="signup")


@router.post("/signup")
async def signup(
    request: Request, session: SessionDep, email: EmailField, password: PasswordField
) -> Response:
    try:
        user = await service.create_user(session, validated(email, password))
    except HTTPException as error:
        return refused(request, "signup", email, error)
    return start_session(request, user)


@router.get("/login")
async def login_form(request: Request) -> HTMLResponse:
    return page(request, "auth.html", mode="login")


@router.post("/login")
async def login(
    request: Request, session: SessionDep, email: EmailField, password: PasswordField
) -> Response:
    try:
        user = await service.authenticate(session, validated(email, password))
    except HTTPException as error:
        return refused(request, "login", email, error)
    return start_session(request, user)


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
