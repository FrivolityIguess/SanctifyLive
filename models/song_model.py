import os
import json
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

class SongModel:
    def __init__(self, settings_manager: SettingsManager):
        """Initialize SongModel with SettingsManager."""
        self.settings_manager = settings_manager
        self.songs: List[Dict] = []
        try:
            self._load_songs()
        except Exception as e:
            raise SanctifyError("SongModel", "INIT_001", f"Initialization failed: {e}")

    def _load_songs(self) -> None:
        """Load songs from the JSON file into memory."""
        songs_path = self.settings_manager.get_setting("paths", "songs", "data/songs/songs.json")
        if not isinstance(songs_path, str):
            raise SanctifyError("SongModel", "PATH_001", f"Invalid songs path type: {type(songs_path)}, expected string")

        self.songs.clear()
        if os.path.exists(songs_path):
            try:
                with open(songs_path, 'r', encoding='utf-8') as f:
                    loaded_songs = json.load(f)
                    if not isinstance(loaded_songs, list):
                        raise SanctifyError("SongModel", "LOAD_001", f"Songs file {songs_path} is not a list")
                    for song in loaded_songs:
                        if self._validate_song(song):
                            self.songs.append(song)
                        else:
                            logger.warning(f"Invalid song data: {song.get('title', 'Unknown')}")
            except json.JSONDecodeError as e:
                raise SanctifyError("SongModel", "LOAD_002", f"Error decoding JSON from {songs_path}: {e}")
            except Exception as e:
                raise SanctifyError("SongModel", "LOAD_003", f"Error loading songs from {songs_path}: {e}")
        else:
            logger.warning(f"Songs file not found: {songs_path}, creating empty file")
            self._save_songs()

    def _save_songs(self) -> None:
        """Save all songs to the JSON file."""
        songs_path = self.settings_manager.get_setting("paths", "songs", "data/songs/songs.json")
        try:
            os.makedirs(os.path.dirname(songs_path), exist_ok=True)
            with open(songs_path, 'w', encoding='utf-8') as f:
                json.dump(self.songs, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved songs to {songs_path}")
        except Exception as e:
            raise SanctifyError("SongModel", "SAVE_001", f"Error saving songs to {songs_path}: {e}")

    def _validate_song(self, song: Dict) -> bool:
        """Validate song data structure."""
        try:
            return (
                isinstance(song, dict) and
                "title" in song and isinstance(song["title"], str) and song["title"].strip() and
                "sections" in song and isinstance(song["sections"], list) and
                all(isinstance(section, list) and len(section) == 2 and
                    isinstance(section[0], str) and isinstance(section[1], str) for section in song["sections"]) and
                "tags" in song and isinstance(song["tags"], str) and
                "created_at" in song and isinstance(song["created_at"], str) and
                "updated_at" in song and isinstance(song["updated_at"], str)
            )
        except Exception as e:
            raise SanctifyError("SongModel", "VALIDATE_001", f"Error validating song: {e}")

    def get_all_songs(self) -> List[Dict]:
        """Return all songs sorted by title."""
        try:
            return sorted(self.songs, key=lambda s: s["title"].lower())
        except Exception as e:
            raise SanctifyError("SongModel", "GET_ALL_001", f"Error retrieving songs: {e}")

    def get_song_by_title(self, title: str) -> Optional[Dict]:
        """Retrieve a song by its exact title."""
        try:
            return next((song for song in self.songs if song["title"].lower() == title.lower()), None)
        except Exception as e:
            raise SanctifyError("SongModel", "GET_BY_TITLE_001", f"Error retrieving song by title {title}: {e}")

    def search_songs(self, query: str, search_mode: str = "title", tag: str = "") -> List[Dict]:
        """Search songs by title, lyrics, or tags."""
        try:
            query = query.lower().strip()
            tag = tag.lower().strip()
            results = []
            for song in self.songs:
                matches_query = False
                if search_mode == "title":
                    matches_query = query in song["title"].lower()
                elif search_mode == "lyrics":
                    matches_query = any(query in text.lower() for _, text in song.get("sections", []))
                elif search_mode == "tags":
                    matches_query = any(query in t.lower() for t in song.get("tags", "").split(","))
                matches_tag = not tag or tag in song.get("tags", "").lower()
                if matches_query and matches_tag:
                    results.append(song)
            return sorted(results, key=lambda s: s["title"].lower())
        except Exception as e:
            raise SanctifyError("SongModel", "SEARCH_001", f"Error searching songs with query {query}: {e}")

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags across all songs."""
        try:
            tags = set()
            for song in self.songs:
                for tag in song.get("tags", "").split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
            return sorted(tags)
        except Exception as e:
            raise SanctifyError("SongModel", "GET_TAGS_001", f"Error retrieving tags: {e}")

    def add_song(self, song_data: Dict) -> bool:
        """Add a new song if it doesn't exist."""
        try:
            if not song_data.get("title", "").strip():
                raise SanctifyError("SongModel", "ADD_001", "Cannot add song: title is empty")
            if any(song["title"].lower() == song_data["title"].lower() for song in self.songs):
                raise SanctifyError("SongModel", "ADD_002", f"Cannot add song: title '{song_data['title']}' already exists")

            song_data = song_data.copy()
            now = datetime.now().isoformat()
            song_data["created_at"] = now
            song_data["updated_at"] = now
            if "sections" not in song_data:
                song_data["sections"] = []
            if "tags" not in song_data:
                song_data["tags"] = ""

            if not self._validate_song(song_data):
                raise SanctifyError("SongModel", "ADD_003", f"Cannot add song: invalid data for '{song_data['title']}'")

            self.songs.append(song_data)
            self._save_songs()
            logger.info(f"Added song: {song_data['title']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("SongModel", "ADD_004", f"Error adding song: {e}")

    def update_song(self, old_title: str, song_data: Dict) -> bool:
        """Update an existing song by its title."""
        try:
            song = self.get_song_by_title(old_title)
            if not song:
                raise SanctifyError("SongModel", "UPDATE_001", f"Cannot update song: title '{old_title}' not found")

            if song_data.get("title", "").strip() and song_data["title"].lower() != old_title.lower():
                if any(s["title"].lower() == song_data["title"].lower() for s in self.songs if s["title"].lower() != old_title.lower()):
                    raise SanctifyError("SongModel", "UPDATE_002", f"Cannot update song: new title '{song_data['title']}' already exists")

            song_data = song_data.copy()
            song_data["updated_at"] = datetime.now().isoformat()
            song_data["created_at"] = song["created_at"]
            if "sections" not in song_data:
                song_data["sections"] = song["sections"]
            if "tags" not in song_data:
                song_data["tags"] = song["tags"]

            if not self._validate_song(song_data):
                raise SanctifyError("SongModel", "UPDATE_003", f"Cannot update song: invalid data for '{song_data['title']}'")

            self.songs.remove(song)
            self.songs.append(song_data)
            self._save_songs()
            logger.info(f"Updated song: {song_data['title']}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("SongModel", "UPDATE_004", f"Error updating song: {e}")

    def delete_song(self, title: str) -> bool:
        """Delete a song by its title."""
        try:
            song = self.get_song_by_title(title)
            if not song:
                raise SanctifyError("SongModel", "DELETE_001", f"Cannot delete song: title '{title}' not found")
            self.songs.remove(song)
            self._save_songs()
            logger.info(f"Deleted song: {title}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("SongModel", "DELETE_002", f"Error deleting song: {e}")

    def duplicate_song(self, title: str) -> bool:
        """Duplicate a song with a new title."""
        try:
            song = self.get_song_by_title(title)
            if not song:
                raise SanctifyError("SongModel", "DUPLICATE_001", f"Cannot duplicate song: title '{title}' not found")

            new_title = f"{song['title']} (Copy)"
            if any(s["title"].lower() == new_title.lower() for s in self.songs):
                raise SanctifyError("SongModel", "DUPLICATE_002", f"Cannot duplicate song: title '{new_title}' already exists")

            new_song = song.copy()
            new_song["title"] = new_title
            new_song["created_at"] = datetime.now().isoformat()
            new_song["updated_at"] = new_song["created_at"]
            self.songs.append(new_song)
            self._save_songs()
            logger.info(f"Duplicated song: {title} -> {new_title}")
            return True
        except SanctifyError as e:
            raise e
        except Exception as e:
            raise SanctifyError("SongModel", "DUPLICATE_003", f"Error duplicating song: {e}")