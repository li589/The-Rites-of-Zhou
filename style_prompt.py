from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

CONFIG_PATH = Path(__file__).with_name("input.json")
USER_PLACEHOLDER = "{{user_request}}"
BUILTIN_PROMPT_ID = "builtin-default"
_CONFIG_LOCK = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_prompt_name() -> str:
    return "默认提示词"


def _custom_prompt_name() -> str:
    return f"自定义提示词 {_now_iso()[0:16].replace('T', ' ')}"


def _read_config_unlocked() -> dict:
    raw = json.loads(CONFIG_PATH.read_text("utf-8"))
    prompts = []
    for item in raw.get("prompts", []):
        if not isinstance(item, dict):
            continue
        prompt_id = str(item.get("id", "")).strip()
        content = str(item.get("content", "")).strip()
        if not prompt_id or not content:
            continue
        builtin = bool(item.get("builtin"))
        created_at = str(item.get("created_at") or _now_iso())
        updated_at = str(item.get("updated_at") or created_at)
        name = str(item.get("name") or "").strip() or (_default_prompt_name() if builtin else "未命名提示词")
        prompts.append(
            {
                "id": prompt_id,
                "name": name,
                "content": content,
                "builtin": builtin,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    if not prompts:
        raise ValueError("input.json 中缺少可用提示词")

    default_prompt_id = str(raw.get("default_prompt_id") or "").strip()
    if default_prompt_id not in {p["id"] for p in prompts}:
        default_prompt_id = prompts[0]["id"]

    return {"default_prompt_id": default_prompt_id, "prompts": prompts}


def _write_config_unlocked(config: dict) -> None:
    payload = {
        "default_prompt_id": config["default_prompt_id"],
        "prompts": config["prompts"],
    }
    CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def _find_prompt(config: dict, prompt_id: str | None) -> dict | None:
    target_id = (prompt_id or "").strip() or config["default_prompt_id"]
    for prompt in config["prompts"]:
        if prompt["id"] == target_id:
            return prompt
    return None


def _serialize_prompt(prompt: dict) -> dict:
    return {
        "id": prompt["id"],
        "name": prompt["name"],
        "content": prompt["content"],
        "builtin": prompt["builtin"],
        "created_at": prompt["created_at"],
        "updated_at": prompt["updated_at"],
    }


def render_prompt(template: str, user_request: str) -> str:
    text = (template or "").strip()
    request = (user_request or "").strip()
    if USER_PLACEHOLDER in text:
        return text.replace(USER_PLACEHOLDER, request)
    suffix = f"\n\n# 用户输入\n\n{request}" if request else ""
    return f"{text}{suffix}".strip()


def export_prompt_config() -> dict:
    with _CONFIG_LOCK:
        config = _read_config_unlocked()
    active = _find_prompt(config, config["default_prompt_id"])
    if active is None:
        raise ValueError("默认提示词不存在")
    prompts_by_recent = sorted(config["prompts"], key=lambda item: item["updated_at"], reverse=True)
    prompts = [p for p in prompts_by_recent if p["id"] == config["default_prompt_id"]] + [
        p for p in prompts_by_recent if p["id"] != config["default_prompt_id"]
    ]
    return {
        "default_prompt_id": config["default_prompt_id"],
        "user_placeholder": USER_PLACEHOLDER,
        "prompts": [_serialize_prompt(prompt) for prompt in prompts],
        "active_prompt": _serialize_prompt(active),
    }


def get_active_prompt() -> dict:
    with _CONFIG_LOCK:
        config = _read_config_unlocked()
    prompt = _find_prompt(config, config["default_prompt_id"])
    if prompt is None:
        raise ValueError("默认提示词不存在")
    return _serialize_prompt(prompt)


def build_prompt(user_request: str) -> str:
    return render_prompt(get_active_prompt()["content"], user_request)


def save_prompt(prompt_id: str | None, content: str, name: str | None = None, create_new: bool = False) -> dict:
    cleaned_content = (content or "").strip()
    cleaned_name = (name or "").strip()
    if not cleaned_content:
        raise ValueError("提示词不能为空")

    with _CONFIG_LOCK:
        config = _read_config_unlocked()
        current = _find_prompt(config, prompt_id)
        now = _now_iso()

        should_create_new = create_new or current is None or current["builtin"]
        if should_create_new:
            new_prompt = {
                "id": f"custom-{uuid4().hex[:10]}",
                "name": cleaned_name or _custom_prompt_name(),
                "content": cleaned_content,
                "builtin": False,
                "created_at": now,
                "updated_at": now,
            }
            config["prompts"].append(new_prompt)
            config["default_prompt_id"] = new_prompt["id"]
            _write_config_unlocked(config)
            return {"action": "created", "prompt": _serialize_prompt(new_prompt)}

        current["name"] = cleaned_name or current["name"]
        current["content"] = cleaned_content
        current["updated_at"] = now
        config["default_prompt_id"] = current["id"]
        _write_config_unlocked(config)
        return {"action": "updated", "prompt": _serialize_prompt(current)}


def set_default_prompt(prompt_id: str) -> dict:
    with _CONFIG_LOCK:
        config = _read_config_unlocked()
        prompt = _find_prompt(config, prompt_id)
        if prompt is None:
            raise ValueError("提示词不存在")
        config["default_prompt_id"] = prompt["id"]
        _write_config_unlocked(config)
        return _serialize_prompt(prompt)


def delete_prompt(prompt_id: str) -> dict:
    with _CONFIG_LOCK:
        config = _read_config_unlocked()
        prompt = _find_prompt(config, prompt_id)
        if prompt is None:
            raise ValueError("提示词不存在")
        if prompt["builtin"]:
            raise ValueError("默认提示词不可删除")

        config["prompts"] = [item for item in config["prompts"] if item["id"] != prompt["id"]]
        if config["default_prompt_id"] == prompt["id"]:
            builtin = _find_prompt(config, BUILTIN_PROMPT_ID)
            config["default_prompt_id"] = builtin["id"] if builtin is not None else config["prompts"][0]["id"]
        _write_config_unlocked(config)
        return _serialize_prompt(prompt)
