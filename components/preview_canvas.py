import logging
import os
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QAction,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QMimeData
from PyQt5.QtGui import QFont, QPixmap
from components.media_player import MediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
import json

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

class PreviewCanvas(QWidget):
    def __init__(self, parent=None, settings_manager=None, main_window=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window
        self.current_content = None
        self.current_style = {}
        self.zoom_level = 1.0
        self.media_player = None

        # Enable drag-and-drop
        self.setAcceptDrops(True)

        # Setup layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Content area (label or media player)
        self.content_label = QLabel("Preview Canvas")
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
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Refresh the preview content")
        self.refresh_button.clicked.connect(self.refresh_preview)
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.setToolTip("Increase content size")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.setToolTip("Decrease content size")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setToolTip("Clear the preview")
        self.clear_button.clicked.connect(self.clear_preview)

        for btn in [self.refresh_button, self.zoom_in_button, self.zoom_out_button, self.clear_button]:
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
        logger.debug(f"Applied preview canvas theme: {theme}")

    def set_content(self, content: str, style: Dict[str, str], content_type: str = "text"):
        """Set preview content with style."""
        if self.media_player:
            self.layout.removeWidget(self.media_player)
            self.media_player.deleteLater()
            self.media_player = None
            self.layout.addWidget(self.content_label)

        self.current_content = content
        self.current_style = style
        self.current_type = content_type

        if content_type == "text":
            font = QFont(style.get("font_family", "Arial"))
            font.setPointSize(int(float(style.get("font_size", 18)) * self.zoom_level))
            self.content_label.setFont(font)
            self.content_label.setText(content)
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
        elif content_type in ["image", "video"]:
            self.layout.removeWidget(self.content_label)
            self.media_player = MediaPlayer()
            self.layout.addWidget(self.media_player)
            if os.path.exists(content):
                self.media_player.setMedia(content)
                self.media_player.play()
            else:
                self.content_label.setText("Media file not found")
                self.layout.addWidget(self.content_label)
                logger.error(f"Media file not found: {content}")
        
        # Animate content change
        if self.settings_manager.get_setting("appearance", "enable_animations"):
            anim = QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(500)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()

        logger.info(f"Preview set: type={content_type}, content={content[:50]}...")
        self.update()

    def refresh_preview(self):
        """Refresh preview based on current tab selection."""
        if not self.main_window:
            self.content_label.setText("No content selected")
            logger.debug("No main window for refresh")
            return

        current_tab = self.main_window.tabs.currentWidget()
        theme = self.main_window.themes_tab.theme_model.get_theme_by_id(
            self.main_window.themes_tab.theme_list.currentItem().data(Qt.UserRole)
        ) if self.main_window.themes_tab.theme_list.currentItem() else {
            "font_color": "#ecf0f1", "background_color": "#2c3e50",
            "font_size": "18", "font_family": "Arial", "alignment": "center"
        }

        content = None
        content_type = "text"
        if isinstance(current_tab, self.main_window.songs_tab.__class__):
            item = current_tab.song_list.currentItem()
            if item:
                content = item.data(Qt.UserRole).get("lyrics", "No lyrics available")
        elif isinstance(current_tab, self.main_window.scriptures_tab.__class__):
            content = "Scripture content (implementation pending)"
        elif isinstance(current_tab, self.main_window.media_tab.__class__):
            item = current_tab.media_list.currentItem()
            if item:
                content = item.data(Qt.UserRole).get("file_path", "")
                content_type = "video" if content.lower().endswith((".mp4", ".avi")) else "image"
        elif isinstance(current_tab, self.main_window.presentation_tab.__class__):
            item = current_tab.presentation_list.currentItem()
            if item:
                content = item.data(Qt.UserRole).get("slides", ["No slides available"])[0]

        if content:
            self.set_content(content, theme, content_type)
            self.main_window.status_bar.showMessage(f"Previewed {content_type} from {current_tab.__class__.__name__}")
        else:
            self.set_content("No content selected", theme, "text")
            self.main_window.status_bar.showMessage("No content selected")
        logger.info(f"Refreshed preview: type={content_type}")

    def zoom_in(self):
        """Increase zoom level."""
        self.zoom_level = min(self.zoom_level + 0.1, 2.0)
        self.refresh_preview()
        self.main_window.status_bar.showMessage(f"Zoom: {int(self.zoom_level * 100)}%")
        logger.info(f"Zoom in: level={self.zoom_level}")

    def zoom_out(self):
        """Decrease zoom level."""
        self.zoom_level = max(self.zoom_level - 0.1, 0.5)
        self.refresh_preview()
        self.main_window.status_bar.showMessage(f"Zoom: {int(self.zoom_level * 100)}%")
        logger.info(f"Zoom out: level={self.zoom_level}")

    def clear_preview(self):
        """Clear the preview content."""
        if self.media_player:
            self.layout.removeWidget(self.media_player)
            self.media_player.deleteLater()
            self.media_player = None
            self.layout.addWidget(self.content_label)
        self.content_label.setText("Preview Canvas")
        self.zoom_level = 1.0
        self.apply_theme()
        self.main_window.status_bar.showMessage("Preview cleared")
        logger.info("Preview cleared")

    def show_context_menu(self, pos):
        """Show context menu for preview canvas."""
        menu = QMenu()
        actions = [
            ("Refresh", self.refresh_preview),
            ("Clear", self.clear_preview),
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
                content_type = "video" if content.lower().endswith((".mp4", ".avi")) else "image"
            elif data["type"] == "presentation":
                content = self.main_window.presentation_tab.presentation_model.get_presentation_by_id(data["id"]).get("slides", ["No slides"])[0]
            if content:
                self.set_content(content, theme, content_type)
                self.main_window.status_bar.showMessage(f"Dropped {data['type']} to preview")
                logger.info(f"Dropped {data['type']} to preview: id={data['id']}")
            event.accept()
        else:
            event.ignore()

    def update(self):
        """Force update of widget."""
        super().update()
        if self.settings_manager.get_setting("appearance", "enable_animations"):
            anim = QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(300)
            anim.setStartValue(0.8)
            anim.setEndValue(1.0)
            anim.start()