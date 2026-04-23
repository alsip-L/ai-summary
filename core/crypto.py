# -*- coding: utf-8 -*-
"""API Key 加密存储模块

使用 Fernet 对称加密保护数据库中的 API Key。
加密密钥从 config.json 的 secret_key 派生（SHA256 → base64 url-safe）。
"""

import base64
import hashlib
from core.config import ConfigManager


def _get_fernet_key() -> bytes:
    """从 secret_key 派生 Fernet 兼容的 32 字节密钥"""
    secret_key = ConfigManager().get("system_settings.secret_key", "")
    if not secret_key:
        secret_key = "default-dev-secret-key-please-change-in-prod"
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_api_key(plain_text: str) -> str:
    """加密 API Key，返回加密后的字符串"""
    if not plain_text:
        return ""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise RuntimeError(
            "cryptography 库未安装，无法加密 API Key。请执行: pip install cryptography"
        )
    f = Fernet(_get_fernet_key())
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_api_key(cipher_text: str) -> str:
    """解密 API Key，返回明文字符串"""
    if not cipher_text:
        return ""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise RuntimeError(
            "cryptography 库未安装，无法解密 API Key。请执行: pip install cryptography"
        )
    try:
        f = Fernet(_get_fernet_key())
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        # 解密失败（可能是旧数据为明文或 secret_key 已更改）
        # 如果看起来像 Fernet token（含 gAAAAA 前缀），说明密钥已更改
        if cipher_text.startswith("gAAAAA"):
            import logging
            logging.getLogger("ai_summary").error(
                "API Key 解密失败：secret_key 可能已更改，请确保使用与加密时相同的 secret_key"
            )
            return ""
        # 否则可能是旧版明文存储的数据，直接返回
        return cipher_text
