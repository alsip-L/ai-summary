# -*- coding: utf-8 -*-
from app.services.processing_state import ProcessingState
from app.repositories.failed_record_repo import FailedRecordRepository
from app.database import get_db_session
from core.log import get_logger

logger = get_logger()


class FailedRecordService:
    """失败记录的持久化管理服务"""

    def persist_from_state(self) -> None:
        """将当前 ProcessingState 中的失败/成功记录同步到数据库"""
        state = ProcessingState()
        failed, succeeded = state.get_results_summary()

        with get_db_session() as db:
            try:
                repo = FailedRecordRepository(db)
                if failed:
                    count = repo.add_batch(failed)
                    logger.info(f"失败记录已写入数据库: {count} 条")
                for source in succeeded:
                    repo.remove_by_source(source)
            except Exception as e:
                logger.error(f"持久化失败记录时出错: {e}")
                if failed:
                    for r in failed:
                        logger.error(f"[失败记录备份] source={r['source']}, error={r.get('error', '')}, retryable={r.get('retryable', False)}")

    @staticmethod
    def get_failed_records() -> dict:
        """读取数据库中的失败记录"""
        with get_db_session() as db:
            try:
                repo = FailedRecordRepository(db)
                records = repo.get_all()
                return {"success": True, "failed": records, "count": len(records)}
            except Exception as e:
                logger.error(f"读取失败记录时出错: {e}")
                return {"success": False, "error": f"读取失败记录出错: {e}"}

    @staticmethod
    def clear_failed_records() -> dict:
        """手动清除所有失败记录"""
        with get_db_session() as db:
            try:
                repo = FailedRecordRepository(db)
                count = repo.clear_all()
                logger.info(f"失败记录已清除: {count} 条")
                return {"success": True, "message": f"已清除 {count} 条失败记录"}
            except Exception as e:
                return {"success": False, "error": f"清除失败记录出错: {e}"}

    @staticmethod
    def get_sources_for_retry() -> tuple[list[dict], list[str]]:
        """获取失败记录及其源文件路径（供 retry_failed 使用）"""
        with get_db_session() as db:
            repo = FailedRecordRepository(db)
            return repo.get_all(), repo.get_sources()
