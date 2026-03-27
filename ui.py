"""
Aios chat UI — non-blocking, streaming token display with hardware status.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer

from llm import init as llm_init, get_model, get_hw_info
from worker import LLMWorker
from settings import SettingsPanel


class DesktopAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aios — Local AI Assistant")
        self.setFixedSize(560, 660)
        self._worker = None
        self._status = {}
        self._typing_dots = 0
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(400)
        self._typing_timer.timeout.connect(self._animate_typing)
        self._first_token = False

        root = QVBoxLayout()

        # Header row: hardware label + settings gear
        header_row = QHBoxLayout()
        self.hw_label = QLabel("⏳ Detecting hardware...")
        self.hw_label.setStyleSheet(
            "color: #9ca3af; font-size: 11px; padding: 4px;"
        )
        header_row.addWidget(self.hw_label, stretch=1)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #9ca3af; "
            "font-size: 16px; border: none; border-radius: 14px; } "
            "QPushButton:hover { background: #374151; color: #f3f4f6; }"
        )
        self.settings_btn.clicked.connect(self._toggle_settings)
        header_row.addWidget(self.settings_btn)
        root.addLayout(header_row)

        # Settings panel (hidden by default)
        self._settings_panel = SettingsPanel()
        self._settings_panel.model_changed.connect(self._on_model_changed)
        self._settings_panel.hide()

        # Chat display
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("Assistant output will appear here...")
        self.chat.setStyleSheet(
            "QTextEdit { background: #1f2937; color: #f3f4f6; "
            "border: 1px solid #374151; border-radius: 8px; "
            "padding: 8px; font-size: 13px; }"
        )
        root.addWidget(self.chat)

        # Input row
        input_row = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask anything...")
        self.input.returnPressed.connect(self.send_message)
        self.input.setStyleSheet(
            "QLineEdit { background: #111827; color: #f9fafb; "
            "border: 1px solid #374151; border-radius: 6px; "
            "padding: 8px; font-size: 13px; }"
        )
        input_row.addWidget(self.input)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet(
            "QPushButton { background: #2563eb; color: white; "
            "border-radius: 6px; padding: 8px 16px; font-weight: bold; } "
            "QPushButton:hover { background: #1d4ed8; } "
            "QPushButton:disabled { background: #374151; color: #6b7280; }"
        )
        input_row.addWidget(self.send_btn)

        root.addLayout(input_row)
        self.setLayout(root)

        # Init LLM (detect hardware + pick model)
        try:
            self._status = llm_init()
            gpu = self._status.get("gpu_name") or "CPU-only"
            vram = self._status.get("vram_gb", 0)
            model = self._status.get("model", "?")
            n_models = len(self._status.get("available_models", []))
            arch = self._status.get("architecture", "")

            hw_text = f"🖥️ {gpu}"
            if vram:
                hw_text += f"  •  {vram} GB"
            if arch:
                hw_text += f" {arch}"
            hw_text += f"  •  Model: {model}  •  {n_models} available"
            self.hw_label.setText(hw_text)
            self.chat.append(f"🤖 Aios ready.\n   Model: {model}\n")
        except Exception as e:
            self.hw_label.setText(f"⚠️ Init error: {e}")
            self.chat.append(f"⚠️ Could not initialize LLM: {e}\n")

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return

        self.chat.append(f"🧑 You: {text}")
        self.input.clear()
        self.chat.append("🤖 Aios: ")
        self._set_busy(True)
        self._first_token = False
        self._start_typing_indicator()

        self._worker = LLMWorker(text)
        self._worker.token_received.connect(self._on_token)
        self._worker.generation_finished.connect(self._on_done)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_token(self, token: str):
        if not self._first_token:
            self._first_token = True
            self._stop_typing_indicator()
        cursor = self.chat.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.chat.setTextCursor(cursor)
        self.chat.verticalScrollBar().setValue(
            self.chat.verticalScrollBar().maximum()
        )

    def _on_done(self):
        self._stop_typing_indicator()
        self.chat.append("")
        self._set_busy(False)

    def _on_error(self, msg: str):
        self._stop_typing_indicator()
        self.chat.append(f"\n⚠️ Error: {msg}\n")
        self._set_busy(False)

    # ── Typing indicator ─────────────────────────────────────

    def _start_typing_indicator(self):
        self._typing_dots = 0
        cursor = self.chat.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText("⬤  ")
        self.chat.setTextCursor(cursor)
        self._typing_timer.start()

    def _animate_typing(self):
        self._typing_dots = (self._typing_dots + 1) % 4
        frames = ["⬤  ", " ⬤ ", "  ⬤", " ⬤ "]
        cursor = self.chat.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        # Select the 3-char indicator and replace it
        cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, 3)
        cursor.insertText(frames[self._typing_dots])
        self.chat.setTextCursor(cursor)
        self.chat.verticalScrollBar().setValue(
            self.chat.verticalScrollBar().maximum()
        )

    def _stop_typing_indicator(self):
        if self._typing_timer.isActive():
            self._typing_timer.stop()
            # Remove the 3-char indicator
            cursor = self.chat.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, 3)
            cursor.removeSelectedText()
            self.chat.setTextCursor(cursor)

    # ── Settings ─────────────────────────────────────────────

    def _toggle_settings(self):
        if self._settings_panel.isVisible():
            self._settings_panel.hide()
        else:
            # Position near the gear button
            btn_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight())
            self._settings_panel.move(btn_pos.x() - self._settings_panel.width(), btn_pos.y() + 4)
            self._settings_panel.show()
            self._settings_panel.raise_()

    def _on_model_changed(self, model: str):
        self.hw_label.setText(
            self.hw_label.text().rsplit("Model:", 1)[0] + f"Model: {model}"
        )
        self.chat.append(f"\n🔄 Model switched to: {model}\n")

    def _set_busy(self, busy: bool):
        self.input.setEnabled(not busy)
        self.send_btn.setEnabled(not busy)
        self.settings_btn.setEnabled(not busy)
        if not busy:
            self.input.setFocus()
