"""
Floating Bubble — Draggable system bubble for quick access
"""

from PySide6.QtWidgets import QWidget, QPushButton, QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QColor, QPainter, QBrush, QFont


class FloatingBubble(QWidget):
    """
    Floating always-on-top bubble for quick assistant access.
    
    Change: Enhanced bubble with animations
    Why:
    - Previous bubble was basic
    - Visual feedback improves UX
    Impact:
    - More engaging quick access
    - Better visual appeal
    """

    def __init__(self, on_activate):
        super().__init__()
        self.on_activate = on_activate
        self.drag_position = None
        
        self.setFixedSize(64, 64)
        
        # Window flags for floating, always-on-top, frameless
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Position at right edge of screen
        self._position_at_right_edge()
        
        # Animation timer for pulse effect
        self._pulse_scale = 1.0
        self._pulse_direction = 1
        
    def _position_at_right_edge(self):
        """Position bubble at right edge, vertically centered."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.center().y() - self.height() // 2
        self.move(x, y)

    def paintEvent(self, event):
        """Custom paint for bubble appearance."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawEllipse(4, 4, 60, 60)
        
        # Main bubble
        gradient_color = QColor(59, 130, 246)  # Blue
        painter.setBrush(QBrush(gradient_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 60, 60)
        
        # Inner glow
        painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
        painter.drawEllipse(10, 10, 40, 40)
        
        # Robot icon
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI Emoji", 24)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🤖")
        
        painter.end()

    def mousePressEvent(self, event):
        """Start drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle drag."""
        if self.drag_position and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """End drag or activate."""
        self.drag_position = None
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_activate()
            self.hide()

    def enterEvent(self, event):
        """Hover enter."""
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def leaveEvent(self, event):
        """Hover leave."""
        self.unsetCursor()

    def showEvent(self, event):
        """Ensure bubble stays on top when shown."""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
