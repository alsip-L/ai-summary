# -*- coding: utf-8 -*-
"""软删除重构的数据库迁移脚本（幂等、原子性）"""
from sqlalchemy import text, inspect
from app.database import engine, SessionLocal
from core.log import get_logger

logger = get_logger()


def migrate_soft_delete():
    """执行软删除重构的数据迁移（幂等）"""
    db = SessionLocal()
    try:
        _migrate_providers(db)
        _migrate_prompts(db)
        db.commit()
        logger.info("软删除迁移完成")
    except Exception as e:
        db.rollback()
        logger.error(f"软删除迁移失败: {e}")
        raise
    finally:
        db.close()


def _migrate_providers(db):
    """迁移 providers 表：添加 is_deleted 列，迁移 trash_providers 数据，删除旧表"""
    insp = inspect(engine)

    # 步骤1: 添加 is_deleted 列（幂等）
    if not _has_column(insp, "providers", "is_deleted"):
        db.execute(text("ALTER TABLE providers ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        db.execute(text("UPDATE providers SET is_deleted = 0 WHERE is_deleted IS NULL"))

    # 步骤2: 迁移 trash_providers 数据（幂等）
    if "trash_providers" in insp.get_table_names():
        # 仅迁移主表中不存在的 name（活跃数据优先）
        db.execute(text("""
            INSERT INTO providers (name, base_url, api_key, models_json, is_active, is_deleted)
            SELECT tp.name, tp.base_url, tp.api_key, tp.models_json, tp.is_active, 1
            FROM trash_providers tp
            WHERE tp.name NOT IN (SELECT name FROM providers WHERE is_deleted = 0)
        """))
        # 步骤3: 删除旧表
        db.execute(text("DROP TABLE trash_providers"))


def _migrate_prompts(db):
    """迁移 prompts 表：添加 is_deleted 列，迁移 trash_prompts 数据，删除旧表"""
    insp = inspect(engine)

    # 步骤1: 添加 is_deleted 列（幂等）
    if not _has_column(insp, "prompts", "is_deleted"):
        db.execute(text("ALTER TABLE prompts ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        db.execute(text("UPDATE prompts SET is_deleted = 0 WHERE is_deleted IS NULL"))

    # 步骤2: 迁移 trash_prompts 数据（幂等）
    if "trash_prompts" in insp.get_table_names():
        db.execute(text("""
            INSERT INTO prompts (name, content, is_deleted)
            SELECT tp.name, tp.content, 1
            FROM trash_prompts tp
            WHERE tp.name NOT IN (SELECT name FROM prompts WHERE is_deleted = 0)
        """))
        # 步骤3: 删除旧表
        db.execute(text("DROP TABLE trash_prompts"))


def _has_column(insp, table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    try:
        columns = [c["name"] for c in insp.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False
