import json
import os
from typing import Any


CONFIG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Small-Demo-Manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "Config.json")


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _load() -> dict[str, Any]:
    _ensure_dir()
    if not os.path.isfile(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict[str, Any]):
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def read(key: str, default: Any = None) -> Any:
    return _load().get(key, default)


def write(key: str, value: Any):
    data = _load()
    data[key] = value
    _save(data)


def key_exists(key: str) -> bool:
    return key in _load()
