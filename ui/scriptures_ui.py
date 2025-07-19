import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame, QStackedWidget, QCompleter, QMenu, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QStringListModel
from PyQt5.QtGui import QIcon, QFont

class ScripturesTab(QWidget):
    def __init__(self):
        super().__init__()

        self.bible_versions_dir = "data/bibles"
        self.current_bible_data = {}
        self.highlighted_verse = None
        self.search_history = []
        self.search_results = []

        # Main layout with vertical splitter for top (search) and bottom (table + preview)
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; height: 4px; }")

        # Top Panel (Bible version + search)
        top_panel = QFrame()
        top_panel.setStyleSheet("background: #ecf0f1; padding: 20px; border-bottom: 2px solid #bdc3c7;")
        top_layout = QVBoxLayout(top_panel)

        # Bible Version Selection
        version_layout = QHBoxLayout()
        version_label = QLabel("Bible Version:")
        version_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.version_combo = QComboBox()
        self.version_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: #fff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(assets/icons/dropdown.png);
                width: 14px;
                height: 14px;
            }
        """)
        self.version_combo.currentTextChanged.connect(self.load_bible_version)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_combo)
        top_layout.addLayout(version_layout)
        top_layout.addSpacing(15)

        # Search Stack
        self.search_stack = QStackedWidget()
        self.search_stack.setStyleSheet("margin-bottom: 10px;")

        # Search Mode 1: Fuzzy single-line input
        self.fuzzy_input = QLineEdit()
        self.fuzzy_input.setPlaceholderText("Search: e.g. John 3:16 or 'God so loved'")
        self.fuzzy_input.setStyleSheet("""
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
        self.fuzzy_input.textChanged.connect(self.perform_fuzzy_search)
        fuzzy_wrapper = QFrame()
        fuzzy_layout = QVBoxLayout(fuzzy_wrapper)
        fuzzy_layout.addWidget(self.fuzzy_input)
        self.search_stack.addWidget(fuzzy_wrapper)

        # Search Mode 2: Segmented search (Book | Chapter | Verse)
        self.book_input = QLineEdit()
        self.chapter_input = QLineEdit()
        self.verse_input = QLineEdit()

        # Setup autocompleters
        self.book_completer = QCompleter()
        self.chapter_completer = QCompleter()
        self.verse_completer = QCompleter()
        for completer in [self.book_completer, self.chapter_completer, self.verse_completer]:
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setMaxVisibleItems(12)
            completer.popup().setStyleSheet("""
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

        self.book_input.setCompleter(self.book_completer)
        self.chapter_input.setCompleter(self.chapter_completer)
        self.verse_input.setCompleter(self.verse_completer)

        for field in [self.book_input, self.chapter_input, self.verse_input]:
            field.setStyleSheet("""
                QLineEdit {
                    padding: 12px;
                    font-size: 18px;
                    border: 2px solid #3498db;
                    border-radius: 6px;
                    background: #fff;
                    min-width: 120px;
                }
                QLineEdit:focus {
                    border: 2px solid #2980b9;
                    background: #f5faff;
                }
            """)
            field.setPlaceholderText(field.objectName().split('_')[0].capitalize())

        segmented_layout = QHBoxLayout()
        segmented_wrapper = QFrame()
        segmented_layout.addWidget(self.book_input)
        segmented_layout.addWidget(self.chapter_input)
        segmented_layout.addWidget(self.verse_input)
        segmented_wrapper.setLayout(segmented_layout)
        self.search_stack.addWidget(segmented_wrapper)

        # Mode toggle button (below search)
        self.search_mode_icon = QPushButton("Switch to Fuzzy Search")
        self.search_mode_icon.setIcon(QIcon("assets/icons/search.png"))
        self.search_mode_icon.setStyleSheet("""
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
        self.search_mode_icon.clicked.connect(self.toggle_search_mode)

        # Search layout
        search_layout = QVBoxLayout()
        search_layout.addWidget(self.search_stack)
        search_layout.addWidget(self.search_mode_icon)
        top_layout.addLayout(search_layout)

        # Search history
        self.history_combo = QComboBox()
        self.history_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: #fff;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.history_combo.activated[str].connect(self.load_search_from_history)
        top_layout.addSpacing(10)
        top_layout.addWidget(QLabel("Recent Searches:"))
        top_layout.addWidget(self.history_combo)
        main_splitter.addWidget(top_panel)

        # Bottom Panel (Table + Preview)
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setChildrenCollapsible(False)
        bottom_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; width: 4px; }")

        # Scripture Table
        table_panel = QFrame()
        table_layout = QVBoxLayout(table_panel)
        self.scripture_table = QTableWidget()
        self.scripture_table.setColumnCount(4)
        self.scripture_table.setHorizontalHeaderLabels(["Book", "Chapter", "Verse", "Scripture"])
        header = self.scripture_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.scripture_table.setColumnWidth(1, 120)
        self.scripture_table.setColumnWidth(2, 100)
        self.scripture_table.verticalHeader().setVisible(False)
        self.scripture_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scripture_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scripture_table.setStyleSheet("""
            QTableWidget {
                font-size: 18px;
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                background: #fff;
            }
            QTableWidget::item:hover {
                background: #f5faff;
            }
        """)
        self.scripture_table.cellClicked.connect(self.highlight_scripture)
        self.scripture_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scripture_table.customContextMenuRequested.connect(self.show_context_menu)
        table_layout.addWidget(self.scripture_table)
        bottom_splitter.addWidget(table_panel)

        # Preview Panel
        preview_panel = QFrame()
        preview_panel.setMinimumWidth(400)
        preview_layout = QVBoxLayout(preview_panel)
        preview_label = QLabel("Live Preview:")
        preview_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.preview_display = QTextEdit()
        self.preview_display.setReadOnly(True)
        self.preview_display.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 20px;
                font-size: 28px;
                font-family: 'Georgia', serif;
                border-radius: 8px;
                border: 2px solid #34495e;
            }
        """)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_display)
        bottom_splitter.addWidget(preview_panel)

        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([200, 600])

        # Final Layout
        layout = QVBoxLayout(self)
        layout.addWidget(main_splitter)

        self.load_available_versions()

        # Timer for debounce
        self.search_debounce = QTimer()
        self.search_debounce.setSingleShot(True)
        self.search_debounce.timeout.connect(self.perform_fuzzy_search)

        # Smart segmented connections
        self.book_input.textEdited.connect(self.update_book_suggestions)
        self.book_input.returnPressed.connect(self.move_to_chapter)
        self.chapter_input.textEdited.connect(self.update_chapter_suggestions)
        self.chapter_input.returnPressed.connect(self.move_to_verse)
        self.verse_input.textEdited.connect(self.update_verse_suggestions)
        self.verse_input.returnPressed.connect(self.perform_segmented_search)

        # Keyboard navigation
        self.scripture_table.keyPressEvent = self.handle_table_keypress
        self.current_search_mode = 1  # Start with segmented search
        self.search_stack.setCurrentIndex(1)
        self.book_input.setFocus()

    def toggle_search_mode(self):
        self.current_search_mode = 1 if self.current_search_mode == 0 else 0
        self.search_stack.setCurrentIndex(self.current_search_mode)
        self.search_mode_icon.setText("Switch to Fuzzy Search" if self.current_search_mode == 1 else "Switch to Segmented Search")
        self.search_mode_icon.setIcon(
            QIcon("assets/icons/search.png" if self.current_search_mode == 1 else "assets/icons/keyboard.png")
        )
        if self.current_search_mode == 0:
            self.fuzzy_input.setFocus()
        else:
            self.book_input.setFocus()

    def update_book_suggestions(self):
        if not self.current_bible_data:
            return
        books = list(self.current_bible_data.keys())
        model = QStringListModel(books)
        self.book_completer.setModel(model)
        self.book_completer.complete()

    def update_chapter_suggestions(self):
        book = self.book_input.text().strip()
        if not book or not self.current_bible_data:
            return
        matched_book = next((b for b in self.current_bible_data.keys() if b.lower() == book.lower()), None)
        if matched_book:
            chapters = list(self.current_bible_data[matched_book].keys())
            model = QStringListModel(chapters)
            self.chapter_completer.setModel(model)
            self.chapter_completer.complete()

    def update_verse_suggestions(self):
        book = self.book_input.text().strip()
        chapter = self.chapter_input.text().strip()
        if not (book and chapter) or not self.current_bible_data:
            return
        matched_book = next((b for b in self.current_bible_data.keys() if b.lower() == book.lower()), None)
        if matched_book and chapter in self.current_bible_data[matched_book]:
            verses = list(self.current_bible_data[matched_book][chapter].keys())
            model = QStringListModel(verses)
            self.verse_completer.setModel(model)
            self.verse_completer.complete()

    def move_to_chapter(self):
        book = self.book_input.text().strip()
        if book and book in self.current_bible_data:
            self.chapter_input.setFocus()

    def move_to_verse(self):
        book = self.book_input.text().strip()
        chapter = self.chapter_input.text().strip()
        if book in self.current_bible_data and chapter in self.current_bible_data[book]:
            self.verse_input.setFocus()

    def perform_segmented_search(self):
        book = self.book_input.text().strip()
        chapter = self.chapter_input.text().strip()
        verse = self.verse_input.text().strip()
        if not (book and chapter and verse):
            return
        try:
            text = self.current_bible_data[book][chapter][verse]
            self.preview_display.setHtml(f"<h3>{book} {chapter}:{verse}</h3><p>{text}</p>")
            self.scroll_to_scripture(book, chapter, verse)
            self.add_to_search_history(f"{book} {chapter}:{verse}")
        except Exception:
            self.preview_display.setText("Verse not found")

    def perform_fuzzy_search(self):
        query = self.fuzzy_input.text().strip().lower()
        if not query:
            return
        self.search_results = []
        self.scripture_table.clearSelection()
        
        if query.startswith('"') and query.endswith('"'):
            query = query[1:-1]  # Remove quotes for phrase search
            for row in range(self.scripture_table.rowCount()):
                text = self.scripture_table.item(row, 3).text().lower()
                if query in text:
                    self.search_results.append(row)
        else:
            for row in range(self.scripture_table.rowCount()):
                full_text = " ".join([self.scripture_table.item(row, i).text().lower() for i in range(4)])
                if query in full_text:
                    self.search_results.append(row)

        if self.search_results:
            self.scripture_table.selectRow(self.search_results[0])
            self.scripture_table.scrollToItem(self.scripture_table.item(self.search_results[0], 0))
            self.highlight_scripture(self.search_results[0], 0)
            self.add_to_search_history(query)
        else:
            self.preview_display.setText("No results found.")

    def scroll_to_scripture(self, book, chapter, verse):
        for row in range(self.scripture_table.rowCount()):
            if (
                self.scripture_table.item(row, 0).text() == book and
                self.scripture_table.item(row, 1).text() == chapter and
                self.scripture_table.item(row, 2).text() == verse
            ):
                self.search_results = [row]
                self.scripture_table.selectRow(row)
                self.scripture_table.scrollToItem(self.scripture_table.item(row, 0))
                self.highlight_scripture(row, 0)
                break

    def highlight_scripture(self, row, col):
        book = self.scripture_table.item(row, 0).text()
        chapter = self.scripture_table.item(row, 1).text()
        verse = self.scripture_table.item(row, 2).text()
        text = self.scripture_table.item(row, 3).text()
        self.highlighted_verse = (book, chapter, verse)
        self.preview_display.setHtml(f"<h3>{book} {chapter}:{verse}</h3><p>{text}</p>")

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = menu.addAction("Copy Verse")
        action = menu.exec_(self.scripture_table.mapToGlobal(pos))
        if action == copy_action:
            row = self.scripture_table.currentRow()
            if row >= 0:
                book = self.scripture_table.item(row, 0).text()
                chapter = self.scripture_table.item(row, 1).text()
                verse = self.scripture_table.item(row, 2).text()
                text = self.scripture_table.item(row, 3).text()
                QApplication.clipboard().setText(f"{book} {chapter}:{verse} - {text}")

    def handle_table_keypress(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current_row = self.scripture_table.currentRow()
            if self.search_results:
                current_index = self.search_results.index(current_row) if current_row in self.search_results else -1
                if event.key() == Qt.Key_Up and current_index > 0:
                    next_row = self.search_results[current_index - 1]
                elif event.key() == Qt.Key_Down and current_index < len(self.search_results) - 1:
                    next_row = self.search_results[current_index + 1]
                else:
                    return
                self.scripture_table.selectRow(next_row)
                self.scripture_table.scrollToItem(self.scripture_table.item(next_row, 0))
                self.highlight_scripture(next_row, 0)
        else:
            super(QTableWidget, self.scripture_table).keyPressEvent(event)

    def add_to_search_history(self, query):
        if query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > 10:
                self.search_history.pop()
            self.history_combo.clear()
            self.history_combo.addItems(self.search_history)

    def load_search_from_history(self, query):
        if self.current_search_mode == 0:
            self.fuzzy_input.setText(query)
            self.perform_fuzzy_search()
        else:
            parts = query.split()
            if len(parts) >= 2:
                book = " ".join(parts[:-1])
                chap_verse = parts[-1].split(":")
                if len(chap_verse) == 2:
                    self.book_input.setText(book)
                    self.chapter_input.setText(chap_verse[0])
                    self.verse_input.setText(chap_verse[1])
                    self.perform_segmented_search()

    def load_available_versions(self):
        self.version_combo.clear()
        self.version_combo.addItem("Loading...")
        self.version_combo.setEnabled(False)
        QTimer.singleShot(100, self._load_versions)

    def _load_versions(self):
        versions = []
        if os.path.exists(self.bible_versions_dir):
            for folder in os.listdir(self.bible_versions_dir):
                folder_path = os.path.join(self.bible_versions_dir, folder)
                if os.path.isdir(folder_path):
                    for file in os.listdir(folder_path):
                        if file.endswith("_bible.json"):
                            versions.append(folder.upper())
                            break
        self.version_combo.clear()
        self.version_combo.addItems(sorted(versions))
        self.version_combo.setEnabled(True)
        if versions:
            self.load_bible_version(versions[0])

    def load_bible_version(self, version):
        self.preview_display.setHtml("<p>Loading...</p>")
        path = os.path.join(self.bible_versions_dir, version.lower(), f"{version.lower()}_bible.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.current_bible_data = json.load(f)
                    self.populate_scripture_table()
                    self.update_book_suggestions()
            except Exception as e:
                self.scripture_table.setRowCount(0)
                self.preview_display.setText(f"Failed to load {version}:\n{str(e)}")
        else:
            self.preview_display.setText("Bible version not found.")
            self.scripture_table.setRowCount(0)

    def populate_scripture_table(self):
        self.scripture_table.setRowCount(0)
        row = 0
        for book, chapters in self.current_bible_data.items():
            for ch, verses in chapters.items():
                for vs, text in verses.items():
                    self.scripture_table.insertRow(row)
                    for col, data in enumerate([book, ch, vs, text]):
                        item = QTableWidgetItem(data)
                        item.setFont(QFont("Arial", 18))
                        self.scripture_table.setItem(row, col, item)
                    row += 1