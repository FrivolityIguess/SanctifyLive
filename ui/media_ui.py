import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QComboBox, QSplitter, QFrame, QMessageBox, QFileDialog,
    QMenu, QAction, QCompleter, QInputDialog, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QStringListModel
from PyQt5.QtGui import QPixmap, QIcon, QFont

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
    def __init__(self, media_file: str = "data/media/media.json", media_dir: str = "data/media"):
        """Initialize MediaModel with a single JSON file for metadata."""
        self.media_file = media_file
        self.media_dir = media_dir
        self.media: List[Dict] = []
        self._load_media()

    def _load_media(self) -> None:
        """Load media metadata from JSON file."""
        self.media.clear()
        if os.path.exists(self.media_file):
            try:
                with open(self.media_file, 'r', encoding='utf-8') as f:
                    loaded_media = json.load(f)
                    if isinstance(loaded_media, list):
                        for item in loaded_media:
                            if self._validate_media(item):
                                self.media.append(item)
                            else:
                                logger.warning(f"Invalid media data: {item.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error loading media from {self.media_file}: {e}")
        else:
            os.makedirs(os.path.dirname(self.media_file), exist_ok=True)
            self._save_media()

    def _save_media(self) -> None:
        """Save media metadata to JSON file."""
        try:
            with open(self.media_file, 'w', encoding='utf-8') as f:
                json.dump(self.media, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving media to {self.media_file}: {e}")

    def _validate_media(self, media: Dict) -> bool:
        """Validate media data structure."""
        return (
            isinstance(media, dict) and
            "name" in media and isinstance(media["name"], str) and media["name"].strip() and
            "path" in media and isinstance(media["path"], str) and os.path.exists(media["path"]) and
            "category" in media and media["category"] in ["Images", "Videos", "Gifs"] and
            "tags" in media and isinstance(media["tags"], str) and
            "scaling" in media and media["scaling"] in ["stretch", "fit", "fill"] and
            "created_at" in media and isinstance(media["created_at"], str) and
            "updated_at" in media and isinstance(media["updated_at"], str)
        )

    def get_all_media(self, category: str = "") -> List[Dict]:
        """Return all media or filtered by category, sorted by name."""
        media = self.media if not category else [m for m in self.media if m["category"] == category]
        return sorted(media, key=lambda m: m["name"].lower())

    def search_media(self, query: str, category: str = "", tag: str = "") -> List[Dict]:
        """Search media by name or tags, optionally filtered by category."""
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

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags."""
        tags = set()
        for media in self.media:
            for tag in media.get("tags", "").split(","):
                tag = tag.strip()
                if tag:
                    tags.add(tag)
        return sorted(tags)

    def add_media(self, file_path: str, category: str, tags: str = "", scaling: str = "fit") -> bool:
        """Add a new media file and metadata."""
        filename = os.path.basename(file_path)
        target_path = os.path.join(self.media_dir, category, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Copy file
        try:
            with open(file_path, "rb") as src, open(target_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            logger.error(f"Failed to copy media file {file_path} to {target_path}: {e}")
            return False

        # Add metadata
        media_data = {
            "name": filename,
            "path": target_path,
            "category": category,
            "tags": tags.strip(),
            "scaling": scaling,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        if any(m["path"] == target_path for m in self.media):
            logger.warning(f"Media already exists: {target_path}")
            return False

        if not self._validate_media(media_data):
            logger.warning(f"Invalid media data for {filename}")
            return False

        self.media.append(media_data)
        self._save_media()
        return True

    def update_media(self, old_path: str, media_data: Dict) -> bool:
        """Update media metadata."""
        media = next((m for m in self.media if m["path"] == old_path), None)
        if not media:
            return False

        media_data = media_data.copy()
        media_data["path"] = media["path"]
        media_data["created_at"] = media["created_at"]
        media_data["updated_at"] = datetime.now().isoformat()
        if "category" not in media_data:
            media_data["category"] = media["category"]
        if "name" not in media_data:
            media_data["name"] = media["name"]
        if "tags" not in media_data:
            media_data["tags"] = media["tags"]
        if "scaling" not in media_data:
            media_data["scaling"] = media["scaling"]

        # Handle rename
        if media_data["name"] != media["name"]:
            new_path = os.path.join(self.media_dir, media["category"], media_data["name"])
            try:
                os.rename(media["path"], new_path)
                media_data["path"] = new_path
            except Exception as e:
                logger.error(f"Failed to rename media from {media['path']} to {new_path}: {e}")
                return False

        if not self._validate_media(media_data):
            return False

        self.media.remove(media)
        self.media.append(media_data)
        self._save_media()
        return True

    def delete_media(self, path: str) -> bool:
        """Delete a media file and its metadata."""
        media = next((m for m in self.media if m["path"] == path), None)
        if not media:
            return False
        try:
            os.remove(media["path"])
        except Exception as e:
            logger.error(f"Failed to delete media file {media['path']}: {e}")
            return False
        self.media.remove(media)
        self._save_media()
        return True

    def set_logo(self, path: str) -> bool:
        """Set a media file as the logo."""
        media = next((m for m in self.media if m["path"] == path), None)
        if not media or media["category"] != "Images":
            return False
        media["is_logo"] = True
        for m in self.media:
            if m["path"] != path and "is_logo" in m:
                del m["is_logo"]
        self._save_media()
        return True

class MediaTab(QWidget):
    def __init__(self):
        super().__init__()
        self.media_model = MediaModel()
        self.current_category = "Images"
        self.logo_path = None
        self.search_history = []
        self.search_results = []

        # Main layout with vertical splitter
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; height: 4px; }")
        layout = QVBoxLayout(self)
        layout.addWidget(main_splitter)

        # Top Panel: Search and Filters
        top_panel = QFrame()
        top_panel.setStyleSheet("background: #ecf0f1; padding: 20px; border-bottom: 2px solid #bdc3c7;")
        top_layout = QVBoxLayout(top_panel)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 18px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QLineEdit:focus {
                border: 2px solid #2980b9;
                background: #f5faff;
            }
        """)
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_completer.popup().setStyleSheet("""
            QAbstractItemView {
                font-size: 18px;
                padding: 8px;
                background: #fff;
                border: 2px solid #3498db;
                border-radius: 6px;
                color: #2c3e50;
            }
            QAbstractItemView::item {
                padding: 10px;
                min-height: 35px;
            }
            QAbstractItemView::item:selected {
                background: #3498db;
                color: #fff;
            }
        """)
        self.search_input.setCompleter(self.search_completer)
        self.search_input.textChanged.connect(self.perform_search)

        self.search_mode_toggle = QPushButton("Switch to Tag Search")
        self.search_mode_toggle.setIcon(QIcon("assets/icons/search.png"))
        self.search_mode_toggle.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #3498db;
                color: #fff;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        self.search_mode_toggle.clicked.connect(self.toggle_search_mode)
        self.search_mode = "name"

        search_layout.addWidget(self.search_mode_toggle)
        search_layout.addWidget(self.search_input)
        top_layout.addLayout(search_layout)

        # Category and Tag Filters
        filter_layout = QHBoxLayout()
        self.category_selector = QComboBox()
        self.category_selector.addItems(["All", "Images", "Videos", "Gifs"])
        self.category_selector.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
        """)
        self.category_selector.currentTextChanged.connect(self.switch_category)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_selector)

        self.tag_filter = QComboBox()
        self.tag_filter.addItem("All Tags")
        self.tag_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
        """)
        self.tag_filter.currentTextChanged.connect(self.perform_search)
        filter_layout.addWidget(QLabel("Tag:"))
        filter_layout.addWidget(self.tag_filter)

        self.history_combo = QComboBox()
        self.history_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
        """)
        self.history_combo.activated[str].connect(self.load_search_from_history)
        filter_layout.addWidget(QLabel("Recent Searches:"))
        filter_layout.addWidget(self.history_combo)
        top_layout.addLayout(filter_layout)

        main_splitter.addWidget(top_panel)

        # Bottom Panel: Media List and Preview
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setChildrenCollapsible(False)
        bottom_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; width: 4px; }")

        # Media List
        list_panel = QFrame()
        list_layout = QVBoxLayout(list_panel)
        self.media_list = QListWidget()
        self.media_list.setViewMode(QListWidget.IconMode)
        self.media_list.setIconSize(QPixmap(120, 120).size())
        self.media_list.setResizeMode(QListWidget.Adjust)
        self.media_list.setSpacing(12)
        self.media_list.setStyleSheet("""
            QListWidget {
                font-size: 18px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: #fff;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: #fff;
            }
            QListWidget::item:hover {
                background: #f5faff;
            }
        """)
        self.media_list.itemClicked.connect(self.preview_media)
        self.media_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.media_list.customContextMenuRequested.connect(self.open_context_menu)
        self.media_list.keyPressEvent = self.handle_list_keypress
        list_layout.addWidget(self.media_list)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Media")
        add_btn.clicked.connect(self.add_media)
        edit_btn = QPushButton("Edit Media")
        edit_btn.clicked.connect(self.edit_media)
        delete_btn = QPushButton("Delete Media")
        delete_btn.clicked.connect(self.delete_media)
        for btn in [add_btn, edit_btn, delete_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px;
                    font-size: 16px;
                    border: 2px solid #3498db;
                    border-radius: 6px;
                    background: #3498db;
                    color: #fff;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addWidget(delete_btn)
        list_layout.addLayout(buttons_layout)
        bottom_splitter.addWidget(list_panel)

        # Preview
        preview_panel = QFrame()
        preview_panel.setMinimumWidth(400)
        preview_layout = QVBoxLayout(preview_panel)
        preview_label = QLabel("Media Preview:")
        preview_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.preview_display = QLabel()
        self.preview_display.setAlignment(Qt.AlignCenter)
        self.preview_display.setStyleSheet("""
            QLabel {
                background: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        self.scaling_combo = QComboBox()
        self.scaling_combo.addItems(["Stretch", "Fit", "Fill"])
        self.scaling_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
        """)
        self.scaling_combo.currentTextChanged.connect(self.update_preview_scaling)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_display)
        preview_layout.addWidget(QLabel("Scaling:"))
        preview_layout.addWidget(self.scaling_combo)
        bottom_splitter.addWidget(preview_panel)

        bottom_splitter.setSizes([400, 600])
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([200, 600])

        self.switch_category("Images")
        self.update_completers()

    def toggle_search_mode(self):
        """Toggle between name and tag search modes."""
        self.search_mode = "tags" if self.search_mode == "name" else "name"
        self.search_mode_toggle.setText(f"Switch to {'Tag' if self.search_mode == 'name' else 'Name'} Search")
        self.search_mode_toggle.setIcon(
            QIcon("assets/icons/search.png" if self.search_mode == "name" else "assets/icons/tag.png")
        )
        self.search_input.setPlaceholderText(f"Search by {self.search_mode}...")
        self.perform_search()

    def switch_category(self, category: str):
        """Switch the current category and refresh the media list."""
        self.current_category = category if category != "All" else ""
        self.perform_search()
        self.update_completers()

    def update_completers(self):
        """Update autocompleters for search and tags."""
        names = [m["name"] for m in self.media_model.get_all_media(self.current_category)]
        self.search_completer.setModel(QStringListModel(names))
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        self.tag_filter.addItems(self.media_model.get_all_tags())
        self.tag_filter.blockSignals(False)

    def perform_search(self):
        """Perform search based on query, category, and tag."""
        query = self.search_input.text().strip()
        tag = self.tag_filter.currentText() if self.tag_filter.currentText() != "All Tags" else ""
        self.search_results = []
        self.media_list.clear()

        media_items = self.media_model.search_media(query, self.current_category, tag)
        for i, media in enumerate(media_items):
            item = QListWidgetItem(QIcon(media["path"]), media["name"])
            item.setData(Qt.UserRole, media["path"])
            self.media_list.addItem(item)
            self.search_results.append(i)

        if media_items and self.media_list.count() > 0:
            self.media_list.setCurrentRow(0)
            self.preview_media(self.media_list.item(0))

        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > 10:
                self.search_history.pop()
            self.history_combo.clear()
            self.history_combo.addItems(self.search_history)

        # Update status bar
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Found {len(media_items)} media items")

    def preview_media(self, item: QListWidgetItem):
        """Display the selected media in the preview."""
        path = item.data(Qt.UserRole)
        media = next((m for m in self.media_model.media if m["path"] == path), None)
        if not media:
            return

        pixmap = QPixmap(path).scaled(400, 400, Qt.KeepAspectRatio)
        self.preview_display.setPixmap(pixmap)
        self.scaling_combo.setCurrentText(media["scaling"].capitalize())
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Previewing {media['name']}")

    def update_preview_scaling(self, scaling: str):
        """Update scaling mode for the current media."""
        current_item = self.media_list.currentItem()
        if not current_item:
            return
        path = current_item.data(Qt.UserRole)
        media_data = {"scaling": scaling.lower()}
        if self.media_model.update_media(path, media_data):
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(f"Scaling updated to {scaling} for {current_item.text()}")
        else:
            QMessageBox.warning(self, "Error", "Failed to update scaling.")

    def add_media(self):
        """Add a new media file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Add Media")
        if not file_path:
            return
        tags, ok = QInputDialog.getText(self, "Add Tags", "Enter comma-separated tags (optional):")
        if not ok:
            tags = ""
        if self.media_model.add_media(file_path, self.current_category or "Images", tags):
            self.perform_search()
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(f"Added {os.path.basename(file_path)}")
        else:
            QMessageBox.warning(self, "Error", "Failed to add media.")

    def edit_media(self):
        """Edit the selected media's metadata."""
        current_item = self.media_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a media item to edit.")
            return
        path = current_item.data(Qt.UserRole)
        media = next((m for m in self.media_model.media if m["path"] == path), None)
        if not media:
            return

        name, ok1 = QInputDialog.getText(self, "Edit Name", "New name:", text=media["name"])
        tags, ok2 = QInputDialog.getText(self, "Edit Tags", "Comma-separated tags:", text=media["tags"])
        scaling, ok3 = QInputDialog.getItem(self, "Edit Scaling", "Scaling mode:", ["Stretch", "Fit", "Fill"], ["stretch", "fit", "fill"].index(media["scaling"]), False)
        
        if ok1 or ok2 or ok3:
            media_data = {
                "name": name if ok1 else media["name"],
                "tags": tags if ok2 else media["tags"],
                "scaling": scaling.lower() if ok3 else media["scaling"]
            }
            if self.media_model.update_media(path, media_data):
                self.perform_search()
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Updated {media_data['name']}")
            else:
                QMessageBox.warning(self, "Error", "Failed to update media.")

    def delete_media(self):
        """Delete the selected media."""
        current_item = self.media_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a media item to delete.")
            return
        path = current_item.data(Qt.UserRole)
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{os.path.basename(path)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.media_model.delete_media(path):
                self.perform_search()
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Deleted {os.path.basename(path)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete media.")

    def set_as_logo(self, item: QListWidgetItem):
        """Set the selected media as the logo."""
        path = item.data(Qt.UserRole)
        if self.media_model.set_logo(path):
            self.logo_path = path
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(f"Set {os.path.basename(path)} as logo")
        else:
            QMessageBox.warning(self, "Error", "Only images can be set as logo.")

    def open_context_menu(self, pos):
        """Open context menu for media list item."""
        item = self.media_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        actions = [
            ("Edit Metadata", lambda: self.edit_media()),
            ("Rename", lambda: self.rename_media(item)),
            ("Delete", lambda: self.delete_media()),
            ("Set as Logo", lambda: self.set_as_logo(item)),
            ("Duplicate", lambda: self.duplicate_media(item))
        ]
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.exec_(self.media_list.mapToGlobal(pos))

    def rename_media(self, item: QListWidgetItem):
        """Rename the selected media."""
        path = item.data(Qt.UserRole)
        media = next((m for m in self.media_model.media if m["path"] == path), None)
        if not media:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Media", "New name:", text=media["name"])
        if ok and new_name:
            if self.media_model.update_media(path, {"name": new_name}):
                self.perform_search()
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Renamed to {new_name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to rename media.")

    def duplicate_media(self, item: QListWidgetItem):
        """Duplicate the selected media."""
        path = item.data(Qt.UserRole)
        media = next((m for m in self.media_model.media if m["path"] == path), None)
        if not media:
            return
        new_name = f"{media['name'].rsplit('.', 1)[0]} (Copy).{media['name'].rsplit('.', 1)[1]}"
        new_path = os.path.join(self.media_dir, media["category"], new_name)
        try:
            with open(path, "rb") as src, open(new_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            logger.error(f"Failed to duplicate media {path} to {new_path}: {e}")
            QMessageBox.warning(self, "Error", "Failed to duplicate media.")
            return

        if self.media_model.add_media(new_path, media["category"], media["tags"], media["scaling"]):
            self.perform_search()
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(f"Duplicated as {new_name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to add duplicated media.")

    def handle_list_keypress(self, event):
        """Handle keyboard navigation in media list."""
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current_row = self.media_list.currentRow()
            if self.search_results:
                current_index = self.search_results.index(current_row) if current_row in self.search_results else -1
                if event.key() == Qt.Key_Up and current_index > 0:
                    next_row = self.search_results[current_index - 1]
                elif event.key() == Qt.Key_Down and current_index < len(self.search_results) - 1:
                    next_row = self.search_results[current_index + 1]
                else:
                    return
                self.media_list.setCurrentRow(next_row)
                self.preview_media(self.media_list.item(next_row))
        else:
            super(QListWidget, self.media_list).keyPressEvent(event)

    def load_search_from_history(self, query: str):
        """Load a search query from history."""
        self.search_input.setText(query)
        self.perform_search()

# Write example schema to file for user reference
sample_media = [
    {
        "name": "sample_image.jpg",
        "path": "data/media/Images/sample_image.jpg",
        "category": "Images",
        "tags": "worship,background",
        "scaling": "fit",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_logo": False
    },
    {
        "name": "sample_video.mp4",
        "path": "data/media/Videos/sample_video.mp4",
        "category": "Videos",
        "tags": "intro,loop",
        "scaling": "fill",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

sample_path = "data/media/media_sample.json"
os.makedirs(os.path.dirname(sample_path), exist_ok=True)
with open(sample_path, "w", encoding="utf-8") as f:
    json.dump(sample_media, f, indent=4, ensure_ascii=False)