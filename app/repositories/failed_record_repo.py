# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import FailedRecord
from core.log import get_logger

logger = get_logger()


class FailedRecordRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, source: str, error: str, retryable: bool = False) -> bool:
        """新增或更新一条失败记录（按 source 去重）"""
        try:
            existing = self._db.query(FailedRecord).filter(FailedRecord.source == source).first()
            if existing:
                existing.error = error
                existing.retryable = retryable
                existing.created_at = datetime.utcnow()
            else:
                record = FailedRecord(source=source, error=error, retryable=retryable)
                self._db.add(record)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def add_batch(self, records: list[dict]) -> int:
        """批量新增失败记录（按 source 去重：已存在则更新，不存在则插入）"""
        try:
            count = 0
            for r in records:
                source = r["source"]
                existing = self._db.query(FailedRecord).filter(FailedRecord.source == source).first()
                if existing:
                    existing.error = r.get("error", "")
                    existing.retryable = r.get("retryable", False)
                    existing.created_at = datetime.utcnow()
                else:
                    record = FailedRecord(
                        source=source,
                        error=r.get("error", ""),
                        retryable=r.get("retryable", False),
                    )
                    self._db.add(record)
                    count += 1
            self._db.commit()
            return count
        except Exception:
            self._db.rollback()
            return 0

    def get_all(self) -> list[dict]:
        """获取所有失败记录"""
        records = self._db.query(FailedRecord).order_by(FailedRecord.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "source": r.source,
                "error": r.error,
                "retryable": r.retryable,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]

    def get_count(self) -> int:
        """获取失败记录数量"""
        return self._db.query(FailedRecord).count()

    def get_sources(self) -> list[str]:
        """获取所有失败文件的路径列表（去重）"""
        records = self._db.query(FailedRecord.source).distinct().all()
        return [r[0] for r in records]

    def remove_by_source(self, source: str) -> bool:
        """按源文件路径删除失败记录（处理成功后调用）"""
        try:
            deleted = self._db.query(FailedRecord).filter(FailedRecord.source == source).delete()
            self._db.commit()
            return deleted > 0
        except Exception:
            self._db.rollback()
            return False

    def clear_all(self) -> int:
        """清除所有失败记录，返回删除数量"""
        try:
            count = self._db.query(FailedRecord).count()
            self._db.query(FailedRecord).delete()
            self._db.commit()
            return count
        except Exception:
            self._db.rollback()
            return 0
