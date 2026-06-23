import os
import shutil
from typing import List

from config import read


SAVED_AUDIO_DIR_VAR = "SavedVoiceFilesPath"


class AudioFileInfo:
    def __init__(self, folder_name: str, file_name: str, full_path: str):
        self.folder_name = folder_name
        self.file_name = file_name
        self.full_path = full_path


class SavedAudioFiles:
    def __init__(self):
        self.files: List[AudioFileInfo] = []


saved_audio_files = SavedAudioFiles()


def get_saved_dir() -> str:
    custom = read(SAVED_AUDIO_DIR_VAR)
    if custom and os.path.isdir(custom):
        return custom
    appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    default = os.path.join(appdata, "Small-Demo-Manager", "Saved-Voice-Files")
    os.makedirs(default, exist_ok=True)
    return default


def refresh_saved_files():
    saved_audio_files.files.clear()
    base = get_saved_dir()
    if not os.path.isdir(base):
        return
    for folder in sorted(os.listdir(base)):
        folder_path = os.path.join(base, folder)
        if not os.path.isdir(folder_path):
            continue
        for fname in sorted(os.listdir(folder_path)):
            if fname.lower().endswith(".wav"):
                saved_audio_files.files.append(AudioFileInfo(
                    folder_name=folder,
                    file_name=fname,
                    full_path=os.path.join(folder_path, fname),
                ))


def copy_to_saved(source_path: str) -> str:
    base = get_saved_dir()
    demo_name = os.path.basename(os.path.dirname(os.path.dirname(source_path)))
    player_name = os.path.basename(os.path.dirname(source_path))
    target_dir = os.path.join(base, demo_name, player_name)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, os.path.basename(source_path))
    shutil.copy2(source_path, target_path)
    return target_path
