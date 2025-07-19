import os
import json
import logging
from typing import Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QFont
from core.exceptions import SanctifyError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/sanctify.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SettingsManager(QObject):
    """Manage application-wide settings stored in a JSON file with change signals."""
    settings_changed = pyqtSignal(str, str, object)  # section, key, value

    def __init__(self, config_file: str = "data/config/settings.json"):
        super().__init__()
        self.config_file = config_file
        self.default_settings = {
            "general": {
                "startup_screen": "Songs",
                "language": "English",
                "enable_tips": True,
                "window_geometry": {"width": 1280, "height": 720, "x": 100, "y": 100}
            },
            "appearance": {
                "theme": "Light",
                "ui_font": QFont("Arial", 12).toString(),
                "enable_animations": True
            },
            "paths": {
                "songs": "data/songs/songs.json",
                "media": "data/media",
                "media_metadata": "data/media/media.json",
                "presentations": "data/presentations/presentations.json",
                "themes": "data/themes/themes.json",
                "bibles": "data/bibles"
            },
            "behavior": {
                "auto_save_interval": 300,  # seconds
                "confirm_before_delete": True,
                "default_playback_speed": 1.0
            },
            "advanced": {
                "developer_mode": False,
                "log_level": "INFO"
            },
            "accessibility": {
                "high_contrast": False
            }
        }
        self.settings: Dict[str, Any] = {}
        self.restart_required = False
        try:
            self._ensure_directories()
            self.load_settings()
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("SettingsManager", "INIT_001", f"Initialization failed: {e}")

    def _ensure_directories(self) -> None:
        """Create config directory if it doesn't exist."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            logger.debug("Ensured config directory exists")
        except Exception as e:
            raise SanctifyError("SettingsManager", "DIR_001", f"Error creating config directory: {e}")

    def load_settings(self) -> None:
        """Load settings from JSON file, falling back to defaults if needed."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings = self._merge_settings(self.default_settings, loaded_settings)
                    self._validate_settings()
            else:
                self.settings = self.default_settings.copy()
                self._save_settings()
            logger.info("Settings loaded successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted settings file {self.config_file}: {e}")
            self.settings = self.default_settings.copy()
            self._save_settings()
        except Exception as e:
            raise SanctifyError("SettingsManager", "LOAD_001", f"Error loading settings from {self.config_file}: {e}")

    def _merge_settings(self, defaults: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded settings with defaults."""
        result = defaults.copy()
        for key, value in loaded.items():
            if key in result and isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def _save_settings(self) -> None:
        """Save settings to JSON file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info("Settings saved successfully")
        except Exception as e:
            raise SanctifyError("SettingsManager", "SAVE_001", f"Error saving settings to {self.config_file}: {e}")

    def _validate_settings(self) -> None:
        """Validate settings values and log warnings for invalid ones."""
        try:
            for section, keys in self.settings.items():
                for key, value in keys.items():
                    if section == "general":
                        if key == "startup_screen" and value not in ["Songs", "Scriptures", "Media", "Presentations", "Themes"]:
                            logger.warning(f"Invalid startup_screen: {value}, resetting to default")
                            self.settings[section][key] = self.default_settings[section][key]
                        elif key == "language" and value not in ["English", "Spanish", "French", "German"]:
                            logger.warning(f"Invalid language: {value}, resetting to default")
                            self.settings[section][key] = self.default_settings[section][key]
                    elif section == "appearance":
                        if key == "theme" and value not in ["Light", "Dark"]:
                            logger.warning(f"Invalid theme: {value}, resetting to default")
                            self.settings[section][key] = self.default_settings[section][key]
                    elif section == "behavior":
                        if key == "auto_save_interval" and (not isinstance(value, int) or value < 60 or value > 3600):
                            logger.warning(f"Invalid auto_save_interval: {value}, resetting to default")
                            self.settings[section][key] = self.default_settings[section][key]
                        elif key == "default_playback_speed" and (not isinstance(value, float) or value < 0.5 or value > 2.0):
                            logger.warning(f"Invalid default_playback_speed: {value}, resetting to default")
                            self.settings[section][key] = self.default_settings[section][key]
                    elif section == "paths":
                        if not isinstance(value, str):
                            logger.warning(f"Invalid path type for {key}: {type(value)}, resetting to default")
                            self.settings[section][key] = self.default_settings[section][key]
            self._save_settings()
        except Exception as e:
            raise SanctifyError("SettingsManager", "VALIDATE_001", f"Error validating settings: {e}")

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Get a setting value from a section."""
        try:
            return self.settings[section][key]
        except KeyError:
            return default if default is not None else self.default_settings.get(section, {}).get(key)
        except Exception as e:
            raise SanctifyError("SettingsManager", "GET_001", f"Error retrieving setting {section}.{key}: {e}")

    def set_setting(self, section: str, key: str, value: Any) -> bool:
        """Set a setting value and save."""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
            self._save_settings()
            self.settings_changed.emit(section, key, value)
            logger.info(f"Set {section}.{key} = {value}")

            if section == "appearance" and key in ["theme", "ui_font"]:
                self.restart_required = True
            elif section == "advanced" and key == "developer_mode":
                logging.getLogger().setLevel(logging.DEBUG if value else logging.INFO)
                self.settings["advanced"]["log_level"] = "DEBUG" if value else "INFO"
                self._save_settings()
            return True
        except Exception as e:
            raise SanctifyError("SettingsManager", "SET_001", f"Failed to set setting {section}.{key}: {e}")

    def reset_settings(self) -> None:
        """Reset settings to defaults."""
        try:
            self.settings = self.default_settings.copy()
            self._save_settings()
            self.restart_required = True
            logger.info("Settings reset to defaults")
            for section, keys in self.settings.items():
                for key, value in keys.items():
                    self.settings_changed.emit(section, key, value)
        except Exception as e:
            raise SanctifyError("SettingsManager", "RESET_001", f"Error resetting settings: {e}")

    def export_settings(self, file_path: str) -> bool:
        """Export settings to a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info(f"Settings exported to {file_path}")
            return True
        except Exception as e:
            raise SanctifyError("SettingsManager", "EXPORT_001", f"Error exporting settings to {file_path}: {e}")

    def import_settings(self, file_path: str) -> bool:
        """Import settings from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            self.settings = self._merge_settings(self.default_settings, imported_settings)
            self._validate_settings()
            self._save_settings()
            self.restart_required = True
            logger.info(f"Settings imported from {file_path}")
            for section, keys in self.settings.items():
                for key, value in keys.items():
                    self.settings_changed.emit(section, key, value)
            return True
        except json.JSONDecodeError as e:
            raise SanctifyError("SettingsManager", "IMPORT_001", f"Corrupted JSON in {file_path}: {e}")
        except Exception as e:
            raise SanctifyError("SettingsManager", "IMPORT_002", f"Error importing settings from {file_path}: {e}")

    def validate_paths(self) -> Dict[str, bool]:
        """Validate configured paths."""
        try:
            paths = self.get_setting("paths", {}, self.default_settings["paths"])
            results = {}
            for key, path in paths.items():
                try:
                    if not isinstance(path, str):
                        raise SanctifyError("SettingsManager", f"PATH_TYPE_{key.upper()}", f"Invalid path type for {key}: {type(path)}, expected string")
                    if key in ["songs", "media_metadata", "presentations", "themes"]:
                        results[key] = os.path.isfile(path) and os.access(path, os.R_OK)
                    else:
                        results[key] = os.path.isdir(path) and os.access(path, os.R_OK)
                    if not results[key]:
                        logger.warning(f"Invalid path for {key}: {path}")
                except SanctifyError as e:
                    results[key] = False
                    raise e
                except Exception as e:
                    results[key] = False
                    raise SanctifyError("SettingsManager", f"PATH_VALIDATE_{key.upper()}", f"Error validating path {key} = {path}: {e}")
            return results
        except Exception as e:
            raise SanctifyError("SettingsManager", "PATH_VALIDATE_001", f"Error validating paths: {e}")

    def is_restart_required(self) -> bool:
        """Check if a restart is required."""
        return self.restart_required

    def clear_restart_required(self) -> None:
        """Clear the restart required flag."""
        self.restart_required = False
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Retrieve all current settings.

        Returns:
            Dict[str, Any]: A deep copy of the current settings dictionary.
        
        Raises:
            SanctifyError: If retrieval fails.
        """
        try:
            return json.loads(json.dumps(self.settings))  # Deep copy to avoid mutation
        except Exception as e:
            raise SanctifyError("SettingsManager", "GET_ALL_001", f"Failed to retrieve all settings: {e}")
        