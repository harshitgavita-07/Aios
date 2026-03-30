"""
Chat UI — Modern PySide6 interface for AIOS
Dark theme with streaming, memory panel, and status indicators.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QMenu, QSystemTrayIcon, QApplication
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QAction

from core.agent import AgentController
from ui.worker import AgentWorker

log = logging.getLogger("aios.ui")


class ChatWindow(QWidget):
    """
    Modern chat interface for AIOS.
    
    Change: Redesigned modern UI with memory panel
    Why:
    - Previous UI was basic and limited
    - Users need conversation history access
    - Dark theme is standard for dev tools
    Impact:
    - Professional appearance
    - Better feature accessibility
    """

    def __init__(self, agent: AgentController):
        super().__init__()
        self.agent = agent
        self.worker: Optional[AgentWorker] = None
        
        self.setWindowTitle("AIOS — Local AI Runtime")
        self.setMinimumSize(900, 700)
        
        self._setup_styles()
        self._setup_ui()
        self._update_memory_panel()
        
        # Status update timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(5000)
        
        log.info("ChatWindow initialized")

    def _setup_styles(self):
        """Configure application styles."""
        # Dark theme palette
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 13px;
            }
            
            QFrame {
                border: none;
            }
            
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.5;
            }
            
            QTextEdit:focus {
                border-color: #3b82f6;
            }
            
            QLineEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
            }
            
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #2563eb;
            }
            
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
            
            QPushButton#secondary {
                background-color: #334155;
            }
            
            QPushButton#secondary:hover {
                background-color: #475569;
            }
            
            QPushButton#danger {
                background-color: #ef4444;
            }
            
            QPushButton#danger:hover {
                background-color: #dc2626;
            }
            
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
            }
            
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 0;
            }
            
            QListWidget::item:selected {
                background-color: #3b82f6;
            }
            
            QListWidget::item:hover {
                background-color: #334155;
            }
            
            QLabel {
                color: #94a3b8;
            }
            
            QLabel#header {
                color: #e2e8f0;
                font-size: 18px;
                font-weight: 700;
            }
            
            QLabel#status {
                color: #64748b;
                font-size: 11px;
            }
            
            QSplitter::handle {
                background-color: #334155;
            }
            
            QSplitter::handle:horizontal {
                width: 2px;
            }
        """)

    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Memory/History
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        splitter.setStretchFactor(0, 0)
        
        # Center panel: Chat
        center_panel = self._create_center_panel()
        splitter.addWidget(center_panel)
        splitter.setStretchFactor(1, 1)
        
        # Right panel: Info/Status
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(2, 0)
        
        # Set splitter sizes
        splitter.setSizes([200, 600, 180])
        
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_left_panel(self) -> QWidget:
        """Create the left sidebar with memory/history."""
        panel = QWidget()
        panel.setMaximumWidth(250)
        panel.setMinimumWidth(180)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 8, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("💬 Conversations")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setObjectName("secondary")
        new_chat_btn.clicked.connect(self._on_new_chat)
        layout.addWidget(new_chat_btn)
        
        # Conversation list
        self.thread_list = QListWidget()
        self.thread_list.itemClicked.connect(self._on_thread_selected)
        layout.addWidget(self.thread_list)
        
        # Memory stats
        self.memory_stats_label = QLabel("No conversations")
        self.memory_stats_label.setObjectName("status")
        self.memory_stats_label.setWordWrap(True)
        layout.addWidget(self.memory_stats_label)
        
        panel.setLayout(layout)
        return panel

    def _create_center_panel(self) -> QWidget:
        """Create the center chat panel."""
        panel = QWidget()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with status
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("🤖 AIOS")
        self.title_label.setObjectName("header")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("● Ready")
        self.status_indicator.setStyleSheet("color: #22c55e; font-size: 12px;")
        header_layout.addWidget(self.status_indicator)
        
        layout.addLayout(header_layout)
        
        # Hardware info bar
        self.hw_label = QLabel(self._get_hw_text())
        self.hw_label.setObjectName("status")
        layout.addWidget(self.hw_label)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Your conversation will appear here...")
        layout.addWidget(self.chat_display)
        
        # Welcome message
        self._show_welcome()
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask anything or type /help for commands...")
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Bottom toolbar
        toolbar = QHBoxLayout()
        
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setObjectName("secondary")
        clear_btn.setFixedWidth(90)
        clear_btn.clicked.connect(self._on_clear)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setObjectName("secondary")
        settings_btn.setFixedWidth(100)
        settings_btn.clicked.connect(self._on_settings)
        toolbar.addWidget(settings_btn)
        
        layout.addLayout(toolbar)
        
        panel.setLayout(layout)
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right info panel."""
        panel = QWidget()
        panel.setMaximumWidth(220)
        panel.setMinimumWidth(160)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 16, 16, 16)
        layout.setSpacing(12)
        
        # Status section
        status_header = QLabel("📊 Status")
        status_header.setObjectName("header")
        status_header.setStyleSheet("font-size: 14px;")
        layout.addWidget(status_header)
        
        self.model_label = QLabel(f"Model: {self.agent.llm.get_model()}")
        self.model_label.setObjectName("status")
        self.model_label.setWordWrap(True)
        layout.addWidget(self.model_label)
        
        self.emotion_label = QLabel("Emotion: neutral")
        self.emotion_label.setObjectName("status")
        layout.addWidget(self.emotion_label)
        
        layout.addSpacing(20)
        
        # Quick actions
        actions_header = QLabel("⚡ Actions")
        actions_header.setObjectName("header")
        actions_header.setStyleSheet("font-size: 14px;")
        layout.addWidget(actions_header)
        
        actions = [
            ("System Info", self._on_system_info),
            ("Clear Memory", self._on_clear_memory),
        ]
        
        for label, handler in actions:
            btn = QPushButton(label)
            btn.setObjectName("secondary")
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Version
        version_label = QLabel("AIOS v2.0")
        version_label.setObjectName("status")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        panel.setLayout(layout)
        return panel

    def _show_welcome(self):
        """Show welcome message."""
        welcome = """<html>
        <body style="color: #94a3b8;">
        <h2 style="color: #e2e8f0;">Welcome to AIOS v2.0</h2>
        <p>Your local AI runtime with memory, emotion, and tool execution.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>💾 Persistent conversation memory</li>
            <li>😊 Emotional intelligence (SoulSync)</li>
            <li>🔧 Tool execution (calculator, files, system)</li>
            <li>⚡ Streaming responses</li>
        </ul>
        <p>Type <code>/help</code> for commands.</p>
        </body>
        </html>"""
        self.chat_display.setHtml(welcome)

    def _get_hw_text(self) -> str:
        """Get hardware info text."""
        hw = self.agent.llm.get_hardware_info()
        gpu = hw.get("gpu_name", "CPU")
        vram = hw.get("vram_gb", 0)
        
        if vram > 0:
            return f"🖥️ {gpu} • {vram:.1f} GB VRAM"
        return f"🖥️ {gpu}"

    def _update_memory_panel(self):
        """Update the memory/thread panel."""
        self.thread_list.clear()
        
        threads = self.agent.memory.get_threads()
        for thread in threads:
            item = QListWidgetItem(thread["title"])
            item.setData(Qt.ItemDataRole.UserRole, thread["id"])
            self.thread_list.addItem(item)
        
        stats = self.agent.memory.get_stats()
        self.memory_stats_label.setText(
            f"{stats['thread_count']} conversations\n"
            f"{stats['message_count']} messages"
        )

    def _update_status(self):
        """Update status indicators."""
        context = self.agent.soulsync.get_context()
        emotion = context.get("emotion", {})
        self.emotion_label.setText(f"Emotion: {emotion.get('dominant', 'neutral')}")

    def _on_send(self):
        """Handle send button."""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Check for commands
        if text.startswith("/"):
            self._handle_command(text)
            self.input_field.clear()
            return
        
        # Disable input during processing
        self._set_processing(True)
        
        # Add user message to display
        self._append_message("user", text)
        self.input_field.clear()
        
        # Start agent worker
        self.worker = AgentWorker(self.agent, text)
        self.worker.token_received.connect(self._on_token)
        self.worker.response_complete.connect(self._on_complete)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_token(self, token: str):
        """Handle streaming token."""
        self._append_token(token)

    def _on_complete(self, response: str):
        """Handle completion."""
        self._set_processing(False)
        self._update_memory_panel()

    def _on_error(self, error: str):
        """Handle error."""
        self._append_message("system", f"Error: {error}")
        self._set_processing(False)

    def _set_processing(self, processing: bool):
        """Set UI processing state."""
        self.send_btn.setEnabled(not processing)
        self.input_field.setEnabled(not processing)
        
        if processing:
            self.status_indicator.setText("● Thinking...")
            self.status_indicator.setStyleSheet("color: #eab308; font-size: 12px;")
        else:
            self.status_indicator.setText("● Ready")
            self.status_indicator.setStyleSheet("color: #22c55e; font-size: 12px;")
            self.input_field.setFocus()

    def _append_message(self, role: str, content: str):
        """Append a message to the chat display."""
        colors = {
            "user": "#3b82f6",
            "assistant": "#22c55e",
            "system": "#f59e0b"
        }
        icons = {
            "user": "🧑",
            "assistant": "🤖",
            "system": "⚙️"
        }
        
        color = colors.get(role, "#e2e8f0")
        icon = icons.get(role, "💬")
        
        html = f"""
        <div style="margin: 8px 0; padding: 8px; border-left: 3px solid {color};">
            <span style="color: {color}; font-weight: bold;">{icon}</span>
            <span style="color: #e2e8f0;">{self._escape_html(content)}</span>
        </div>
        """
        
        self.chat_display.append(html)

    def _append_token(self, token: str):
        """Append a streaming token."""
        # This is a simplified approach - in production, you'd track the current
        # assistant message and append to it
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("\n", "<br>"))

    def _handle_command(self, command: str):
        """Handle slash commands."""
        cmd = command.lower().split()[0]
        
        if cmd == "/help":
            self._show_help()
        elif cmd == "/clear":
            self._on_clear()
        elif cmd == "/status":
            self._show_status()
        elif cmd == "/memory":
            self._show_memory()
        else:
            self._append_message("system", f"Unknown command: {command}")

    def _show_help(self):
        """Show help message."""
        help_text = """<b>Available commands:</b>
<ul>
<li><code>/help</code> - Show this help</li>
<li><code>/clear</code> - Clear current conversation</li>
<li><code>/status</code> - Show system status</li>
<li><code>/memory</code> - Show memory statistics</li>
</ul>"""
        self.chat_display.append(help_text)

    def _show_status(self):
        """Show system status."""
        status = self.agent.get_status()
        status_text = f"""<b>System Status:</b>
<ul>
<li>Model: {status['model']}</li>
<li>Emotion: {status['emotion']}</li>
<li>Threads: {status['memory_stats']['thread_count']}</li>
<li>Messages: {status['memory_stats']['message_count']}</li>
</ul>"""
        self.chat_display.append(status_text)

    def _show_memory(self):
        """Show memory statistics."""
        stats = self.agent.memory.get_stats()
        memory_text = f"""<b>Memory Statistics:</b>
<ul>
<li>Conversations: {stats['thread_count']}</li>
<li>Total Messages: {stats['message_count']}</li>
<li>User Messages: {stats['user_messages']}</li>
<li>Assistant Messages: {stats['assistant_messages']}</li>
</ul>"""
        self.chat_display.append(memory_text)

    def _on_new_chat(self):
        """Create new conversation."""
        thread_id = self.agent.memory.create_thread()
        self.agent.memory.switch_thread(thread_id)
        self.chat_display.clear()
        self._show_welcome()
        self._update_memory_panel()

    def _on_thread_selected(self, item: QListWidgetItem):
        """Switch to selected thread."""
        thread_id = item.data(Qt.ItemDataRole.UserRole)
        self.agent.memory.switch_thread(thread_id)
        self._load_thread_messages()

    def _load_thread_messages(self):
        """Load messages for current thread."""
        self.chat_display.clear()
        messages = self.agent.memory.get_messages(limit=50)
        
        for msg in messages:
            self._append_message(msg.role, msg.content)

    def _on_clear(self):
        """Clear current conversation."""
        self.agent.clear_conversation()
        self.chat_display.clear()
        self._show_welcome()
        self._update_memory_panel()

    def _on_clear_memory(self):
        """Clear all memory."""
        reply = QMessageBox.question(
            self, "Clear Memory",
            "Clear all conversations? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.agent.clear_conversation()
            self._update_memory_panel()
            self.chat_display.append("<i>Memory cleared.</i>")

    def _on_settings(self):
        """Open settings dialog."""
        self.chat_display.append("<i>Settings dialog not yet implemented.</i>")

    def _on_system_info(self):
        """Show system info."""
        status = self.agent.get_status()
        hw = status.get("hardware", {})
        info_text = f"""<b>System Information:</b>
<ul>
<li>GPU: {hw.get('gpu_name', 'CPU')}</li>
<li>VRAM: {hw.get('vram_gb', 0):.1f} GB</li>
<li>RAM: {hw.get('ram_gb', 0):.1f} GB</li>
<li>CPU Cores: {hw.get('cpu_cores', '?')}</li>
</ul>"""
        self.chat_display.append(info_text)

    def closeEvent(self, event):
        """Handle window close."""
        # Stop any running worker
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()
