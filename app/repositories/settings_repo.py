# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import Session
from app.models import UserPreference


class SettingsRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_all(self) -> dict:
        """获取所有用户偏好"""
        prefs = self._db.query(UserPreference).all()
        result = {}
        for p in prefs:
            result[p.key] = self._parse_value(p.value)
        return result

    def save(self, data: dict) -> dict:
        """保存用户偏好"""
        try:
            for key, value in data.items():
                p = self._db.query(UserPreference).filter(UserPreference.key == key).first()
                str_value = json.dumps(value, ensure_ascii=False)
                if p:
                    p.value = str_value
                else:
                    p = UserPreference(key=key, value=str_value)
                    self._db.add(p)
            self._db.commit()
            return {"success": True}
        except Exception:
            self._db.rollback()
            return {"success": False, "error": "保存失败"}

    @staticmethod
    def _parse_value(value: str):
        if not value:
            return ""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
