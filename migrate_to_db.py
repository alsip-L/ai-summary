# -*- coding: utf-8 -*-
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import Provider, Prompt, TrashProvider, TrashPrompt, UserPreference


def migrate():
    Base.metadata.create_all(bind=engine)

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print("config.json 不存在，跳过数据迁移")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    db = SessionLocal()
    try:
        if db.query(Provider).first() is None:
            for p in config.get("providers", []):
                provider = Provider(
                    name=p["name"],
                    base_url=p["base_url"],
                    api_key=p.get("api_key", ""),
                    models_json=json.dumps(p.get("models", {}), ensure_ascii=False),
                    is_active=p.get("is_active", True),
                )
                db.add(provider)
            print(f"迁移了 {len(config.get('providers', []))} 个提供商")

        if db.query(Prompt).first() is None:
            for name, content in config.get("custom_prompts", {}).items():
                value = "\n".join(content) if isinstance(content, list) else content
                prompt = Prompt(name=name, content=value)
                db.add(prompt)
            print(f"迁移了 {len(config.get('custom_prompts', {}))} 个提示词")

        trash = config.get("trash", {})
        if db.query(TrashProvider).first() is None:
            for name, p in trash.get("providers", {}).items():
                tp = TrashProvider(
                    name=name,
                    base_url=p.get("base_url", ""),
                    api_key=p.get("api_key", ""),
                    models_json=json.dumps(p.get("models", {}), ensure_ascii=False),
                    is_active=p.get("is_active", True),
                )
                db.add(tp)
            print(f"迁移了 {len(trash.get('providers', {}))} 个回收站提供商")

        if db.query(TrashPrompt).first() is None:
            for name, content in trash.get("custom_prompts", {}).items():
                value = "\n".join(content) if isinstance(content, list) else content
                tp = TrashPrompt(name=name, content=value)
                db.add(tp)
            print(f"迁移了 {len(trash.get('custom_prompts', {}))} 个回收站提示词")

        if db.query(UserPreference).first() is None:
            prefs = config.get("user_preferences", {})
            for key, value in prefs.items():
                str_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                up = UserPreference(key=key, value=str_value)
                db.add(up)
            print(f"迁移了 {len(prefs)} 个用户偏好")

        db.commit()
        print("数据迁移完成！")
    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
