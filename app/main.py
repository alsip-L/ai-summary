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
from fastapi.staticfiles import StaticFiles
from core.config import ConfigManager
from core.errors import AISummaryException, ValidationError, ProviderError, FileProcessingError
from app.database import engine, Base
from app.routers import providers, prompts, tasks, files, trash, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    config = ConfigManager()
    secret_key = config.get(
        'system_settings.flask_secret_key', 'default-dev-secret-key-please-change-in-prod'
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

    @app.exception_handler(AISummaryException)
    async def base_error_handler(request: Request, exc: AISummaryException):
        return JSONResponse(status_code=500, content={"success": False, "error": exc.message})

    app.include_router(providers.router)
    app.include_router(prompts.router)
    app.include_router(tasks.router)
    app.include_router(files.router)
    app.include_router(trash.router)
    app.include_router(settings.router)

    from sqladmin import Admin
    from sqladmin.authentication import AuthenticationBackend
    from app.admin import (
        ProviderAdmin, PromptAdmin,
        TrashProviderAdmin, TrashPromptAdmin,
        UserPreferenceAdmin,
    )

    class AdminAuth(AuthenticationBackend):
        async def login(self, request):
            form = await request.form()
            if form.get("username") == "admin" and form.get("password") == "admin":
                request.session.update({"authenticated": True})
                return True
            return False

        async def logout(self, request):
            request.session.clear()
            return True

        async def authenticate(self, request):
            return request.session.get("authenticated")

    admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key=secret_key))
    admin.add_view(ProviderAdmin)
    admin.add_view(PromptAdmin)
    admin.add_view(TrashProviderAdmin)
    admin.add_view(TrashPromptAdmin)
    admin.add_view(UserPreferenceAdmin)

    frontend_dir = Path(__file__).parent.parent / "frontend"
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def index():
        return FileResponse(str(frontend_dir / "index.html"))

    return app


app = create_app()
