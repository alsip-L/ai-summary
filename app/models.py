# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Text, Boolean
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
