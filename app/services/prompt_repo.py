# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.models import Prompt
from core.log import get_logger

logger = get_logger()


class PromptRepository:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    def get_all(self) -> dict[str, str]:
        prompts = self._db.query(Prompt).all()
        return {p.name: p.content for p in prompts}

    def get(self, name: str) -> str | None:
        p = self._db.query(Prompt).filter(Prompt.name == name).first()
        return p.content if p else None

    def save(self, name: str, content: str, auto_commit: bool = True) -> bool:
        try:
            p = self._db.query(Prompt).filter(Prompt.name == name).first()
            if p:
                p.content = content
                logger.info(f"更新提示词: {name}")
            else:
                p = Prompt(name=name, content=content)
                self._db.add(p)
                logger.info(f"新增提示词: {name}")
            if auto_commit:
                self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def remove(self, name: str) -> str | None:
        try:
            p = self._db.query(Prompt).filter(Prompt.name == name).first()
            if not p:
                return None
            content = p.content
            self._db.delete(p)
            self._db.commit()
            logger.info(f"删除提示词: {name}")
            return content
        except Exception:
            self._db.rollback()
            return None
