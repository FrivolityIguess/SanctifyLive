import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from core.settings_manager import SettingsManager
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

class ThemeModel:
    def __init__(self, settings_manager: SettingsManager):
        """Initialize ThemeModel with SettingsManager."""
        self.settings_manager = settings_manager
        self.themes: List[Dict] = []
        try:
            self._ensure_directories()
            self._load_themes()
        except Exception as e:
            raise SanctifyError("ThemeModel", "INIT_001", f"Initialization failed: {e}")

    def _ensure_directories(self) -> None:
        """Create themes directory if it doesn't exist."""
        theme_file = self.settings_manager.get_setting("paths", "themes", "data/themes/themes.json")
        if not isinstance(theme_file, str):
            raise SanctifyError("ThemeModel", "PATH_001", f"Invalid themes path type: {type(theme_file)}, expected string")
        try:
            os.makedirs(os.path.dirname(theme_file), exist_ok=True)
            logger.debug(f"Ensured themes directory: {os.path.dirname(theme_file)}")
        except Exception as e:
            raise SanctifyError("ThemeModel", "DIR_001", f"Error creating themes directory: {e}")

    def _load_themes(self) -> None:
        """Load theme metadata from JSON file."""
        theme_file = self.settings_manager.get_setting("paths", "themes", "data/themes/themes.json")
        self.themes.clear()
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    loaded_themes = json.load(f)
                    if not isinstance(loaded_themes, list):
                        raise SanctifyError("ThemeModel", "LOAD_001", f"Themes file {theme_file} is not a list")
                    for item in loaded_themes:
                        if self._validate_theme(item):
                            self.themes.append(item)
                        else:
                            logger.warning(f"Invalid theme data: {item.get('name', 'Unknown')}")
            except json.JSONDecodeError as e:
                raise SanctifyError("ThemeModel", "LOAD_002", f"Error decoding JSON from {theme_file}: {e}")
            except Exception as e:
                raise SanctifyError("ThemeModel", "LOAD_003", f"Error loading themes from {theme_file}: {e}")
        else:
            logger.warning(f"Themes file not found: {theme_file}, creating empty file")
            self._save_themes()

    def _save_themes(self) -> None:
        """Save theme metadata to JSON file."""
        theme_file = self.settings_manager.get_setting("paths", "themes", "data/themes/themes.json")
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(self.themes, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved themes to {theme_file}")
        except Exception as e:
            raise SanctifyError("ThemeModel", "SAVE_001", f"Error saving themes to {theme_file}: {e}")

    def _validate_theme(self, theme: Dict) -> bool:
        """Validate theme data structure."""
        try:
            return (
                isinstance(theme, dict) and
                "id" in theme and isinstance(theme["id"], str) and
                "name" in theme and isinstance(theme["name"], str) and theme["name"].strip() and
                "context" in theme and theme["context"] in ["Songs", "Scriptures", "Presentations"] and
                "alignment" in theme and theme["alignment"] in ["Left", "Centered", "Right"] and
                "font_color" in theme and isinstance(theme["font_color"], str) and theme["font_color"].startswith("#") and
                "background_color" in theme and isinstance(theme["background_color"], str) and theme["background_color"].startswith("#") and
                "font_size" in theme and isinstance(theme["font_size"], int) and theme["font_size"] > 0 and
                "font_family" in theme and isinstance(theme["font_family"], str) and theme["font_family"].strip() and
                "tags" in theme and isinstance(theme["tags"], str) and
                "created_at" in theme and isinstance(theme["created_at"], str) and
                "updated_at" in theme and isinstance(theme["updated_at"], str)
            )
        except Exception as e:
            raise SanctifyError("ThemeModel", "VALIDATE_001", f"Error validating theme: {e}")

    def get_all_themes(self, context: str = "") -> List[Dict]:
        """Return all themes or filtered by context, sorted by name."""
        try:
            themes = self.themes if not context else [t for t in self.themes if t["context"] == context]
            return sorted(themes, key=lambda t: t["name"].lower())
        except Exception as e:
            raise SanctifyError("ThemeModel", "GET_ALL_001", f"Error retrieving themes: {e}")

    def get_theme_by_id(self, theme_id: str) -> Optional[Dict]:
        """Retrieve a theme by its ID."""
        try:
            return next((t for t in self.themes if t["id"] == theme_id), None)
        except Exception as e:
            raise SanctifyError("ThemeModel", "GET_BY_ID_001", f"Error retrieving theme by ID {theme_id}: {e}")

    def search_themes(self, query: str, context: str = "", tag: str = "") -> List[Dict]:
        """Search themes by name or tags, optionally filtered by context."""
        try:
            query = query.lower().strip()
            tag = tag.lower().strip()
            results = []
            for theme in self.themes:
                if context and theme["context"] != context:
                    continue
                matches_query = query in theme["name"].lower() or any(query in t.lower() for t in theme.get("tags", "").split(","))
                matches_tag = not tag or tag in theme.get("tags", "").lower()
                if matches_query and matches_tag:
                    results.append(theme)
            return sorted(results, key=lambda t: t["name"].lower())
        except Exception as e:
            raise SanctifyError("ThemeModel", "SEARCH_001", f"Error searching themes with query {query}: {e}")

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags."""
        try:
            tags = set()
            for theme in self.themes:
                for tag in theme.get("tags", "").split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
            return sorted(tags)
        except Exception as e:
            raise SanctifyError("ThemeModel", "GET_TAGS_001", f"Error retrieving tags: {e}")

    def create_theme(self, name: str, context: str, alignment: str, font_color: str, background_color: str, font_size: int, font_family: str, tags: str = "") -> Optional[Dict]:
        """Create a new theme."""
        try:
            if not name.strip():
                raise SanctifyError("ThemeModel", "CREATE_001", "Theme name is required")
            if any(t["name"].lower() == name.lower() for t in self.themes):
                raise SanctifyError("ThemeModel", "CREATE_002", f"Theme already exists: {name}")

            theme = {
                "id": str(uuid.uuid4()),
                "name": name,
                "context": context,
                "alignment": alignment,
                "font_color": font_color,
                "background_color": background_color,
                "font_size": font_size,
                "font_family": font_family,
                "tags": tags.strip(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            if not self._validate_theme(theme):
                raise SanctifyError("ThemeModel", "CREATE_003", f"Invalid theme data for {name}")

            self.themes.append(theme)
            self._save_themes()
            logger.info(f"Created theme: {name}")
            return theme
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ThemeModel", "CREATE_004", f"Error creating theme: {e}")

    def update_theme(self, theme_id: str, updated_data: Dict) -> bool:
        """Update an existing theme."""
        try:
            theme = self.get_theme_by_id(theme_id)
            if not theme:
                raise SanctifyError("ThemeModel", "UPDATE_001", f"Theme not found: {theme_id}")

            if updated_data.get("name", "").strip() and updated_data["name"].lower() != theme["name"].lower():
                if any(t["name"].lower() == updated_data["name"].lower() for t in self.themes if t["id"] != theme_id):
                    raise SanctifyError("ThemeModel", "UPDATE_002", f"Theme name already exists: {updated_data['name']}")

            updated_theme = theme.copy()
            updated_theme.update(updated_data)
            updated_theme["id"] = theme["id"]
            updated_theme["created_at"] = theme["created_at"]
            updated_theme["updated_at"] = datetime.now().isoformat()

            if not self._validate_theme(updated_theme):
                raise SanctifyError("ThemeModel", "UPDATE_003", f"Invalid updated theme data for {updated_theme['name']}")

            self.themes.remove(theme)
            self.themes.append(updated_theme)
            self._save_themes()
            logger.info(f"Updated theme: {updated_theme['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ThemeModel", "UPDATE_004", f"Error updating theme: {e}")

    def delete_theme(self, theme_id: str) -> bool:
        """Delete a theme by its ID."""
        try:
            theme = self.get_theme_by_id(theme_id)
            if not theme:
                raise SanctifyError("ThemeModel", "DELETE_001", f"Theme not found: {theme_id}")
            self.themes.remove(theme)
            self._save_themes()
            logger.info(f"Deleted theme: {theme['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ThemeModel", "DELETE_002", f"Error deleting theme: {e}")

    def duplicate_theme(self, theme_id: str) -> Optional[Dict]:
        """Duplicate a theme with a new ID."""
        try:
            theme = self.get_theme_by_id(theme_id)
            if not theme:
                raise SanctifyError("ThemeModel", "DUPLICATE_001", f"Theme not found: {theme_id}")

            new_theme = theme.copy()
            new_theme["id"] = str(uuid.uuid4())
            new_theme["name"] = f"{theme['name']} (Copy)"
            new_theme["created_at"] = datetime.now().isoformat()
            new_theme["updated_at"] = new_theme["created_at"]

            if any(t["name"].lower() == new_theme["name"].lower() for t in self.themes):
                raise SanctifyError("ThemeModel", "DUPLICATE_002", f"Duplicate theme name already exists: {new_theme['name']}")

            self.themes.append(new_theme)
            self._save_themes()
            logger.info(f"Duplicated theme: {new_theme['name']}")
            return new_theme
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ThemeModel", "DUPLICATE_003", f"Error duplicating theme: {e}")