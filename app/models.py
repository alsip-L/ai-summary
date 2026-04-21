# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.database import Base


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    models_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)


class TrashProvider(Base):
    __tablename__ = "trash_providers"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    models_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)


class TrashPrompt(Base):
    __tablename__ = "trash_prompts"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, default="")


class FailedRecord(Base):
    __tablename__ = "failed_records"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    error = Column(Text, default="")
    retryable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
