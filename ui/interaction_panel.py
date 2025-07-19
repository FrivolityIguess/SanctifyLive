# ui/interaction_panel.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QStringListModel

class InteractionPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        # Left: Schedule Area (placeholder)
        self.schedule_box = QGroupBox("Schedule")
        self.schedule_box.setFixedWidth(220)
        self.schedule_layout = QVBoxLayout()
        self.schedule_layout.addWidget(QLabel("(Upcoming events here)"))
        self.schedule_box.setLayout(self.schedule_layout)

        # Center: Preview Area
        self.preview_box = QGroupBox("Preview")
        self.preview_layout = QVBoxLayout()
        self.preview_display = QTextEdit()
        self.preview_display.setReadOnly(True)
        self.preview_layout.addWidget(self.preview_display)
        self.preview_box.setLayout(self.preview_layout)

        # Right: Live Output
        self.live_box = QGroupBox("Live Output")
        self.live_layout = QVBoxLayout()
        self.live_display = QTextEdit()
        self.live_display.setReadOnly(True)
        self.live_layout.addWidget(self.live_display)
        self.live_box.setLayout(self.live_layout)

        layout.addWidget(self.schedule_box)
        layout.addWidget(self.preview_box, stretch=2)
        layout.addWidget(self.live_box, stretch=2)

    def set_preview_content(self, text: str):
        self.preview_display.setPlainText(text)

    def set_live_content(self, text: str):
        self.live_display.setPlainText(text)

    def clear_outputs(self):
        self.preview_display.clear()
        self.live_display.clear()

    def append_to_schedule(self, text: str):
        self.schedule_layout.addWidget(QLabel(text))
