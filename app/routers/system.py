# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import threading
import signal
import time
from pathlib import Path
from fastapi import APIRouter, Depends
from app.auth import require_auth

router = APIRouter(prefix="/api/system", tags=["system"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend-vue"

# 记录后端启动时间，用于前端确认重启成功
_started_at = time.time()


@router.get(
    "/info",
    summary="获取系统信息",
    description="返回系统信息，包含启动时间和进程ID，前端用于确认重启后连接的是新进程。",
    responses={200: {"description": "系统信息"}},
)
def system_info():
    """返回系统信息，前端用于确认重启后连接的是新进程。"""
    return {
        "started_at": _started_at,
        "pid": os.getpid(),
    }


@router.post(
    "/rebuild",
    summary="重建前端并重启",
    description="重新构建前端并重启后端服务。前端构建成功后，后端将在延迟 2 秒后自动重启。",
    responses={
        200: {"description": "重建结果"},
        500: {"description": "前端构建失败"},
    },
)
def rebuild(_auth=Depends(require_auth)):
    """重新构建前端并重启后端服务。"""
    result = {"frontend": None, "backend": None}

    # 1. 构建前端
    try:
        if sys.platform == "win32":
            npm_cmd = "npm.cmd"
        else:
            npm_cmd = "npm"

        build_proc = subprocess.run(
            [npm_cmd, "run", "build"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if build_proc.returncode == 0:
            result["frontend"] = "success"
        else:
            result["frontend"] = f"failed: {build_proc.stderr[-500:]}" if build_proc.stderr else f"failed with code {build_proc.returncode}"
    except subprocess.TimeoutExpired:
        result["frontend"] = "failed: build timed out (120s)"
    except FileNotFoundError:
        result["frontend"] = "failed: npm not found"
    except Exception as e:
        result["frontend"] = f"failed: {str(e)}"

    # 2. 重启后端（在子线程中延迟执行，先返回响应）
    def _restart_backend():
        time.sleep(2)  # 等待响应发送完毕

        run_py = str(PROJECT_ROOT / "run.py")
        cwd = str(PROJECT_ROOT)

        # 清理旧的临时重启脚本
        for helper_name in ("_restart_helper.py", "_restart_helper.sh", "_restart_helper.bat"):
            helper_path = PROJECT_ROOT / helper_name
            try:
                if helper_path.exists():
                    helper_path.unlink()
            except Exception:
                pass

        if sys.platform == "win32":
            # Windows: 用 Python 脚本做重启助手，避免弹出 CMD 窗口
            helper_script = (
                "import subprocess, time, sys, os, pathlib\n"
                "time.sleep(3)\n"
                # 清理自身
                "try: pathlib.Path(sys.argv[0]).unlink(missing_ok=True)\n"
                "except Exception: pass\n"
                f"subprocess.Popen([sys.executable, r'{run_py}'], cwd=r'{cwd}',"
                " creationflags=0x08000000)\n"  # CREATE_NO_WINDOW
            )
            helper_file = PROJECT_ROOT / "_restart_helper.py"
            helper_file.write_text(helper_script, encoding="utf-8")
            # CREATE_NO_WINDOW = 0x08000000 防止弹出控制台窗口
            subprocess.Popen(
                [sys.executable, str(helper_file)],
                creationflags=0x08000000,
                close_fds=True,
            )
        else:
            # Linux/macOS: 用 nohup + sleep 后台启动（不使用 shell=True）
            script = (
                f'#!/bin/bash\n'
                f'sleep 3\n'
                # 清理自身
                f'rm -f "$0"\n'
                f'cd "{cwd}"\n'
                f'"{sys.executable}" "{run_py}"\n'
            )
            script_file = PROJECT_ROOT / "_restart_helper.sh"
            script_file.write_text(script, encoding="utf-8")
            script_file.chmod(0o755)
            subprocess.Popen(
                ["/usr/bin/env", "bash", str(script_file)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # 终止当前进程
        pid = os.getpid()
        try:
            os.kill(pid, signal.SIGINT)
        except Exception:
            os._exit(0)

    if result["frontend"] == "success":
        result["backend"] = "restarting"
        t = threading.Thread(target=_restart_backend, daemon=True)
        t.start()
    else:
        result["backend"] = "skipped (frontend build failed)"

    return {"success": result["frontend"] == "success", "detail": result}
