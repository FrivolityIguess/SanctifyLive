import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from core.settings_manager import SettingsManager
from core.exceptions import SanctifyError
from models.media_model import MediaModel
from models.theme_model import ThemeModel

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

class PresentationModel:
    def __init__(self, settings_manager: SettingsManager, media_model: Optional[MediaModel] = None, theme_model: Optional[ThemeModel] = None):
        """Initialize PresentationModel with SettingsManager and optional MediaModel, ThemeModel."""
        self.settings_manager = settings_manager
        self.media_model = media_model
        self.theme_model = theme_model
        self.presentations: List[Dict] = []
        try:
            self._ensure_directories()
            self._load_presentations()
        except Exception as e:
            raise SanctifyError("PresentationModel", "INIT_001", f"Initialization failed: {e}")

    def _ensure_directories(self) -> None:
        """Create presentations directory if it doesn't exist."""
        presentations_file = self.settings_manager.get_setting("paths", "presentations", "data/presentations/presentations.json")
        if not isinstance(presentations_file, str):
            raise SanctifyError("PresentationModel", "PATH_001", f"Invalid presentations path type: {type(presentations_file)}, expected string")
        try:
            os.makedirs(os.path.dirname(presentations_file), exist_ok=True)
            logger.debug(f"Ensured presentations directory: {os.path.dirname(presentations_file)}")
        except Exception as e:
            raise SanctifyError("PresentationModel", "DIR_001", f"Error creating presentations directory: {e}")

    def _load_presentations(self) -> None:
        """Load presentation metadata from JSON file."""
        presentations_file = self.settings_manager.get_setting("paths", "presentations", "data/presentations/presentations.json")
        self.presentations.clear()
        if os.path.exists(presentations_file):
            try:
                with open(presentations_file, 'r', encoding='utf-8') as f:
                    loaded_presentations = json.load(f)
                    if not isinstance(loaded_presentations, list):
                        raise SanctifyError("PresentationModel", "LOAD_001", f"Presentations file {presentations_file} is not a list")
                    for item in loaded_presentations:
                        if self._validate_presentation(item):
                            self.presentations.append(item)
                        else:
                            logger.warning(f"Invalid presentation data: {item.get('name', 'Unknown')}")
            except json.JSONDecodeError as e:
                raise SanctifyError("PresentationModel", "LOAD_002", f"Error decoding JSON from {presentations_file}: {e}")
            except Exception as e:
                raise SanctifyError("PresentationModel", "LOAD_003", f"Error loading presentations from {presentations_file}: {e}")
        else:
            logger.warning(f"Presentations file not found: {presentations_file}, creating empty file")
            self._save_presentations()

    def _save_presentations(self) -> None:
        """Save presentation metadata to JSON file."""
        presentations_file = self.settings_manager.get_setting("paths", "presentations", "data/presentations/presentations.json")
        try:
            with open(presentations_file, 'w', encoding='utf-8') as f:
                json.dump(self.presentations, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved presentations to {presentations_file}")
        except Exception as e:
            raise SanctifyError("PresentationModel", "SAVE_001", f"Error saving presentations to {presentations_file}: {e}")

    def _validate_presentation(self, presentation: Dict) -> bool:
        """Validate presentation data structure and references."""
        try:
            valid = (
                isinstance(presentation, dict) and
                "id" in presentation and isinstance(presentation["id"], str) and
                "name" in presentation and isinstance(presentation["name"], str) and presentation["name"].strip() and
                "slides" in presentation and isinstance(presentation["slides"], list) and
                all(isinstance(slide, list) and len(slide) == 2 and
                    isinstance(slide[0], str) and slide[0] in ["Text", "Image", "Video"] and
                    isinstance(slide[1], str) for slide in presentation["slides"]) and
                "theme" in presentation and isinstance(presentation["theme"], str) and
                "tags" in presentation and isinstance(presentation["tags"], str) and
                "created_at" in presentation and isinstance(presentation["created_at"], str) and
                "updated_at" in presentation and isinstance(presentation["updated_at"], str)
            )
            if not valid:
                return False

            # Validate media paths and theme
            if self.media_model:
                media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
                for slide_type, content in presentation["slides"]:
                    if slide_type in ["Image", "Video"]:
                        if not os.path.exists(os.path.join(media_dir, content)):
                            logger.warning(f"Invalid media path in presentation {presentation['name']}: {content}")
                            return False
            if self.theme_model:
                if not self.theme_model.get_theme_by_id(presentation["theme"]):
                    logger.warning(f"Invalid theme ID in presentation {presentation['name']}: {presentation['theme']}")
                    return False
            return True
        except Exception as e:
            raise SanctifyError("PresentationModel", "VALIDATE_001", f"Error validating presentation: {e}")

    def get_all_presentations(self) -> List[Dict]:
        """Return all presentations sorted by name."""
        try:
            return sorted(self.presentations, key=lambda p: p["name"].lower())
        except Exception as e:
            raise SanctifyError("PresentationModel", "GET_ALL_001", f"Error retrieving presentations: {e}")

    def get_presentation_by_id(self, presentation_id: str) -> Optional[Dict]:
        """Retrieve a presentation by its ID."""
        try:
            return next((p for p in self.presentations if p["id"] == presentation_id), None)
        except Exception as e:
            raise SanctifyError("PresentationModel", "GET_BY_ID_001", f"Error retrieving presentation by ID {presentation_id}: {e}")

    def search_presentations(self, query: str, tag: str = "") -> List[Dict]:
        """Search presentations by name or tags."""
        try:
            query = query.lower().strip()
            tag = tag.lower().strip()
            results = []
            for presentation in self.presentations:
                matches_query = query in presentation["name"].lower() or any(query in t.lower() for t in presentation.get("tags", "").split(","))
                matches_tag = not tag or tag in presentation.get("tags", "").lower()
                if matches_query and matches_tag:
                    results.append(presentation)
            return sorted(results, key=lambda p: p["name"].lower())
        except Exception as e:
            raise SanctifyError("PresentationModel", "SEARCH_001", f"Error searching presentations with query {query}: {e}")

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags."""
        try:
            tags = set()
            for presentation in self.presentations:
                for tag in presentation.get("tags", "").split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
            return sorted(tags)
        except Exception as e:
            raise SanctifyError("PresentationModel", "GET_TAGS_001", f"Error retrieving tags: {e}")

    def create_presentation(self, name: str, theme: str = "default", slides: Optional[List[List[str]]] = None, tags: str = "") -> Optional[Dict]:
        """Create a new presentation."""
        try:
            if not name.strip():
                raise SanctifyError("PresentationModel", "CREATE_001", "Presentation name is required")
            if any(p["name"].lower() == name.lower() for p in self.presentations):
                raise SanctifyError("PresentationModel", "CREATE_002", f"Presentation already exists: {name}")

            presentation = {
                "id": str(uuid.uuid4()),
                "name": name,
                "theme": theme,
                "slides": slides or [],
                "tags": tags.strip(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            if not self._validate_presentation(presentation):
                raise SanctifyError("PresentationModel", "CREATE_003", f"Invalid presentation data for {name}")

            self.presentations.append(presentation)
            self._save_presentations()
            logger.info(f"Created presentation: {name}")
            return presentation
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("PresentationModel", "CREATE_004", f"Error creating presentation: {e}")

    def update_presentation(self, presentation_id: str, updated_data: Dict) -> bool:
        """Update an existing presentation."""
        try:
            presentation = self.get_presentation_by_id(presentation_id)
            if not presentation:
                raise SanctifyError("PresentationModel", "UPDATE_001", f"Presentation not found: {presentation_id}")

            if updated_data.get("name", "").strip() and updated_data["name"].lower() != presentation["name"].lower():
                if any(p["name"].lower() == updated_data["name"].lower() for p in self.presentations if p["id"] != presentation_id):
                    raise SanctifyError("PresentationModel", "UPDATE_002", f"Presentation name already exists: {updated_data['name']}")

            updated_presentation = presentation.copy()
            updated_presentation.update(updated_data)
            updated_presentation["id"] = presentation["id"]
            updated_presentation["created_at"] = presentation["created_at"]
            updated_presentation["updated_at"] = datetime.now().isoformat()
            if "slides" not in updated_data:
                updated_presentation["slides"] = presentation["slides"]
            if "theme" not in updated_data:
                updated_presentation["theme"] = presentation["theme"]
            if "tags" not in updated_data:
                updated_presentation["tags"] = presentation["tags"]

            if not self._validate_presentation(updated_presentation):
                raise SanctifyError("PresentationModel", "UPDATE_003", f"Invalid updated presentation data for {updated_presentation['name']}")

            self.presentations.remove(presentation)
            self.presentations.append(updated_presentation)
            self._save_presentations()
            logger.info(f"Updated presentation: {updated_presentation['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("PresentationModel", "UPDATE_004", f"Error updating presentation: {e}")

    def delete_presentation(self, presentation_id: str) -> bool:
        """Delete a presentation by its ID."""
        try:
            presentation = self.get_presentation_by_id(presentation_id)
            if not presentation:
                raise SanctifyError("PresentationModel", "DELETE_001", f"Presentation not found: {presentation_id}")
            self.presentations.remove(presentation)
            self._save_presentations()
            logger.info(f"Deleted presentation: {presentation['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("PresentationModel", "DELETE_002", f"Error deleting presentation: {e}")

    def duplicate_presentation(self, presentation_id: str) -> Optional[Dict]:
        """Duplicate a presentation with a new ID."""
        try:
            presentation = self.get_presentation_by_id(presentation_id)
            if not presentation:
                raise SanctifyError("PresentationModel", "DUPLICATE_001", f"Presentation not found: {presentation_id}")

            new_presentation = presentation.copy()
            new_presentation["id"] = str(uuid.uuid4())
            new_presentation["name"] = f"{presentation['name']} (Copy)"
            new_presentation["created_at"] = datetime.now().isoformat()
            new_presentation["updated_at"] = new_presentation["created_at"]

            if any(p["name"].lower() == new_presentation["name"].lower() for p in self.presentations):
                raise SanctifyError("PresentationModel", "DUPLICATE_002", f"Duplicate presentation name already exists: {new_presentation['name']}")

            self.presentations.append(new_presentation)
            self._save_presentations()
            logger.info(f"Duplicated presentation: {new_presentation['name']}")
            return new_presentation
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("PresentationModel", "DUPLICATE_003", f"Error duplicating presentation: {e}")

    def import_from_ppt(self, ppt_path: str) -> Optional[Dict]:
        """Import a presentation from PPTX (placeholder)."""
        try:
            name = os.path.splitext(os.path.basename(ppt_path))[0]
            presentation = {
                "id": str(uuid.uuid4()),
                "name": name,
                "theme": "default",
                "slides": [
                    ["Text", "Slide 1: Imported content..."],
                    ["Text", "Slide 2: More content..."]
                ],
                "tags": "imported,pptx",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            if not self._validate_presentation(presentation):
                raise SanctifyError("PresentationModel", "IMPORT_001", f"Invalid imported presentation data for {name}")
            self.presentations.append(presentation)
            self._save_presentations()
            logger.info(f"Imported presentation: {name}")
            return presentation
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("PresentationModel", "IMPORT_002", f"Failed to import PPTX: {e}")