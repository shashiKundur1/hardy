from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.auth.exceptions import NotAuthenticated
from src.auth.router import router as auth_router
from src.catalog.router import api_router as catalog_api_router
from src.catalog.router import router as catalog_router
from src.config import settings
from src.database import create_schema
from src.events.router import router as events_router
from src.integrations import vectorstore
from src.observability import configure_logging, get_logger
from src.recommendations.router import router as recommendations_router
from src.rendering import page
from src.storefront.router import router as storefront_router

SRC_DIR = Path(__file__).parent
BRAND_DIR = SRC_DIR.parent / "brand"

logger = get_logger("requests")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_schema()
    await vectorstore.ensure_collection()
    yield


async def to_sign_in(request: Request, exception: Exception) -> Response:
    return RedirectResponse("/login", status.HTTP_303_SEE_OTHER)


async def error_page(request: Request, exception: HTTPException) -> Response:
    return page(
        request,
        "error.html",
        exception.status_code,
        status=exception.status_code,
        message=exception.detail,
    )


async def failure_page(request: Request, exception: Exception) -> Response:
    logger.exception("unhandled request failure", exc_info=exception)
    return page(
        request,
        "error.html",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Something broke on our side",
    )


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
    )
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    app.mount("/static", StaticFiles(directory=SRC_DIR / "static"), name="static")
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(catalog_api_router)
    app.include_router(events_router)
    app.include_router(recommendations_router)
    app.include_router(storefront_router)
    app.add_exception_handler(NotAuthenticated, to_sign_in)
    app.add_exception_handler(HTTPException, error_page)
    app.add_exception_handler(Exception, failure_page)
    return app


app = create_app()
