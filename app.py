"""
Aios — entry point.

Launches the floating bubble and the chat assistant window.
"""

import sys

from PySide6.QtWidgets import QApplication

from bubble import Bubble
from ui import DesktopAssistant


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    assistant = DesktopAssistant()

    def open_assistant():
        assistant.show()
        assistant.raise_()
        assistant.activateWindow()

    bubble = Bubble(on_open=open_assistant)
    bubble.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
