import os
import threading
from typing import Optional

import pygame


_initialized = False
_init_lock = threading.Lock()


def _ensure_init():
    global _initialized
    with _init_lock:
        if not _initialized:
            pygame.mixer.init(frequency=48000, size=-16, channels=1)
            _initialized = True


_channel: Optional[pygame.mixer.Channel] = None
_lock = threading.Lock()


def play_wav(file_path: str):
    global _channel
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    if not file_path.lower().endswith(".wav"):
        raise ValueError("Only WAV files are supported")

    _ensure_init()

    with _lock:
        stop()
        sound = pygame.mixer.Sound(file_path)
        _channel = sound.play()


def stop():
    global _channel
    with _lock:
        if _channel is not None:
            try:
                _channel.stop()
            except Exception:
                pass
            _channel = None


def is_playing() -> bool:
    global _channel
    with _lock:
        if _channel is not None:
            try:
                return _channel.get_busy()
            except Exception:
                return False
        return False
