from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor


class Bubble(QWidget):
    def __init__(self, on_open):
        super().__init__()
        self.on_open = on_open
        self.drag_position = None

        self.setFixedSize(60, 60)

        # Window flags → floating system bubble
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)

        # Bubble button
        self.button = QPushButton("🤖", self)
        self.button.setFixedSize(60, 60)
        self.button.setCursor(QCursor(Qt.PointingHandCursor))
        self.button.setStyleSheet("""
            QPushButton {
                border-radius: 30px;
                background-color: #1f2937;
                color: white;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)

        self.button.clicked.connect(self.open_assistant)

        self.move_to_right_center()

    # ---- Positioning ----
    def move_to_right_center(self):
        screen = self.screen().availableGeometry()
        x = screen.right() - self.width() - 16
        y = screen.center().y() - self.height() // 2
        self.move(x, y)

    # ---- Interaction ----
    def open_assistant(self):
        self.hide()
        self.on_open()

    # ---- Drag support ----
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None