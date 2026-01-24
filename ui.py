from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton
)
from PySide6.QtCore import Qt

# Import router safely
try:
    from agent import agent_router
except Exception as e:
    agent_router = None
    IMPORT_ERROR = str(e)
else:
    IMPORT_ERROR = None


class DesktopAssistant(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Desktop AI Assistant – V1")
        self.setFixedSize(520, 620)

        # ---- Layout ----
        layout = QVBoxLayout()

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("Assistant output will appear here...")

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask anything...")
        self.input.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        layout.addWidget(self.chat)
        layout.addWidget(self.input)
        layout.addWidget(send_btn)
        self.setLayout(layout)

        # ---- Startup message ----
        self.chat.append("🤖 Assistant: Ready.\n")

        if IMPORT_ERROR:
            self.chat.append(
                f"⚠️ System Warning:\nAgent failed to load.\n{IMPORT_ERROR}\n"
            )

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return

        # Show user message
        self.chat.append(f"🧑 You: {text}")
        self.input.clear()

        # ---- Safeguarded response pipeline ----
        response = None

        if agent_router is None:
            response = "System Error: Agent router is not available."
        else:
            try:
                response = agent_router(text)
            except Exception as e:
                response = f"Runtime Error: {str(e)}"

        if not response:
            response = "⚠️ Empty response from assistant."

        self.chat.append(f"🤖 Assistant: {response}\n")

        # Auto-scroll
        self.chat.verticalScrollBar().setValue(
            self.chat.verticalScrollBar().maximum()
        )