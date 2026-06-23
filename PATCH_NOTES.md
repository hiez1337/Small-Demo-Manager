# Patch Notes

---

## v2.0.2 — 24.06.2026
*Timeline, Duration, UI polish*

### Новое
- **Timeline tab** — хронологическая лента убийств по раундам, фильтр по раунду, оружие, HS
- **Duration** — длительность матча теперь высчитывается и отображается (MM:SS)
- **8 вкладок**: Home, Spectator, Stats, Timeline, Voice, Settings, About, Guide
- **README** — двуязычный (EN/RU) с collapsible секциями
- **Release CI** — GitHub Actions собирает .exe и создаёт Release с описанием

### Исправлено
- **Сортировка статистики** — игроки сортируются по Score (CCSPlayerController.m_iScore), как в TAB в игре
- **Вёрстка** — контент не уплывает при вертикальном растягивании окна (addStretch)
- **Цветовой контраст** — accent #1565C0 для WCAG AA (был #64B5F6, 2.21:1 FAIL)
- **Копирайтинг** — все UI-тексты переписаны: табы (Spectator, Stats, Voice, Guide), кнопки, сообщения
- **Дизайн-токены** — tokens.py, централизованные цвета, типографика, отступы
- **Анимация табов** — fade-in 150ms OutCubic при переключении
- **URL leetify** — исправлен на /app/profile/
- **Импорт sys** — audio_extractor.py и main_window.py

---

## v2.0.1 — 23.06.2026
*Hotfix: исправления после порта*

### Исправлено
- **Аудио**: `opuslib` не находил `opus.dll` на Windows — теперь используется DLL из pygame
- **Аудио**: `bytes.tobytes()` — decode уже возвращает `bytes`, убрал лишний вызов
- **Аудио**: `QProgressBar.setValue()` принимает только `int` — обёртка `int(v)`
- **Аудио**: краш `Field object has no attribute 'clear'` — `SavedAudioFiles` был не dataclass
- **Аудио**: проверка пути перед сохранением — диалог, если путь не указан
- **Парсинг**: `NameError: name 'parser' not defined` — SourceTV флаг теперь в сигнале
- **Парсинг**: счёт команд через `CCSTeam.m_iScore` вместо подсчёта `round_end`
- **Парсинг**: имена команд FACEIT через `CCSTeam.m_szClanTeamname`
- **Парсинг**: точные K/D/A/DMG/MVP через `ActionTrackingServices`
- **Парсинг**: `>` между `str` и `int` — `try/except` для всех SteamID
- **Парсинг**: `list has no attribute 'empty'` — `round_mvp` возвращает `[]`
- **Парсинг**: правильные имена колонок: `team_number`, `user_steamid`, `dmg_health`
- **UI**: краш на старте — `setPlainText()` из фонового потока, заменён на `pyqtSignal`
- **UI**: QTimer в фоновом потоке не срабатывал — заменён на сигналы
- **UI**: QComboBox текст обрезался и был справа — заменён на Toggle-кнопки

### Новое
- **i18n**: Английский / Русский язык интерфейса (locales/en.json, ru.json)
- **i18n**: Переключатель в Settings (две кнопки English / Русский)
- **About**: Кнопка "Python Port Repository" на форк
- **About**: Авторские кредиты (оригинал + порт)
- **Аудио**: Кнопка "Save All Player Audio" — сохранить все файлы игрока
- **Аудио**: ПКМ по игроку → "Save All Player Audio"
- **Аудио**: ПКМ по файлу → "Save One Round" / "Save All Player Audio"
- **Аудио**: Диалог проверки пути перед сохранением
- **Патчноты**: Загружаются с GitHub (`PATCH_NOTES.md`)
- **Патчноты**: Новый формат с версиями и категориями

---

## [FIX]  v2.0.0 — 23.06.2026
*Полный порт с C# .NET 8 WinForms на Python*

### Основное
- **Парсинг .dem** через `demoparser2` — точная статистика K/D/A/DMG/MVP/HS
- **Имена команд** из FACEIT (`team_BubenoLatino`, `team_MegaSosateI`)
- **Opus → WAV** извлечение голосового чата (opuslib + pygame DLL)
- **WAV плеер** (pygame.mixer)
- **Bitfield Calculator** — выбор игроков, копирование `tv_listen_voice_indices`
- **Match Results** — таблица 12 колонок на команду

### UI (PyQt6 + qt-material)
- **Material Design 3** — тёмная/светлая тема (Teal)
- **7 вкладок**: Home, Bitfield-Calc, Match-Results, Audio-Player, Settings, About, HowTo
- **Drag-and-drop** .dem файлов на окно
- **Контекстные меню** игроков: SteamID64, Steam, cswatch.in, leetify.com, csstats.gg
- **Shell контекстное меню** для .dem файлов (реестр Windows)
- **JSON конфиг** в `%LOCALAPPDATA%/Small-Demo-Manager/Config.json`
- **Проверка обновлений** через GitHub Releases API
- **Патчноты** с GitHub (`PATCH_NOTES.md`)

---

## C# Original (до порта)

### 23.12.2025
- Update Parser to read older demos.

### 20.11.2025
- The new demo versions have caused a loop.

### 18.10.2025
- The last selection when moving the demo file is now saved.

### 07.10.2025
- Fix a small Bitfield Calc. bug

### 23.09.2025
- Renaming demo when moving improved

### 22.09.2025
- Parser adapted to new demo version dated 17 September 2025

### 08.09.2025
- Fixed an error when loading the patch notes.
- The option for the Shell Context Menu has been removed from the settings.

### 03.09.2025
- Revise tab blocking during import, etc.
- After selecting a CS2 path, this is now also displayed correctly in the settings.
- Bots, spectators, or admins are skipped when reading the demo.

### 02.09.2025
- The Home page has been completed.
- The About page has been completed.
- MessageBox and other dialogue boxes revised

### 01.09.2025
- The Settings page has been completed.

### 31.08.2025
- Voice audio extractor logic implemented.
- Improve Audioplayer, start/stop.

### 21.08.2025
- Dark and Light mode added.
- Design created for Voice Audio Extractor.

### 20.08.2025
- Tab page for match details created.
- Evaluate game data and integrate it into match details.
- Performance improved for Material Design.

### 19.08.2025
- Improved demo loading.
- Player data expanded.
- Bitfield calculator integrated into the new GUI.
- Tab page lock class created.

### 18.08.2025
- Project created for version 2.0.
- The new GUI design has been created.
- All controls and events have been bound.

---

## 🔜 ToDo
- [ ] Option to extract deep Data?
- [ ] Create a TabPage with Full-Details, all rounds (maybe PreAim degree & TTD)
