import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QComboBox, QSplitter, QFrame, QMessageBox, QDialog,
    QTextEdit, QFontComboBox, QSpinBox, QColorDialog, QCompleter, QInputDialog, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtGui import QIcon
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
    def __init__(self, theme_file: str = "data/themes/themes.json"):
        """Initialize ThemeModel with a single JSON file for metadata."""
        self.theme_file = theme_file
        self.themes: List[Dict] = []
        self._ensure_directories()
        self._load_themes()

    def _ensure_directories(self) -> None:
        """Create themes directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.theme_file), exist_ok=True)

    def _load_themes(self) -> None:
        """Load theme metadata from JSON file."""
        self.themes.clear()
        if os.path.exists(self.theme_file):
            try:
                with open(self.theme_file, 'r', encoding='utf-8') as f:
                    loaded_themes = json.load(f)
                    if isinstance(loaded_themes, list):
                        for item in loaded_themes:
                            if self._validate_theme(item):
                                self.themes.append(item)
                            else:
                                logger.warning(f"Invalid theme data: {item.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error loading themes from {self.theme_file}: {e}")
        else:
            self._save_themes()

    def _save_themes(self) -> None:
        """Save theme metadata to JSON file."""
        try:
            with open(self.theme_file, 'w', encoding='utf-8') as f:
                json.dump(self.themes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving themes to {self.theme_file}: {e}")

    def _validate_theme(self, theme: Dict) -> bool:
        """Validate theme data structure."""
        return (
            isinstance(theme, dict) and
            "id" in theme and isinstance(theme["id"], str) and
            "name" in theme and isinstance(theme["name"], str) and theme["name"].strip() and
            "context" in theme and theme["context"] in ["Songs", "Scriptures", "Presentations"] and
            "alignment" in theme and theme["alignment"] in ["Centered", "Justified", "Left", "Right"] and
            "font_color" in theme and isinstance(theme["font_color"], str) and
            "background_color" in theme and isinstance(theme["background_color"], str) and
            "font_size" in theme and isinstance(theme["font_size"], int) and theme["font_size"] >= 8 and
            "font_family" in theme and isinstance(theme["font_family"], str) and
            "tags" in theme and isinstance(theme["tags"], str) and
            "created_at" in theme and isinstance(theme["created_at"], str) and
            "updated_at" in theme and isinstance(theme["updated_at"], str)
        )

    def get_all_themes(self, context: str = "") -> List[Dict]:
        """Return all themes or filtered by context, sorted by name."""
        themes = self.themes if not context else [t for t in self.themes if t["context"] == context]
        return sorted(themes, key=lambda t: t["name"].lower())

    def get_theme_by_id(self, theme_id: str) -> Optional[Dict]:
        """Retrieve a theme by its ID."""
        return next((t for t in self.themes if t["id"] == theme_id), None)

    def search_themes(self, query: str, context: str = "", tag: str = "") -> List[Dict]:
        """Search themes by name or tags, optionally filtered by context."""
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

    def get_all_tags(self) -> List[str]:
        """Return a sorted list of unique tags."""
        tags = set()
        for theme in self.themes:
            for tag in theme.get("tags", "").split(","):
                tag = tag.strip()
                if tag:
                    tags.add(tag)
        return sorted(tags)

    def save_theme(self, theme_data: Dict) -> Optional[Dict]:
        """Save a new theme."""
        if not theme_data.get("name", "").strip():
            logger.error("Theme name is required")
            return None
        if any(t["name"].lower() == theme_data["name"].lower() for t in self.themes):
            logger.error(f"Theme already exists: {theme_data['name']}")
            return None

        theme_data = theme_data.copy()
        theme_data["id"] = str(uuid.uuid4())
        now = datetime.now().isoformat()
        theme_data["created_at"] = now
        theme_data["updated_at"] = now
        if "tags" not in theme_data:
            theme_data["tags"] = ""
        if "font_size" not in theme_data:
            theme_data["font_size"] = 18
        if "font_family" not in theme_data:
            theme_data["font_family"] = "Arial"
        if "background_color" not in theme_data:
            theme_data["background_color"] = "#ffffff"

        if not self._validate_theme(theme_data):
            logger.error(f"Invalid theme data for {theme_data['name']}")
            return None

        self.themes.append(theme_data)
        self._save_themes()
        logger.info(f"Saved theme: {theme_data['name']}")
        return theme_data

    def update_theme(self, theme_id: str, theme_data: Dict) -> bool:
        """Update an existing theme."""
        theme = self.get_theme_by_id(theme_id)
        if not theme:
            logger.error(f"Theme not found: {theme_id}")
            return False

        if theme_data.get("name", "").strip() and theme_data["name"].lower() != theme["name"].lower():
            if any(t["name"].lower() == theme_data["name"].lower() for t in self.themes if t["id"] != theme_id):
                logger.error(f"Theme name already exists: {theme_data['name']}")
                return False

        updated_theme = theme.copy()
        updated_theme.update(theme_data)
        updated_theme["id"] = theme["id"]
        updated_theme["created_at"] = theme["created_at"]
        updated_theme["updated_at"] = datetime.now().isoformat()
        if "tags" not in theme_data:
            updated_theme["tags"] = theme["tags"]
        if "font_size" not in theme_data:
            updated_theme["font_size"] = theme["font_size"]
        if "font_family" not in theme_data:
            updated_theme["font_family"] = theme["font_family"]
        if "background_color" not in theme_data:
            updated_theme["background_color"] = theme["background_color"]

        if not self._validate_theme(updated_theme):
            logger.error(f"Invalid updated theme data for {updated_theme['name']}")
            return False

        self.themes.remove(theme)
        self.themes.append(updated_theme)
        self._save_themes()
        logger.info(f"Updated theme: {updated_theme['name']}")
        return True

    def delete_theme(self, theme_id: str) -> bool:
        """Delete a theme by its ID."""
        theme = self.get_theme_by_id(theme_id)
        if not theme:
            logger.error(f"Theme not found: {theme_id}")
            return False
        self.themes.remove(theme)
        self._save_themes()
        logger.info(f"Deleted theme: {theme['name']}")
        return True

    def duplicate_theme(self, theme_id: str) -> Optional[Dict]:
        """Duplicate a theme with a new ID."""
        theme = self.get_theme_by_id(theme_id)
        if not theme:
            logger.error(f"Theme not found: {theme_id}")
            return None

        new_theme = theme.copy()
        new_theme["id"] = str(uuid.uuid4())
        new_theme["name"] = f"{theme['name']} (Copy)"
        new_theme["created_at"] = datetime.now().isoformat()
        new_theme["updated_at"] = new_theme["created_at"]

        if any(t["name"].lower() == new_theme["name"].lower() for t in self.themes):
            logger.error(f"Duplicate theme name already exists: {new_theme['name']}")
            return None

        self.themes.append(new_theme)
        self._save_themes()
        logger.info(f"Duplicated theme: {new_theme['name']}")
        return new_theme

class ThemeEditor(QDialog):
    def __init__(self, model, parent=None, existing_data: Optional[Dict] = None):
        super().__init__(parent)
        self.model = model
        self.existing_data = existing_data
        self.setWindowTitle("Edit Theme Template" if existing_data else "Add Theme Template")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background: #ecf0f1;
            }
            QLineEdit, QTextEdit, QComboBox, QFontComboBox, QSpinBox {
                padding: 12px;
                font-size: 18px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QFontComboBox:focus, QSpinBox:focus {
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
            QLabel {
                font-size: 18px;
                color: #2c3e50;
            }
        """)

        layout = QVBoxLayout(self)

        # Name Input
        self.name_input = QLineEdit(existing_data["name"] if existing_data else "")
        self.name_input.setPlaceholderText("Theme Name (required)")
        layout.addWidget(QLabel("Theme Name:"))
        layout.addWidget(self.name_input)

        # Tags Input
        self.tags_input = QLineEdit(existing_data["tags"] if existing_data else "")
        self.tags_input.setPlaceholderText("Comma-separated tags (e.g., modern,dark)")
        layout.addWidget(QLabel("Tags:"))
        layout.addWidget(self.tags_input)

        # Context Selector
        self.context_selector = QComboBox()
        self.context_selector.addItems(["Songs", "Scriptures", "Presentations"])
        if existing_data:
            self.context_selector.setCurrentText(existing_data["context"])
        layout.addWidget(QLabel("Context:"))
        layout.addWidget(self.context_selector)

        # Style Options
        style_layout = QHBoxLayout()
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)

        self.alignment_selector = QComboBox()
        self.alignment_selector.addItems(["Centered", "Justified", "Left", "Right"])
        if existing_data:
            self.alignment_selector.setCurrentText(existing_data["alignment"])
        left_layout.addWidget(QLabel("Alignment:"))
        left_layout.addWidget(self.alignment_selector)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(existing_data["font_size"] if existing_data else 18)
        left_layout.addWidget(QLabel("Font Size:"))
        left_layout.addWidget(self.font_size_spin)

        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setCurrentFont(QFont(existing_data["font_family"] if existing_data else "Arial"))
        left_layout.addWidget(QLabel("Font Family:"))
        left_layout.addWidget(self.font_family_combo)

        style_layout.addWidget(left_panel, 1)

        # Color Options
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        self.font_color = existing_data["font_color"] if existing_data else "#000000"
        self.font_color_btn = QPushButton("Choose Font Color")
        self.font_color_btn.clicked.connect(self.choose_font_color)
        right_layout.addWidget(QLabel("Font Color:"))
        right_layout.addWidget(self.font_color_btn)

        self.background_color = existing_data["background_color"] if existing_data else "#ffffff"
        self.background_color_btn = QPushButton("Choose Background Color")
        self.background_color_btn.clicked.connect(self.choose_background_color)
        right_layout.addWidget(QLabel("Background Color:"))
        right_layout.addWidget(self.background_color_btn)

        style_layout.addWidget(right_panel, 1)
        layout.addLayout(style_layout)

        # Preview
        self.sample_display = QTextEdit("Sample Preview Text\nThis is how your theme will look.")
        self.sample_display.setReadOnly(True)
        self.update_preview()
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.sample_display)

        # Save Button
        self.save_btn = QPushButton("Save Theme Template")
        self.save_btn.clicked.connect(self.save_template)
        layout.addWidget(self.save_btn)

    def choose_font_color(self):
        """Choose font color and update preview."""
        color = QColorDialog.getColor(QColor(self.font_color))
        if color.isValid():
            self.font_color = color.name()
            self.update_preview()

    def choose_background_color(self):
        """Choose background color and update preview."""
        color = QColorDialog.getColor(QColor(self.background_color))
        if color.isValid():
            self.background_color = color.name()
            self.update_preview()

    def update_preview(self):
        """Update the sample display with current theme settings."""
        alignment_map = {
            "Centered": "center",
            "Justified": "justify",
            "Left": "left",
            "Right": "right"
        }
        alignment = alignment_map[self.alignment_selector.currentText()]
        font_size = self.font_size_spin.value()
        font_family = self.font_family_combo.currentFont().family()
        self.sample_display.setStyleSheet(f"""
            QTextEdit {{
                color: {self.font_color};
                background-color: {self.background_color};
                font-family: {font_family};
                font-size: {font_size}px;
                text-align: {alignment};
                padding: 10px;
                border: 2px solid #34495e;
                border-radius: 8px;
            }}
        """)

    def save_template(self):
        """Save the theme and close the dialog."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the theme.")
            return

        theme_data = {
            "name": name,
            "context": self.context_selector.currentText(),
            "alignment": self.alignment_selector.currentText(),
            "font_color": self.font_color,
            "background_color": self.background_color,
            "font_size": self.font_size_spin.value(),
            "font_family": self.font_family_combo.currentFont().family(),
            "tags": self.tags_input.text().strip()
        }

        main_window = self.window()
        if self.existing_data:
            success = self.model.update_theme(self.existing_data["id"], theme_data)
            msg = f"Updated theme: {name}" if success else "Failed to update theme"
        else:
            result = self.model.save_theme(theme_data)
            msg = f"Saved theme: {name}" if result else "Failed to save theme"

        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(msg)
        if result or success:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)

class ThemesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.theme_model = ThemeModel()
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

        # Context and Tag Filters
        filter_layout = QHBoxLayout()
        self.context_selector = QComboBox()
        self.context_selector.addItems(["All", "Songs", "Scriptures", "Presentations"])
        self.context_selector.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
        """)
        self.context_selector.currentTextChanged.connect(self.perform_search)
        filter_layout.addWidget(QLabel("Context:"))
        filter_layout.addWidget(self.context_selector)

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

        # Action Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Theme")
        add_btn.clicked.connect(self.open_editor)
        edit_btn = QPushButton("Edit Theme")
        edit_btn.clicked.connect(self.edit_theme)
        delete_btn = QPushButton("Delete Theme")
        delete_btn.clicked.connect(self.delete_theme)
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
        top_layout.addLayout(buttons_layout)
        main_splitter.addWidget(top_panel)

        # Bottom Panel: Theme List and Preview
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setChildrenCollapsible(False)
        bottom_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; width: 4px; }")

        # Theme List
        list_panel = QFrame()
        list_layout = QVBoxLayout(list_panel)
        self.theme_list = QListWidget()
        self.theme_list.setStyleSheet("""
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
        self.theme_list.itemClicked.connect(self.update_preview)
        self.theme_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.theme_list.customContextMenuRequested.connect(self.open_context_menu)
        self.theme_list.keyPressEvent = self.handle_list_keypress
        list_layout.addWidget(QLabel("Themes:"))
        list_layout.addWidget(self.theme_list)
        bottom_splitter.addWidget(list_panel)

        # Preview
        preview_panel = QFrame()
        preview_panel.setMinimumWidth(400)
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_label = QTextEdit("Select a theme to preview")
        self.preview_label.setReadOnly(True)
        self.preview_label.setStyleSheet("""
            QTextEdit {
                font-size: 18px;
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        preview_layout.addWidget(QLabel("Preview:"))
        preview_layout.addWidget(self.preview_label)
        bottom_splitter.addWidget(preview_panel)

        bottom_splitter.setSizes([400, 600])
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([200, 600])

        self.load_themes()
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
        names = [t["name"] for t in self.theme_model.get_all_themes()]
        self.search_completer.setModel(QStringListModel(names))
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        self.tag_filter.addItems(self.theme_model.get_all_tags())
        self.tag_filter.blockSignals(False)

    def perform_search(self):
        """Perform search based on query, context, and tag."""
        query = self.search_input.text().strip()
        context = self.context_selector.currentText() if self.context_selector.currentText() != "All" else ""
        tag = self.tag_filter.currentText() if self.tag_filter.currentText() != "All Tags" else ""
        self.search_results = []
        self.theme_list.clear()

        themes = self.theme_model.search_themes(query, context, tag)
        for i, theme in enumerate(themes):
            item = QListWidgetItem(f"{theme['name']} ({theme['context']})")
            item.setData(Qt.UserRole, theme["id"])
            self.theme_list.addItem(item)
            self.search_results.append(i)

        if themes and self.theme_list.count() > 0:
            self.theme_list.setCurrentRow(0)
            self.update_preview(self.theme_list.item(0))

        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > 10:
                self.search_history.pop()
            self.history_combo.clear()
            self.history_combo.addItems(self.search_history)

        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Found {len(themes)} themes")

    def load_themes(self):
        """Load all themes into the list."""
        self.perform_search()

    def update_preview(self, item: QListWidgetItem):
        """Update the preview with the selected theme."""
        theme_id = item.data(Qt.UserRole)
        theme = self.theme_model.get_theme_by_id(theme_id)
        if not theme:
            return
        alignment_map = {
            "Centered": "center",
            "Justified": "justify",
            "Left": "left",
            "Right": "right"
        }
        alignment = alignment_map[theme["alignment"]]
        self.preview_label.setStyleSheet(f"""
            QTextEdit {{
                color: {theme['font_color']};
                background-color: {theme['background_color']};
                font-family: {theme['font_family']};
                font-size: {theme['font_size']}px;
                text-align: {alignment};
                padding: 20px;
                border: 2px solid #34495e;
                border-radius: 8px;
            }}
        """)
        self.preview_label.setText(f"Theme: {theme['name']}\nContext: {theme['context']}\nTags: {theme['tags']}\nSample content styled with your theme.")
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Previewing {theme['name']}")

    def open_editor(self):
        """Open the editor for a new theme."""
        dialog = ThemeEditor(self.theme_model, self)
        if dialog.exec_():
            self.load_themes()

    def edit_theme(self):
        """Edit the selected theme."""
        item = self.theme_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a theme to edit.")
            return
        theme_id = item.data(Qt.UserRole)
        theme = self.theme_model.get_theme_by_id(theme_id)
        if not theme:
            return
        dialog = ThemeEditor(self.theme_model, self, existing_data=theme)
        if dialog.exec_():
            self.load_themes()

    def delete_theme(self):
        """Delete the selected theme."""
        item = self.theme_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a theme to delete.")
            return
        theme_id = item.data(Qt.UserRole)
        theme = self.theme_model.get_theme_by_id(theme_id)
        if not theme:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{theme['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.theme_model.delete_theme(theme_id):
                self.load_themes()
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Deleted {theme['name']}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete theme.")

    def duplicate_theme(self):
        """Duplicate the selected theme."""
        item = self.theme_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a theme to duplicate.")
            return
        theme_id = item.data(Qt.UserRole)
        if self.theme_model.duplicate_theme(theme_id):
            self.load_themes()
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage(f"Duplicated {self.theme_model.get_theme_by_id(theme_id)['name']} (Copy)")
        else:
            QMessageBox.warning(self, "Error", "Failed to duplicate theme.")

    def apply_theme(self):
        """Apply the selected theme (placeholder)."""
        item = self.theme_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a theme to apply.")
            return
        theme_id = item.data(Qt.UserRole)
        theme = self.theme_model.get_theme_by_id(theme_id)
        if not theme:
            return
        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage(f"Applied theme: {theme['name']} (not implemented)")
        logger.info(f"Placeholder: Apply theme {theme['name']} to {theme['context']}")

    def open_context_menu(self, pos):
        """Open context menu for theme list item."""
        item = self.theme_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        actions = [
            ("Edit", self.edit_theme),
            ("Delete", self.delete_theme),
            ("Duplicate", self.duplicate_theme),
            ("Apply Theme", self.apply_theme)
        ]
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.exec_(self.theme_list.mapToGlobal(pos))

    def handle_list_keypress(self, event):
        """Handle keyboard navigation in theme list."""
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current_row = self.theme_list.currentRow()
            if self.search_results:
                current_index = self.search_results.index(current_row) if current_row in self.search_results else -1
                if event.key() == Qt.Key_Up and current_index > 0:
                    next_row = self.search_results[current_index - 1]
                elif event.key() == Qt.Key_Down and current_index < len(self.search_results) - 1:
                    next_row = self.search_results[current_index + 1]
                else:
                    return
                self.theme_list.setCurrentRow(next_row)
                self.update_preview(self.theme_list.item(next_row))
        else:
            super(QListWidget, self.theme_list).keyPressEvent(event)

    def load_search_from_history(self, query: str):
        """Load a search query from history."""
        self.search_input.setText(query)
        self.perform_search()

# Write example schema to file for user reference
sample_themes = [
    {
        "id": str(uuid.uuid4()),
        "name": "Modern Worship",
        "context": "Songs",
        "alignment": "Centered",
        "font_color": "#ffffff",
        "background_color": "#2c3e50",
        "font_size": 24,
        "font_family": "Arial",
        "tags": "modern,worship",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Classic Sermon",
        "context": "Presentations",
        "alignment": "Left",
        "font_color": "#000000",
        "background_color": "#f4f4f4",
        "font_size": 18,
        "font_family": "Times New Roman",
        "tags": "sermon,classic",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

sample_path = "data/themes/themes_sample.json"
os.makedirs(os.path.dirname(sample_path), exist_ok=True)
with open(sample_path, "w", encoding="utf-8") as f:
    json.dump(sample_themes, f, indent=4, ensure_ascii=False)