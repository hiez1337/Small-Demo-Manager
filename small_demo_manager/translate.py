import json
import os
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


_LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
_SUPPORTED = {
    "en": "English",
    "ru": "Русский",
}


class Translator(QObject):
    language_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._strings: dict[str, str] = {}
        self._current_lang = "en"

    def load(self, lang: str):
        path = os.path.join(_LOCALES_DIR, f"{lang}.json")
        if not os.path.isfile(path):
            path = os.path.join(_LOCALES_DIR, "en.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._strings = json.load(f)
        except (OSError, json.JSONDecodeError):
            self._strings = {}
        self._current_lang = lang if lang in _SUPPORTED else "en"
        self.language_changed.emit()

    def tr(self, key: str, default: str = "") -> str:
        return self._strings.get(key, default if default else key)

    @property
    def current_language(self) -> str:
        return self._current_lang

    @classmethod
    def supported_languages(cls) -> dict[str, str]:
        return dict(_SUPPORTED)


_instance: Optional[Translator] = None


def get_translator() -> Translator:
    global _instance
    if _instance is None:
        _instance = Translator()
        _instance.load("en")
    return _instance


def tr(key: str, default: str = "") -> str:
    return get_translator().tr(key, default)
