import os
import json
import logging
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

class ScriptureModel:
    def __init__(self, settings_manager: SettingsManager):
        """Initialize ScriptureModel with SettingsManager."""
        self.settings_manager = settings_manager
        self.bible_root = self.settings_manager.get_setting("paths", "bibles", "data/bibles")
        self.bibles: Dict[str, Dict] = {}
        try:
            self._load_bibles()
        except Exception as e:
            raise SanctifyError("ScriptureModel", "INIT_001", f"Initialization failed: {e}")

    def _ensure_directories(self) -> None:
        """Create bibles directory if it doesn't exist."""
        if not isinstance(self.bible_root, str):
            raise SanctifyError("ScriptureModel", "PATH_001", f"Invalid bibles path type: {type(self.bible_root)}, expected string")
        try:
            os.makedirs(self.bible_root, exist_ok=True)
            logger.debug(f"Ensured bibles directory: {self.bible_root}")
        except Exception as e:
            raise SanctifyError("ScriptureModel", "DIR_001", f"Error creating bibles directory: {e}")

    def _load_bibles(self) -> None:
        """Load all available bibles from the bibles directory."""
        self._ensure_directories()
        self.bibles.clear()
        try:
            for file in os.listdir(self.bible_root):
                if file.endswith('.json'):
                    file_path = os.path.join(self.bible_root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            bible_data = json.load(f)
                            if self._validate_bible(bible_data):
                                bible_id = os.path.splitext(file)[0]
                                self.bibles[bible_id] = bible_data
                                logger.debug(f"Loaded bible: {bible_id}")
                            else:
                                logger.warning(f"Invalid bible data: {file}")
                    except json.JSONDecodeError as e:
                        raise SanctifyError("ScriptureModel", "LOAD_002", f"Error decoding JSON from {file_path}: {e}")
                    except Exception as e:
                        raise SanctifyError("ScriptureModel", "LOAD_003", f"Error loading bible from {file_path}: {e}")
            if not self.bibles:
                logger.warning(f"No valid bibles found in {self.bible_root}")
        except Exception as e:
            raise SanctifyError("ScriptureModel", "LOAD_001", f"Error scanning bibles directory {self.bible_root}: {e}")

    def _validate_bible(self, bible: Dict) -> bool:
        """Validate bible data structure."""
        try:
            return (
                isinstance(bible, dict) and
                "name" in bible and isinstance(bible["name"], str) and bible["name"].strip() and
                "books" in bible and isinstance(bible["books"], list) and
                all(
                    isinstance(book, dict) and
                    "name" in book and isinstance(book["name"], str) and book["name"].strip() and
                    "chapters" in book and isinstance(book["chapters"], list) and
                    all(
                        isinstance(chapter, dict) and
                        "chapter" in chapter and isinstance(chapter["chapter"], int) and chapter["chapter"] > 0 and
                        "verses" in chapter and isinstance(chapter["verses"], list) and
                        all(
                            isinstance(verse, dict) and
                            "verse" in verse and isinstance(verse["verse"], int) and verse["verse"] > 0 and
                            "text" in verse and isinstance(verse["text"], str) and verse["text"].strip()
                            for verse in chapter["verses"]
                        )
                        for chapter in book["chapters"]
                    )
                    for book in bible["books"]
                )
            )
        except Exception as e:
            raise SanctifyError("ScriptureModel", "VALIDATE_001", f"Error validating bible: {e}")

    def get_all_bibles(self) -> List[Dict]:
        """Return a list of all loaded bibles."""
        try:
            return sorted([{"id": k, "name": v["name"]} for k, v in self.bibles.items()], key=lambda x: x["name"].lower())
        except Exception as e:
            raise SanctifyError("ScriptureModel", "GET_ALL_001", f"Error retrieving bibles: {e}")

    def get_bible_by_id(self, bible_id: str) -> Optional[Dict]:
        """Retrieve a bible by its ID."""
        try:
            return self.bibles.get(bible_id)
        except Exception as e:
            raise SanctifyError("ScriptureModel", "GET_BY_ID_001", f"Error retrieving bible by ID {bible_id}: {e}")

    def get_books(self, bible_id: str) -> List[Dict]:
        """Return a list of books for a specific bible."""
        try:
            bible = self.get_bible_by_id(bible_id)
            if not bible:
                raise SanctifyError("ScriptureModel", "GET_BOOKS_001", f"Bible not found: {bible_id}")
            return sorted([{"name": book["name"]} for book in bible["books"]], key=lambda x: x["name"].lower())
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ScriptureModel", "GET_BOOKS_002", f"Error retrieving books for bible {bible_id}: {e}")

    def get_chapters(self, bible_id: str, book_name: str) -> List[int]:
        """Return a list of chapter numbers for a specific book."""
        try:
            bible = self.get_bible_by_id(bible_id)
            if not bible:
                raise SanctifyError("ScriptureModel", "GET_CHAPTERS_001", f"Bible not found: {bible_id}")
            book = next((b for b in bible["books"] if b["name"].lower() == book_name.lower()), None)
            if not book:
                raise SanctifyError("ScriptureModel", "GET_CHAPTERS_002", f"Book not found: {book_name}")
            return sorted([chapter["chapter"] for chapter in book["chapters"]])
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ScriptureModel", "GET_CHAPTERS_003", f"Error retrieving chapters for {book_name} in bible {bible_id}: {e}")

    def get_verses(self, bible_id: str, book_name: str, chapter_number: int) -> List[Dict]:
        """Return a list of verses for a specific chapter."""
        try:
            bible = self.get_bible_by_id(bible_id)
            if not bible:
                raise SanctifyError("ScriptureModel", "GET_VERSES_001", f"Bible not found: {bible_id}")
            book = next((b for b in bible["books"] if b["name"].lower() == book_name.lower()), None)
            if not book:
                raise SanctifyError("ScriptureModel", "GET_VERSES_002", f"Book not found: {book_name}")
            chapter = next((c for c in book["chapters"] if c["chapter"] == chapter_number), None)
            if not chapter:
                raise SanctifyError("ScriptureModel", "GET_VERSES_003", f"Chapter not found: {chapter_number}")
            return sorted(chapter["verses"], key=lambda x: x["verse"])
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ScriptureModel", "GET_VERSES_004", f"Error retrieving verses for {book_name} chapter {chapter_number} in bible {bible_id}: {e}")

    def search_verses(self, bible_id: str, query: str) -> List[Dict]:
        """Search verses containing the query string."""
        try:
            bible = self.get_bible_by_id(bible_id)
            if not bible:
                raise SanctifyError("ScriptureModel", "SEARCH_001", f"Bible not found: {bible_id}")
            query = query.lower().strip()
            results = []
            for book in bible["books"]:
                for chapter in book["chapters"]:
                    for verse in chapter["verses"]:
                        if query in verse["text"].lower():
                            results.append({
                                "book": book["name"],
                                "chapter": chapter["chapter"],
                                "verse": verse["verse"],
                                "text": verse["text"]
                            })
            return sorted(results, key=lambda x: (x["book"].lower(), x["chapter"], x["verse"]))
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ScriptureModel", "SEARCH_002", f"Error searching verses in bible {bible_id}: {e}")

    def add_bible(self, bible_data: Dict, bible_id: str) -> bool:
        """Add a new bible to the collection."""
        try:
            if bible_id in self.bibles:
                raise SanctifyError("ScriptureModel", "ADD_001", f"Bible already exists: {bible_id}")
            if not self._validate_bible(bible_data):
                raise SanctifyError("ScriptureModel", "ADD_002", f"Invalid bible data for {bible_data.get('name', 'Unknown')}")
            file_path = os.path.join(self.bible_root, f"{bible_id}.json")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(bible_data, f, indent=4, ensure_ascii=False)
                self.bibles[bible_id] = bible_data
                logger.info(f"Added bible: {bible_id}")
                return True
            except Exception as e:
                raise SanctifyError("ScriptureModel", "ADD_003", f"Error saving bible {bible_id} to {file_path}: {e}")
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ScriptureModel", "ADD_004", f"Error adding bible: {e}")

    def delete_bible(self, bible_id: str) -> bool:
        """Delete a bible from the collection."""
        try:
            bible = self.get_bible_by_id(bible_id)
            if not bible:
                raise SanctifyError("ScriptureModel", "DELETE_001", f"Bible not found: {bible_id}")
            file_path = os.path.join(self.bible_root, f"{bible_id}.json")
            try:
                os.remove(file_path)
                del self.bibles[bible_id]
                logger.info(f"Deleted bible: {bible_id}")
                return True
            except Exception as e:
                raise SanctifyError("ScriptureModel", "DELETE_002", f"Error deleting bible file {file_path}: {e}")
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("ScriptureModel", "DELETE_003", f"Error deleting bible: {e}")