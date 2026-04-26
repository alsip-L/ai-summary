# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, Index, func, ForeignKey
from app.database import Base


class Provider(Base):
    __tablename__ = "providers"
    __table_args__ = (
        Index("ix_providers_is_deleted", "is_deleted"),
        Index("ix_providers_is_active_is_deleted", "is_active", "is_deleted"),
        Index("ix_providers_name_is_deleted", "name", "is_deleted", unique=True),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    models_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class Model(Base):
    """模型表：每个模型独立一行，关联到Provider"""
    __tablename__ = "models"
    __table_args__ = (
        Index("ix_models_provider_id", "provider_id"),
        Index("ix_models_display_name_provider", "display_name", "provider_id", unique=True),
    )

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    display_name = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    temperature = Column(Float, default=0.7, server_default="0.7")
    frequency_penalty = Column(Float, default=0.4, server_default="0.4")
    presence_penalty = Column(Float, default=0.2, server_default="0.2")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class ApiKey(Base):
    """API Key表：每个Key独立一行，关联到Provider或作为全局偏好Key"""
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_provider_id", "provider_id"),
    )

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    key_value = Column(String, nullable=False)
    source = Column(String, nullable=False, default="provider")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = (
        Index("ix_prompts_is_deleted", "is_deleted"),
        Index("ix_prompts_name_is_deleted", "name", "is_deleted", unique=True),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class Trash(Base):
    """回收站表：记录被软删除的提供商和提示词"""
    __tablename__ = "trash"
    __table_args__ = (
        Index("ix_trash_item_type", "item_type"),
    )

    id = Column(Integer, primary_key=True)
    item_type = Column(String, nullable=False)
    item_id = Column(Integer, nullable=False)
    item_name = Column(String, nullable=False)
    item_data = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class FailedRecord(Base):
    __tablename__ = "failed_records"
    __table_args__ = (
        Index("ix_failed_records_source", "source"),
        Index("ix_failed_records_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    error = Column(Text, default="")
    retryable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
