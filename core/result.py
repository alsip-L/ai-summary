# -*- coding: utf-8 -*-
"""通用响应辅助函数"""

from fastapi import HTTPException


def ok(**kwargs) -> dict:
    """构造成功响应"""
    return {"success": True, **kwargs}


def fail(error: str) -> dict:
    """构造失败响应"""
    return {"success": False, "error": error}


def check_result(result: dict, status_code: int = 400) -> dict:
    """检查 Service 返回结果，失败时抛出 HTTPException"""
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail=f"内部错误: 返回值类型异常 ({type(result).__name__})")
    if not result.get("success"):
        raise HTTPException(status_code=status_code, detail=result.get("error"))
    return result
