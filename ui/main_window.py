import os
import json
import logging
import traceback
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QSplitter, QFrame, QLabel, QStatusBar, QMenuBar, QAction, QMenu,
    QMessageBox, QDesktopWidget, QDockWidget, QToolBar, QFileDialog, QListWidget
)
from PyQt5.QtCore import Qt, QTimer, QSettings, QPropertyAnimation
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPalette, QColor
from PyQt5.QtWidgets import QApplication
from core.settings_manager import SettingsManager
from ui.songs_ui import SongsTab
from ui.scriptures_ui import ScripturesTab
from ui.media_ui import MediaTab
from ui.presentation_ui import PresentationTab
from ui.themes_ui import ThemesTab
from ui.settings_dialog import SettingsDialog
from components.live_output import LiveOutput
from components.media_player import MediaPlayer
from components.preview_canvas import PreviewCanvas


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

class SanctifyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()  # Initialize SettingsManager
        self.setWindowTitle("Sanctify Live")
        self.setMinimumSize(1280, 720)
        self.setObjectName("SanctifyMainWindow")  # For accessibility

        # Initialize UI components
        try:
            self.setup_ui()
        except Exception as e:
            logger.error("Failed to setup UI: %s", traceback.format_exc())
            QMessageBox.critical(self, "Setup Error", f"Failed to initialize UI:\n{e}")
            raise

        # Validate assets
        try:
            self.validate_assets()
        except Exception as e:
            logger.error("Asset validation failed: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Asset validation failed: {str(e)}")

        # Load window state
        try:
            self.load_window_state()
        except Exception as e:
            logger.error("Failed to load window state: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Failed to load window state: {str(e)}")

        # Connect settings changes
        try:
            self.settings_manager.settings_changed.connect(self.on_settings_changed)
        except Exception as e:
            logger.error("Failed to connect settings_changed signal: %s", traceback.format_exc())

        # Auto-preview on tab item selection
        try:
            self.songs_tab.song_list.currentItemChanged.connect(self.auto_preview)
            self.media_tab.media_list.currentItemChanged.connect(self.auto_preview)
            self.presentation_tab.presentation_list.currentItemChanged.connect(self.auto_preview)
            self.themes_tab.theme_list.currentItemChanged.connect(self.auto_preview)
        except Exception as e:
            logger.error("Failed to connect item changed signals: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Signal connection failed: {str(e)}")

        # Set startup tab
        try:
            startup_screen = self.settings_manager.get_setting("general", "startup_screen", "Songs")
            tab_index = {"Songs": 0, "Scriptures": 1, "Media": 2, "Presentations": 3, "Themes": 4}.get(startup_screen, 0)
            self.tabs.setCurrentIndex(tab_index)
            self.status_bar.showMessage(f"Started on {startup_screen} tab")
            logger.info(f"Initialized SanctifyApp on {startup_screen} tab")
        except Exception as e:
            logger.error("Failed to set startup tab: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Startup tab setup failed: {str(e)}")

    def setup_ui(self):
        """Setup the main UI components."""
        # Enable accessibility
        QApplication.instance().setAttribute(Qt.AA_EnableHighDpiScaling)
        self.setAccessibleName("Sanctify Live")

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        self.toolbar = self.create_toolbar()
        main_layout.addWidget(self.toolbar)

        # Main splitter (vertical: top controls + tabs/content)
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; height: 4px; }")
        main_layout.addWidget(self.main_splitter)

        # Top Control Panel
        self.top_panel = self.create_top_control_panel()
        self.main_splitter.addWidget(self.top_panel)

        # Content Splitter (interaction panel + content tabs)
        content_splitter = QSplitter(Qt.Vertical)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; height: 4px; }")

        # Interaction Panel (Schedule, Preview, Live Output)
        self.interaction_panel = self.create_interaction_panel()
        content_splitter.addWidget(self.interaction_panel)

        # Content Tabs
        self.tabs = self.create_content_tabs()
        content_splitter.addWidget(self.tabs)
        content_splitter.setSizes([400, 600])

        self.main_splitter.addWidget(content_splitter)
        self.main_splitter.setSizes([150, 850])

        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                font-size: 14px;
                color: #2c3e50;
                background: #dfe6e9;
                padding: 5px;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Menu Bar
        self.create_menu_bar()

        # Apply theme
        self.apply_theme()

        # Keyboard Shortcuts
        self.setup_shortcuts()

    def validate_assets(self):
        """Validate required assets."""
        assets = [
            "assets/icons/settings.png",
            "assets/icons/browse.png",
            "assets/icons/alert.png",
            "assets/icons/logo.png",
            "assets/icons/black.png",
            "assets/icons/white.png",
            "assets/icons/live.png"
        ]
        for asset in assets:
            if not os.path.exists(asset):
                logger.warning(f"Missing asset: {asset}")
                self.status_bar.showMessage(f"Missing asset: {asset}")
        logger.debug("Asset validation completed")

    def apply_theme(self):
        """Apply theme based on settings."""
        try:
            theme = self.settings_manager.get_setting("appearance", "theme", "Light")
            font = QFont()
            font.fromString(self.settings_manager.get_setting("appearance", "ui_font", "Arial,14"))
            stylesheet = """
                QMainWindow, QWidget {
                    background: #ecf0f1;
                    color: #2c3e50;
                    font-family: %s;
                    font-size: %dpt;
                }
                QTabWidget::pane {
                    border: 2px solid #bdc3c7;
                    border-radius: 6px;
                    background: #fff;
                }
                QTabBar::tab {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 12px 24px;
                    color: #2c3e50;
                    background: #dfe6e9;
                    border: 2px solid #bdc3c7;
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
                QTabBar::tab:selected {
                    background: #3498db;
                    color: #fff;
                }
                QTabBar::tab:hover {
                    background: #2980b9;
                    color: #fff;
                }
                QPushButton {
                    padding: 10px 15px;
                    font-size: 16px;
                    border: 2px solid #3498db;
                    border-radius: 6px;
                    background: #3498db;
                    color: #fff;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
                QToolBar {
                    background: #2c3e50;
                    padding: 5px;
                }
                QToolBar::separator {
                    background: #34495e;
                    width: 2px;
                }
            """ % (font.family(), font.pointSize())
            if theme == "Dark":
                stylesheet = stylesheet.replace("#ecf0f1", "#2c3e50").replace("#2c3e50", "#ecf0f1").replace("#dfe6e9", "#34495e")
            QApplication.instance().setStyleSheet(stylesheet)
            QApplication.instance().setFont(font)
            self.preview_canvas.apply_theme()
            self.live_output.apply_theme()
            logger.info(f"Applied {theme} theme with font {font.family()}")
        except Exception as e:
            logger.error("Failed to apply theme: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Theme application failed: {str(e)}")

    def create_toolbar(self):
        """Create a toolbar for quick actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background: #2c3e50;
                padding: 5px;
            }
            QToolBar::separator {
                background: #34495e;
                width: 2px;
            }
        """)
        actions = [
            ("Settings", "assets/icons/settings.png", self.open_settings, "Open settings"),
            ("Browse", "assets/icons/browse.png", self.open_browse, "Browse content"),
            ("Go Live", "assets/icons/live.png", self.go_live, "Go live with selected content"),
            ("Full Screen", None, self.toggle_full_screen, "Toggle full-screen live output")
        ]
        for label, icon, callback, tooltip in actions:
            action = QAction(QIcon(icon), label, self) if icon else QAction(label, self)
            action.triggered.connect(callback)
            action.setToolTip(tooltip)
            toolbar.addAction(action)
        toolbar.addSeparator()
        self.live_indicator = QLabel("●")
        self.live_indicator.setStyleSheet("color: red; font-size: 16px; padding: 5px;")
        toolbar.addWidget(self.live_indicator)
        return toolbar

    def create_top_control_panel(self):
        """Create a modern top control panel with actionable buttons."""
        top_panel = QFrame()
        top_panel.setStyleSheet("background: #2c3e50; padding: 10px; border-bottom: 2px solid #34495e;")
        layout = QHBoxLayout(top_panel)
        layout.setContentsMargins(10, 5, 10, 5)

        # Left Buttons
        left_buttons = QHBoxLayout()
        button_configs = [
            ("Settings", "assets/icons/settings.png", self.open_settings, "Open application settings"),
            ("Browse", "assets/icons/browse.png", self.open_browse, "Browse content"),
            ("Alert", "assets/icons/alert.png", self.show_alert, "Show emergency alert")
        ]
        for label, icon, callback, tooltip in button_configs:
            btn = QPushButton(label)
            btn.setIcon(QIcon(icon))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 15px;
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
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            left_buttons.addWidget(btn)
        layout.addLayout(left_buttons)

        layout.addStretch()

        # Right Buttons
        right_buttons = QHBoxLayout()
        right_configs = [
            ("Logo", "assets/icons/logo.png", self.toggle_logo, "Toggle logo display"),
            ("Black", "assets/icons/black.png", self.toggle_black, "Toggle black screen"),
            ("White", "assets/icons/white.png", self.toggle_white, "Toggle white screen"),
            ("Go Live", "assets/icons/live.png", self.go_live, "Go live with selected content")
        ]
        for label, icon, callback, tooltip in right_configs:
            btn = QPushButton(label)
            btn.setIcon(QIcon(icon))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 15px;
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
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            right_buttons.addWidget(btn)
        layout.addLayout(right_buttons)

        return top_panel

    def create_interaction_panel(self):
        """Create interaction panel with schedule, preview, and live output."""
        interaction_panel = QFrame()
        interaction_panel.setStyleSheet("background: #ecf0f1; padding: 15px;")
        layout = QHBoxLayout(interaction_panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Horizontal Splitter
        self.interaction_splitter = QSplitter(Qt.Horizontal)
        self.interaction_splitter.setChildrenCollapsible(False)
        self.interaction_splitter.setStyleSheet("QSplitter::handle { background: #2c3e50; width: 4px; }")

        # Schedule (Left)
        self.schedule_frame = QFrame(objectName="ScheduleFrame")
        schedule_layout = QVBoxLayout(self.schedule_frame)
        schedule_layout.addWidget(QLabel("Schedule"))
        self.schedule_list = QListWidget()
        self.schedule_list.setStyleSheet("""
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
        self.schedule_list.setToolTip("Drag items from tabs to schedule")
        self.schedule_list.setAcceptDrops(True)
        self.schedule_list.setDragEnabled(True)
        self.schedule_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schedule_list.customContextMenuRequested.connect(self.open_schedule_context_menu)
        self.schedule_list.itemDoubleClicked.connect(self.schedule_item_activated)
        schedule_layout.addWidget(self.schedule_list)
        self.interaction_splitter.addWidget(self.schedule_frame)

        # Preview (Center)
        self.preview_canvas = PreviewCanvas(parent=self, settings_manager=self.settings_manager, main_window=self)
        self.preview_canvas.setStyleSheet("""
            background: #2c3e50;
            border: 2px solid #34495e;
            border-radius: 6px;
            padding: 10px;
        """)
        self.preview_canvas.setToolTip("Preview selected content")
        self.interaction_splitter.addWidget(self.preview_canvas)

        # Live Output (Right, as dockable widget)
        self.live_output_dock = QDockWidget("Live Output", self)
        self.live_output = LiveOutput(parent=self, settings_manager=self.settings_manager, main_window=self)
        self.live_output.setStyleSheet("""
            background: #2c3e50;
            border: 2px solid #34495e;
            border-radius: 6px;
            padding: 10px;
        """)
        self.live_output.setToolTip("Live output display")
        self.live_output_dock.setWidget(self.live_output)
        self.live_output_dock.setFloating(False)
        self.interaction_splitter.addWidget(self.live_output_dock)

        # Set splitter sizes
        desktop = QDesktopWidget()
        screen_count = desktop.screenCount()
        total_width = sum(desktop.screen(i).width() for i in range(screen_count))
        panel_width = total_width // 3
        self.interaction_splitter.setSizes([panel_width, panel_width, panel_width])
        layout.addWidget(self.interaction_splitter)
        return interaction_panel

    def create_content_tabs(self):
        """Create content tabs with modern styling."""
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: #fff;
            }
            QTabBar::tab {
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                color: #2c3e50;
                background: #dfe6e9;
                border: 2px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: #fff;
            }
            QTabBar::tab:hover {
                background: #2980b9;
                color: #fff;
            }
        """)
        self.songs_tab = SongsTab()
        self.scriptures_tab = ScripturesTab()
        self.media_tab = MediaTab()
        self.presentation_tab = PresentationTab()
        self.themes_tab = ThemesTab()
        tabs.addTab(self.songs_tab, "Songs")
        tabs.addTab(self.scriptures_tab, "Scriptures")
        tabs.addTab(self.media_tab, "Media")
        tabs.addTab(self.presentation_tab, "Presentations")
        tabs.addTab(self.themes_tab, "Themes")
        tabs.currentChanged.connect(self.on_tab_changed)
        return tabs

    def create_menu_bar(self):
        """Create a menu bar with advanced actions."""
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background: #2c3e50;
                color: #ecf0f1;
                font-size: 14px;
            }
            QMenuBar::item:selected {
                background: #3498db;
            }
            QMenu {
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                font-size: 14px;
            }
            QMenu::item:selected {
                background: #3498db;
            }
        """)

        # File Menu
        file_menu = menu_bar.addMenu("File")
        actions = [
            ("Open Settings", "Ctrl+T", self.open_settings),
            ("Export Schedule", "Ctrl+E", self.export_schedule),
            ("Import Schedule", "Ctrl+I", self.import_schedule),
            ("Save State", "Ctrl+S", self.save_window_state),
            ("Exit", "Ctrl+Q", self.close)
        ]
        for label, shortcut, callback in actions:
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            file_menu.addAction(action)

        # View Menu
        view_menu = menu_bar.addMenu("View")
        view_actions = [
            ("Toggle Schedule", "Ctrl+Shift+S", self.toggle_schedule_visibility),
            ("Toggle Full Screen", "F11", self.toggle_full_screen),
            ("Reset Layout", "Ctrl+R", self.reset_layout),
            ("Move Live Output to Second Screen", "Ctrl+M", self.move_live_output_to_second_screen)
        ]
        for label, shortcut, callback in view_actions:
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            view_menu.addAction(action)

        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Show Tips", self)
        help_action.setShortcut("Ctrl+H")
        help_action.triggered.connect(self.show_tips)
        help_menu.addAction(help_action)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for quick actions."""
        shortcuts = [
            (self.open_settings, "Ctrl+T"),
            (self.open_browse, "Ctrl+B"),
            (self.show_alert, "Ctrl+A"),
            (self.toggle_logo, "Ctrl+L"),
            (self.toggle_black, "Ctrl+K"),
            (self.toggle_white, "Ctrl+W"),
            (self.go_live, "Ctrl+G"),
            (self.toggle_full_screen, "F11"),
            (self.move_live_output_to_second_screen, "Ctrl+M")
        ]
        for callback, shortcut in shortcuts:
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def open_settings(self):
        """Open the settings dialog."""
        try:
            dialog = SettingsDialog(self.settings_manager, self)
            if dialog.exec_():
                self.apply_theme()
                self.status_bar.showMessage("Settings updated")
                logger.info("Settings dialog closed with changes")
            else:
                self.status_bar.showMessage("Settings dialog closed without changes")
                logger.info("Settings dialog closed without changes")
        except Exception as e:
            logger.error("Failed to open settings dialog: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Settings dialog error: {str(e)}")

    def open_browse(self):
        """Browse content from current tab."""
        try:
            current_tab = self.tabs.currentWidget()
            if hasattr(current_tab, "search_input"):
                current_tab.search_input.setFocus()
                self.status_bar.showMessage("Search bar focused")
                logger.info(f"Focused search in {current_tab.__class__.__name__}")
            else:
                self.status_bar.showMessage("Browse not supported in this tab")
                logger.warning(f"Browse not supported in {current_tab.__class__.__name__}")
        except Exception as e:
            logger.error("Failed to open browse: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Browse error: {str(e)}")

    def show_alert(self):
        """Display an emergency alert on live output."""
        try:
            alert_text = "Emergency Alert: Please stand by."
            theme = {
                "font_color": "#ffffff",
                "background_color": "#e74c3c",
                "font_size": "24",
                "font_family": "Arial",
                "alignment": "center"
            }
            self.live_output.setText(alert_text, theme)
            self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
            self.status_bar.showMessage("Emergency alert displayed")
            logger.info("Displayed emergency alert")
        except Exception as e:
            logger.error("Failed to show alert: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Alert error: {str(e)}")

    def toggle_logo(self):
        """Toggle logo display on live output."""
        try:
            logo_path = "assets/logo.png"
            if os.path.exists(logo_path):
                self.live_output.setMedia(logo_path)
                self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
                self.status_bar.showMessage("Logo displayed")
                logger.info("Displayed logo")
            else:
                self.status_bar.showMessage("Logo file not found")
                logger.error(f"Logo file not found: {logo_path}")
        except Exception as e:
            logger.error("Failed to toggle logo: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Logo toggle error: {str(e)}")

    def toggle_black(self):
        """Toggle black screen on live output."""
        try:
            self.live_output.setText("", {"background_color": "#000000", "font_size": "18", "font_family": "Arial", "alignment": "center"})
            self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
            self.status_bar.showMessage("Black screen displayed")
            logger.info("Toggled black screen")
        except Exception as e:
            logger.error("Failed to toggle black screen: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Black screen error: {str(e)}")

    def toggle_white(self):
        """Toggle white screen on live output."""
        try:
            self.live_output.setText("", {"background_color": "#ffffff", "font_size": "18", "font_family": "Arial", "alignment": "center"})
            self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
            self.status_bar.showMessage("White screen displayed")
            logger.info("Toggled white screen")
        except Exception as e:
            logger.error("Failed to toggle white screen: %s", traceback.format_exc())
            self.status_bar.showMessage(f"White screen error: {str(e)}")

    def go_live(self):
        """Send selected content to live output with theme."""
        try:
            current_tab = self.tabs.currentWidget()
            theme_item = self.themes_tab.theme_list.currentItem()
            theme_data = theme_item.data(Qt.UserRole) if theme_item else {
                "font_color": "#ecf0f1", "background_color": "#2c3e50",
                "font_size": "18", "font_family": "Arial", "alignment": "center"
            }
            content = None
            content_type = "text"
            content_id = None
            content_title = None

            if isinstance(current_tab, SongsTab):
                item = current_tab.song_list.currentItem()
                if item:
                    title = item.text()
                    song = next((s for s in current_tab.filtered_songs if s["title"] == title), None)
                    if song:
                        content = "\n\n".join(f"{section_type}:\n{text}" for section_type, text in song.get("sections", []))
                        content_id = title  # Using title as ID since no explicit ID in SongsTab
                        content_title = song.get("title")
                    else:
                        logger.warning("Song not found in filtered_songs: %s", title)
                        self.status_bar.showMessage("Song not found")
                        return
            elif isinstance(current_tab, ScripturesTab):
                content = "Scripture content (implementation pending)"
                content_id = "scripture_temp"
                content_title = "Scripture"
            elif isinstance(current_tab, MediaTab):
                item = current_tab.media_list.currentItem()
                if item:
                    content = item.data(Qt.UserRole).get("file_path", "")
                    content_id = item.data(Qt.UserRole).get("id")
                    content_title = item.data(Qt.UserRole).get("title", "Media")
                    content_type = "video" if content.lower().endswith((".mp4", ".avi", ".mov")) else "image"
            elif isinstance(current_tab, PresentationTab):
                item = current_tab.presentation_list.currentItem()
                if item:
                    content = item.data(Qt.UserRole).get("slides", ["No slides available"])[0]
                    content_id = item.data(Qt.UserRole).get("id")
                    content_title = item.data(Qt.UserRole).get("title", "Presentation")

            if content and content_type == "text":
                style = {
                    "font_color": theme_data["font_color"],
                    "background_color": theme_data["background_color"],
                    "font_size": theme_data["font_size"],
                    "font_family": theme_data["font_family"],
                    "alignment": theme_data["alignment"].lower()
                }
                self.live_output.setText(content, style)
                self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
                self.status_bar.showMessage(f"Live: {content_title or current_tab.__class__.__name__}")
                logger.info(f"Sent {current_tab.__class__.__name__} to live output: id={content_id}")
            elif content and content_type in ["image", "video"]:
                self.live_output.setMedia(content)
                self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
                self.status_bar.showMessage(f"Live: {content_title or 'Media'}")
                logger.info(f"Sent media to live output: id={content_id}, path={content}")
            else:
                self.status_bar.showMessage("No content or theme selected")
                logger.warning("Go Live failed: No content or theme selected")
        except Exception as e:
            logger.error("Failed to go live: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Go Live error: {str(e)}")

    def auto_preview(self):
        """Automatically preview selected content."""
        try:
            current_tab = self.tabs.currentWidget()
            theme_item = self.themes_tab.theme_list.currentItem()
            theme_data = theme_item.data(Qt.UserRole) if theme_item else {
                "font_color": "#ecf0f1", "background_color": "#2c3e50",
                "font_size": "18", "font_family": "Arial", "alignment": "center"
            }
            content = None
            content_type = "text"

            if isinstance(current_tab, SongsTab):
                item = current_tab.song_list.currentItem()
                if item:
                    title = item.text()
                    song = next((s for s in current_tab.filtered_songs if s["title"] == title), None)
                    if song:
                        content = "\n\n".join(f"{section_type}:\n{text}" for section_type, text in song.get("sections", []))
                    else:
                        logger.warning("Song not found in filtered_songs: %s", title)
                        self.status_bar.showMessage("Song not found")
                        return
            elif isinstance(current_tab, ScripturesTab):
                content = "Scripture content (implementation pending)"
            elif isinstance(current_tab, MediaTab):
                item = current_tab.media_list.currentItem()
                if item:
                    content = item.data(Qt.UserRole).get("file_path", "")
                    content_type = "video" if content.lower().endswith((".mp4", ".avi", ".mov")) else "image"
            elif isinstance(current_tab, PresentationTab):
                item = current_tab.presentation_list.currentItem()
                if item:
                    content = item.data(Qt.UserRole).get("slides", ["No slides available"])[0]

            if content:
                self.preview_canvas.set_content(content, theme_data, content_type)
                self.status_bar.showMessage(f"Previewed {current_tab.__class__.__name__}")
                logger.info(f"Auto-previewed {current_tab.__class__.__name__}")
            else:
                self.preview_canvas.set_content("No content selected", theme_data, "text")
                self.status_bar.showMessage("No content selected")
                logger.debug("No content for auto-preview")
        except Exception as e:
            logger.error("Failed to auto-preview: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Auto-preview error: {str(e)}")

    def toggle_schedule_visibility(self):
        """Toggle visibility of the schedule panel."""
        try:
            self.schedule_frame.setVisible(not self.schedule_frame.isVisible())
            self.status_bar.showMessage("Schedule " + ("shown" if self.schedule_frame.isVisible() else "hidden"))
            logger.info(f"Schedule visibility: {self.schedule_frame.isVisible()}")
        except Exception as e:
            logger.error("Failed to toggle schedule visibility: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Schedule toggle error: {str(e)}")

    def toggle_full_screen(self):
        """Toggle full-screen mode for live output."""
        try:
            self.live_output.toggle_fullscreen()
            self.status_bar.showMessage("Live output " + ("full-screen" if self.live_output.isFullScreen() else "normal"))
            logger.info(f"Live output full-screen: {self.live_output.isFullScreen()}")
        except Exception as e:
            logger.error("Failed to toggle full-screen: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Full-screen toggle error: {str(e)}")

    def move_live_output_to_second_screen(self):
        """Move live output to second screen if available."""
        try:
            desktop = QDesktopWidget()
            if desktop.screenCount() > 1:
                second_screen = desktop.screenGeometry(1)
                self.live_output_dock.setFloating(True)
                self.live_output_dock.move(second_screen.left(), second_screen.top())
                self.live_output_dock.showFullScreen()
                self.status_bar.showMessage("Live output moved to second screen")
                logger.info("Live output moved to second screen")
            else:
                self.status_bar.showMessage("No second screen detected")
                logger.warning("No second screen available")
        except Exception as e:
            logger.error("Failed to move live output to second screen: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Second screen error: {str(e)}")

    def reset_layout(self):
        """Reset splitter sizes to default."""
        try:
            desktop = QDesktopWidget()
            screen_count = desktop.screenCount()
            total_width = sum(desktop.screen(i).width() for i in range(screen_count))
            panel_width = total_width // 3
            self.interaction_splitter.setSizes([panel_width, panel_width, panel_width])
            self.main_splitter.setSizes([150, 850])
            self.status_bar.showMessage("Layout reset")
            logger.info("Reset layout to default")
        except Exception as e:
            logger.error("Failed to reset layout: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Layout reset error: {str(e)}")

    def show_tips(self):
        """Show tips/help dialog."""
        try:
            if self.settings_manager.get_setting("general", "enable_tips", True):
                QMessageBox.information(
                    self,
                    "Tips",
                    "Welcome to Sanctify Live!\n"
                    "- Ctrl+T: Open Settings\n"
                    "- Ctrl+G: Go Live\n"
                    "- F11: Toggle Full-Screen Live Output\n"
                    "- Ctrl+M: Move Live Output to Second Screen\n"
                    "- Drag items to Schedule or Live Output\n"
                    "- Double-click Schedule items to go live"
                )
                self.status_bar.showMessage("Tips displayed")
                logger.info("Displayed tips")
            else:
                self.status_bar.showMessage("Tips are disabled in settings")
                logger.info("Tips display skipped (disabled in settings)")
        except Exception as e:
            logger.error("Failed to show tips: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Tips display error: {str(e)}")

    def open_schedule_context_menu(self, pos):
        """Open context menu for schedule list."""
        try:
            item = self.schedule_list.itemAt(pos)
            menu = QMenu()
            actions = [
                ("Go Live", self.schedule_item_activated if item else None),
                ("Remove", self.remove_schedule_item if item else None),
                ("Clear Schedule", self.clear_schedule)
            ]
            for label, callback in actions:
                action = QAction(label, self)
                if callback:
                    action.triggered.connect(callback)
                    action.setEnabled(True)
                else:
                    action.setEnabled(False)
                menu.addAction(action)
            menu.exec_(self.schedule_list.mapToGlobal(pos))
        except Exception as e:
            logger.error("Failed to open schedule context menu: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Schedule context menu error: {str(e)}")

    def schedule_item_activated(self):
        """Send schedule item to live output."""
        try:
            item = self.schedule_list.currentItem()
            if not item:
                self.status_bar.showMessage("No schedule item selected")
                logger.warning("No schedule item selected")
                return
            try:
                data = json.loads(item.data(Qt.UserRole))
            except json.JSONDecodeError as e:
                logger.error("Invalid schedule item data: %s", traceback.format_exc())
                self.status_bar.showMessage("Invalid schedule item data")
                return
            content_type = data.get("type")
            content_id = data.get("id")
            if not content_type or not content_id:
                logger.error("Schedule item missing type or id: %s", data)
                self.status_bar.showMessage("Invalid schedule item")
                return
            theme_item = self.themes_tab.theme_list.currentItem()
            theme_data = theme_item.data(Qt.UserRole) if theme_item else {
                "font_color": "#ecf0f1", "background_color": "#2c3e50",
                "font_size": "18", "font_family": "Arial", "alignment": "center"
            }
            content = None
            content_title = None
            if content_type == "song":
                song = next((s for s in self.songs_tab.songs if s["title"] == content_id), None)
                if song:
                    content = "\n\n".join(f"{section_type}:\n{text}" for section_type, text in song.get("sections", []))
                    content_title = song.get("title", "Song")
                else:
                    logger.warning("Song not found for id: %s", content_id)
                    self.status_bar.showMessage("Song not found")
                    return
            elif content_type == "media":
                # Assuming MediaTab has similar structure; replace with actual logic if available
                logger.warning("MediaTab model not implemented; assuming item data")
                self.status_bar.showMessage("MediaTab model not implemented")
                return
            elif content_type == "presentation":
                # Assuming PresentationTab has similar structure; replace with actual logic if available
                logger.warning("PresentationTab model not implemented; assuming item data")
                self.status_bar.showMessage("PresentationTab model not implemented")
                return
            if content:
                if content_type == "text":
                    style = {
                        "font_color": theme_data["font_color"],
                        "background_color": theme_data["background_color"],
                        "font_size": theme_data["font_size"],
                        "font_family": theme_data["font_family"],
                        "alignment": theme_data["alignment"].lower()
                    }
                    self.live_output.setText(content, style)
                else:
                    self.live_output.setMedia(content)
                self.live_indicator.setStyleSheet("color: green; font-size: 16px; padding: 5px;")
                self.status_bar.showMessage(f"Live: {content_title}")
                logger.info(f"Schedule item sent to live output: type={content_type}, id={content_id}")
            else:
                self.status_bar.showMessage(f"No content found for {content_type}")
                logger.warning(f"No content found for type={content_type}, id={content_id}")
        except Exception as e:
            logger.error("Failed to activate schedule item: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Schedule item error: {str(e)}")

    def remove_schedule_item(self):
        """Remove selected item from schedule."""
        try:
            item = self.schedule_list.currentItem()
            if item and self.settings_manager.get_setting("behavior", "confirm_before_delete", True):
                confirm = QMessageBox.question(
                    self, "Confirm Remove",
                    f"Remove '{item.text()}' from schedule?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm != QMessageBox.Yes:
                    return
            if item:
                row = self.schedule_list.row(item)
                self.schedule_list.takeItem(row)
                self.status_bar.showMessage("Item removed from schedule")
                logger.info("Removed item from schedule")
        except Exception as e:
            logger.error("Failed to remove schedule item: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Remove schedule item error: {str(e)}")

    def clear_schedule(self):
        """Clear all items from schedule."""
        try:
            if self.settings_manager.get_setting("behavior", "confirm_before_delete", True):
                confirm = QMessageBox.question(
                    self, "Confirm Clear",
                    "Clear all items from the schedule?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm != QMessageBox.Yes:
                    return
            self.schedule_list.clear()
            self.status_bar.showMessage("Schedule cleared")
            logger.info("Cleared schedule")
        except Exception as e:
            logger.error("Failed to clear schedule: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Clear schedule error: {str(e)}")

    def export_schedule(self):
        """Export schedule to JSON."""
        try:
            items = []
            for i in range(self.schedule_list.count()):
                item = self.schedule_list.item(i)
                try:
                    items.append(json.loads(item.data(Qt.UserRole)))
                except json.JSONDecodeError as e:
                    logger.error("Invalid schedule item data at index %d: %s", i, traceback.format_exc())
                    continue
            file_path, _ = QFileDialog.getSaveFileName(self, "Export Schedule", "schedule.json", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=4)
                self.status_bar.showMessage(f"Schedule exported to {os.path.basename(file_path)}")
                logger.info(f"Exported schedule to {file_path}")
        except Exception as e:
            logger.error("Failed to export schedule: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Export schedule error: {str(e)}")

    def import_schedule(self):
        """Import schedule from JSON."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Import Schedule", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                self.schedule_list.clear()
                for item in items:
                    content_type = item.get("type")
                    content_id = item.get("id")
                    display_text = item.get("title", "Unknown")
                    list_item = QListWidgetItem(display_text)
                    list_item.setData(Qt.UserRole, json.dumps(item))
                    self.schedule_list.addItem(list_item)
                self.status_bar.showMessage(f"Schedule imported from {os.path.basename(file_path)}")
                logger.info(f"Imported schedule from {file_path}")
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in schedule file: %s", traceback.format_exc())
            self.status_bar.showMessage("Invalid schedule file format")
        except Exception as e:
            logger.error("Failed to import schedule: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Import schedule error: {str(e)}")

    def on_settings_changed(self, section: str, key: str, value: Any):
        """Handle settings changes."""
        try:
            if section == "appearance" and key in ["theme", "ui_font"]:
                self.apply_theme()
                self.status_bar.showMessage(f"Applied {key} change: {value}")
                logger.info(f"Applied settings change: {section}.{key} = {value}")
            elif section == "paths":
                self.status_bar.showMessage(f"Path updated: {key}")
                logger.info(f"Path updated: {key} = {value}")
        except Exception as e:
            logger.error("Failed to handle settings change: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Settings change error: {str(e)}")

    def on_tab_changed(self, index):
        """Handle tab changes with animation."""
        try:
            tab_name = self.tabs.tabText(index)
            self.status_bar.showMessage(f"Switched to {tab_name} tab")
            logger.info(f"Switched to {tab_name} tab")
            if self.settings_manager.get_setting("appearance", "enable_animations", True):
                anim = QPropertyAnimation(self.tabs, b"windowOpacity")
                anim.setDuration(300)
                anim.setStartValue(0.8)
                anim.setEndValue(1.0)
                anim.start()
            self.auto_preview()
        except Exception as e:
            logger.error("Failed to handle tab change: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Tab change error: {str(e)}")

    def load_window_state(self):
        """Load window state (size, splitter positions, tab)."""
        try:
            settings = QSettings("SanctifyLive", "MainWindow")
            self.restoreGeometry(settings.value("geometry", self.saveGeometry()))
            self.main_splitter.restoreState(settings.value("main_splitter", self.main_splitter.saveState()))
            self.interaction_splitter.restoreState(settings.value("interaction_splitter", self.interaction_splitter.saveState()))
            self.tabs.setCurrentIndex(int(settings.value("current_tab", 0)))
            schedule_items = settings.value("schedule", [])
            for item in schedule_items:
                try:
                    list_item = QListWidgetItem(item.get("title", "Unknown"))
                    list_item.setData(Qt.UserRole, json.dumps(item))
                    self.schedule_list.addItem(list_item)
                except Exception as e:
                    logger.error("Failed to load schedule item: %s", traceback.format_exc())
                    continue
            logger.info("Loaded window state")
        except Exception as e:
            logger.error("Failed to load window state: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Window state load error: {str(e)}")

    def save_window_state(self):
        """Save window state (size, splitter positions, tab, schedule)."""
        try:
            settings = QSettings("SanctifyLive", "MainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("main_splitter", self.main_splitter.saveState())
            settings.setValue("interaction_splitter", self.interaction_splitter.saveState())
            settings.setValue("current_tab", self.tabs.currentIndex())
            schedule_items = []
            for i in range(self.schedule_list.count()):
                item = self.schedule_list.item(i)
                try:
                    schedule_items.append(json.loads(item.data(Qt.UserRole)))
                except json.JSONDecodeError as e:
                    logger.error("Invalid schedule item data at index %d: %s", i, traceback.format_exc())
                    continue
            settings.setValue("schedule", schedule_items)
            logger.info("Saved window state")
        except Exception as e:
            logger.error("Failed to save window state: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Window state save error: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event."""
        try:
            self.save_window_state()
            event.accept()
        except Exception as e:
            logger.error("Failed to handle close event: %s", traceback.format_exc())
            self.status_bar.showMessage(f"Close event error: {str(e)}")
            event.accept()