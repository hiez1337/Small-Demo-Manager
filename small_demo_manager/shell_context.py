import os
import sys
import winreg


DEM_EXT_KEY = r"Software\Classes\SystemFileAssociations\.dem\shell\Open with Small Demo Manager"
COMMAND_KEY = DEM_EXT_KEY + r"\command"


def _get_exe_path() -> str:
    return sys.executable


def _get_script_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")


def add_shell_context():
    exe_path = _get_exe_path()
    script_path = _get_script_path()
    command = f'"{exe_path}" "{script_path}" "%1"'

    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, DEM_EXT_KEY)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open with Small Demo Manager")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)

        cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY)
        winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        winreg.CloseKey(cmd_key)
        return True
    except Exception:
        return False


def remove_shell_context():
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, DEM_EXT_KEY)
        return True
    except Exception:
        return False


def validate_shell_integration() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return "main.py" in value
    except FileNotFoundError:
        return False
