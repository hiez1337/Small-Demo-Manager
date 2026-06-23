<div align="center">

# 🎧 Small Demo Manager

**Analyze CS2 demos — match stats, voice extraction, spectator tools**

<br>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.11-41CD52?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)

<br>

**Python port** of the original C# .NET app by [pythaeusone](https://github.com/pythaeusone/Small-Demo-Manager)

<br>

---

<br>

</div>

---

<details>
<summary><b>🇬🇧 English</b></summary>
<br>

## What is this?

A desktop tool that reads Counter-Strike 2 demo files (`.dem`) and gives you:

- **Match statistics** — kills, deaths, assists, headshots, damage, MVPs for all 10 players, sorted the same way as the in-game scoreboard
- **Voice extraction** — pull Opus voice chat out of any SourceTV demo, decode it to WAV, save clips by player
- **Spectator bitfield** — pick which players you want to hear, get the exact console command to paste into CS2
- **Audio player** — play back extracted voice clips, grouped by player and round
- **Player profiles** — right-click any player to open their Steam / Leetify / CSStats / CSWatch profile or copy their SteamID64

No .NET required. No installation. Runs on any Windows machine with Python 3.12.

---

## Features

| Feature | What it does |
|---|---|
| **Demo parsing** | Reads `.dem` through `demoparser2` — extracts all 10 players, match score, team names (FACEIT / ESL / any) |
| **Match stats** | 12-column table per team: Player, K, D, A, K/D, HS, HS%, MVP, 3K, 4K, 5K, Damage |
| **Spectator bitfield** | Checkboxes → `1 << (slot-1)` → `tv_listen_voice_indices` command. Copy and paste into CS2 console |
| **Voice extraction** | Opus → WAV decoding via `opuslib` + `libopus`. Segmented by silence (>2s gaps), grouped by player |
| **Audio player** | WAV playback with `pygame`. Per-player playlist, per-round files, double-click to play |
| **File management** | Save one clip or all of a player's clips. Configurable output folder |
| **Move & rename** | Copy a demo to your CS2 folder with SHA256 integrity check. Three rename modes |
| **Shell integration** | Register `.dem` context menu in Windows Registry — right-click any demo to open it |
| **Drag & drop** | Drop `.dem` files anywhere onto the app window |
| **Dark / Light theme** | Material Design 3 toggle. Saves preference to config |
| **i18n** | English and Russian interface. Switch in Settings |
| **Player context menus** | Copy SteamID64, open Steam / Leetify / CSStats / CSWatch profiles |

---

## Quick start

### Prerequisites

```bash
pip install PyQt6 qt-material demoparser2 opuslib pygame pyperclip
```

### Run

```bash
cd small_demo_manager
python main.py

# With a demo loaded on startup:
python main.py "C:\path\to\demo.dem"
```

### Build a standalone .exe

```bash
pip install pyinstaller pillow
pyinstaller --onefile --name "SmallDemoManager" --distpath dist `
  --add-data "small_demo_manager/locales;locales" `
  --add-data "small_demo_manager/resources;resources" `
  --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui `
  --hidden-import PyQt6.QtWidgets --hidden-import qt_material `
  --hidden-import demoparser2 --hidden-import opuslib `
  --hidden-import pygame --hidden-import pyperclip `
  --collect-data qt_material --icon small_demo_manager/resources/homeNew.png `
  small_demo_manager/main.py
```

The `.exe` ends up in `dist/SmallDemoManager.exe`.

---

## How it works

1. **Open a demo** — drag a `.dem` file onto the window or use the file dialog
2. **See match stats** — switch to the Stats tab. Players are sorted by score, just like TAB in-game
3. **Set up spectator** — go to the Spectator tab, check the players you want to hear, copy the command
4. **Extract voice** — switch to Voice, click "Extract Voice". Wait for the progress bar
5. **Play clips** — select a player, double-click any clip. Right-click to save one or all

---

## Project structure

```
small_demo_manager/
├── main.py                 # Entry point
├── app.py                  # QApplication setup
├── config.py               # JSON config (%LOCALAPPDATA%/Small-Demo-Manager/Config.json)
├── models.py               # Data classes (PlayerSnapshot, MatchResult, AudioEntry)
├── tokens.py               # Design tokens (colors, typography, spacing)
├── translate.py            # i18n engine (EN / RU)
├── demo_parser.py          # CS2 demo parsing (demoparser2)
├── audio_extractor.py      # Opus → WAV
├── audio_player.py         # WAV playback (pygame)
├── audio_file_manager.py   # Saved clip management
├── shell_context.py        # Windows Registry shell integration
├── locales/                # Translation files
│   ├── en.json
│   └── ru.json
├── resources/              # Icons, opus.dll
├── ui/
│   ├── main_window.py      # Main window (7 tabs, ~1200 lines)
│   ├── custom_dialog.py    # Rename dialog
│   └── widgets.py          # Reusable widgets (Card, IconButton, SectionHeader)
├── .github/workflows/      # CI/CD
└── requirements.txt
```

---

## Dependencies

| Library | Why |
|---|---|
| [PyQt6](https://pypi.org/project/PyQt6/) | Desktop GUI framework |
| [qt-material](https://github.com/UN-GCPDS/qt-material) | Material Design 3 theme (light + dark) |
| [demoparser2](https://pypi.org/project/demoparser2/) | CS2 demo parser (Rust, pre-built wheels) |
| [opuslib](https://pypi.org/project/opuslib/) | Opus audio decoding |
| [pygame](https://pypi.org/project/pygame/) | WAV playback + bundled libopus DLL |
| [pyperclip](https://pypi.org/project/pyperclip/) | Clipboard access |

---

## Original vs Python port

| | C# (.NET 8) | Python |
|---|---|---|
| Runtime | .NET 8.0 Desktop Runtime | Python 3.12 |
| UI | WinForms + ReaLTaiizor | PyQt6 + qt-material |
| Demo parser | DemoFile (.NET) | demoparser2 (Rust) |
| Opus decoder | Concentus | opuslib + libopus DLL |
| Audio playback | NAudio | pygame.mixer |
| i18n | ❌ | ✅ EN / RU |
| Themes | Dark / Light | Dark / Light (Material Design 3) |
| Build | Visual Studio / MSBuild | pyinstaller (one-file .exe) |
| Platforms | Windows | Windows (cross-platform possible) |

---

## Credits

- **pythaeusone** — original C# version
- **KEROVSKI**, **Throw** — testing and feedback on the original

## License

MIT — commercial use is prohibited.

---

</details>

<details>
<summary><b>🇷🇺 Русский</b></summary>
<br>

## Что это?

Десктопное приложение для анализа демо-файлов Counter-Strike 2 (`.dem`). Всё, что нужно для разбора матча — без .NET, без установки, просто запусти и работай.

**Что умеет:**

- **Статистика матча** — убийства, смерти, помощи, хедшоты, урон, MVP для всех 10 игроков. Сортировка как в игре (по очкам)
- **Извлечение голоса** — достаёт Opus-голосовой чат из SourceTV демок, декодирует в WAV, группирует по игрокам
- **Bitfield для спектатора** — выбираешь игроков, приложение генерирует `tv_listen_voice_indices` — копируешь и вставляешь в консоль CS2
- **Аудиоплеер** — проигрывание WAV, список по раундам, двойной клик для воспроизведения
- **Профили игроков** — правый клик → Steam / Leetify / CSStats / CSWatch или копирование SteamID64

---

## Возможности

| Функция | Как работает |
|---|---|
| **Парсинг демок** | `demoparser2` читает `.dem` — 10 игроков, счёт, названия команд (FACEIT, ESL, любые) |
| **Статистика** | 12 колонок на команду: Игрок, У, С, П, У/С, HS, HS%, MVP, 3К, 4К, 5К, Урон |
| **Bitfield** | Чекбоксы → `1 << (slot-1)` → `tv_listen_voice_indices`. Скопировал — вставил в CS2 |
| **Голос** | Opus → WAV. Демка разбивается на фрагменты по паузам >2с. Всё рассортировано по игрокам |
| **Плеер** | `pygame`. Выбрал игрока — видишь его файлы. Двойной клик — играет. Правый клик — сохранить |
| **Сохранение** | Можно сохранить один фрагмент или все фрагменты игрока разом |
| **Перемещение демок** | Копирование в папку CS2 с проверкой SHA256. Три режима переименования |
| **Интеграция** | Контекстное меню `.dem` в проводнике Windows |
| **Drag-and-drop** | Перетащил `.dem` на окно — всё загрузилось |
| **Тёмная/светлая тема** | Material Design 3. Выбор сохраняется в настройках |
| **Язык** | Английский и русский интерфейс. Переключение в Settings |
| **Меню игроков** | SteamID64 в буфер, профили Steam / Leetify / CSStats / CSWatch |

---

## Быстрый старт

### Зависимости

```bash
pip install PyQt6 qt-material demoparser2 opuslib pygame pyperclip
```

### Запуск

```bash
cd small_demo_manager
python main.py

# С авто-загрузкой демки:
python main.py "C:\путь\к\демке.dem"
```

### Сборка .exe

```bash
pip install pyinstaller pillow
pyinstaller --onefile --name "SmallDemoManager" --distpath dist `
  --add-data "small_demo_manager/locales;locales" `
  --add-data "small_demo_manager/resources;resources" `
  --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui `
  --hidden-import PyQt6.QtWidgets --hidden-import qt_material `
  --hidden-import demoparser2 --hidden-import opuslib `
  --hidden-import pygame --hidden-import pyperclip `
  --collect-data qt_material --icon small_demo_manager/resources/homeNew.png `
  small_demo_manager/main.py
```

Готовый `.exe` в `dist/SmallDemoManager.exe`.

---

## Как пользоваться

1. **Загрузи демку** — перетащи `.dem` в окно или нажми «Открыть демку»
2. **Смотри статистику** — вкладка «Статистика». Игроки отсортированы по очкам, как в игре
3. **Настрой спектатора** — вкладка «Спектатор», отметь кого хочешь слышать, скопируй команду
4. **Извлеки голос** — вкладка «Голос», нажми «Извлечь голос», подожди
5. **Слушай** — выбери игрока, двойной клик по файлу. Правый клик — сохранить

---

## Оригинал и Python порт

| | C# (.NET 8) | Python |
|---|---|---|
| Запуск | .NET 8.0 Desktop Runtime | Python 3.12 |
| Интерфейс | WinForms + ReaLTaiizor | PyQt6 + qt-material |
| Парсер демок | DemoFile (.NET) | demoparser2 (Rust) |
| Opus декодер | Concentus | opuslib + libopus DLL |
| Аудиоплеер | NAudio | pygame.mixer |
| Языки | ❌ только EN | ✅ EN + RU |
| Темы | Темная / Светлая | Material Design 3 |
| Сборка | Visual Studio | pyinstaller (один .exe) |
| Платформа | Windows | Windows |

---

## Благодарности

- **pythaeusone** — оригинальная C# версия
- **KEROVSKI**, **Throw** — тестирование и фидбек оригинала

## Лицензия

MIT. Коммерческое использование запрещено.

---

</details>

---

*Patch notes: [PATCH_NOTES.md](PATCH_NOTES.md)*
