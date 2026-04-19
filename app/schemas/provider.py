# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    models: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True


class ProviderResponse(BaseModel):
    name: str
    base_url: str
    api_key: str = Field(repr=False)
    models: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True


class ApiKeyUpdate(BaseModel):
    api_key: str


class ModelCreate(BaseModel):
    display_name: str
    model_id: str
