from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from src.auth import service
from src.auth.constants import ONBOARDING_PATH, SESSION_USER_KEY, SHOP_HOME
from src.auth.dependencies import CurrentUser
from src.auth.exceptions import AdminOnly, InvalidForm
from src.auth.models import User
from src.auth.schemas import Credentials, OnboardingChoices
from src.catalog import service as catalog
from src.constants import Role
from src.database import SessionDep
from src.redirects import safe_path
from src.rendering import page

router = APIRouter(tags=["auth"])

EmailField = Annotated[str, Form()]
PasswordField = Annotated[str, Form()]

ONBOARDING_STEPS = 3


def safe_next(target: str | None) -> str:
    return safe_path(target, SHOP_HOME)


def validated(email: str, password: str) -> Credentials:
    try:
        return Credentials(email=email, password=password)
    except ValidationError as error:
        raise InvalidForm(error) from error


def start_session(request: Request, user: User, target: str) -> RedirectResponse:
    request.session[SESSION_USER_KEY] = user.id
    return RedirectResponse(target, status.HTTP_303_SEE_OTHER)


def refused(
    request: Request, template: str, error: HTTPException, **context: object
) -> HTMLResponse:
    return page(
        request,
        template,
        error.status_code,
        error=error.detail,
        error_field=getattr(error, "field", "form"),
        **context,
    )


@router.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request) -> HTMLResponse:
    return page(request, "signup.html")


@router.post("/signup")
async def signup(
    request: Request, session: SessionDep, email: EmailField, password: PasswordField
) -> Response:
    try:
        user = await service.create_user(session, validated(email, password))
    except HTTPException as error:
        return refused(request, "signup.html", error, email=email)
    return start_session(request, user, ONBOARDING_PATH)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, next: str = "") -> HTMLResponse:
    return page(request, "login.html", next=safe_next(next))


@router.post("/login")
async def login(
    request: Request,
    session: SessionDep,
    email: EmailField,
    password: PasswordField,
    next: Annotated[str, Form()] = "",
) -> Response:
    target = safe_next(next)
    try:
        user = await service.authenticate(session, validated(email, password))
    except HTTPException as error:
        return refused(request, "login.html", error, email=email, next=target)
    if user.onboarded_at is None:
        return start_session(request, user, ONBOARDING_PATH)
    return start_session(request, user, target)


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request) -> HTMLResponse:
    return page(request, "admin_login.html")


@router.post("/admin/login")
async def admin_login(
    request: Request, session: SessionDep, email: EmailField, password: PasswordField
) -> Response:
    try:
        user = await service.authenticate(session, validated(email, password))
    except HTTPException as error:
        return refused(request, "admin_login.html", error, email=email)
    if user.role != Role.ADMIN:
        raise AdminOnly()
    return start_session(request, user, "/admin")


@router.get("/welcome", response_class=HTMLResponse)
async def welcome(
    request: Request, session: SessionDep, user: CurrentUser, step: int = 1
) -> Response:
    if user.onboarded_at is not None:
        return RedirectResponse(SHOP_HOME, status.HTTP_303_SEE_OTHER)
    return page(
        request,
        "welcome.html",
        step=min(max(step, 1), ONBOARDING_STEPS),
        steps=ONBOARDING_STEPS,
        user=user,
        categories=await catalog.navigation(session),
        chosen=service.declared_interests(user),
    )


@router.post("/welcome/interests")
async def choose_interests(
    session: SessionDep, user: CurrentUser, interests: Annotated[list[str] | None, Form()] = None
) -> RedirectResponse:
    try:
        choices = OnboardingChoices(interests=interests or [])
    except ValidationError as error:
        raise InvalidForm(error) from error
    await service.save_interests(session, user, choices.interests)
    return RedirectResponse(f"{ONBOARDING_PATH}?step=3", status.HTTP_303_SEE_OTHER)


@router.post("/welcome/finish")
async def finish_welcome(
    session: SessionDep,
    user: CurrentUser,
    shopping_for: Annotated[str, Form()] = "",
    display_name: Annotated[str, Form()] = "",
) -> RedirectResponse:
    try:
        choices = OnboardingChoices(shopping_for=shopping_for, display_name=display_name)
    except ValidationError as error:
        raise InvalidForm(error) from error
    await service.complete_onboarding(session, user, choices)
    return RedirectResponse(SHOP_HOME, status.HTTP_303_SEE_OTHER)


@router.post("/welcome/skip")
async def skip_welcome(session: SessionDep, user: CurrentUser) -> RedirectResponse:
    await service.skip_onboarding(session, user)
    return RedirectResponse(SHOP_HOME, status.HTTP_303_SEE_OTHER)


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
