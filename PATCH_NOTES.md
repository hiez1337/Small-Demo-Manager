# Patch Notes

## v2.0.0 — 23.06.2026
- Полный порт с C# .NET 8 WinForms на Python
- Material Design 3 интерфейс (PyQt6 + qt-material)
- Парсинг .dem через demoparser2 с точной статистикой K/D/A/DMG/MVP
- Имена команд из FACEIT (team_BubenoLatino и т.д.)
- Opus → WAV извлечение голосового чата (opuslib)
- WAV плеер (pygame)
- Bitfield Calculator с копированием команды в буфер
- Drag-and-drop .dem файлов на окно
- Контекстные меню игроков (SteamID64, Steam/cswatch/leetify/csstats)
- Shell контекстное меню для .dem файлов (реестр)
- Тёмная/светлая тема Material Design
- JSON конфиг в %LOCALAPPDATA%/Small-Demo-Manager
- Проверка обновлений через GitHub Releases
- Патчноты загружаются с GitHub

## 23.12.2025
- Update Parser to read older demos.

## 20.11.2025
- The new demo versions have caused a loop.

## 18.10.2025
- The last selection when moving the demo file is now saved.

## 07.10.2025
- Fix a small Bitfield Calc. bug

## 23.09.2025
- Renaming demo when moving improved

## 22.09.2025
- Parser adapted to new demo version dated 17 September 2025

## 08.09.2025
- Fixed an error when loading the patch notes.
- The option for the Shell Context Menu has been removed from the settings.

## 03.09.2025
- Revise tab blocking during import, etc.
- After selecting a CS2 path, this is now also displayed correctly in the settings.
- Bots, spectators, or admins are skipped when reading the demo.

## 02.09.2025
- The Home page has been completed.
- The About page has been completed.
- MessageBox and other dialogue boxes revised

## 01.09.2025
- The Settings page has been completed.

## 31.08.2025
- Voice audio extractor logic implemented.
- Improve Audioplayer, start/stop.

## 21.08.2025
- Dark and Light mode added.
- Design created for Voice Audio Extractor.

## 20.08.2025
- Tab page for match details created.
- Evaluate game data and integrate it into match details.
- Performance improved for Material Design.

## 19.08.2025
- Improved demo loading.
- Player data expanded.
- Bitfield calculator integrated into the new GUI.
- Tab page lock class created.

## 18.08.2025
- Project created for version 2.0.
- The new GUI design has been created.
- All controls and events have been bound.

## ToDo
- Option to extract deep Data?
- Create a TabPage with Full-Details, all rounds (maybe PreAim degree & TTD).
