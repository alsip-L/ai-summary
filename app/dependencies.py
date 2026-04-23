# -*- coding: utf-8 -*-
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repositories.settings_repo import SettingsRepository
from app.services.provider_service import ProviderService
from app.services.prompt_service import PromptService
from app.services.trash_service import TrashService
from app.services.settings_service import SettingsService
from app.services.task_service import TaskService
from app.services.file_browser_service import FileBrowserService


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_provider_service(db: Session = Depends(get_db)) -> ProviderService:
    return ProviderService(db)


def get_prompt_service(db: Session = Depends(get_db)) -> PromptService:
    return PromptService(db)


def get_trash_service(db: Session = Depends(get_db)) -> TrashService:
    return TrashService(db)


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    repo = SettingsRepository(db)
    return SettingsService(repo)


def get_task_service() -> TaskService:
    return TaskService()


def get_file_browser_service() -> FileBrowserService:
    return FileBrowserService()
