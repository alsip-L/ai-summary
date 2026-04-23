# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from app.models import FailedRecord
from app.repositories.base_repo import BaseRepository
from core.log import get_logger

logger = get_logger()


class FailedRecordRepository(BaseRepository):

    def add(self, source: str, error: str, retryable: bool = False) -> bool:
        """新增或更新一条失败记录（按 source 去重）"""
        try:
            with self._write_session():
                existing = self._db.query(FailedRecord).filter(FailedRecord.source == source).first()
                if existing:
                    existing.error = error
                    existing.retryable = retryable
                    existing.created_at = datetime.now(timezone.utc)
                else:
                    record = FailedRecord(source=source, error=error, retryable=retryable)
                    self._db.add(record)
            return True
        except Exception as e:
            logger.error(f"新增失败记录失败: {e}", exc_info=True)
            return False

    def add_batch(self, records: list[dict]) -> int:
        """批量新增失败记录（按 source 去重：已存在则更新，不存在则插入）"""
        try:
            count = 0
            with self._write_session():
                # 批量查询所有已存在的 source，避免 N+1 查询
                sources = [r["source"] for r in records]
                existing_records = self._db.query(FailedRecord).filter(
                    FailedRecord.source.in_(sources)
                ).all()
                existing_map = {r.source: r for r in existing_records}

                for r in records:
                    source = r["source"]
                    existing = existing_map.get(source)
                    if existing:
                        existing.error = r.get("error", "")
                        existing.retryable = r.get("retryable", False)
                        existing.created_at = datetime.now(timezone.utc)
                    else:
                        record = FailedRecord(
                            source=source,
                            error=r.get("error", ""),
                            retryable=r.get("retryable", False),
                        )
                        self._db.add(record)
                        count += 1
            return count
        except Exception as e:
            logger.error(f"批量新增失败记录失败: {e}", exc_info=True)
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
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
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
            with self._write_session():
                deleted = self._db.query(FailedRecord).filter(FailedRecord.source == source).delete()
            return deleted > 0
        except Exception as e:
            logger.error(f"删除失败记录失败: {e}", exc_info=True)
            return False

    def clear_all(self) -> int:
        """清除所有失败记录，返回删除数量"""
        try:
            with self._write_session() as auto_commit:
                # 在同一事务内计数并删除
                count = self._db.query(FailedRecord).count()
                self._db.query(FailedRecord).delete()
            return count
        except Exception as e:
            logger.error(f"清除失败记录失败: {e}", exc_info=True)
            return 0
