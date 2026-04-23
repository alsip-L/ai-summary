# -*- coding: utf-8 -*-
from app.models import Prompt
from app.repositories.base_repo import BaseRepository
from core.log import get_logger

logger = get_logger()


class PromptRepository(BaseRepository):

    def get_all(self) -> list[dict]:
        prompts = self._db.query(Prompt).filter(Prompt.is_deleted == False).all()
        return [{"name": p.name, "content": p.content} for p in prompts]

    def get(self, name: str) -> str | None:
        p = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == False).first()
        return p.content if p else None

    def save(self, name: str, content: str, auto_commit: bool = True) -> bool:
        try:
            with self._write_session(auto_commit):
                p = self._db.query(Prompt).filter(Prompt.name == name).first()
                if p:
                    p.content = content
                    if p.is_deleted:
                        p.is_deleted = False
                    logger.info(f"更新提示词: {name}")
                else:
                    p = Prompt(name=name, content=content)
                    self._db.add(p)
                    logger.info(f"新增提示词: {name}")
            return True
        except Exception as e:
            logger.error(f"保存提示词失败: {e}", exc_info=True)
            return False

    def soft_delete(self, name: str) -> bool:
        """软删除：设置 is_deleted=True"""
        try:
            with self._write_session():
                p = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == False).first()
                if not p:
                    return False
                p.is_deleted = True
                logger.info(f"软删除提示词: {name}")
            return True
        except Exception as e:
            logger.error(f"软删除提示词失败: {e}", exc_info=True)
            return False

    def restore(self, name: str) -> bool:
        """恢复：设置 is_deleted=False"""
        try:
            with self._write_session():
                p = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == True).first()
                if not p:
                    return False
                active = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == False).first()
                if active:
                    return False
                p.is_deleted = False
                logger.info(f"恢复提示词: {name}")
            return True
        except Exception as e:
            logger.error(f"恢复提示词失败: {e}", exc_info=True)
            return False

    def permanent_delete(self, name: str) -> bool:
        """永久删除：从数据库中物理移除"""
        try:
            with self._write_session():
                p = self._db.query(Prompt).filter(Prompt.name == name, Prompt.is_deleted == True).first()
                if not p:
                    return False
                self._db.delete(p)
                logger.info(f"永久删除提示词: {name}")
            return True
        except Exception as e:
            logger.error(f"永久删除提示词失败: {e}", exc_info=True)
            return False

    def get_all_deleted(self) -> list[dict]:
        """获取所有已软删除的 Prompt"""
        prompts = self._db.query(Prompt).filter(Prompt.is_deleted == True).all()
        return [{"name": p.name, "content": p.content} for p in prompts]
