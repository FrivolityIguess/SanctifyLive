import os
import json
import uuid
import shutil
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

class MediaModel:
    SUPPORTED_FORMATS = {
        "Images": [".jpg", ".jpeg", ".png", ".bmp"],
        "Videos": [".mp4", ".mov", ".avi"],
        "Gifs": [".gif"]
    }

    def __init__(self, settings_manager: SettingsManager):
        """Initialize MediaModel with SettingsManager."""
        self.settings_manager = settings_manager
        self.media: List[Dict] = []
        try:
            self._ensure_directories()
            self._load_media()
        except Exception as e:
            raise SanctifyError("MediaModel", "INIT_001", f"Initialization failed: {e}")

    def _ensure_directories(self) -> None:
        """Create media directories if they don't exist."""
        media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
        if not isinstance(media_dir, str):
            raise SanctifyError("MediaModel", "PATH_001", f"Invalid media directory type: {type(media_dir)}, expected string")
        try:
            os.makedirs(media_dir, exist_ok=True)
            for category in self.SUPPORTED_FORMATS:
                os.makedirs(os.path.join(media_dir, category), exist_ok=True)
            logger.debug(f"Ensured media directories: {media_dir}")
        except Exception as e:
            raise SanctifyError("MediaModel", "DIR_001", f"Failed to create media directories: {e}")

    def _load_media(self) -> None:
        """Load media metadata from JSON file."""
        media_file = self.settings_manager.get_setting("paths", "media_metadata", "data/media/media.json")
        if not isinstance(media_file, str):
            raise SanctifyError("MediaModel", "PATH_002", f"Invalid media metadata path type: {type(media_file)}, expected string")

        self.media.clear()
        if os.path.exists(media_file):
            try:
                with open(media_file, 'r', encoding='utf-8') as f:
                    loaded_media = json.load(f)
                    if not isinstance(loaded_media, list):
                        raise SanctifyError("MediaModel", "LOAD_001", f"Media file {media_file} is not a list")
                    for item in loaded_media:
                        if self._validate_media(item):
                            self.media.append(item)
                        else:
                            logger.warning(f"Invalid media data: {item.get('name', 'Unknown')}")
            except json.JSONDecodeError as e:
                raise SanctifyError("MediaModel", "LOAD_002", f"Error decoding JSON from {media_file}: {e}")
            except Exception as e:
                raise SanctifyError("MediaModel", "LOAD_003", f"Error loading media from {media_file}: {e}")
        else:
            logger.warning(f"Media metadata file not found: {media_file}, creating empty file")
            self._save_media()

    def _save_media(self) -> None:
        """Save media metadata to JSON file."""
        media_file = self.settings_manager.get_setting("paths", "media_metadata", "data/media/media.json")
        try:
            os.makedirs(os.path.dirname(media_file), exist_ok=True)
            with open(media_file, 'w', encoding='utf-8') as f:
                json.dump(self.media, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved media metadata to {media_file}")
        except Exception as e:
            raise SanctifyError("MediaModel", "SAVE_001", f"Error saving media to {media_file}: {e}")

    def _validate_media(self, media: Dict) -> bool:
        """Validate media data structure."""
        try:
            media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
            return (
                isinstance(media, dict) and
                "id" in media and isinstance(media["id"], str) and
                "name" in media and isinstance(media["name"], str) and media["name"].strip() and
                "path" in media and isinstance(media["path"], str) and os.path.exists(os.path.join(media_dir, media["path"])) and
                "category" in media and media["category"] in self.SUPPORTED_FORMATS and
                "tags" in media and isinstance(media["tags"], str) and
                "scaling" in media and media["scaling"] in ["stretch", "fit", "fill"] and
                "created_at" in media and isinstance(media["created_at"], str) and
                "updated_at" in media and isinstance(media["updated_at"], str) and
                "is_logo" in media and isinstance(media["is_logo"], bool)
            )
        except Exception as e:
            raise SanctifyError("MediaModel", "VALIDATE_001", f"Error validating media: {e}")

    def get_all_media(self, category: str = "") -> List[Dict]:
        """Return all media or filtered by category, sorted by name."""
        try:
            media = self.media if not category else [m for m in self.media if m["category"] == category]
            return sorted(media, key=lambda m: m["name"].lower())
        except Exception as e:
            raise SanctifyError("MediaModel", "GET_ALL_001", f"Error retrieving media: {e}")

    def get_media_by_id(self, media_id: str) -> Optional[Dict]:
        """Retrieve a media item by its ID."""
        try:
            return next((m for m in self.media if m["id"] == media_id), None)
        except Exception as e:
            raise SanctifyError("MediaModel", "GET_BY_ID_001", f"Error retrieving media by ID {media_id}: {e}")

    def search_media(self, query: str, category: str = "", tag: str = "") -> List[Dict]:
        """Search media by name or tags, optionally filtered by category."""
        try:
            query = query.lower().strip()
            tag = tag.lower().strip()
            results = []
            for media in self.media:
                if category and media["category"] != category:
                    continue
                matches_query = query in media["name"].lower() or any(query in t.lower() for t in media.get("tags", "").split(","))
                matches_tag = not tag or tag in media.get("tags", "").lower()
                if matches_query and matches_tag:
                    results.append(media)
            return sorted(results, key=lambda m: m["name"].lower())
        except Exception as e:
            raise SanctifyError("MediaModel", "SEARCH_001", f"Error searching media with query {query}: {e}")

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags."""
        try:
            tags = set()
            for media in self.media:
                for tag in media.get("tags", "").split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
            return sorted(tags)
        except Exception as e:
            raise SanctifyError("MediaModel", "GET_TAGS_001", f"Error retrieving tags: {e}")

    def add_media(self, source_path: str, category: str, display_name: str = "", tags: str = "", scaling: str = "fit") -> Optional[Dict]:
        """Add a new media file and metadata."""
        try:
            media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
            ext = os.path.splitext(source_path)[1].lower()
            if not any(ext in formats for formats in self.SUPPORTED_FORMATS.values()):
                raise SanctifyError("MediaModel", "ADD_001", f"Unsupported media format: {ext}")
            if category not in self.SUPPORTED_FORMATS:
                raise SanctifyError("MediaModel", "ADD_002", f"Invalid category: {category}")

            media_id = str(uuid.uuid4())
            display_name = display_name or os.path.basename(source_path)
            filename = f"{media_id}{ext}"
            target_path = os.path.join(media_dir, category, filename)

            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(source_path, target_path)
            except Exception as e:
                raise SanctifyError("MediaModel", "ADD_003", f"Failed to copy media file {source_path} to {target_path}: {e}")

            media_data = {
                "id": media_id,
                "name": display_name,
                "path": os.path.join(category, filename),
                "category": category,
                "tags": tags.strip(),
                "scaling": scaling.lower(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_logo": False
            }

            if any(m["path"] == media_data["path"] for m in self.media):
                try:
                    os.remove(target_path)
                except Exception:
                    pass
                raise SanctifyError("MediaModel", "ADD_004", f"Media already exists: {target_path}")

            if not self._validate_media(media_data):
                try:
                    os.remove(target_path)
                except Exception:
                    pass
                raise SanctifyError("MediaModel", "ADD_005", f"Invalid media data for {display_name}")

            self.media.append(media_data)
            self._save_media()
            logger.info(f"Added media: {display_name}")
            return media_data
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("MediaModel", "ADD_006", f"Error adding media: {e}")

    def update_media(self, media_id: str, media_data: Dict) -> bool:
        """Update media metadata."""
        try:
            media = self.get_media_by_id(media_id)
            if not media:
                raise SanctifyError("MediaModel", "UPDATE_001", f"Media not found: {media_id}")

            media_data = media_data.copy()
            media_data["id"] = media["id"]
            media_data["path"] = media["path"]
            media_data["created_at"] = media["created_at"]
            media_data["updated_at"] = datetime.now().isoformat()
            media_data["is_logo"] = media["is_logo"]
            if "category" not in media_data:
                media_data["category"] = media["category"]
            if "name" not in media_data:
                media_data["name"] = media["name"]
            if "tags" not in media_data:
                media_data["tags"] = media["tags"]
            if "scaling" not in media_data:
                media_data["scaling"] = media["scaling"]

            media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
            if media_data["name"] != media["name"] or media_data["category"] != media["category"]:
                new_filename = f"{media_id}{os.path.splitext(media['path'])[1]}"
                new_path = os.path.join(media_dir, media_data["category"], new_filename)
                try:
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    os.rename(os.path.join(media_dir, media["path"]), os.path.join(media_dir, new_path))
                    media_data["path"] = os.path.join(media_data["category"], new_filename)
                except Exception as e:
                    raise SanctifyError("MediaModel", "UPDATE_002", f"Failed to rename media from {media['path']} to {new_path}: {e}")

            if not self._validate_media(media_data):
                raise SanctifyError("MediaModel", "UPDATE_003", f"Invalid media data for {media_data['name']}")

            self.media.remove(media)
            self.media.append(media_data)
            self._save_media()
            logger.info(f"Updated media: {media_data['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("MediaModel", "UPDATE_004", f"Error updating media: {e}")

    def delete_media(self, media_id: str) -> bool:
        """Delete a media file and its metadata."""
        try:
            media = self.get_media_by_id(media_id)
            if not media:
                raise SanctifyError("MediaModel", "DELETE_001", f"Media not found: {media_id}")
            try:
                media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
                os.remove(os.path.join(media_dir, media["path"]))
            except Exception as e:
                raise SanctifyError("MediaModel", "DELETE_002", f"Failed to delete media file {media['path']}: {e}")
            self.media.remove(media)
            self._save_media()
            logger.info(f"Deleted media: {media['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("MediaModel", "DELETE_003", f"Error deleting media: {e}")

    def duplicate_media(self, media_id: str) -> Optional[Dict]:
        """Duplicate a media file and its metadata."""
        try:
            media = self.get_media_by_id(media_id)
            if not media:
                raise SanctifyError("MediaModel", "DUPLICATE_001", f"Media not found: {media_id}")

            media_dir = self.settings_manager.get_setting("paths", "media", "data/media")
            new_id = str(uuid.uuid4())
            ext = os.path.splitext(media["path"])[1]
            new_filename = f"{new_id}{ext}"
            new_path = os.path.join(media_dir, media["category"], new_filename)
            new_name = f"{media['name'].rsplit('.', 1)[0]} (Copy).{media['name'].rsplit('.', 1)[1]}"

            try:
                shutil.copy2(os.path.join(media_dir, media["path"]), new_path)
            except Exception as e:
                raise SanctifyError("MediaModel", "DUPLICATE_002", f"Failed to duplicate media {media['path']} to {new_path}: {e}")

            new_media = {
                "id": new_id,
                "name": new_name,
                "path": os.path.join(media["category"], new_filename),
                "category": media["category"],
                "tags": media["tags"],
                "scaling": media["scaling"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_logo": False
            }

            if not self._validate_media(new_media):
                try:
                    os.remove(new_path)
                except Exception:
                    pass
                raise SanctifyError("MediaModel", "DUPLICATE_003", f"Invalid duplicated media data for {new_name}")

            self.media.append(new_media)
            self._save_media()
            logger.info(f"Duplicated media: {new_name}")
            return new_media
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("MediaModel", "DUPLICATE_004", f"Error duplicating media: {e}")

    def set_logo(self, media_id: str) -> bool:
        """Set a media file as the logo."""
        try:
            media = self.get_media_by_id(media_id)
            if not media or media["category"] != "Images":
                raise SanctifyError("MediaModel", "SET_LOGO_001", f"Invalid logo media: {media_id} (must be an image)")
            for m in self.media:
                m["is_logo"] = (m["id"] == media_id)
            self._save_media()
            logger.info(f"Set logo: {media['name']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("MediaModel", "SET_LOGO_002", f"Error setting logo: {e}")

    def get_logo_media(self) -> Optional[Dict]:
        """Return the current logo media."""
        try:
            return next((m for m in self.media if m.get("is_logo", False)), None)
        except Exception as e:
            raise SanctifyError("MediaModel", "GET_LOGO_001", f"Error retrieving logo media: {e}")