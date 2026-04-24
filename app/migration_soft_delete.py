# -*- coding: utf-8 -*-
"""数据库迁移脚本（幂等、原子性）

包含：
1. 软删除重构迁移（trash_providers/trash_prompts → is_deleted）
2. 通用 schema 同步（检测模型定义中新增的列并自动添加）
"""
from sqlalchemy import text, inspect
from sqlalchemy.types import Boolean, Integer, String, Text, DateTime
from app.database import engine, SessionLocal
from app.models import Base
from core.log import get_logger

logger = get_logger()

# SQLAlchemy 类型 → SQLite 类型映射
_TYPE_MAP = {
    Boolean: "BOOLEAN",
    Integer: "INTEGER",
    String: "VARCHAR",
    Text: "TEXT",
    DateTime: "DATETIME",
}


def migrate_soft_delete():
    """执行软删除重构的数据迁移（幂等）"""
    db = SessionLocal()
    try:
        changed = _migrate_providers(db)
        changed = _migrate_prompts(db) or changed
        changed = _migrate_unique_constraints(db) or changed
        db.commit()
        if changed:
            logger.info("软删除迁移完成")
    except Exception as e:
        db.rollback()
        logger.error(f"软删除迁移失败: {e}")
        raise
    finally:
        db.close()


def sync_schema():
    """同步模型定义到数据库：检测并添加模型中新增但数据库中缺失的列

    在 Base.metadata.create_all() 之后调用，处理已存在表的新增列。
    仅支持添加列，不支持修改列类型或删除列。
    """
    insp = inspect(engine)
    db = SessionLocal()
    try:
        added = False
        for table_name, table in Base.metadata.tables.items():
            if table_name not in insp.get_table_names():
                continue  # 新表由 create_all 处理
            existing_cols = {c["name"] for c in insp.get_columns(table_name)}
            for column in table.columns:
                if column.name not in existing_cols:
                    sqlite_type = _TYPE_MAP.get(type(column.type), "TEXT")
                    default_clause = ""
                    if column.default is not None:
                        default_val = column.default.arg
                        # callable (如 lambda) 是 Python 层默认值，不能写入 SQL，跳过由 server_default 处理
                        if callable(default_val):
                            pass
                        elif isinstance(default_val, bool):
                            default_clause = f" DEFAULT {1 if default_val else 0}"
                        elif isinstance(default_val, str):
                            default_clause = f" DEFAULT '{default_val}'"
                        elif isinstance(default_val, (int, float)):
                            default_clause = f" DEFAULT {default_val}"
                    non_constant_default = False
                    if not default_clause and column.server_default is not None:
                        sd_arg = column.server_default.arg
                        # 处理 func.now() 等 SQL 函数表达式
                        if hasattr(sd_arg, 'compile'):
                            from sqlalchemy.dialects import sqlite as sqlite_dialect
                            compiled = str(sd_arg.compile(dialect=sqlite_dialect.dialect()))
                            # SQLite ALTER TABLE 不支持非常量默认值（如 CURRENT_TIMESTAMP）
                            # 需要先添加列不带默认值，再 UPDATE 现有行
                            non_constant_default = True
                        elif isinstance(sd_arg, str):
                            default_clause = f" DEFAULT '{sd_arg}'"
                        else:
                            default_clause = f" DEFAULT {sd_arg}"
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {sqlite_type}{default_clause}"
                    logger.info(f"Schema 同步: {sql}")
                    db.execute(text(sql))
                    # 对非常量默认值的列，UPDATE 现有行
                    if non_constant_default:
                        from sqlalchemy.dialects import sqlite as sqlite_dialect
                        db.execute(text(
                            f"UPDATE {table_name} SET {column.name} = {compiled}"
                        ))
                    added = True
        if added:
            db.commit()
            logger.info("Schema 同步完成")
    except Exception as e:
        db.rollback()
        logger.error(f"Schema 同步失败: {e}")
        raise
    finally:
        db.close()


def _migrate_providers(db):
    """迁移 providers 表：添加 is_deleted 列，迁移 trash_providers 数据，删除旧表"""
    insp = inspect(engine)
    changed = False

    # 步骤1: 添加 is_deleted 列（幂等）
    if not _has_column(insp, "providers", "is_deleted"):
        db.execute(text("ALTER TABLE providers ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        db.execute(text("UPDATE providers SET is_deleted = 0 WHERE is_deleted IS NULL"))
        changed = True

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
        changed = True

    return changed


def _migrate_prompts(db):
    """迁移 prompts 表：添加 is_deleted 列，迁移 trash_prompts 数据，删除旧表"""
    insp = inspect(engine)
    changed = False

    # 步骤1: 添加 is_deleted 列（幂等）
    if not _has_column(insp, "prompts", "is_deleted"):
        db.execute(text("ALTER TABLE prompts ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        db.execute(text("UPDATE prompts SET is_deleted = 0 WHERE is_deleted IS NULL"))
        changed = True

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
        changed = True

    return changed


def _has_column(insp, table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    try:
        columns = [c["name"] for c in insp.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def _migrate_unique_constraints(db):
    """将 name 列的单一 unique 约束迁移为 (name, is_deleted) 复合 unique 约束

    SQLite 不支持 ALTER INDEX，需要重建表。幂等：如果旧索引不存在则跳过。
    """
    insp = inspect(engine)
    changed = False

    for table_name in ("providers", "prompts"):
        # 检查是否存在旧的 name 单列 unique 索引
        old_index_name = None
        for idx in insp.get_indexes(table_name):
            if idx["column_names"] == ["name"] and idx.get("unique", False):
                old_index_name = idx["name"]
                break

        if not old_index_name:
            continue

        changed = True
        logger.info(f"迁移 {table_name} 的 name unique 约束为 (name, is_deleted) 复合约束")

        # 获取当前表结构
        columns = insp.get_columns(table_name)
        col_defs = []
        for col in columns:
            col_type = _TYPE_MAP.get(type(col.get("type")), "TEXT")
            col_name = col["name"]
            nullable = "" if col.get("nullable", True) else " NOT NULL"
            default = ""
            default_val = col.get("default")
            if default_val is not None:
                # 处理 SQLAlchemy DefaultClause 对象
                if hasattr(default_val, 'arg'):
                    default_val = default_val.arg
                if isinstance(default_val, bool):
                    default_val = 1 if default_val else 0
                if isinstance(default_val, (int, float, str)):
                    if isinstance(default_val, str):
                        default = f" DEFAULT '{default_val}'"
                    else:
                        default = f" DEFAULT {default_val}"
                # 处理 func.now() 等 SQL 函数表达式
                elif hasattr(default_val, 'compile'):
                    from sqlalchemy.dialects import sqlite as sqlite_dialect
                    compiled = default_val.compile(dialect=sqlite_dialect.dialect())
                    default = f" DEFAULT {compiled}"
            elif col.get("server_default") is not None:
                sd = col["server_default"]
                if hasattr(sd, 'arg'):
                    sd_arg = sd.arg
                    if hasattr(sd_arg, 'compile'):
                        from sqlalchemy.dialects import sqlite as sqlite_dialect
                        compiled = sd_arg.compile(dialect=sqlite_dialect.dialect())
                        default = f" DEFAULT {compiled}"
                    else:
                        default = f" DEFAULT {sd_arg}"
                elif isinstance(sd, str):
                    default = f" DEFAULT {sd}"
            col_defs.append(f"{col_name} {col_type}{nullable}{default}")

        # 获取非 name-unique 的其他索引
        other_indexes = []
        for idx in insp.get_indexes(table_name):
            if idx["name"] != old_index_name:
                cols = ", ".join(idx["column_names"])
                unique = "UNIQUE" if idx.get("unique") else ""
                other_indexes.append(f"CREATE {unique} INDEX IF NOT EXISTS {idx['name']} ON {table_name} ({cols})")

        # 获取外键约束
        foreign_keys = insp.get_foreign_keys(table_name)
        fk_clauses = []
        for fk in foreign_keys:
            constrained_cols = ", ".join(fk["constrained_columns"])
            referred_table = fk["referred_table"]
            referred_cols = ", ".join(fk["referred_columns"])
            fk_clauses.append(
                f"FOREIGN KEY ({constrained_cols}) REFERENCES {referred_table} ({referred_cols})"
            )

        # 重建表：去掉 name 的单列 unique，加上 (name, is_deleted) 复合 unique
        temp_table = f"{table_name}_temp"
        pk_col = columns[0]["name"]  # id

        col_defs_str = ", ".join(col_defs)
        # 包含外键约束
        fk_str = ", ".join(fk_clauses)
        create_parts = f"{col_defs_str}, PRIMARY KEY ({pk_col})"
        if fk_str:
            create_parts += f", {fk_str}"
        db.execute(text(f"CREATE TABLE {temp_table} ({create_parts})"))
        db.execute(text(f"INSERT INTO {temp_table} SELECT * FROM {table_name}"))
        db.execute(text(f"DROP TABLE {table_name}"))
        db.execute(text(f"ALTER TABLE {temp_table} RENAME TO {table_name}"))

        # 重建其他索引
        for idx_sql in other_indexes:
            db.execute(text(idx_sql))

        # 添加复合唯一索引
        db.execute(text(
            f"CREATE UNIQUE INDEX IF NOT EXISTS ix_{table_name}_name_is_deleted ON {table_name} (name, is_deleted)"
        ))

        logger.info(f"{table_name} unique 约束迁移完成")

    return changed
