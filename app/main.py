# -*- coding: utf-8 -*-
import sys
import codecs

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        pass

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from core.config import ConfigManager
from core.errors import (
    AISummaryException, ValidationError, ProviderError,
    FileProcessingError, RetryableError, NetworkError, RateLimitError,
)
from app.database import engine, Base
from app.routers import providers, prompts, tasks, files, trash, settings, logs, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    config = ConfigManager()
    secret_key = config.get(
        'system_settings.secret_key', 'default-dev-secret-key-please-change-in-prod'
    )

    app = FastAPI(
        title="AI Summary",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"success": False, "error": exc.message})

    @app.exception_handler(ProviderError)
    async def provider_error_handler(request: Request, exc: ProviderError):
        return JSONResponse(status_code=400, content={"success": False, "error": exc.message})

    @app.exception_handler(FileProcessingError)
    async def file_error_handler(request: Request, exc: FileProcessingError):
        return JSONResponse(status_code=500, content={"success": False, "error": exc.message})

    @app.exception_handler(RetryableError)
    async def retryable_error_handler(request: Request, exc: RetryableError):
        return JSONResponse(status_code=503, content={"success": False, "error": str(exc), "retryable": True})

    @app.exception_handler(AISummaryException)
    async def base_error_handler(request: Request, exc: AISummaryException):
        return JSONResponse(status_code=500, content={"success": False, "error": exc.message})

    app.include_router(providers.router)
    app.include_router(prompts.router)
    app.include_router(tasks.router)
    app.include_router(files.router)
    app.include_router(trash.router)
    app.include_router(settings.router)
    app.include_router(logs.router)
    app.include_router(system.router)

    from sqladmin import Admin
    from app.admin import (
        ProviderAdmin, PromptAdmin,
        TrashProviderAdmin, TrashPromptAdmin,
        UserPreferenceAdmin, FailedRecordAdmin,
    )

    templates_dir = Path(__file__).parent.parent / "templates"
    admin = Admin(app, engine, templates_dir=str(templates_dir))
    admin.add_view(ProviderAdmin)
    admin.add_view(PromptAdmin)
    admin.add_view(TrashProviderAdmin)
    admin.add_view(TrashPromptAdmin)
    admin.add_view(UserPreferenceAdmin)
    admin.add_view(FailedRecordAdmin)

    frontend_dist = Path(__file__).parent.parent / "frontend-vue" / "dist"
    if frontend_dist.is_dir():
        assets_dir = frontend_dist / "assets"

        @app.get("/")
        async def index():
            from starlette.responses import Response
            content = (frontend_dist / "index.html").read_bytes()
            return Response(
                content=content,
                media_type="text/html; charset=utf-8",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

        @app.get("/assets/{file_path:path}")
        async def serve_asset(file_path: str):
            from starlette.responses import Response
            full_path = assets_dir / file_path
            if not full_path.is_file():
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            content = full_path.read_bytes()
            # 根据扩展名推断 MIME 类型
            ext = full_path.suffix.lower()
            mime_map = {".js": "application/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2"}
            media_type = mime_map.get(ext, "application/octet-stream")
            return Response(
                content=content,
                media_type=media_type,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

        @app.middleware("http")
        async def spa_fallback(request: Request, call_next):
            response = await call_next(request)
            if response.status_code == 404 and request.method == "GET" and not request.url.path.startswith("/api"):
                file_path = frontend_dist / request.url.path.lstrip("/")
                if file_path.is_file():
                    return FileResponse(str(file_path))
                return FileResponse(str(frontend_dist / "index.html"))
            return response

    return app


app = create_app()
