# -*- coding: utf-8 -*-
"""测试公共辅助函数"""
import os
import shutil
import tempfile

from sqlalchemy import text, inspect
from app.database import DB_PATH


def _backup_production_db():
    """从生产数据库备份一份到临时文件，返回临时文件路径。"""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
    os.close(tmp_fd)
    if DB_PATH.exists():
        shutil.copy2(str(DB_PATH), tmp_path)
    return tmp_path


def _ensure_soft_delete_columns(engine):
    """确保测试数据库包含 is_deleted 列和模型采样参数列"""
    insp = inspect(engine)
    for table, col, col_type, default in [
        ("providers", "is_deleted", "BOOLEAN", "0"),
        ("prompts", "is_deleted", "BOOLEAN", "0"),
        ("models", "temperature", "FLOAT", "0.7"),
        ("models", "frequency_penalty", "FLOAT", "0.4"),
        ("models", "presence_penalty", "FLOAT", "0.2"),
    ]:
        try:
            columns = [c["name"] for c in insp.get_columns(table)]
        except Exception:
            columns = []
        if col not in columns:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}"))
                conn.execute(text(f"UPDATE {table} SET {col} = {default} WHERE {col} IS NULL"))
                conn.commit()
