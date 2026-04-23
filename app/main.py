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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from core.config import ConfigManager
from core.errors import (
    AISummaryException, ValidationError, ProviderError,
    FileProcessingError, RetryableError, NetworkError, RateLimitError,
)
from app.database import engine, Base
from app.routers import providers, prompts, tasks, files, trash, settings, logs, system
from app.openapi_config import custom_openapi
from app.schemas.common import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.migration_soft_delete import migrate_soft_delete, sync_schema
    migrate_soft_delete()
    sync_schema()
    yield


def create_app() -> FastAPI:
    config = ConfigManager()
    # secret_key 用于 API Token 认证（app.auth.require_auth 依赖此值）
    secret_key = config.get(
        'system_settings.secret_key', 'default-dev-secret-key-please-change-in-prod'
    )

    app = FastAPI(
        title="AI Summary API",
        summary="基于 FastAPI + OpenAI API 的智能文本批量处理服务",
        description=(
            "AI Summary 提供 AI 提供商管理、提示词管理、批量文件处理、"
            "实时进度追踪、回收站和用户偏好等 REST API。\n\n"
            "## 快速开始\n"
            "1. 创建 AI 提供商（POST /api/providers/）\n"
            "2. 创建提示词（POST /api/prompts/）\n"
            "3. 启动处理任务（POST /api/tasks/start）\n"
            "4. 查询处理状态（GET /api/tasks/status）\n"
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS 配置：允许独立部署的前端跨域访问
    cors_origins = config.get("system_settings.cors_origins", [])
    # credentials=True 时 origins 不能为 ["*"]，需指定具体域名
    if not cors_origins or cors_origins == ["*"]:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 生产环境默认凭据安全校验
    if not config.get("system_settings.debug", False):
        if secret_key == "default-dev-secret-key-please-change-in-prod":
            import warnings
            warnings.warn(
                "安全警告: 生产环境中使用了默认 secret_key，请修改 config.json 中的 system_settings.secret_key"
            )
        admin_user = config.get("system_settings.admin_username", "admin")
        admin_pass = config.get("system_settings.admin_password", "admin")
        if admin_user == "admin" and admin_pass == "admin":
            import warnings
            warnings.warn(
                "安全警告: 生产环境中使用了默认管理员凭据 (admin/admin)，请修改 config.json"
            )

    # 注入增强的 OpenAPI 规范
    _original_openapi = app.openapi
    app.openapi = lambda: custom_openapi(app, _original_openapi)

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

    from sqladmin import Admin, AdminAuth
    from app.admin import (
        ProviderAdmin, PromptAdmin,
        UserPreferenceAdmin, FailedRecordAdmin,
    )

    class SimpleAdminAuth(AdminAuth):
        """SQLAdmin 认证：使用与 API 相同的 secret_key 派生 token"""
        async def authenticate(self, request):
            token = request.cookies.get("admin_token") or request.headers.get("X-API-Token")
            if not token:
                return False
            from app.auth import generate_api_token
            expected = generate_api_token(secret_key)
            import hmac
            return hmac.compare_digest(token, expected)

    templates_dir = Path(__file__).parent.parent / "templates"
    admin_auth = SimpleAdminAuth(secret_key=secret_key)
    admin = Admin(app, engine, templates_dir=str(templates_dir), authentication_backend=admin_auth)
    admin.add_view(ProviderAdmin)
    admin.add_view(PromptAdmin)
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
            # Vite 构建的 assets 文件名含 hash（如 index-abc123.js），可长期缓存
            cache_control = "public, max-age=31536000, immutable"
            return Response(
                content=content,
                media_type=media_type,
                headers={"Cache-Control": cache_control},
            )

        @app.middleware("http")
        async def spa_fallback(request: Request, call_next):
            response = await call_next(request)
            if response.status_code == 404 and request.method == "GET" and not request.url.path.startswith("/api"):
                file_path = frontend_dist / request.url.path.lstrip("/")
                # 防止路径遍历：确保解析后的路径仍在前端目录内
                try:
                    resolved = file_path.resolve()
                    if resolved.is_file() and resolved.is_relative_to(frontend_dist.resolve()):
                        return FileResponse(str(resolved))
                except (ValueError, OSError):
                    pass
                return FileResponse(str(frontend_dist / "index.html"))
            return response

    return app


app = create_app()
