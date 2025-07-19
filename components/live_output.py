import os
import logging
import json
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QAction,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QFont, QPixmap
from components.media_player import MediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget

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

class LiveOutput(QWidget):
    def __init__(self, parent=None, settings_manager=None, main_window=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window
        self.media_player = None
        self.current_content = None
        self.current_style = {}
        self.current_type = "text"
        self.zoom_level = 1.0

        # Enable drag-and-drop
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Content area
        self.content_label = QLabel("Live Output")
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setWordWrap(True)
        self.content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #ecf0f1;
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 20px;
            }
        """)
        self.layout.addWidget(self.content_label)

        # Control buttons
        control_layout = QHBoxLayout()
        self.fullscreen_button = QPushButton("Full Screen")
        self.fullscreen_button.setToolTip("Toggle full-screen mode")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setToolTip("Clear the live output")
        self.clear_button.clicked.connect(self.set_blank)
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.setToolTip("Increase content size")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.setToolTip("Decrease content size")
        self.zoom_out_button.clicked.connect(self.zoom_out)

        for btn in [self.fullscreen_button, self.clear_button, self.zoom_in_button, self.zoom_out_button]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    font-size: 14px;
                    border: 2px solid #3498db;
                    border-radius: 6px;
                    background: #3498db;
                    color: #fff;
                    transition: background 0.3s;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
            control_layout.addWidget(btn)
        control_layout.addStretch()
        self.layout.addLayout(control_layout)

        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Apply initial theme
        self.apply_theme()

        # Check full-screen on startup
        if self.settings_manager and self.settings_manager.get_setting("general", "fullscreen_on_startup", False):
            QTimer.singleShot(1000, self.toggle_fullscreen)

    def apply_theme(self):
        """Apply theme and font from settings."""
        if not self.settings_manager:
            return
        theme = self.settings_manager.get_setting("appearance", "theme")
        font = QFont()
        font.fromString(self.settings_manager.get_setting("appearance", "ui_font"))
        bg_color = "#2c3e50" if theme == "Light" else "#ecf0f1"
        text_color = "#ecf0f1" if theme == "Light" else "#2c3e50"
        self.content_label.setStyleSheet(f"""
            QLabel {{
                font-family: {font.family()};
                font-size: {int(font.pointSize() * self.zoom_level)}pt;
                color: {text_color};
                background-color: {bg_color};
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 20px;
            }}
        """)
        logger.debug(f"Applied live output theme: {theme}")

    def setText(self, text: str, style: Dict[str, str]):
        """Set text content with style."""
        if self.media_player:
            self.layout.removeWidget(self.media_player)
            self.media_player.deleteLater()
            self.media_player = None
            self.layout.addWidget(self.content_label)

        self.current_content = text
        self.current_style = style
        self.current_type = "text"

        font = QFont(style.get("font_family", "Arial"))
        font.setPointSize(int(float(style.get("font_size", 18)) * self.zoom_level))
        self.content_label.setFont(font)
        self.content_label.setText(text)
        alignment = {
            "left": Qt.AlignLeft,
            "center": Qt.AlignCenter,
            "right": Qt.AlignRight
        }.get(style.get("alignment", "center").lower(), Qt.AlignCenter)
        self.content_label.setAlignment(alignment)
        self.content_label.setStyleSheet(f"""
            QLabel {{
                font-family: {style.get("font_family", "Arial")};
                font-size: {int(float(style.get("font_size", 18)) * self.zoom_level)}pt;
                color: {style.get("font_color", "#ecf0f1")};
                background-color: {style.get("background_color", "#2c3e50")};
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 20px;
            }}
        """)

        # Animate content change
        if self.settings_manager and self.settings_manager.get_setting("appearance", "enable_animations"):
            anim = QPropertyAnimation(self.content_label, b"windowOpacity")
            anim.setDuration(500)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()

        self.main_window.status_bar.showMessage("Live text updated")
        logger.info(f"Live output set: text={text[:50]}...")

    def setMedia(self, file_path: str):
        """Set media content (image or video)."""
        if not os.path.exists(file_path):
            self.main_window.status_bar.showMessage(f"Media file not found: {file_path}")
            logger.error(f"Media file not found: {file_path}")
            return

        if self.media_player:
            self.layout.removeWidget(self.media_player)
            self.media_player.deleteLater()
        self.layout.removeWidget(self.content_label)
        self.media_player = MediaPlayer(parent=self, settings_manager=self.settings_manager, main_window=self.main_window)
        self.layout.addWidget(self.media_player)
        self.media_player.setMedia(file_path)
        self.media_player.play()

        self.current_content = file_path
        self.current_type = "video" if file_path.lower().endswith((".mp4", ".avi", ".mov")) else "image"
        self.main_window.status_bar.showMessage(f"Live media: {os.path.basename(file_path)}")
        logger.info(f"Live output set: media={file_path}, type={self.current_type}")

    def set_blank(self):
        """Clear the live output."""
        if self.media_player:
            self.layout.removeWidget(self.media_player)
            self.media_player.deleteLater()
            self.media_player = None
            self.layout.addWidget(self.content_label)
        self.content_label.setText("")
        self.zoom_level = 1.0
        self.apply_theme()
        self.main_window.status_bar.showMessage("Live output cleared")
        logger.info("Live output cleared")

    def toggle_fullscreen(self):
        """Toggle full-screen mode."""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("Full Screen")
            self.main_window.status_bar.showMessage("Exited full-screen mode")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("Exit Full Screen")
            self.main_window.status_bar.showMessage("Entered full-screen mode")
        logger.info(f"Live output full-screen: {self.isFullScreen()}")

    def zoom_in(self):
        """Increase zoom level."""
        self.zoom_level = min(self.zoom_level + 0.1, 2.0)
        if self.current_type == "text":
            self.setText(self.current_content, self.current_style)
        elif self.current_type in ["image", "video"] and self.media_player:
            self.media_player.setMedia(self.current_content)
        self.main_window.status_bar.showMessage(f"Zoom: {int(self.zoom_level * 100)}%")
        logger.info(f"Zoom in: level={self.zoom_level}")

    def zoom_out(self):
        """Decrease zoom level."""
        self.zoom_level = max(self.zoom_level - 0.1, 0.5)
        if self.current_type == "text":
            self.setText(self.current_content, self.current_style)
        elif self.current_type in ["image", "video"] and self.media_player:
            self.media_player.setMedia(self.current_content)
        self.main_window.status_bar.showMessage(f"Zoom: {int(self.zoom_level * 100)}%")
        logger.info(f"Zoom out: level={self.zoom_level}")

    def show_context_menu(self, pos):
        """Show context menu for live output."""
        menu = QMenu()
        actions = [
            ("Clear", self.set_blank),
            ("Toggle Full Screen", self.toggle_fullscreen),
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out)
        ]
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.exec_(self.mapToGlobal(pos))

    def dragEnterEvent(self, event):
        """Handle drag enter for content drop."""
        if event.mimeData().hasFormat("application/x-sanctify-item"):
            event.acceptProposedAction()
            logger.debug("Drag entered with sanctify item")

    def dropEvent(self, event):
        """Handle drop of content from tabs."""
        mime_data = event.mimeData()
        if mime_data.hasFormat("application/x-sanctify-item"):
            data = json.loads(mime_data.data("application/x-sanctify-item").data().decode())
            theme = self.main_window.themes_tab.theme_model.get_theme_by_id(
                self.main_window.themes_tab.theme_list.currentItem().data(Qt.UserRole)
            ) if self.main_window.themes_tab.theme_list.currentItem() else {
                "font_color": "#ecf0f1", "background_color": "#2c3e50",
                "font_size": "18", "font_family": "Arial", "alignment": "center"
            }
            content = None
            content_type = "text"
            if data["type"] == "song":
                content = self.main_window.songs_tab.song_model.get_song_by_id(data["id"]).get("lyrics", "No lyrics")
            elif data["type"] == "media":
                content = self.main_window.media_tab.media_model.get_media_by_id(data["id"]).get("file_path", "")
                content_type = "video" if content.lower().endswith((".mp4", ".avi", ".mov")) else "image"
            elif data["type"] == "presentation":
                content = self.main_window.presentation_tab.presentation_model.get_presentation_by_id(data["id"]).get("slides", ["No slides"])[0]
            if content:
                if content_type == "text":
                    self.setText(content, theme)
                else:
                    self.setMedia(content)
                self.main_window.status_bar.showMessage(f"Dropped {data['type']} to live output")
                logger.info(f"Dropped {data['type']} to live output: id={data['id']}")
            event.accept()
        else:
            event.ignore()

    def update(self):
        """Force update with animation."""
        super().update()
        if self.settings_manager and self.settings_manager.get_setting("appearance", "enable_animations"):
            anim = QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(300)
            anim.setStartValue(0.8)
            anim.setEndValue(1.0)
            anim.start()