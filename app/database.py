# -*- coding: utf-8 -*-
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ai_summary.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLite 连接池配置：
# - pool_size=5: 保持 5 个连接复用，减少频繁创建/销毁开销
# - max_overflow=3: 最多额外创建 3 个连接应对突发并发
# - pool_recycle=1800: 30 分钟回收连接，防止长时间空闲连接异常
# - pool_pre_ping=True: 使用前检测连接可用性，避免 SQLite 文件锁等问题
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=pool.QueuePool,
    pool_size=5,
    max_overflow=3,
    pool_recycle=1800,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """为 SQLite 连接设置 WAL 模式和外键支持，提高并发读写安全性"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_db_session():
    """数据库会话上下文管理器，自动管理会话的获取、回滚和释放"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
