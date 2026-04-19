# -*- coding: utf-8 -*-
from pydantic import BaseModel


class TaskStartRequest(BaseModel):
    provider: str = ""
    model: str = ""
    api_key: str = ""
    prompt: str = ""
    directory: str = ""
    skip_existing: bool = False
