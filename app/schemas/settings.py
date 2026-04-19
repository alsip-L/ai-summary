# -*- coding: utf-8 -*-
from pydantic import BaseModel


class PreferencesUpdate(BaseModel):
    selected_provider: str | None = None
    selected_model: str | None = None
    selected_prompt: str | None = None
    directory_path: str | None = None
    api_key: str | None = None
