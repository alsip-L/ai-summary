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
        return JSONResponse(status_code=503, content={"success": False, "error": exc.message, "retryable": True})

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
        ProviderAdmin, ModelAdmin, ApiKeyAdmin,
        PromptAdmin, UserPreferenceAdmin, TrashAdmin, FailedRecordAdmin,
    )

    templates_dir = Path(__file__).parent.parent / "templates"
    admin = Admin(app, engine, templates_dir=str(templates_dir))

    # 按指定顺序注册：提供商、模型、API Key、提示词、用户偏好、回收站、失败记录
    admin.add_view(ProviderAdmin)
    admin.add_view(ModelAdmin)
    admin.add_view(ApiKeyAdmin)
    admin.add_view(PromptAdmin)
    admin.add_view(UserPreferenceAdmin)
    admin.add_view(TrashAdmin)
    admin.add_view(FailedRecordAdmin)

    # 重写 Admin 首页路由，传递各表记录数给模板
    async def custom_index(request):
        from sqlalchemy import text
        with engine.connect() as conn:
            tables_info = [
                {"name": "提供商", "count": 0, "key": "provider"},
                {"name": "模型", "count": 0, "key": "model"},
                {"name": "API Key", "count": 0, "key": "api-key"},
                {"name": "提示词", "count": 0, "key": "prompt"},
                {"name": "用户偏好", "count": 0, "key": "user-preference"},
                {"name": "回收站", "count": 0, "key": "trash"},
                {"name": "失败记录", "count": 0, "key": "failed-record"},
            ]
            counts = [
                ("SELECT COUNT(*) FROM providers WHERE is_deleted = 0", 0),
                ("SELECT COUNT(*) FROM models", 1),
                ("SELECT COUNT(*) FROM api_keys", 2),
                ("SELECT COUNT(*) FROM prompts WHERE is_deleted = 0", 3),
                ("SELECT COUNT(*) FROM user_preferences", 4),
                ("SELECT COUNT(*) FROM trash", 5),
                ("SELECT COUNT(*) FROM failed_records", 6),
            ]
            for sql, idx in counts:
                try:
                    tables_info[idx]["count"] = conn.execute(text(sql)).scalar()
                except Exception:
                    pass
        return await admin.templates.TemplateResponse(
            request, "sqladmin/index.html", {"tables_info": tables_info}
        )

    # 替换已注册的index路由
    from starlette.routing import Route
    for mount_route in app.routes:
        if type(mount_route).__name__ == "Mount" and mount_route.path == "/admin":
            admin_starlette = mount_route.app
            for i, sub_route in enumerate(admin_starlette.router.routes):
                if getattr(sub_route, "name", "") == "index":
                    admin_starlette.router.routes[i] = Route("/", custom_index, name="index")
                    break
            break

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
            # 防止路径遍历：确保解析后的路径仍在 assets 目录内
            try:
                resolved = full_path.resolve()
                if not resolved.is_relative_to(assets_dir.resolve()):
                    return JSONResponse(status_code=403, content={"detail": "Forbidden"})
            except (ValueError, OSError):
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})
            if not resolved.is_file():
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            content = resolved.read_bytes()
            # 根据扩展名推断 MIME 类型
            ext = resolved.suffix.lower()
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
