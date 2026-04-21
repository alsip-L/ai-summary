# -*- coding: utf-8 -*-
"""SDK 构建脚本"""
import subprocess
import sys
from pathlib import Path


def build():
    sdk_dir = Path(__file__).parent
    result = subprocess.run(
        [sys.executable, "-m", "build", str(sdk_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"构建失败:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"构建成功，分发包在 {sdk_dir / 'dist'} 目录")


if __name__ == "__main__":
    build()
