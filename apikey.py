from __future__ import annotations

import json
import os
from pathlib import Path

# API_TYPE 可选：openai / gemini / anthropic
#   openai     —— OpenAI 兼容协议（DeepSeek / Moonshot / 智谱 / SiliconFlow / OpenRouter / 通义千问 OpenAI 模式 等绝大多数厂商）
#   gemini     —— Google Gemini 原生协议（generativelanguage.googleapis.com）
#   anthropic  —— Anthropic Claude 原生协议（api.anthropic.com）
#
# 注意：
# 1. 页面保存的配置会写入 apikey.local.json（本地文件，建议不要提交到仓库）。
# 2. 环境变量 WENYAN_API_KEY 的优先级高于本地文件中的 API_KEY。
# 3. 如果你在界面上手动选择了协议类型，以界面为准。否则将根据 API_BASE 自动推断。
DEFAULT_CONFIG = {
    "API_TYPE": "gemini",
    "API_BASE": "https://generativelanguage.googleapis.com",
    "API_KEY": "",
    "MODEL": "gemini-2.5-flash",
}
CONFIG_KEYS = ("API_TYPE", "API_BASE", "API_KEY", "MODEL")
LOCAL_CONFIG_PATH = Path(__file__).with_name("apikey.local.json")


def _read_local_config() -> dict[str, str]:
    try:
        raw = json.loads(LOCAL_CONFIG_PATH.read_text("utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}

    result = {}
    if isinstance(raw, dict):
        for key in CONFIG_KEYS:
            value = raw.get(key)
            if isinstance(value, str):
                result[key] = value
    return result


def _effective_config() -> dict[str, str]:
    config = dict(DEFAULT_CONFIG)
    config.update(_read_local_config())
    env_key = os.getenv("WENYAN_API_KEY")
    if env_key is not None:
        config["API_KEY"] = env_key
    return config


def _refresh_globals() -> None:
    config = _effective_config()
    for key, value in config.items():
        globals()[key] = value


def save_config(data: dict[str, str]) -> None:
    """把界面上的配置写入本地配置文件，支持清空字段。"""
    current = _read_local_config()
    for key in CONFIG_KEYS:
        if key in data and isinstance(data[key], str):
            current[key] = data[key]
    LOCAL_CONFIG_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", "utf-8")


def apply_runtime_config(data: dict[str, str]) -> None:
    """同步更新当前进程中的配置，避免必须重启服务才能生效。"""
    for key in CONFIG_KEYS:
        if key in data and isinstance(data[key], str):
            globals()[key] = data[key]


def export_public_config() -> dict[str, str | bool]:
    """导出可返回给前端的配置，不直接暴露 API Key。"""
    return {
        "api_type": API_TYPE,
        "api_base": API_BASE,
        "model": MODEL,
        "has_api_key": bool(API_KEY),
    }


def detect_type(api_type: str | None, api_base: str | None) -> str:
    """根据用户选择或 URL 推断协议类型。"""
    if api_type:
        t = api_type.strip().lower()
        if t in ("openai", "gemini", "anthropic"):
            return t

    base = (api_base or API_BASE).lower()
    if "anthropic.com" in base:
        return "anthropic"
    if "generativelanguage.googleapis.com" in base or "googleapis.com" in base:
        return "gemini"
    return "openai"


_refresh_globals()
