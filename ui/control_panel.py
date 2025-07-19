# ui/control_panel.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QStringListModel

class ControlPanel(QWidget):
    go_live_clicked = pyqtSignal()
    logo_clicked = pyqtSignal()
    black_clicked = pyqtSignal()
    white_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        # Left: Settings, Browse, Alert
        self.settings_btn = QPushButton("Settings")
        self.browse_btn = QPushButton("Browse")
        self.alert_btn = QPushButton("Alert")

        layout.addWidget(self.settings_btn)
        layout.addWidget(self.browse_btn)
        layout.addWidget(self.alert_btn)

        # Spacer (Middle section)
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Right: Logo, Black, White, Go Live
        self.logo_btn = QPushButton("Logo")
        self.black_btn = QPushButton("Black")
        self.white_btn = QPushButton("White")
        self.go_live_btn = QPushButton("Go Live")

        layout.addWidget(self.logo_btn)
        layout.addWidget(self.black_btn)
        layout.addWidget(self.white_btn)
        layout.addWidget(self.go_live_btn)

        # Connect signals
        self.go_live_btn.clicked.connect(self.go_live_clicked.emit)
        self.logo_btn.clicked.connect(self.logo_clicked.emit)
        self.black_btn.clicked.connect(self.black_clicked.emit)
        self.white_btn.clicked.connect(self.white_clicked.emit)
