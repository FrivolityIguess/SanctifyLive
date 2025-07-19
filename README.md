# Sanctify Live

Sanctify Live is a desktop application for managing church worship services, built with Python and PyQt5. It supports songs, scriptures, media, presentations, and themes, with a tabbed interface and features like tag distribution charts.

## Current Status
- Splash screen loads, but the main window crashes due to a missing `QListWidget` import in `ui/main_window.py`.
- `SettingsManager` has an unresolved `unhashable type: 'dict'` error (bypassed for now).
- Hymn parsing for `.txt` files in `data/songs/Hymns` needs improvement.

## How to Run
1. Install Python 3.11 (avoid 3.13 due to PyQt5 issues).
2. Install dependencies: `pip install PyQt5 PyQtWebEngine`.
3. Run: `python main.py`.
4. Check `data/logs/sanctify.log` for errors.

## Contributing
We need help with:
- Fixing `QListWidget` import in `ui/main_window.py`.
- Resolving `SettingsManager` errors in `core/settings_manager.py`.
- Enhancing hymn parsing in `songs_ui.py` for `.txt` files.
- Testing the UI (tabs, toolbar, tag distribution chart).

## Directory Structure
- `main.py`: App entry point.
- `ui/main_window.py`: Main window and UI setup.
- `core/settings_manager.py`: Settings management (needs fixing).
- `data/songs/Hymns/*.txt`: Hymn files.
- `data/logs/sanctify.log`: Logs.

Join us to make Sanctify Live shine for worship services!