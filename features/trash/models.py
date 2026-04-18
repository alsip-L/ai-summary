# -*- coding: utf-8 -*-
"""回收站数据模型"""

from pydantic import BaseModel
from typing import Any


class TrashItem(BaseModel):
    """回收站条目"""
    type: str          # "provider" 或 "prompt"
    name: str
    data: Any = None
