# 🎧 Small Demo Manager

> **Python port** — полностью переписан с C# .NET 8 WinForms на Python.
>
> Оригинал: [pythaeusone/Small-Demo-Manager](https://github.com/pythaeusone/Small-Demo-Manager)

![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Инструмент для анализа демо-файлов Counter-Strike 2 (.dem).  
Парсинг статистики матча, извлечение голосового чата (Opus → WAV), расчёт bitfield для `tv_listen_voice_indices`, просмотр результатов и управление демками.

---

## ✨ Возможности

- **Парсинг .dem** через `demoparser2` — 10 игроков, точная статистика K/D/A/DMG/HS/MVP, имена команд из FACEIT
- **Bitfield Calculator** — выбор игроков, генерация `tv_listen_voice_indices <bitfield>; tv_listen_voice_indices_h <bitfield>`, копирование в буфер
- **Match Results** — таблица на команду: Player, K, D, A, K/D, HS, HS%, MVP, 3K, 4K, 5K, Damage
- **Audio Extraction** — извлечение Opus-голоса → WAV (48000Hz mono), сегментация по паузам >2с
- **Audio Player** — проигрывание WAV, список по раундам, прогресс-бар
- **Audio File Manager** — сохранение отдельных раундов или всего игрока в `Saved-Voice-Files`
- **Drag-and-drop** — перетаскивание .dem файлов на окно
- **Shell Integration** — контекстное меню для .dem файлов (реестр Windows)
- **Контекстные меню игроков** — SteamID64, Steam / cswatch.in / leetify.com / csstats.gg
- **Тёмная/светлая тема** — Material Design 3 toggle
- **i18n** — English / Русский язык интерфейса
- **Move & Rename** — копирование демки в папку CS2 с SHA256 проверкой

---

## 🖼️ Скриншоты

| Bitfield-Calc | Match-Results | Audio-Player |
|---|---|---|
| *(скоро)* | *(скоро)* | *(скоро)* |

---

## 📦 Установка

### Зависимости

```bash
pip install PyQt6 qt-material demoparser2 opuslib pygame pyperclip
```

### Запуск

```bash
cd small_demo_manager
python main.py

# или с авто-загрузкой демки:
python main.py "C:\path\to\demo.dem"
```

---

## 🏗️ Структура проекта

```
small_demo_manager/
├── main.py                 # Точка входа
├── app.py                  # QApplication + MainWindow
├── config.py               # JSON конфиг (%LOCALAPPDATA%/Small-Demo-Manager/Config.json)
├── models.py               # Data-классы (PlayerSnapshot, MatchResult, AudioEntry)
├── demo_parser.py          # Парсинг .dem через demoparser2
├── audio_extractor.py      # Opus → WAV
├── audio_player.py         # WAV плеер (pygame.mixer)
├── audio_file_manager.py   # Управление сохранёнными файлами
├── shell_context.py        # Реестр Windows (.dem контекстное меню)
├── translate.py            # i18n (EN/RU)
├── locales/                # Translation JSON файлы
│   ├── en.json
│   └── ru.json
├── resources/              # Иконки, opus.dll
├── ui/
│   ├── main_window.py      # Главное окно с 7 вкладками
│   ├── custom_dialog.py    # Диалог переименования демки
│   └── widgets.py          # Card, IconButton, SectionHeader
└── requirements.txt
```

---

## 🧩 Используемые библиотеки

| Библиотека | Назначение |
|---|---|
| [PyQt6](https://pypi.org/project/PyQt6/) | GUI framework |
| [qt-material](https://github.com/UN-GCPDS/qt-material) | Material Design 3 тема |
| [demoparser2](https://pypi.org/project/demoparser2/) | Парсинг CS2 .dem файлов |
| [opuslib](https://pypi.org/project/opuslib/) | Opus → PCM декодирование |
| [pygame](https://pypi.org/project/pygame/) | WAV аудиоплеер + opus.dll |
| [pyperclip](https://pypi.org/project/pyperclip/) | Буфер обмена |

---

## 🔄 Сравнение с оригиналом (C# .NET)

| Характеристика | C# оригинал | Python порт |
|---|---|---|
| Runtime | .NET 8.0 | Python 3.12 |
| UI | WinForms + ReaLTaiizor | PyQt6 + qt-material |
| Парсинг .dem | DemoFile (.NET) | demoparser2 (Rust) |
| Opus декодер | Concentus | opuslib + libopus |
| Аудиоплеер | NAudio | pygame.mixer |
| i18n | ❌ | ✅ EN/RU |
| Платформа | Windows only | Windows (возможно macOS/Linux) |

---

## 📋 Patch Notes

Актуальный список изменений: [PATCH_NOTES.md](PATCH_NOTES.md)  
(загружается в приложении на вкладке Home)

---

## ❤️ Благодарности

- **pythaeusone** — оригинальный автор Small Demo Manager
- **KEROVSKI**, **Throw** — тестирование и фидбек

---

## 📜 Лицензия

MIT License. Коммерческое использование запрещено.
