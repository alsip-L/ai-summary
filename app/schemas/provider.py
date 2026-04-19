# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    name: str
    base_url: str = Field(min_length=1, pattern=r"^https?://")
    api_key: str = Field(min_length=1)
    models: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True


class ApiKeyUpdate(BaseModel):
    api_key: str = Field(min_length=1)


class ModelCreate(BaseModel):
    display_name: str
    model_id: str
