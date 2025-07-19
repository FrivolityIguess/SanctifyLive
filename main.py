import sys
import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict

# Temporary logger for early failures
temp_logger = logging.getLogger('SanctifyEarly')
temp_handler = logging.StreamHandler()
temp_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
temp_logger.addHandler(temp_handler)
temp_logger.setLevel(logging.INFO)

try:
    temp_logger.info("Starting import of standard libraries")
    import sys
    temp_logger.info("Imported sys")
    import os
    temp_logger.info("Imported os")
    import json
    temp_logger.info("Imported json")
    import uuid
    temp_logger.info("Imported uuid")
    from datetime import datetime
    temp_logger.info("Imported datetime")
    from typing import Dict
    temp_logger.info("Imported typing.Dict")
except Exception as e:
    temp_logger.error("Failed to import standard libraries: %s", e)
    raise

try:
    temp_logger.info("Starting import of PyQt5 modules")
    from PyQt5.QtWidgets import QApplication, QSplashScreen, QProgressBar, QMessageBox
    temp_logger.info("Imported PyQt5.QtWidgets")
    from PyQt5.QtGui import QPixmap, QFont, QIcon
    temp_logger.info("Imported PyQt5.QtGui")
    from PyQt5.QtCore import Qt, QTimer, QCoreApplication, QTranslator, QPropertyAnimation
    temp_logger.info("Imported PyQt5.QtCore")
except Exception as e:
    temp_logger.error("Failed to import PyQt5 modules: %s", e)
    raise

try:
    temp_logger.info("Starting import of custom modules")
    from ui.main_window import SanctifyApp
    temp_logger.info("Imported ui.main_window.SanctifyApp")
    from core.settings_manager import SettingsManager
    temp_logger.info("Imported core.settings_manager.SettingsManager")
    from core.exceptions import SanctifyError
    temp_logger.info("Imported core.exceptions.SanctifyError")
    from models.song_model import SongModel
    temp_logger.info("Imported models.song_model.SongModel")
    from models.media_model import MediaModel
    temp_logger.info("Imported models.media_model.MediaModel")
    from models.presentation_model import PresentationModel
    temp_logger.info("Imported models.presentation_model.PresentationModel")
    from models.theme_model import ThemeModel
    temp_logger.info("Imported models.theme_model.ThemeModel")
    from models.scripture_model import ScriptureModel
    temp_logger.info("Imported models.scripture_model.ScriptureModel")
except Exception as e:
    temp_logger.error("Failed to import custom modules: %s", e)
    raise

# Setup main logging
try:
    temp_logger.info("Setting up main logging")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/sanctify.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Main logging setup complete")
except Exception as e:
    temp_logger.error("Failed to setup main logging: %s", e)
    raise SanctifyError("Main", "LOG_001", f"Failed to setup logging: {e}")

def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        'data/config',
        'data/logs',
        'data/songs',
        'data/media/Images',
        'data/media/Videos',
        'data/media/Gifs',
        'data/presentations',
        'data/themes',
        'data/bibles',
        'assets/translations'
    ]
    for directory in directories:
        try:
            logger.info(f"Checking directory: {directory}")
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: %s", e)
            raise SanctifyError("Main", "DIR_001", f"Failed to create directory {directory}: {e}")
    logger.info("All directories ensured")
    return True

def validate_assets():
    """Validate required assets exist."""
    assets = [
        'assets/images/splash.png',
        'assets/icons/settings.png',
        'assets/icons/browse.png',
        'assets/icons/alert.png',
        'assets/icons/logo.png',
        'assets/icons/black.png',
        'assets/icons/white.png',
        'assets/icons/live.png'
    ]
    missing = []
    for asset in assets:
        try:
            logger.info(f"Checking asset: {asset}")
            if not os.path.exists(asset):
                logger.warning(f"Missing asset: {asset}")
                missing.append(asset)
            else:
                logger.debug(f"Asset exists: {asset}")
        except Exception as e:
            logger.error(f"Error checking asset {asset}: %s", e)
            raise SanctifyError("Main", "ASSET_001", f"Error checking asset {asset}: {e}")
    logger.info("Asset validation complete")
    return missing

def validate_data_files(settings_manager: SettingsManager):
    """Validate required data files and create defaults if missing."""
    try:
        logger.info("Starting data file validation")
        sample_song = {
            "title": "Amazing Grace",
            "sections": [
                ["Verse", "Amazing grace! How sweet the sound\nThat saved a wretch like me."],
                ["Chorus", "I once was lost, but now am found\nWas blind, but now I see."]
            ],
            "tags": "worship,classic,grace",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        sample_media = [
            {
                "id": str(uuid.uuid4()),
                "name": "sample_image.jpg",
                "path": "Images/sample_image.jpg",
                "category": "Images",
                "tags": "worship,background",
                "scaling": "fit",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_logo": True
            },
            {
                "id": str(uuid.uuid4()),
                "name": "sample_video.mp4",
                "path": "Videos/sample_video.mp4",
                "category": "Videos",
                "tags": "intro,loop",
                "scaling": "fill",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_logo": False
            }
        ]
        sample_presentation = [
            {
                "id": str(uuid.uuid4()),
                "name": "Sample Sermon",
                "theme": "default",
                "slides": [
                    ["Text", "Welcome to our service!\nGod bless you all."],
                    ["Image", "Images/sample_image.jpg"],
                    ["Text", "Today's message: Love and Grace"]
                ],
                "tags": "sermon,worship,teaching",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        sample_themes = [
            {
                "id": "default",
                "name": "Default Theme",
                "context": "Presentations",
                "alignment": "Centered",
                "font_color": "#ecf0f1",
                "background_color": "#2c3e50",
                "font_size": 18,
                "font_family": "Arial",
                "tags": "default,presentation",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        sample_settings = {
            "general": {
                "startup_screen": "Songs",
                "language": "English",
                "enable_tips": True,
                "window_geometry": {"width": 1280, "height": 720, "x": 100, "y": 100}
            },
            "appearance": {
                "theme": "Light",
                "ui_font": QFont("Arial", 12).toString(),
                "enable_animations": True
            },
            "paths": {
                "songs": "data/songs/songs.json",
                "media": "data/media",
                "media_metadata": "data/media/media.json",
                "presentations": "data/presentations/presentations.json",
                "themes": "data/themes/themes.json",
                "bibles": "data/bibles",
                "config": "data/config/settings.json"
            },
            "behavior": {
                "auto_save_interval": 300,
                "confirm_before_delete": True,
                "default_playback_speed": 1.0
            },
            "advanced": {
                "developer_mode": False,
                "log_level": "INFO"
            },
            "accessibility": {
                "high_contrast": False
            }
        }
        data_files = {
            settings_manager.get_setting("paths", "songs", "data/songs/songs.json"): [sample_song],
            settings_manager.get_setting("paths", "media_metadata", "data/media/media.json"): sample_media,
            settings_manager.get_setting("paths", "presentations", "data/presentations/presentations.json"): sample_presentation,
            settings_manager.get_setting("paths", "themes", "data/themes/themes.json"): sample_themes,
            settings_manager.get_setting("paths", "config", "data/config/settings.json"): sample_settings
        }
        logger.info(f"Settings loaded: {settings_manager.get_all_settings()}")
        missing_or_corrupted = []
        for file_path, default_content in data_files.items():
            try:
                if file_path is None:
                    logger.error(f"Invalid file path: None detected in data_files")
                    raise SanctifyError("Main", "DATA_FILE_004", "Invalid file path: None detected")
                logger.info(f"Checking data file: {file_path}")
                if not os.path.exists(file_path):
                    logger.info(f"Data file missing, creating: {file_path}")
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, indent=4, ensure_ascii=False)
                    logger.info(f"Created default data file: {file_path}")
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)  # Validate JSON
                    logger.debug(f"Validated data file: {file_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted data file {file_path}: %s", e)
                missing_or_corrupted.append(file_path)
                try:
                    logger.info(f"Restoring default data file: {file_path}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, indent=4, ensure_ascii=False)
                    logger.info(f"Restored default data file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to restore data file {file_path}: %s", e)
                    raise SanctifyError("Main", "DATA_FILE_001", f"Failed to restore data file {file_path}: {e}")
            except Exception as e:
                logger.error(f"Error validating data file {file_path}: %s", e)
                raise SanctifyError("Main", "DATA_FILE_002", f"Error validating data file {file_path}: {e}")
        logger.info("Data file validation complete")
        return missing_or_corrupted
    except Exception as e:
        logger.error("Failed data file validation: %s", e)
        raise SanctifyError("Main", "DATA_FILE_003", f"Data file validation failed: {e}")

def main():
    """Main entry point for Sanctify Live."""
    splash = None  # Initialize splash to None
    try:
        logger.info("Starting Sanctify Live...")
        # Enable high-DPI scaling before QApplication
        logger.info("Enabling high-DPI scaling")
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        logger.debug("Enabled high-DPI scaling")

        # Initialize QApplication
        logger.info("Initializing QApplication")
        app = QApplication(sys.argv)
        app.setApplicationName("Sanctify Live")
        app.setApplicationVersion("1.0.1")
        logger.info(f"Application: {app.applicationName()} v{app.applicationVersion()}")

        # Ensure directories
        logger.info("Ensuring directories")
        ensure_directories()
        logger.info("Directories ensured")

        # Initialize SettingsManager
        logger.info("Initializing SettingsManager")
        settings_manager = SettingsManager()
        logger.info("SettingsManager initialized")

        # Validate assets
        logger.info("Validating assets")
        missing_assets = validate_assets()
        if missing_assets:
            logger.warning(f"Missing assets: {', '.join(missing_assets)}")
            QMessageBox.warning(None, "Asset Warning", f"Missing assets: {', '.join(missing_assets)}. UI may be incomplete.")
        logger.info("Assets validated")

        # Validate data files
        logger.info("Validating data files")
        missing_data_files = validate_data_files(settings_manager)
        if missing_data_files:
            logger.warning(f"Corrupted or missing data files: {', '.join(missing_data_files)}")
            QMessageBox.warning(None, "Data Warning", f"Restored default data for: {', '.join(missing_data_files)}")
        logger.info("Data files validated")

        # Validate paths (temporarily skip due to SettingsManager error)
        logger.info("Validating settings paths")
        try:
            path_validity = settings_manager.validate_paths()
            for key, valid in path_validity.items():
                if not valid:
                    logger.warning(f"Invalid path in settings: {key} = {settings_manager.get_setting('paths', key)}")
            logger.info("Settings paths validated")
        except Exception as e:
            logger.warning(f"Skipping path validation due to error: {e}")
            QMessageBox.warning(None, "Settings Warning", f"Path validation failed: {e}. Continuing with default paths.")

        # Load translations
        logger.info("Loading translations")
        translator = QTranslator()
        language = settings_manager.get_setting("general", "language", "English")
        if translator.load(f"assets/translations/{language.lower()}.qm"):
            app.installTranslator(translator)
            logger.info(f"Loaded translation: {language}")
        else:
            logger.debug(f"No translation file found for language: {language}")
        logger.info("Translations loaded")

        # Show splash screen with progress bar
        logger.info("Showing splash screen")
        splash_path = "assets/images/splash.png"
        splash_pixmap = QPixmap(splash_path) if os.path.exists(splash_path) else QPixmap()
        splash = QSplashScreen(splash_pixmap)
        splash.setStyleSheet("""
            QSplashScreen {
                background: #2c3e50;
                border: 2px solid #3498db;
            }
        """)
        progress_bar = QProgressBar(splash)
        progress_bar.setGeometry(50, splash.height() - 50, splash.width() - 100, 20)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3498db;
                border-radius: 3px;
                background: #ecf0f1;
                text-align: center;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background: #3498db;
            }
        """)
        splash.show()
        splash.showMessage("Initializing Sanctify Live...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()
        logger.info("Splash screen shown")

        # Initialize components with progress updates
        logger.info("Initializing components")
        components = {}
        progress_steps = [
            ("Loading song model...", lambda: SongModel(settings_manager)),
            ("Loading media model...", lambda: MediaModel(settings_manager)),
            ("Loading presentation model...", lambda: PresentationModel(settings_manager)),
            ("Loading theme model...", lambda: ThemeModel(settings_manager)),
            ("Loading scripture model...", lambda: ScriptureModel(settings_manager)),
            ("Initializing main window...", lambda: SanctifyApp())
        ]
        for i, (message, task) in enumerate(progress_steps):
            try:
                logger.info(f"Starting task: {message}")
                progress = int((i + 1) / len(progress_steps) * 100)
                splash.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
                progress_bar.setValue(progress)
                app.processEvents()
                components[message] = task()
                logger.debug(f"Completed startup task: {message}")
            except Exception as e:
                logger.error(f"Failed startup task '{message}': %s", e)
                raise SanctifyError("Main", f"INIT_{i+1:03d}", f"Failed startup task '{message}': {e}")
        logger.info("Components initialized")

        # Get main window
        logger.info("Retrieving main window")
        window = components.get("Initializing main window...")
        if not window:
            logger.error("Main window initialization failed")
            raise SanctifyError("Main", "INIT_WINDOW_001", "Main window initialization failed")
        logger.info("Main window retrieved")

        # Configure main window
        logger.info("Configuring main window")
        window.setAccessibleName("Sanctify Live")
        window.status_bar.showMessage("Initializing...")
        geometry = settings_manager.get_setting("general", "window_geometry", {"width": 1280, "height": 720, "x": 100, "y": 100})
        window.setGeometry(geometry["x"], geometry["y"], geometry["width"], geometry["height"])
        logger.info("Main window geometry set")

        # Set startup screen
        logger.info("Setting startup screen")
        startup_screen = settings_manager.get_setting("general", "startup_screen", "Songs")
        tab_index = {"Songs": 0, "Scriptures": 1, "Media": 2, "Presentations": 3, "Themes": 4}.get(startup_screen, 0)
        window.tabs.setCurrentIndex(tab_index)
        logger.info(f"Startup screen set to {startup_screen}")

        # Apply accessibility settings
        logger.info("Applying accessibility settings")
        if settings_manager.get_setting("accessibility", "high_contrast", False):
            app.setStyleSheet(app.styleSheet() + """
                QWidget {
                    background: #000000;
                    color: #ffffff;
                }
                QPushButton {
                    border: 2px solid #ffffff;
                    background: #000000;
                    color: #ffffff;
                }
            """)
            logger.info("Applied high-contrast accessibility mode")
        logger.info("Accessibility settings applied")

        # Show window with animation
        logger.info("Showing main window")
        window.setWindowOpacity(0.0)
        window.show()
        if settings_manager.get_setting("appearance", "enable_animations", True):
            logger.info("Starting window animation")
            anim = QPropertyAnimation(window, b"windowOpacity")
            anim.setDuration(500)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()
            logger.info("Window animation started")
        QTimer.singleShot(500, splash.close)
        window.status_bar.showMessage(f"Started on {startup_screen} tab")
        logger.info(f"Main window shown on {startup_screen} tab")

        # Save window geometry on close
        logger.info("Setting up close event handler")
        def save_geometry(event):
            try:
                logger.info("Saving window geometry")
                settings_manager.set_setting("general", "window_geometry", {
                    "width": window.width(),
                    "height": window.height(),
                    "x": window.x(),
                    "y": window.y()
                })
                logger.info("Window geometry saved")
                event.accept()
            except Exception as e:
                logger.error("Failed to save window geometry: %s", e)
                raise SanctifyError("Main", "SAVE_GEOMETRY_001", f"Failed to save window geometry: {e}")
        window.closeEvent = save_geometry
        logger.info("Close event handler set")

        # Start event loop
        logger.info("Starting application event loop")
        sys.exit(app.exec_())

    except SanctifyError as e:
        logger.error("SanctifyError: %s", e)
        if splash is not None:
            splash.close()
        QMessageBox.critical(None, "Startup Error", str(e))
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        if splash is not None:
            splash.close()
        raise SanctifyError("Main", "STARTUP_001", f"Application failed to start: {e}")

if __name__ == "__main__":
    try:
        logger.info("Entering main block")
        main()
    except Exception as e:
        logger.error("Failed in main block: %s", e)
        raise