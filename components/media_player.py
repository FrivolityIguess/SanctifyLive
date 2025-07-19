import os
import logging
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog, QMenu, QAction, QSizePolicy
)
from PyQt5.QtMultimediaWidgets import QVideoWidget
import json
from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QImage

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

class MediaPlayer(QWidget):
    def __init__(self, parent=None, settings_manager=None, main_window=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.current_media = None
        self.is_image = False
        self.loop_enabled = False

        # Enable drag-and-drop
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Content area (video or image)
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 6px;
            }
        """)
        self.media_player.setVideoOutput(self.video_widget)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        self.layout.addWidget(self.video_widget)
        self.video_widget.hide()  # Hidden until video is loaded
        self.image_label.hide()   # Hidden until image is loaded

        # Control panel
        control_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.setToolTip("Play or pause the media")
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Stop the media")
        self.stop_button.clicked.connect(self.stop)
        self.load_button = QPushButton("Load Media")
        self.load_button.setToolTip("Load a media file")
        self.load_button.clicked.connect(self.load_media)
        self.loop_button = QPushButton("Loop")
        self.loop_button.setToolTip("Toggle looping")
        self.loop_button.clicked.connect(self.toggle_loop)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setToolTip("Adjust volume")
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setToolTip("Seek through media")
        self.seek_slider.sliderMoved.connect(self.set_position)

        for btn in [self.play_button, self.stop_button, self.load_button, self.loop_button]:
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
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #34495e;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #34495e;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.loop_button)
        control_layout.addWidget(QLabel("Volume:"))
        control_layout.addWidget(self.volume_slider)
        control_layout.addWidget(QLabel("Seek:"))
        control_layout.addWidget(self.seek_slider)
        control_layout.addStretch()
        self.layout.addLayout(control_layout)

        # Media player signals
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.stateChanged.connect(self.update_buttons)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)

        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Apply initial settings
        self.apply_settings()

    def apply_settings(self):
        """Apply settings from settings_manager."""
        if not self.settings_manager:
            return
        self.loop_enabled = self.settings_manager.get_setting("behavior", "loop_media", False)
        self.loop_button.setText("Loop On" if self.loop_enabled else "Loop Off")
        playback_speed = self.settings_manager.get_setting("behavior", "default_playback_speed", 1.0)
        self.media_player.setPlaybackRate(playback_speed)
        logger.debug(f"Applied settings: loop={self.loop_enabled}, playback_speed={playback_speed}")

    def setMedia(self, file_path: str):
        """Set media file to play."""
        if not os.path.exists(file_path):
            self.main_window.status_bar.showMessage(f"Media file not found: {file_path}")
            logger.error(f"Media file not found: {file_path}")
            return

        self.current_media = file_path
        self.is_image = file_path.lower().endswith((".jpg", ".png", ".bmp"))
        
        if self.is_image:
            self.video_widget.hide()
            self.image_label.show()
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                # Apply theme for image background
                theme = self.main_window.themes_tab.theme_model.get_theme_by_id(
                    self.main_window.themes_tab.theme_list.currentItem().data(Qt.UserRole)
                ) if self.main_window.themes_tab.theme_list.currentItem() else {
                    "background_color": "#2c3e50"
                }
                self.image_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {theme.get("background_color", "#2c3e50")};
                        border: 2px solid #34495e;
                        border-radius: 6px;
                        padding: 10px;
                    }}
                """)
            else:
                self.image_label.setText("Invalid image")
                logger.error(f"Invalid image: {file_path}")
        else:
            self.image_label.hide()
            self.video_widget.show()
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        
        logger.info(f"Set media: {file_path}, type={'image' if self.is_image else 'video'}")

    def play(self):
        """Play the media."""
        if self.is_image:
            self.image_label.show()
            self.main_window.status_bar.showMessage(f"Displaying image: {os.path.basename(self.current_media)}")
        else:
            self.media_player.play()
            self.main_window.status_bar.showMessage(f"Playing video: {os.path.basename(self.current_media)}")
        logger.info(f"Playing media: {self.current_media}")

    def toggle_play_pause(self):
        """Toggle play/pause state."""
        if self.is_image:
            return
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.main_window.status_bar.showMessage("Media paused")
            logger.info("Media paused")
        else:
            self.media_player.play()
            self.main_window.status_bar.showMessage(f"Playing: {os.path.basename(self.current_media)}")
            logger.info(f"Media playing: {self.current_media}")

    def stop(self):
        """Stop the media."""
        self.media_player.stop()
        if self.is_image:
            self.image_label.hide()
            self.video_widget.show()
        self.main_window.status_bar.showMessage("Media stopped")
        logger.info("Media stopped")

    def load_media(self):
        """Load media file via dialog."""
        media_folder = self.settings_manager.get_setting("paths", "media_folder") if self.settings_manager else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", media_folder,
            "Media Files (*.mp4 *.avi *.mov *.jpg *.png *.bmp)"
        )
        if file_path:
            self.setMedia(file_path)
            self.play()
            self.main_window.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")

    def toggle_loop(self):
        """Toggle looping state."""
        self.loop_enabled = not self.loop_enabled
        self.loop_button.setText("Loop On" if self.loop_enabled else "Loop Off")
        self.media_player.setNotifyInterval(1000 if self.loop_enabled else 0)
        if self.settings_manager:
            self.settings_manager.set_setting("behavior", "loop_media", self.loop_enabled)
        self.main_window.status_bar.showMessage(f"Loop {'enabled' if self.loop_enabled else 'disabled'}")
        logger.info(f"Loop {'enabled' if self.loop_enabled else 'disabled'}")

    def set_volume(self, value: int):
        """Set media volume."""
        self.media_player.setVolume(value)
        self.main_window.status_bar.showMessage(f"Volume: {value}%")
        logger.info(f"Set volume: {value}%")

    def set_position(self, position: int):
        """Set media position."""
        self.media_player.setPosition(position)
        logger.debug(f"Set position: {position}ms")

    def update_position(self, position: int):
        """Update seek slider position."""
        self.seek_slider.setValue(position)
        logger.debug(f"Position updated: {position}ms")

    def update_duration(self, duration: int):
        """Update seek slider range."""
        self.seek_slider.setRange(0, duration)
        logger.debug(f"Duration set: {duration}ms")

    def handle_media_status(self, status: QMediaPlayer.MediaStatus):
        """Handle media status changes."""
        if status == QMediaPlayer.EndOfMedia and self.loop_enabled and not self.is_image:
            self.media_player.setPosition(0)
            self.media_player.play()
            logger.info("Media looped")
        elif status == QMediaPlayer.InvalidMedia:
            self.main_window.status_bar.showMessage("Invalid media file")
            logger.error("Invalid media file loaded")
        elif status == QMediaPlayer.LoadedMedia:
            self.main_window.status_bar.showMessage(f"Loaded: {os.path.basename(self.current_media)}")
            logger.info(f"Media loaded: {self.current_media}")

    def update_buttons(self, state: QMediaPlayer.State):
        """Update play/pause button text."""
        if self.is_image:
            self.play_button.setEnabled(False)
        else:
            self.play_button.setText("Pause" if state == QMediaPlayer.PlayingState else "Play")
            self.play_button.setEnabled(True)

    def show_context_menu(self, pos):
        """Show context menu for media player."""
        menu = QMenu()
        actions = [
            ("Play/Pause", self.toggle_play_pause, not self.is_image),
            ("Stop", self.stop, True),
            ("Load Media", self.load_media, True),
            ("Toggle Loop", self.toggle_loop, True)
        ]
        for label, callback, enabled in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            action.setEnabled(enabled)
            menu.addAction(action)
        menu.exec_(self.mapToGlobal(pos))

    def dragEnterEvent(self, event):
        """Handle drag enter for media drop."""
        if event.mimeData().hasFormat("application/x-sanctify-item") or event.mimeData().hasUrls():
            event.acceptProposedAction()
            logger.debug("Drag entered with media item")

    def dropEvent(self, event):
        """Handle drop of media from tabs or file system."""
        if event.mimeData().hasFormat("application/x-sanctify-item"):
            data = json.loads(event.mimeData().data("application/x-sanctify-item").data().decode())
            if data["type"] == "media":
                file_path = self.main_window.media_tab.media_model.get_media_by_id(data["id"]).get("file_path", "")
                if file_path:
                    self.setMedia(file_path)
                    self.play()
                    self.main_window.status_bar.showMessage(f"Dropped media: {os.path.basename(file_path)}")
                    logger.info(f"Dropped media: {file_path}")
            event.accept()
        elif event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            if url.lower().endswith((".mp4", ".avi", ".mov", ".jpg", ".png", ".bmp")):
                self.setMedia(url)
                self.play()
                self.main_window.status_bar.showMessage(f"Dropped file: {os.path.basename(url)}")
                logger.info(f"Dropped file: {url}")
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