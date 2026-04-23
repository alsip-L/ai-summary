# -*- coding: utf-8 -*-
from contextlib import contextmanager
from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    @contextmanager
    def _write_session(self, auto_commit: bool = True):
        """写操作上下文管理器，统一处理 commit/rollback"""
        try:
            yield
            if auto_commit:
                self._db.commit()
        except Exception:
            try:
                self._db.rollback()
            except Exception:
                pass  # rollback 失败不应掩盖原始异常
            raise
