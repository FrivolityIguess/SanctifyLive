import os
import json
import logging
import glob
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QTextEdit, QDialog, QLabel, QComboBox, QSplitter, QFrame,
    QFormLayout, QMessageBox, QCompleter, QMenu, QApplication, QDialogButtonBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer, QStringListModel
from PyQt5.QtGui import QIcon, QFont

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SONGS_FILE = "data/songs/songs.json"
HYMNS_DIR = "data/songs/Hymns"
HYMNS_JSON = "data/songs/hymns.json"

# Debug print to confirm file loading
logger.debug("Loading songs_ui.py from %s", __file__)

class AddEditSongDialog(QDialog):
    def __init__(self, parent=None, song=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Song")
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background: #ecf0f1;")
        self.song = song or {"title": "", "sections": [], "tags": ""}
        self.sections = self.song.get("sections", [])

        layout = QVBoxLayout(self)

        # Title and Tags
        form_layout = QFormLayout()
        self.title_input = QLineEdit(self.song["title"])
        self.title_input.setPlaceholderText("Enter song title")
        self.title_input.setToolTip("Enter the song title")
        self.title_input.setStyleSheet("""
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
        self.title_completer = QCompleter()
        self.title_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.title_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.title_completer.popup().setStyleSheet("""
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
        self.title_input.setCompleter(self.title_completer)
        form_layout.addRow("Title:", self.title_input)

        self.tags_input = QLineEdit(self.song.get("tags", ""))
        self.tags_input.setPlaceholderText("Comma-separated tags, e.g., worship, fast")
        self.tags_input.setToolTip("Enter tags, separated by commas")
        self.tags_input.setStyleSheet("""
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
        self.tags_completer = QCompleter()
        self.tags_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.tags_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.tags_completer.popup().setStyleSheet("""
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
        self.tags_input.setCompleter(self.tags_completer)
        form_layout.addRow("Tags:", self.tags_input)
        layout.addLayout(form_layout)

        # Section Editor
        section_layout = QVBoxLayout()
        section_layout.addWidget(QLabel("Add Section:"))
        self.section_type = QComboBox()
        self.section_type.addItems(["Verse", "Chorus", "Bridge", "Tag", "Other"])
        self.section_type.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QComboBox:hover {
                background: #f5faff;
            }
        """)
        self.section_type.setToolTip("Select section type")
        section_layout.addWidget(self.section_type)

        self.section_editor = QTextEdit()
        self.section_editor.setPlaceholderText("Type lyrics for this section...")
        self.section_editor.setToolTip("Enter lyrics for the selected section")
        self.section_editor.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                font-size: 18px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
        """)
        section_layout.addWidget(self.section_editor)

        # Section buttons
        section_buttons_layout = QHBoxLayout()
        self.add_section_btn = QPushButton("Add Section")
        self.add_section_btn.setToolTip("Add a new section to the song")
        self.add_section_btn.setStyleSheet("""
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
        self.add_section_btn.clicked.connect(self.add_section)
        section_buttons_layout.addWidget(self.add_section_btn)

        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.setToolTip("Move selected section up")
        self.move_up_btn.setStyleSheet("""
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
        self.move_up_btn.clicked.connect(self.move_section_up)
        section_buttons_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.setToolTip("Move selected section down")
        self.move_down_btn.setStyleSheet("""
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
        self.move_down_btn.clicked.connect(self.move_section_down)
        section_buttons_layout.addWidget(self.move_down_btn)

        section_layout.addLayout(section_buttons_layout)

        self.sections_display = QListWidget()
        self.sections_display.setStyleSheet("""
            QListWidget {
                font-size: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: #fff;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: #fff;
            }
        """)
        self.sections_display.setToolTip("List of song sections (drag to reorder)")
        self.sections_display.setDragEnabled(True)
        self.sections_display.setAcceptDrops(True)
        self.sections_display.setDropIndicatorShown(True)
        self.sections_display.setDragDropMode(QListWidget.InternalMove)
        self.sections_display.model().rowsMoved.connect(self.update_sections_order)
        section_layout.addWidget(self.sections_display)
        layout.addLayout(section_layout)

        # Preview
        self.preview_label = QLabel("Section Preview:")
        self.preview_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.preview_display = QTextEdit()
        self.preview_display.setReadOnly(True)
        self.preview_display.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                font-size: 18px;
                font-family: 'Georgia', serif;
                border-radius: 8px;
                border: 2px solid #34495e;
            }
        """)
        self.preview_display.setToolTip("Preview of the song sections")
        layout.addWidget(self.preview_label)
        layout.addWidget(self.preview_display)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                border-radius: 6px;
                background: #3498db;
                color: #fff;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        layout.addWidget(buttons)

        # Populate sections
        for section_type, text in self.sections:
            item = QListWidgetItem(f"[{section_type}] {text[:40]}...")
            item.setData(Qt.UserRole, (section_type, text))
            self.sections_display.addItem(item)
        self.update_preview()
        logger.debug("AddEditSongDialog initialized")

    def add_section(self):
        section_type = self.section_type.currentText()
        text = self.section_editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty Section", "Please enter lyrics for the section.")
            return
        self.sections.append((section_type, text))
        item = QListWidgetItem(f"[{section_type}] {text[:40]}...")
        item.setData(Qt.UserRole, (section_type, text))
        self.sections_display.addItem(item)
        self.section_editor.clear()
        self.update_preview()
        logger.debug("Added section: %s", section_type)

    def move_section_up(self):
        current_row = self.sections_display.currentRow()
        if current_row <= 0:
            return
        self.sections[current_row], self.sections[current_row - 1] = self.sections[current_row - 1], self.sections[current_row]
        self.sections_display.clear()
        for section_type, text in self.sections:
            item = QListWidgetItem(f"[{section_type}] {text[:40]}...")
            item.setData(Qt.UserRole, (section_type, text))
            self.sections_display.addItem(item)
        self.sections_display.setCurrentRow(current_row - 1)
        self.update_preview()
        logger.debug("Moved section up at index %d", current_row)

    def move_section_down(self):
        current_row = self.sections_display.currentRow()
        if current_row < 0 or current_row >= len(self.sections) - 1:
            return
        self.sections[current_row], self.sections[current_row + 1] = self.sections[current_row + 1], self.sections[current_row]
        self.sections_display.clear()
        for section_type, text in self.sections:
            item = QListWidgetItem(f"[{section_type}] {text[:40]}...")
            item.setData(Qt.UserRole, (section_type, text))
            self.sections_display.addItem(item)
        self.sections_display.setCurrentRow(current_row + 1)
        self.update_preview()
        logger.debug("Moved section down at index %d", current_row)

    def update_sections_order(self):
        self.sections = []
        for i in range(self.sections_display.count()):
            item = self.sections_display.item(i)
            try:
                section_type, text = item.data(Qt.UserRole)
                self.sections.append((section_type, text))
            except Exception as e:
                logger.error("Failed to parse section item at index %d: %s", i, traceback.format_exc())
                continue
        self.update_preview()
        logger.debug("Reordered sections via drag-and-drop")

    def update_preview(self):
        html = ""
        for section_type, text in self.sections:
            html += f"<b>{section_type}</b><br>{text.replace('\n', '<br>')}<br><br>"
        self.preview_display.setHtml(html)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "sections": self.sections,
            "tags": ",".join(tag.strip() for tag in self.tags_input.text().split(",") if tag.strip())
        }

class TagDistributionDialog(QDialog):
    def __init__(self, tag_counts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tag Distribution")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background: #ecf0f1;")
        layout = QVBoxLayout(self)

        # Chart display using QWebEngineView
        self.chart_view = QWebEngineView()
        layout.addWidget(self.chart_view)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                border-radius: 6px;
                background: #3498db;
                color: #fff;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        layout.addWidget(buttons)

        # Generate and load chart
        self.load_chart(tag_counts)

    def load_chart(self, tag_counts):
        # Create Chart.js HTML content
        chart_html = """
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <canvas id="tagChart" style="max-height: 300px;"></canvas>
            <script>
                const ctx = document.getElementById('tagChart').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: %s,
                        datasets: [{
                            label: 'Number of Songs',
                            data: %s,
                            backgroundColor: ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c'],
                            borderColor: ['#2980b9', '#c0392b', '#27ae60', '#f39c12', '#8e44ad', '#16a085'],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'Number of Songs', color: '#2c3e50' },
                                ticks: { color: '#2c3e50' }
                            },
                            x: {
                                title: { display: true, text: 'Tags', color: '#2c3e50' },
                                ticks: { color: '#2c3e50' }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            title: { display: true, text: 'Song Tag Distribution', color: '#2c3e50', font: { size: 18 } }
                        }
                    }
                });
            </script>
        </body>
        </html>
        """ % (json.dumps(list(tag_counts.keys())), json.dumps(list(tag_counts.values())))
        # Save HTML to a temporary file and load it
        temp_file = "data/temp_chart.html"
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(chart_html)
        self.chart_view.load(QUrl.fromLocalFile(os.path.abspath(temp_file)))
        logger.debug("Loaded tag distribution chart")

class SongsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.songs = []
        self.filtered_songs = []
        self.search_history = []
        self.tag_cache = set()
        self.hymn_file_cache = {}  # Cache for hymn file timestamps

        # Main layout with vertical splitter
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; height: 4px; }")

        # Top Panel: Search and Filters
        top_panel = QFrame()
        top_panel.setStyleSheet("background: #ecf0f1; padding: 20px; border-bottom: 2px solid #bdc3c7;")
        top_layout = QVBoxLayout(top_panel)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title...")
        self.search_input.setToolTip("Search songs by title or lyrics")
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
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.search_input.textChanged.connect(lambda: self.search_timer.start(300))  # Debounce search
        self.search_mode = "title"

        self.search_mode_toggle = QPushButton("Switch to Lyrics Search")
        self.search_mode_toggle.setIcon(QIcon("assets/icons/search.png"))
        self.search_mode_toggle.setToolTip("Toggle between title and lyrics search")
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

        self.clear_search_btn = QPushButton("Clear Search")
        self.clear_search_btn.setToolTip("Clear search input and filters")
        self.clear_search_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #e74c3c;
                border-radius: 6px;
                background: #e74c3c;
                color: #fff;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_mode_toggle)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_btn)
        top_layout.addLayout(search_layout)

        # Tag Filter and Search History
        filter_layout = QHBoxLayout()
        self.tag_filter = QComboBox()
        self.tag_filter.setEditable(True)  # Enable autocompletion
        self.tag_filter.addItem("All Tags")
        self.tag_filter.setToolTip("Filter songs by tag (type to autocomplete)")
        self.tag_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QComboBox:hover {
                background: #f5faff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.tag_filter.currentTextChanged.connect(self.apply_tag_filter)
        self.tag_completer = QCompleter()
        self.tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.tag_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.tag_completer.popup().setStyleSheet("""
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
        self.tag_filter.setCompleter(self.tag_completer)
        filter_layout.addWidget(QLabel("Filter by Tag:"))
        filter_layout.addWidget(self.tag_filter)

        self.history_combo = QComboBox()
        self.history_combo.setToolTip("Select recent searches")
        self.history_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QComboBox:hover {
                background: #f5faff;
            }
        """)
        self.history_combo.activated[str].connect(self.load_search_from_history)
        filter_layout.addWidget(QLabel("Recent Searches:"))
        filter_layout.addWidget(self.history_combo)
        top_layout.addLayout(filter_layout)

        main_splitter.addWidget(top_panel)

        # Bottom Panel: Song List and Preview
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setChildrenCollapsible(False)
        bottom_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; width: 4px; }")

        # Song List
        list_panel = QFrame()
        list_layout = QVBoxLayout(list_panel)
        self.song_list = QListWidget()
        self.song_list.setStyleSheet("""
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
        self.song_list.setToolTip("List of songs")
        self.song_list.itemClicked.connect(self.show_song_preview)
        self.song_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.song_list.customContextMenuRequested.connect(self.show_context_menu)
        self.song_list.keyPressEvent = self.handle_list_keypress
        list_layout.addWidget(self.song_list)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Song")
        add_btn.setToolTip("Add a new song")
        add_btn.clicked.connect(self.add_song)
        edit_btn = QPushButton("Edit Song")
        edit_btn.setToolTip("Edit selected song")
        edit_btn.clicked.connect(self.edit_song)
        delete_btn = QPushButton("Delete Song")
        delete_btn.setToolTip("Delete selected song")
        delete_btn.clicked.connect(self.delete_song)
        tag_chart_btn = QPushButton("Show Tag Distribution")
        tag_chart_btn.setToolTip("Display chart of song tag distribution")
        tag_chart_btn.clicked.connect(self.show_tag_distribution)
        for btn in [add_btn, edit_btn, delete_btn, tag_chart_btn]:
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
        buttons_layout.addWidget(tag_chart_btn)
        list_layout.addLayout(buttons_layout)
        bottom_splitter.addWidget(list_panel)

        # Preview
        preview_panel = QFrame()
        preview_panel.setMinimumWidth(400)
        preview_layout = QVBoxLayout(preview_panel)
        preview_label = QLabel("Song Preview:")
        preview_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 20px;
                font-size: 20px;
                font-family: 'Georgia', serif;
                border-radius: 8px;
                border: 2px solid #34495e;
            }
        """)
        self.preview.setToolTip("Preview of the selected song")
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview)
        bottom_splitter.addWidget(preview_panel)

        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([200, 600])
        bottom_splitter.setSizes([400, 600])

        layout = QVBoxLayout(self)
        layout.addWidget(main_splitter)

        # Initialize tags_completer
        self.tags_completer = QCompleter()
        self.tags_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.tags_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.tags_completer.popup().setStyleSheet("""
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

        self.load_songs()
        self.search_input.setFocus()
        logger.debug("SongsTab initialized")

    def show_tag_distribution(self):
        # Count tags
        tag_counts = {}
        for song in self.songs:
            for tag in song.get("tags", "").split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if not tag_counts:
            QMessageBox.information(self, "No Tags", "No tags found in songs.")
            logger.debug("No tags available for chart")
            return

        # Show chart dialog
        dialog = TagDistributionDialog(tag_counts, self)
        dialog.exec_()
        logger.debug("Displayed tag distribution chart")

    def parse_txt_hymn(self, file_path):
        """Parse a .txt hymn file into the song format."""
        try:
            file_mtime = os.path.getmtime(file_path)
            if file_path in self.hymn_file_cache and self.hymn_file_cache[file_path]["mtime"] == file_mtime:
                logger.debug("Using cached hymn for %s", file_path)
                return self.hymn_file_cache[file_path]["data"]

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if not lines:
                logger.warning("Empty hymn file: %s", file_path)
                return None

            # Extract title from filename (remove numbering and extension)
            title = os.path.basename(file_path).split(".", 1)[-1].rsplit(".", 1)[0].strip()
            if not title:
                logger.warning("No title in hymn file: %s", file_path)
                return None

            sections = []
            current_text = []
            verse_count = 0
            chorus_text = None
            stanza_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    if stanza_lines:
                        # Process the previous stanza
                        text = "\n".join(stanza_lines).strip()
                        if text:
                            # Check if this text matches a previous stanza (likely a chorus)
                            if chorus_text and text == chorus_text:
                                sections.append(("Chorus", text))
                            else:
                                verse_count += 1
                                sections.append((f"Verse {verse_count}", text))
                                if not chorus_text and len(stanza_lines) <= 6:
                                    # Heuristic: short stanzas after first verse might be chorus
                                    chorus_text = text
                        stanza_lines = []
                    continue
                stanza_lines.append(line)

            # Process the last stanza
            if stanza_lines:
                text = "\n".join(stanza_lines).strip()
                if text:
                    if chorus_text and text == chorus_text:
                        sections.append(("Chorus", text))
                    else:
                        verse_count += 1
                        sections.append((f"Verse {verse_count}", text))

            if not sections:
                logger.warning("No valid sections in hymn file: %s", file_path)
                return None

            hymn = {
                "title": title,
                "sections": sections,
                "tags": "hymn"
            }
            self.hymn_file_cache[file_path] = {"mtime": file_mtime, "data": hymn}
            logger.debug("Parsed hymn file %s: %s", file_path, hymn["title"])
            return hymn
        except Exception as e:
            logger.error("Failed to parse hymn file %s: %s", file_path, traceback.format_exc())
            return None

    def load_songs(self):
        self.preview.setHtml("<p>Loading...</p>")
        self.songs = []

        # Load from songs.json
        if os.path.exists(SONGS_FILE):
            try:
                with open(SONGS_FILE, 'r', encoding='utf-8') as f:
                    self.songs = json.load(f)
                logger.debug("Loaded %d songs from %s", len(self.songs), SONGS_FILE)
            except json.JSONDecodeError as e:
                logger.error("JSON decode error in %s: %s", SONGS_FILE, traceback.format_exc())
                QMessageBox.critical(self, "Load Error", f"Invalid JSON format in {SONGS_FILE}:\n{e}")
            except Exception as e:
                logger.error("Failed to load %s: %s", SONGS_FILE, traceback.format_exc())
                QMessageBox.critical(self, "Load Error", f"Could not load {SONGS_FILE}:\n{e}")
        else:
            logger.warning("Songs file %s does not exist", SONGS_FILE)
            os.makedirs(os.path.dirname(SONGS_FILE), exist_ok=True)
            with open(SONGS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            logger.debug("Created empty %s", SONGS_FILE)

        # Load from hymns.json
        if os.path.exists(HYMNS_JSON):
            try:
                with open(HYMNS_JSON, 'r', encoding='utf-8') as f:
                    hymns = json.load(f)
                for hymn in hymns:
                    if isinstance(hymn, dict) and "title" in hymn:
                        hymn.setdefault("sections", [])
                        hymn.setdefault("tags", "hymn")
                        if not any(s["title"] == hymn["title"] for s in self.songs):
                            self.songs.append(hymn)
                logger.debug("Loaded %d hymns from %s", len(hymns), HYMNS_JSON)
            except json.JSONDecodeError as e:
                logger.error("JSON decode error in %s: %s", HYMNS_JSON, traceback.format_exc())
                QMessageBox.critical(self, "Load Error", f"Invalid JSON format in {HYMNS_JSON}:\n{e}")
            except Exception as e:
                logger.error("Failed to load %s: %s", HYMNS_JSON, traceback.format_exc())
                QMessageBox.critical(self, "Load Error", f"Could not load {HYMNS_JSON}:\n{e}")

        # Load from Hymns/*.txt
        if os.path.exists(HYMNS_DIR):
            for txt_file in glob.glob(os.path.join(HYMNS_DIR, "*.txt")):
                hymn = self.parse_txt_hymn(txt_file)
                if hymn and not any(s["title"] == hymn["title"] for s in self.songs):
                    self.songs.append(hymn)
            logger.debug("Loaded hymns from %s", HYMNS_DIR)

        # Save merged songs to songs.json
        self.save_songs()
        self.populate_tag_filter()
        self.update_completers()
        self.perform_search()

    def save_songs(self):
        os.makedirs(os.path.dirname(SONGS_FILE), exist_ok=True)
        try:
            with open(SONGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.songs, f, indent=2)
            logger.debug("Saved %d songs to %s", len(self.songs), SONGS_FILE)
        except Exception as e:
            logger.error("Failed to save songs: %s", traceback.format_exc())
            QMessageBox.critical(self, "Save Error", f"Could not save songs:\n{e}")

    def populate_tag_filter(self):
        self.tag_cache = set()
        for song in self.songs:
            for tag in song.get("tags", "").split(","):
                tag = tag.strip()
                if tag:
                    self.tag_cache.add(tag)
        current = self.tag_filter.currentText()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        for tag in sorted(self.tag_cache):
            self.tag_filter.addItem(tag)
        self.tag_filter.setCurrentText(current if current in self.tag_cache else "All Tags")
        self.tag_filter.blockSignals(False)
        self.tag_completer.setModel(QStringListModel(sorted(self.tag_cache)))
        logger.debug("Populated tag filter with %d tags", len(self.tag_cache))

    def update_completers(self):
        logger.debug("Updating completers")
        titles = [song["title"] for song in self.songs]
        self.search_completer.setModel(QStringListModel(titles))
        self.tags_completer.setModel(QStringListModel(sorted(self.tag_cache)))
        logger.debug("Completers updated with %d titles and %d tags", len(titles), len(self.tag_cache))

    def perform_search(self):
        query = self.search_input.text().lower().strip()
        selected_tag = self.tag_filter.currentText()
        self.filtered_songs = []
        self.search_results = []

        for i, song in enumerate(self.songs):
            matches_query = (
                query in song["title"].lower() if self.search_mode == "title"
                else any(query in text.lower() for _, text in song.get("sections", []))
            )
            matches_tag = (
                selected_tag == "All Tags" or selected_tag in song.get("tags", "").split(",")
            )
            if matches_query and matches_tag:
                self.filtered_songs.append(song)
                self.search_results.append(i)

        self.song_list.clear()
        for song in self.filtered_songs:
            item = QListWidgetItem(song["title"])
            self.song_list.addItem(item)

        if self.filtered_songs and self.song_list.count() > 0:
            self.song_list.setCurrentRow(0)
            self.show_song_preview(self.song_list.item(0))
        else:
            self.preview.setHtml("<p>No results found.</p>")

        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > 10:
                self.search_history.pop()
            self.history_combo.clear()
            self.history_combo.addItems(self.search_history)
        logger.debug("Performed search with query '%s' and tag '%s', found %d results", query, selected_tag, len(self.filtered_songs))

    def clear_search(self):
        self.search_input.clear()
        self.tag_filter.setCurrentText("All Tags")
        self.search_mode = "title"
        self.search_mode_toggle.setText("Switch to Lyrics Search")
        self.search_input.setPlaceholderText("Search by title...")
        self.perform_search()
        logger.debug("Cleared search")

    def show_song_preview(self, item):
        title = item.text()
        for song in self.filtered_songs:
            if song["title"] == title:
                html = f"<h3>{song['title']}</h3>"
                for section_type, text in song.get("sections", []):
                    html += f"<b>{section_type}</b><br>{text.replace('\n', '<br>')}<br><br>"
                self.preview.setHtml(html)
                logger.debug("Showing preview for song: %s", title)
                return

    def add_song(self):
        dialog = AddEditSongDialog(self)
        dialog.title_completer.setModel(QStringListModel([s["title"] for s in self.songs]))
        dialog.tags_completer.setModel(self.tags_completer.model())
        if dialog.exec_() == QDialog.Accepted:
            new_song = dialog.get_data()
            if not new_song["title"]:
                QMessageBox.warning(self, "Missing Title", "Please enter a song title.")
                logger.warning("Attempted to add song with empty title")
                return
            if any(s["title"] == new_song["title"] for s in self.songs):
                QMessageBox.warning(self, "Duplicate Title", "A song with this title already exists.")
                logger.warning("Duplicate song title: %s", new_song["title"])
                return
            self.songs.append(new_song)
            self.save_songs()
            self.populate_tag_filter()
            self.update_completers()
            self.perform_search()
            logger.debug("Added new song: %s", new_song["title"])

    def edit_song(self):
        current_item = self.song_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a song to edit.")
            logger.warning("No song selected for editing")
            return
        title = current_item.text()
        song = next((s for s in self.songs if s["title"] == title), None)
        if not song:
            logger.error("Song not found: %s", title)
            return
        dialog = AddEditSongDialog(self, song)
        dialog.title_completer.setModel(QStringListModel([s["title"] for s in self.songs if s["title"] != title]))
        dialog.tags_completer.setModel(self.tags_completer.model())
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            if not updated_data["title"]:
                QMessageBox.warning(self, "Missing Title", "Please enter a song title.")
                logger.warning("Attempted to edit song with empty title")
                return
            if updated_data["title"] != title and any(s["title"] == updated_data["title"] for s in self.songs):
                QMessageBox.warning(self, "Duplicate Title", "A song with this title already exists.")
                logger.warning("Duplicate song title on edit: %s", updated_data["title"])
                return
            song.update(updated_data)
            self.save_songs()
            self.populate_tag_filter()
            self.update_completers()
            self.perform_search()
            logger.debug("Edited song: %s", title)

    def delete_song(self):
        current_item = self.song_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a song to delete.")
            logger.warning("No song selected for deletion")
            return
        title = current_item.text()
        confirm = QMessageBox.question(
            self, "Delete Song",
            f"Are you sure you want to delete '{title}'?",
            QMessageBox.Yes | QDialogButtonBox.No
        )
        if confirm == QMessageBox.Yes:
            self.songs = [s for s in self.songs if s["title"] != title]
            self.save_songs()
            self.populate_tag_filter()
            self.update_completers()
            self.perform_search()
            logger.debug("Deleted song: %s", title)

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_lyrics_action = menu.addAction("Copy Lyrics")
        copy_title_action = menu.addAction("Copy Title")
        duplicate_action = menu.addAction("Duplicate Song")
        action = menu.exec_(self.song_list.mapToGlobal(pos))
        if not action:
            return
        current_item = self.song_list.currentItem()
        if not current_item:
            logger.warning("No song selected for context menu")
            return
        title = current_item.text()
        song = next((s for s in self.filtered_songs if s["title"] == title), None)
        if not song:
            logger.error("Song not found for context menu: %s", title)
            return
        if action == copy_lyrics_action:
            lyrics = "\n\n".join(f"{section_type}:\n{text}" for section_type, text in song.get("sections", []))
            QApplication.clipboard().setText(f"{song['title']}\n\n{lyrics}")
            logger.debug("Copied lyrics for song: %s", title)
        elif action == copy_title_action:
            QApplication.clipboard().setText(song["title"])
            logger.debug("Copied title for song: %s", title)
        elif action == duplicate_action:
            new_song = {
                "title": f"{song['title']} (Copy)",
                "sections": song["sections"],
                "tags": song["tags"]
            }
            if any(s["title"] == new_song["title"] for s in self.songs):
                QMessageBox.warning(self, "Duplicate Title", "A song with this title already exists.")
                logger.warning("Duplicate title on copy: %s", new_song["title"])
                return
            self.songs.append(new_song)
            self.save_songs()
            self.populate_tag_filter()
            self.update_completers()
            self.perform_search()
            logger.debug("Duplicated song: %s", new_song["title"])

    def handle_list_keypress(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current_row = self.song_list.currentRow()
            if self.search_results:
                current_index = self.search_results.index(current_row) if current_row in self.search_results else -1
                if event.key() == Qt.Key_Up and current_index > 0:
                    next_row = self.search_results[current_index - 1]
                elif event.key() == Qt.Key_Down and current_index < len(self.search_results) - 1:
                    next_row = self.search_results[current_index + 1]
                else:
                    return
                self.song_list.setCurrentRow(next_row)
                self.show_song_preview(self.song_list.item(next_row))
        else:
            super(QListWidget, self.song_list).keyPressEvent(event)

    def load_search_from_history(self, query):
        self.search_input.setText(query)
        self.perform_search()
        logger.debug("Loaded search from history: %s", query)

    def apply_tag_filter(self, selected_tag):
        self.perform_search()
        logger.debug("Applied tag filter: %s", selected_tag)

    def toggle_search_mode(self):
        self.search_mode = "lyrics" if self.search_mode == "title" else "title"
        self.search_mode_toggle.setText(f"Switch to {'Title' if self.search_mode == 'lyrics' else 'Lyrics'} Search")
        self.search_input.setPlaceholderText(f"Search by {self.search_mode}...")
        self.perform_search()
        logger.debug("Toggled search mode to %s", self.search_mode)