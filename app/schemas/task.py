# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class TaskStartRequest(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    directory: str = Field(min_length=1)
    skip_existing: bool = False


class RetryFailedRequest(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
