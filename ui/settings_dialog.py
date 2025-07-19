import json
import os
import logging
from typing import Dict
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QCheckBox, QFontDialog, QFileDialog, QMessageBox, QSpinBox, QLabel,
    QCompleter, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QStringListModel
from PyQt5.QtCore import Qt
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

class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Settings")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background: #ecf0f1;
            }
            QTabWidget::pane {
                border: 2px solid #34495e;
                border-radius: 8px;
                background: #fff;
            }
            QTabBar::tab {
                background: #3498db;
                color: #fff;
                padding: 12px;
                font-size: 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #2980b9;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 12px;
                font-size: 18px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background: #fff;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
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
            QCheckBox, QLabel {
                font-size: 18px;
                color: #2c3e50;
            }
        """)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Initialize tabs
        self.setup_general_tab()
        self.setup_appearance_tab()
        self.setup_paths_tab()
        self.setup_behavior_tab()
        self.setup_advanced_tab()

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        self.restart_required = False
        self.load_settings()

    def setup_general_tab(self):
        """Setup General settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.startup_screen = QComboBox()
        self.startup_screen.addItems(["Songs", "Scriptures", "Media", "Presentations", "Themes"])
        layout.addWidget(QLabel("Startup Screen:"))
        layout.addWidget(self.startup_screen)

        self.language = QComboBox()
        self.language.addItems(["English", "Spanish", "French", "German"])  # Future-ready
        layout.addWidget(QLabel("Language:"))
        layout.addWidget(self.language)

        self.enable_tips = QCheckBox("Enable Tips/Help")
        layout.addWidget(self.enable_tips)

        layout.addStretch()
        self.tabs.addTab(tab, "General")

    def setup_appearance_tab(self):
        """Setup Appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.theme = QComboBox()
        self.theme.addItems(["Light", "Dark"])
        self.theme.currentTextChanged.connect(self.on_theme_changed)
        layout.addWidget(QLabel("Theme:"))
        layout.addWidget(self.theme)

        self.ui_font = QPushButton("Choose UI Font")
        self.ui_font.clicked.connect(self.choose_font)
        self.font_display = QLabel("Current Font: Arial, 12")
        layout.addWidget(QLabel("Default UI Font:"))
        layout.addWidget(self.ui_font)
        layout.addWidget(self.font_display)

        self.enable_animations = QCheckBox("Enable Animations")
        layout.addWidget(self.enable_animations)

        layout.addStretch()
        self.tabs.addTab(tab, "Appearance")

    def setup_paths_tab(self):
        """Setup Paths settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.bible_versions_dir = QLineEdit()
        self.bible_versions_dir.setPlaceholderText("Path to Bible versions directory")
        self.bible_browse = QPushButton("Browse")
        self.bible_browse.clicked.connect(lambda: self.browse_directory(self.bible_versions_dir))
        bible_layout = QHBoxLayout()
        bible_layout.addWidget(self.bible_versions_dir)
        bible_layout.addWidget(self.bible_browse)
        layout.addWidget(QLabel("Bible Versions Directory:"))
        layout.addLayout(bible_layout)

        self.media_folder = QLineEdit()
        self.media_folder.setPlaceholderText("Path to media folder")
        self.media_browse = QPushButton("Browse")
        self.media_browse.clicked.connect(lambda: self.browse_directory(self.media_folder))
        media_layout = QHBoxLayout()
        media_layout.addWidget(self.media_folder)
        media_layout.addWidget(self.media_browse)
        layout.addWidget(QLabel("Media Folder:"))
        layout.addLayout(media_layout)

        self.songs_file = QLineEdit()
        self.songs_file.setPlaceholderText("Path to songs file")
        self.songs_browse = QPushButton("Browse")
        self.songs_browse.clicked.connect(lambda: self.browse_file(self.songs_file, "JSON Files (*.json)"))
        songs_layout = QHBoxLayout()
        songs_layout.addWidget(self.songs_file)
        songs_layout.addWidget(self.songs_browse)
        layout.addWidget(QLabel("Songs File:"))
        layout.addLayout(songs_layout)

        layout.addStretch()
        self.tabs.addTab(tab, "Paths")

    def setup_behavior_tab(self):
        """Setup Behavior settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(60, 3600)
        self.auto_save_interval.setSingleStep(60)
        self.auto_save_interval.setSuffix(" seconds")
        layout.addWidget(QLabel("Auto-save Interval:"))
        layout.addWidget(self.auto_save_interval)

        self.confirm_before_delete = QCheckBox("Confirm Before Delete")
        layout.addWidget(self.confirm_before_delete)

        self.default_playback_speed = QComboBox()
        self.default_playback_speed.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x"])
        layout.addWidget(QLabel("Default Playback Speed:"))
        layout.addWidget(self.default_playback_speed)

        layout.addStretch()
        self.tabs.addTab(tab, "Behavior")

    def setup_advanced_tab(self):
        """Setup Advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.reset_settings = QPushButton("Reset All Settings")
        self.reset_settings.clicked.connect(self.on_reset_settings)
        layout.addWidget(self.reset_settings)

        self.export_config = QPushButton("Export Configuration")
        self.export_config.clicked.connect(self.export_settings)
        layout.addWidget(self.export_config)

        self.import_config = QPushButton("Import Configuration")
        self.import_config.clicked.connect(self.import_settings)
        layout.addWidget(self.import_config)

        self.developer_mode = QCheckBox("Developer Mode (Verbose Logging)")
        self.developer_mode.stateChanged.connect(self.on_developer_mode_changed)
        layout.addWidget(self.developer_mode)

        layout.addStretch()
        self.tabs.addTab(tab, "Advanced")

    def load_settings(self):
        """Load settings into UI elements."""
        self.startup_screen.setCurrentText(self.settings_manager.get_setting("general", "startup_screen"))
        self.language.setCurrentText(self.settings_manager.get_setting("general", "language"))
        self.enable_tips.setChecked(self.settings_manager.get_setting("general", "enable_tips"))

        self.theme.setCurrentText(self.settings_manager.get_setting("appearance", "theme"))
        font = QFont()
        font.fromString(self.settings_manager.get_setting("appearance", "ui_font"))
        self.font_display.setText(f"Current Font: {font.family()}, {font.pointSize()}")
        self.enable_animations.setChecked(self.settings_manager.get_setting("appearance", "enable_animations"))

        self.bible_versions_dir.setText(self.settings_manager.get_setting("paths", "bible_versions_dir"))
        self.media_folder.setText(self.settings_manager.get_setting("paths", "media_folder"))
        self.songs_file.setText(self.settings_manager.get_setting("paths", "songs_file"))

        self.auto_save_interval.setValue(self.settings_manager.get_setting("behavior", "auto_save_interval"))
        self.confirm_before_delete.setChecked(self.settings_manager.get_setting("behavior", "confirm_before_delete"))
        speed = str(self.settings_manager.get_setting("behavior", "default_playback_speed")) + "x"
        self.default_playback_speed.setCurrentText(speed)

        self.developer_mode.setChecked(self.settings_manager.get_setting("advanced", "developer_mode"))

    def choose_font(self):
        """Open font dialog and update font display."""
        font, ok = QFontDialog.getFont(QFont().fromString(self.settings_manager.get_setting("appearance", "ui_font")), self)
        if ok:
            self.font_display.setText(f"Current Font: {font.family()}, {font.pointSize()}")
            self.restart_required = True

    def browse_directory(self, line_edit: QLineEdit):
        """Browse for a directory and update the line edit."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if directory:
            line_edit.setText(directory)

    def browse_file(self, line_edit: QLineEdit, filter: str):
        """Browse for a file and update the line edit."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text(), filter)
        if file_path:
            line_edit.setText(file_path)

    def on_theme_changed(self):
        """Mark restart required on theme change."""
        self.restart_required = True

    def on_developer_mode_changed(self, state):
        """Update log level based on developer mode."""
        logging.getLogger().setLevel(logging.DEBUG if state else logging.INFO)
        logger.info(f"Developer mode {'enabled' if state else 'disabled'}")

    def on_reset_settings(self):
        """Reset settings to defaults after confirmation."""
        confirm = QMessageBox.question(
            self, "Confirm Reset",
            "Reset all settings to defaults? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.settings_manager.reset_settings()
            self.load_settings()
            self.restart_required = True
            main_window = self.window()
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.showMessage("Settings reset to defaults")

    def export_settings(self):
        """Export settings to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Settings", "sanctify_settings.json", "JSON Files (*.json)")
        if file_path:
            if self.settings_manager.export_settings(file_path):
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Settings exported to {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export settings.")

    def import_settings(self):
        """Import settings from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if file_path:
            if self.settings_manager.import_settings(file_path):
                self.load_settings()
                self.restart_required = True
                main_window = self.window()
                if hasattr(main_window, "status_bar"):
                    main_window.status_bar.showMessage(f"Settings imported from {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to import settings.")

    def save_settings(self):
        """Save settings and validate paths."""
        settings = {
            "general": {
                "startup_screen": self.startup_screen.currentText(),
                "language": self.language.currentText(),
                "enable_tips": self.enable_tips.isChecked()
            },
            "appearance": {
                "theme": self.theme.currentText(),
                "ui_font": self.font_display.text().replace("Current Font: ", ""),
                "enable_animations": self.enable_animations.isChecked()
            },
            "paths": {
                "bible_versions_dir": self.bible_versions_dir.text().strip(),
                "media_folder": self.media_folder.text().strip(),
                "songs_file": self.songs_file.text().strip()
            },
            "behavior": {
                "auto_save_interval": self.auto_save_interval.value(),
                "confirm_before_delete": self.confirm_before_delete.isChecked(),
                "default_playback_speed": float(self.default_playback_speed.currentText().replace("x", ""))
            },
            "advanced": {
                "developer_mode": self.developer_mode.isChecked(),
                "log_level": "DEBUG" if self.developer_mode.isChecked() else "INFO"
            }
        }

        for section, section_settings in settings.items():
            for key, value in section_settings.items():
                self.settings_manager.set_setting(section, key, value)

        # Validate paths
        path_validity = self.settings_manager.validate_paths()
        invalid_paths = [key for key, valid in path_validity.items() if not valid]
        if invalid_paths:
            QMessageBox.warning(
                self,
                "Invalid Paths",
                f"The following paths are invalid or inaccessible:\n{', '.join(invalid_paths)}.\nPlease correct them."
            )
            return

        main_window = self.window()
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.showMessage("Settings saved successfully")

        if self.restart_required:
            QMessageBox.information(
                self,
                "Restart Required",
                "Some changes (e.g., theme or font) require a restart to take effect."
            )

        self.accept()

# Write example settings schema to file for user reference
sample_settings = {
    "general": {
        "startup_screen": "Songs",
        "language": "English",
        "enable_tips": True
    },
    "appearance": {
        "theme": "Light",
        "ui_font": "Arial,12,-1,5,50,0,0,0,0,0",
        "enable_animations": True
    },
    "paths": {
        "bible_versions_dir": "data/bibles",
        "media_folder": "data/media",
        "songs_file": "data/songs/songs.json"
    },
    "behavior": {
        "auto_save_interval": 300,
        "confirm_before_delete": True,
        "default_playback_speed": 1.0
    },
    "advanced": {
        "developer_mode": False,
        "log_level": "INFO"
    }
}

sample_path = "data/config/settings_sample.json"
os.makedirs(os.path.dirname(sample_path), exist_ok=True)
with open(sample_path, "w", encoding="utf-8") as f:
    json.dump(sample_settings, f, indent=4, ensure_ascii=False)