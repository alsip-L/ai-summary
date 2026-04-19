# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.models import Prompt, TrashPrompt


class PromptRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_all(self) -> dict[str, str]:
        prompts = self._db.query(Prompt).all()
        return {p.name: p.content for p in prompts}

    def get(self, name: str) -> str | None:
        p = self._db.query(Prompt).filter(Prompt.name == name).first()
        return p.content if p else None

    def save(self, name: str, content: str) -> bool:
        try:
            p = self._db.query(Prompt).filter(Prompt.name == name).first()
            if p:
                p.content = content
            else:
                p = Prompt(name=name, content=content)
                self._db.add(p)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False

    def remove(self, name: str) -> str | None:
        p = self._db.query(Prompt).filter(Prompt.name == name).first()
        if not p:
            return None
        content = p.content
        self._db.delete(p)
        self._db.commit()
        return content
