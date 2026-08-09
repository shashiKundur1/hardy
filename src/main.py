from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from src.auth.exceptions import AdminSignInRequired, NotAuthenticated
from src.auth.router import router as auth_router
from src.catalog.router import api_router as catalog_api_router
from src.catalog.router import router as catalog_router
from src.config import settings
from src.constants import RESPONSE_GUARDS
from src.database import SessionDep, create_schema
from src.debug.router import router as debug_router
from src.events.router import router as events_router
from src.exceptions import fault_for
from src.integrations import vectorstore
from src.observability import configure_logging, get_logger
from src.orders.router import router as orders_router
from src.recommendations import schedule
from src.recommendations.router import router as recommendations_router
from src.rendering import page
from src.storefront.router import router as storefront_router

SRC_DIR = Path(__file__).parent
BRAND_DIR = SRC_DIR.parent / "brand"

logger = get_logger("requests")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_schema()
    try:
        await vectorstore.ensure_collection()
    except Exception as unreachable:
        logger.warning("vector store unreachable at startup: %s", unreachable)
    scheduler = schedule.start_if_enabled()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def wants_json(request: Request) -> bool:
    return request.url.path.startswith("/api")


def fault(request: Request, status_code: int, detail: str, headers: dict | None = None) -> Response:
    if wants_json(request):
        return JSONResponse({"detail": detail}, status_code, headers=headers)
    written = page(
        request,
        "error.html",
        status_code,
        status=status_code,
        detail=detail,
        **fault_for(status_code),
    )
    for name, value in (headers or {}).items():
        written.headers[name] = value
    return written


async def to_sign_in(request: Request, exception: Exception) -> Response:
    if wants_json(request):
        return JSONResponse({"detail": "Sign in to continue"}, status.HTTP_401_UNAUTHORIZED)
    return RedirectResponse(f"/login?next={quote(request.url.path)}", status.HTTP_303_SEE_OTHER)


async def to_admin_sign_in(request: Request, exception: Exception) -> Response:
    if wants_json(request):
        return JSONResponse(
            {"detail": "Sign in as an administrator to continue"}, status.HTTP_401_UNAUTHORIZED
        )
    return RedirectResponse("/admin/login", status.HTTP_303_SEE_OTHER)


async def guard_headers(request: Request, call_next) -> Response:
    written = await call_next(request)
    for name, value in RESPONSE_GUARDS.items():
        written.headers.setdefault(name, value)
    if settings.https_only:
        written.headers.setdefault(
            "strict-transport-security", "max-age=31536000; includeSubDomains"
        )
    return written


async def error_page(request: Request, exception: HTTPException) -> Response:
    return fault(request, exception.status_code, exception.detail, exception.headers)


async def invalid_request(request: Request, exception: RequestValidationError) -> Response:
    if wants_json(request):
        return JSONResponse({"detail": exception.errors()}, status.HTTP_422_UNPROCESSABLE_CONTENT)
    return fault(request, status.HTTP_422_UNPROCESSABLE_CONTENT, "That request could not be read")


async def failure_page(request: Request, exception: Exception) -> Response:
    logger.exception("unhandled request failure", exc_info=exception)
    return fault(request, status.HTTP_500_INTERNAL_SERVER_ERROR, "Something broke on our side")


async def favicon() -> FileResponse:
    return FileResponse(SRC_DIR / "static" / "favicon-32.png", media_type="image/png")


async def design_tokens() -> FileResponse:
    return FileResponse(BRAND_DIR / "tokens.css", media_type="text/css")


async def health(session: SessionDep) -> JSONResponse:
    await session.execute(text("SELECT 1"))
    try:
        await vectorstore.count()
        vectors = True
    except Exception:
        vectors = False
    return JSONResponse({"status": "ok", "database": True, "vector_store": vectors})


def create_app() -> FastAPI:
    configure_logging()
    if not settings.session_secret:
        raise RuntimeError("SESSION_SECRET is unset; session cookies cannot be signed")

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        max_age=settings.session_max_age,
        same_site="lax",
        https_only=settings.https_only,
    )
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    app.middleware("http")(guard_headers)
    app.mount("/static", StaticFiles(directory=SRC_DIR / "static"), name="static")
    app.add_api_route("/brand/tokens.css", design_tokens, methods=["GET"], include_in_schema=False)
    app.add_api_route("/health", health, methods=["GET"], tags=["ops"])
    app.add_api_route("/favicon.ico", favicon, methods=["GET"], include_in_schema=False)
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(catalog_api_router)
    app.include_router(debug_router)
    app.include_router(events_router)
    app.include_router(orders_router)
    app.include_router(recommendations_router)
    app.include_router(storefront_router)
    app.add_exception_handler(NotAuthenticated, to_sign_in)
    app.add_exception_handler(AdminSignInRequired, to_admin_sign_in)
    app.add_exception_handler(HTTPException, error_page)
    app.add_exception_handler(RequestValidationError, invalid_request)
    app.add_exception_handler(Exception, failure_page)
    return app


app = create_app()
