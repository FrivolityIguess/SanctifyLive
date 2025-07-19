import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QComboBox, QSplitter, QFrame, QMessageBox, QFileDialog,
    QMenu, QAction, QCompleter, QInputDialog, QDialog, QTextEdit, QApplication
)
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtGui import QFont

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
    def __init__(self, presentation_file: str = "data/presentations/presentations.json"):
        """Initialize PresentationModel with a single JSON file for metadata."""
        self.presentation_file = presentation_file
        self.presentations: List[Dict] = []
        self._ensure_directories()
        self._load_presentations()

    def _ensure_directories(self) -> None:
        """Create presentations directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.presentation_file), exist_ok=True)

    def _load_presentations(self) -> None:
        """Load presentation metadata from JSON file."""
        self.presentations.clear()
        if os.path.exists(self.presentation_file):
            try:
                with open(self.presentation_file, 'r', encoding='utf-8') as f:
                    loaded_presentations = json.load(f)
                    if isinstance(loaded_presentations, list):
                        for item in loaded_presentations:
                            if self._validate_presentation(item):
                                self.presentations.append(item)
                            else:
                                logger.warning(f"Invalid presentation data: {item.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error loading presentations from {self.presentation_file}: {e}")
        else:
            self._save_presentations()

    def _save_presentations(self) -> None:
        """Save presentation metadata to JSON file."""
        try:
            with open(self.presentation_file, 'w', encoding='utf-8') as f:
                json.dump(self.presentations, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving presentations to {self.presentation_file}: {e}")

    def _validate_presentation(self, presentation: Dict) -> bool:
        """Validate presentation data structure."""
        return (
            isinstance(presentation, dict) and
            "id" in presentation and isinstance(presentation["id"], str) and
            "name" in presentation and isinstance(presentation["name"], str) and presentation["name"].strip() and
            "slides" in presentation and isinstance(presentation["slides"], list) and
            all(isinstance(slide, list) and len(slide) == 2 and
                isinstance(slide[0], str) and isinstance(slide[1], str) for slide in presentation["slides"]) and
            "tags" in presentation and isinstance(presentation["tags"], str) and
            "created_at" in presentation and isinstance(presentation["created_at"], str) and
            "updated_at" in presentation and isinstance(presentation["updated_at"], str)
        )

    def get_all_presentations(self) -> List[Dict]:
        """Return all presentations sorted by name."""
        return sorted(self.presentations, key=lambda p: p["name"].lower())

    def get_presentation_by_id(self, presentation_id: str) -> Optional[Dict]:
        """Retrieve a presentation by its ID."""
        return next((p for p in self.presentations if p["id"] == presentation_id), None)

    def search_presentations(self, query: str, tag: str = "") -> List[Dict]:
        """Search presentations by name or tags."""
        query = query.lower().strip()
        tag = tag.lower().strip()
        results = []
        for presentation in self.presentations:
            matches_query = query in presentation["name"].lower() or any(query in t.lower() for t in presentation.get("tags", "").split(","))
            matches_tag = not tag or tag in presentation.get("tags", "").lower()
            if matches_query and matches_tag:
                results.append(presentation)
        return sorted(results, key=lambda p: p["name"].lower())

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags."""
        tags = set()
        for presentation in self.presentations:
            for tag in presentation.get("tags", "").split(","):
                tag = tag.strip()
                if tag:
                    tags.add(tag)
        return sorted(tags)

    def add_presentation(self, presentation_data: Dict) -> Optional[Dict]:
        """Add a new presentation."""
        if not presentation_data.get("name", "").strip():
            logger.error("Presentation name is required")
            return None
        if any(p["name"].lower() == presentation_data["name"].lower() for p in self.presentations):
            logger.error(f"Presentation already exists: {presentation_data['name']}")
            return None

        presentation_data = presentation_data.copy()
        presentation_data["id"] = str(uuid.uuid4())
        now = datetime.now().isoformat()
        presentation_data["created_at"] = now
        presentation_data["updated_at"] = now
        if "slides" not in presentation_data:
            presentation_data["slides"] = []
        if "tags" not in presentation_data:
            presentation_data["tags"] = ""

        if not self._validate_presentation(presentation_data):
            logger.error(f"Invalid presentation data for {presentation_data['name']}")
            return None

        self.presentations.append(presentation_data)
        self._save_presentations()
        logger.info(f"Added presentation: {presentation_data['name']}")
        return presentation_data

    def update_presentation(self, presentation_id: str, presentation_data: Dict) -> bool:
        """Update an existing presentation."""
        presentation = self.get_presentation_by_id(presentation_id)
        if not presentation:
            logger.error(f"Presentation not found: {presentation_id}")
            return False

        if presentation_data.get("name", "").strip() and presentation_data["name"].lower() != presentation["name"].lower():
            if any(p["name"].lower() == presentation_data["name"].lower() for p in self.presentations if p["id"] != presentation_id):
                logger.error(f"Presentation name already exists: {presentation_data['name']}")
                return False

        presentation_data = presentation_data.copy()
        presentation_data["id"] = presentation["id"]
        presentation_data["created_at"] = presentation["created_at"]
        presentation_data["updated_at"] = datetime.now().isoformat()
        if "slides" not in presentation_data:
            presentation_data["slides"] = presentation["slides"]
        if "tags" not in presentation_data:
            presentation_data["tags"] = presentation["tags"]

        if not self._validate_presentation(presentation_data):
            logger.error(f"Invalid presentation data for {presentation_data['name']}")
            return False

        self.presentations.remove(presentation)
        self.presentations.append(presentation_data)
        self._save_presentations()
        logger.info(f"Updated presentation: {presentation_data['name']}")
        return True

    def delete_presentation(self, presentation_id: str) -> bool:
        """Delete a presentation by its ID."""
        presentation = self.get_presentation_by_id(presentation_id)
        if not presentation:
            logger.error(f"Presentation not found: {presentation_id}")
            return False
        self.presentations.remove(presentation)
        self._save_presentations()
        logger.info(f"Deleted presentation: {presentation['name']}")
        return True

    def duplicate_presentation(self, presentation_id: str) -> Optional[Dict]:
        """Duplicate a presentation with a new ID."""
        presentation = self.get_presentation_by_id(presentation_id)
        if not presentation:
            logger.error(f"Presentation not found: {presentation_id}")
            return None

        new_presentation = presentation.copy()
        new_presentation["id"] = str(uuid.uuid4())
        new_presentation["name"] = f"{presentation['name']} (Copy)"
        new_presentation["created_at"] = datetime.now().isoformat()
        new_presentation["updated_at"] = new_presentation["created_at"]

        if any(p["name"].lower() == new_presentation["name"].lower() for p in self.presentations):
            logger.error(f"Duplicate presentation name already exists: {new_presentation['name']}")
            return None

        self.presentations.append(new_presentation)
        self._save_presentations()
        logger.info(f"Duplicated presentation: {new_presentation['name']}")
        return new_presentation

class PresentationEditor(QDialog):
    def __init__(self, parent=None, existing_data: Optional[Dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Presentation" if existing_data else "Add Presentation")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background: #ecf0f1;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 12px;
                font-size: 18px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #2980b9;
                background: #f5faff;
            }
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
        self.existing_data = existing_data
        self.slides = existing_data["slides"] if existing_data else []
        self.name = existing_data["name"] if existing_data else ""
        self.tags = existing_data["tags"] if existing_data else ""

        layout = QVBoxLayout(self)

        # Name Input
        self.name_input = QLineEdit(self.name)
        self.name_input.setPlaceholderText("Presentation Name (required)")
        layout.addWidget(QLabel("Presentation Name:", styleSheet="font-size: 18px; color: #2c3e50;"))
        layout.addWidget(self.name_input)

        # Tags Input
        self.tags_input = QLineEdit(self.tags)
        self.tags_input.setPlaceholderText("Comma-separated tags (e.g., sermon,teaching)")
        layout.addWidget(QLabel("Tags:", styleSheet="font-size: 18px; color: #2c3e50;"))
        layout.addWidget(self.tags_input)

        # Slide Editor
        slide_layout = QHBoxLayout()
        editor_panel = QFrame()
        editor_layout = QVBoxLayout(editor_panel)
        self.slide_type = QComboBox()
        self.slide_type.addItems(["Text", "Image", "Video"])
        editor_layout.addWidget(QLabel("Slide Type:", styleSheet="font-size: 18px; color: #2c3e50;"))
        editor_layout.addWidget(self.slide_type)
        self.slide_editor = QTextEdit()
        self.slide_editor.setPlaceholderText("Enter slide content (text, image path, or video path)...")
        editor_layout.addWidget(self.slide_editor)
        slide_layout.addWidget(editor_panel, 1)

        # Slide List
        slides_panel = QFrame()
        slides_layout = QVBoxLayout(slides_panel)
        self.slides_list = QListWidget()
        self.slides_list.setStyleSheet("""
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
        self.slides_list.setDragDropMode(QListWidget.InternalMove)
        self.slides_list.itemClicked.connect(self.load_slide)
        for slide in self.slides:
            self.slides_list.addItem(slide[1][:40])
        slides_layout.addWidget(QLabel("Slides:", styleSheet="font-size: 18px; color: #2c3e50;"))
        slides_layout.addWidget(self.slides_list)

        # Slide Actions
        slide_btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Slide")
        add_btn.clicked.connect(self.add_slide)
        update_btn = QPushButton("Update Slide")
        update_btn.clicked.connect(self.update_slide)
        del_btn = QPushButton("Delete Slide")
        del_btn.clicked.connect(self.delete_slide)
        for btn in [add_btn, update_btn, del_btn]:
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
        slide_btn_layout.addWidget(add_btn)
        slide_btn_layout.addWidget(update_btn)
        slide_btn_layout.addWidget(del_btn)
        slides_layout.addLayout(slide_btn_layout)
        slide_layout.addWidget(slides_panel, 1)
        layout.addLayout(slide_layout)

        # Save Button
        save_btn = QPushButton("Save Presentation")
        save_btn.clicked.connect(self.save_presentation)
        layout.addWidget(save_btn)

    def add_slide(self):
        """Add a new slide to the presentation."""
        content = self.slide_editor.toPlainText().strip()
        slide_type = self.slide_type.currentText()
        if not content:
            QMessageBox.warning(self, "Empty Slide", "Slide content is required.")
            return
        if slide_type != "Text":
            if not os.path.exists(content):
                QMessageBox.warning(self, "Invalid Path", f"{slide_type} file does not exist: {content}")
                return
        self.slides.append([slide_type, content])
        self.slides_list.addItem(content[:40])
        self.slide_editor.clear()
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage("Slide added")

    def update_slide(self):
        """Update the selected slide."""
        index = self.slides_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "No Selection", "Please select a slide to update.")
            return
        content = self.slide_editor.toPlainText().strip()
        slide_type = self.slide_type.currentText()
        if not content:
            QMessageBox.warning(self, "Empty Slide", "Slide content is required.")
            return
        if slide_type != "Text":
            if not os.path.exists(content):
                QMessageBox.warning(self, "Invalid Path", f"{slide_type} file does not exist: {content}")
                return
        self.slides[index] = [slide_type, content]
        self.slides_list.item(index).setText(content[:40])
        self.slide_editor.clear()
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage("Slide updated")

    def delete_slide(self):
        """Delete the selected slide."""
        index = self.slides_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "No Selection", "Please select a slide to delete.")
            return
        self.slides.pop(index)
        self.slides_list.takeItem(index)
        self.slide_editor.clear()
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage("Slide deleted")

    def load_slide(self, item: QListWidgetItem):
        """Load the selected slide into the editor."""
        index = self.slides_list.currentRow()
        if index >= 0:
            slide_type, content = self.slides[index]
            self.slide_type.setCurrentText(slide_type)
            self.slide_editor.setPlainText(content)

    def save_presentation(self):
        """Save the presentation and close the dialog."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Title", "Presentation name is required.")
            return
        if not self.slides:
            QMessageBox.warning(self, "No Slides", "At least one slide is required.")
            return
        tags = self.tags_input.text().strip()
        presentation_data = {
            "name": name,
            "slides": self.slides,
            "tags": tags
        }
        main_window = self.window()
        model = getattr(main_window, "presentation_model", None)
        if model:
            if self.existing_data:
                success = model.update_presentation(self.existing_data["id"], presentation_data)
                msg = f"Updated presentation: {name}" if success else "Failed to update presentation"
            else:
                result = model.add_presentation(presentation_data)
                msg = f"Saved presentation: {name}" if result else "Failed to save presentation"
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(msg)
            if result or success:
                self.accept()
            else:
                QMessageBox.warning(self, "Error", msg)
        else:
            QMessageBox.warning(self, "Error", "Presentation model not found.")

class PresentationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.presentation_model = PresentationModel()
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

        # Tag Filter and History
        filter_layout = QHBoxLayout()
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
        filter_layout.addWidget(QLabel("Tag:", styleSheet="font-size: 18px; color: #2c3e50;"))
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
        filter_layout.addWidget(QLabel("Recent Searches:", styleSheet="font-size: 18px; color: #2c3e50;"))
        filter_layout.addWidget(self.history_combo)
        top_layout.addLayout(filter_layout)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Presentation")
        add_btn.clicked.connect(self.open_editor)
        import_btn = QPushButton("Import Presentation")
        import_btn.clicked.connect(self.import_presentation)
        for btn in [add_btn, import_btn]:
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
        buttons_layout.addWidget(import_btn)
        top_layout.addLayout(buttons_layout)
        main_splitter.addWidget(top_panel)

        # Bottom Panel: Presentation List and Preview
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setChildrenCollapsible(False)
        bottom_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; width: 4px; }")

        # Presentation List
        list_panel = QFrame()
        list_layout = QVBoxLayout(list_panel)
        self.presentation_list = QListWidget()
        self.presentation_list.setStyleSheet("""
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
        self.presentation_list.itemClicked.connect(self.update_preview)
        self.presentation_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.presentation_list.customContextMenuRequested.connect(self.open_context_menu)
        self.presentation_list.keyPressEvent = self.handle_list_keypress
        list_layout.addWidget(QLabel("Presentations:", styleSheet="font-size: 18px; color: #2c3e50;"))
        list_layout.addWidget(self.presentation_list)
        bottom_splitter.addWidget(list_panel)

        # Preview
        preview_panel = QFrame()
        preview_panel.setMinimumWidth(400)
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_label = QLabel("Presentation Preview")
        self.preview_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.preview_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(QLabel("Preview:", styleSheet="font-size: 18px; color: #2c3e50;"))
        preview_layout.addWidget(self.preview_label)
        bottom_splitter.addWidget(preview_panel)

        bottom_splitter.setSizes([400, 600])
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([200, 600])

        self.load_presentations()
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

    def update_completers(self):
        """Update autocompleters for search and tags."""
        names = [p["name"] for p in self.presentation_model.get_all_presentations()]
        self.search_completer.setModel(QStringListModel(names))
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        self.tag_filter.addItems(self.presentation_model.get_all_tags())
        self.tag_filter.blockSignals(False)

    def perform_search(self):
        """Perform search based on query and tag."""
        query = self.search_input.text().strip()
        tag = self.tag_filter.currentText() if self.tag_filter.currentText() != "All Tags" else ""
        self.search_results = []
        self.presentation_list.clear()

        presentations = self.presentation_model.search_presentations(query, tag)
        for i, presentation in enumerate(presentations):
            item = QListWidgetItem(presentation["name"])
            item.setData(Qt.UserRole, presentation["id"])
            self.presentation_list.addItem(item)
            self.search_results.append(i)

        if presentations and self.presentation_list.count() > 0:
            self.presentation_list.setCurrentRow(0)
            self.update_preview(self.presentation_list.item(0))

        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > 10:
                self.search_history.pop()
            self.history_combo.clear()
            self.history_combo.addItems(self.search_history)

        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Found {len(presentations)} presentations")

    def load_presentations(self):
        """Load all presentations into the list."""
        self.perform_search()

    def update_preview(self, item: QListWidgetItem):
        """Update the preview with the selected presentation."""
        presentation_id = item.data(Qt.UserRole)
        presentation = self.presentation_model.get_presentation_by_id(presentation_id)
        if not presentation:
            return
        slides_html = "".join(f"<p><b>{slide[0]}</b>: {slide[1]}</p><hr>" for slide in presentation["slides"])
        self.preview_label.setText(f"<h3>{presentation['name']}</h3>{slides_html}")
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Previewing {presentation['name']}")

    def open_editor(self):
        """Open the editor for a new presentation."""
        dialog = PresentationEditor(self)
        if dialog.exec_():
            self.load_presentations()

    def edit_presentation(self):
        """Edit the selected presentation."""
        item = self.presentation_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a presentation to edit.")
            return
        presentation_id = item.data(Qt.UserRole)
        presentation = self.presentation_model.get_presentation_by_id(presentation_id)
        if not presentation:
            return
        dialog = PresentationEditor(self, existing_data=presentation)
        if dialog.exec_():
            self.load_presentations()

    def import_presentation(self):
        """Import a presentation file (placeholder for PPTX/PDF)."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Presentation", filter="Presentation Files (*.json *.pptx *.odp *.pdf)")
        if file_path:
            if file_path.endswith(".json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if self._validate_imported_presentation(data):
                        data["tags"] = data.get("tags", "")
                        data["id"] = str(uuid.uuid4())
                        data["created_at"] = datetime.now().isoformat()
                        data["updated_at"] = data["created_at"]
                        if self.presentation_model.add_presentation(data):
                            self.load_presentations()
                            main_window = self.window()
                            if hasattr(main_window, "status_bar"):
                                main_window.status_bar.showMessage(f"Imported {os.path.basename(file_path)}")
                        else:
                            QMessageBox.warning(self, "Error", "Failed to import presentation.")
                    else:
                        QMessageBox.warning(self, "Error", "Invalid JSON format.")
                except Exception as e:
                    logger.error(f"Failed to import JSON: {e}")
                    QMessageBox.warning(self, "Error", f"Failed to import: {e}")
            else:
                QMessageBox.information(self, "Imported", f"Imported: {os.path.basename(file_path)} (conversion not implemented)")
                logger.info(f"Placeholder import for {file_path} (PPTX/ODP/PDF not supported)")

    def _validate_imported_presentation(self, data: Dict) -> bool:
        """Validate imported presentation data."""
        return (
            isinstance(data, dict) and
            "name" in data and isinstance(data["name"], str) and data["name"].strip() and
            "slides" in data and isinstance(data["slides"], list) and
            all(isinstance(slide, list) and len(slide) == 2 and
                isinstance(slide[0], str) and isinstance(slide[1], str) for slide in data["slides"])
        )

    def delete_presentation(self):
        """Delete the selected presentation."""
        item = self.presentation_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a presentation to delete.")
            return
        presentation_id = item.data(Qt.UserRole)
        presentation = self.presentation_model.get_presentation_by_id(presentation_id)
        if not presentation:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{presentation['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.presentation_model.delete_presentation(presentation_id):
                self.load_presentations()
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Deleted {presentation['name']}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete presentation.")

    def duplicate_presentation(self):
        """Duplicate the selected presentation."""
        item = self.presentation_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a presentation to duplicate.")
            return
        presentation_id = item.data(Qt.UserRole)
        if self.presentation_model.duplicate_presentation(presentation_id):
            self.load_presentations()
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(f"Duplicated {self.presentation_model.get_presentation_by_id(presentation_id)['name']} (Copy)")
        else:
            QMessageBox.warning(self, "Error", "Failed to duplicate presentation.")

    def export_presentation(self):
        """Export the selected presentation as JSON."""
        item = self.presentation_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a presentation to export.")
            return
        presentation_id = item.data(Qt.UserRole)
        presentation = self.presentation_model.get_presentation_by_id(presentation_id)
        if not presentation:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Presentation", f"{presentation['name']}.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(presentation, f, indent=4)
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Exported {presentation['name']} to {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"Failed to export presentation: {e}")
                QMessageBox.warning(self, "Error", f"Failed to export: {e}")

    def open_context_menu(self, pos):
        """Open context menu for presentation list item."""
        item = self.presentation_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        actions = [
            ("Edit", self.edit_presentation),
            ("Delete", self.delete_presentation),
            ("Duplicate", self.duplicate_presentation),
            ("Export", self.export_presentation)
        ]
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.exec_(self.presentation_list.mapToGlobal(pos))

    def handle_list_keypress(self, event):
        """Handle keyboard navigation in presentation list."""
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current_row = self.presentation_list.currentRow()
            if self.search_results:
                current_index = self.search_results.index(current_row) if current_row in self.search_results else -1
                if event.key() == Qt.Key_Up and current_index > 0:
                    next_row = self.search_results[current_index - 1]
                elif event.key() == Qt.Key_Down and current_index < len(self.search_results) - 1:
                    next_row = self.search_results[current_index + 1]
                else:
                    return
                self.presentation_list.setCurrentRow(next_row)
                self.update_preview(self.presentation_list.item(next_row))
        else:
            super(QListWidget, self.presentation_list).keyPressEvent(event)

    def load_search_from_history(self, query: str):
        """Load a search query from history."""
        self.search_input.setText(query)
        self.perform_search()

# Write example schema to file for user reference
sample_presentation = [
    {
        "id": str(uuid.uuid4()),
        "name": "Sample Sermon",
        "slides": [
            ["Text", "Welcome to our service!\nGod bless you all."],
            ["Image", "data/media/Images/worship_background.jpg"],
            ["Text", "Today's message: Love and Grace"]
        ],
        "tags": "sermon,worship,teaching",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

sample_path = "data/presentations/presentations_sample.json"
os.makedirs(os.path.dirname(sample_path), exist_ok=True)
with open(sample_path, "w", encoding="utf-8") as f:
    json.dump(sample_presentation, f, indent=4, ensure_ascii=False)