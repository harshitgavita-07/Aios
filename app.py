"""
Aios — entry point.

Launches the floating bubble and the chat assistant window.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from core import memory

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

from bubble import Bubble
from ui import DesktopAssistant


def main():
    memory.init()  # create SQLite tables if needed
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
