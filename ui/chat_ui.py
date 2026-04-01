"""
Chat UI — Agent-First Design for AIOS
Shows intelligence, not just chat.
"""

import logging
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QScrollArea, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPalette

from core.agent import AgentController

log = logging.getLogger("aios.ui")


class StreamWorker(QThread):
    """Worker thread for streaming responses."""
    
    token_signal = Signal(str)
    thinking_signal = Signal(str)
    mode_signal = Signal(str)
    sources_signal = Signal(dict)  # sources data dict
    complete_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, agent, user_input):
        super().__init__()
        self.agent = agent
        self.user_input = user_input
        self.current_sources = []

    def run(self):
        try:
            for update in self.agent.process_stream(self.user_input):
                if update["type"] == "token":
                    self.token_signal.emit(update["content"])
                elif update["type"] == "thinking":
                    self.thinking_signal.emit(update["message"])
                elif update["type"] == "mode":
                    self.mode_signal.emit(update["mode"])
                elif update["type"] == "sources":
                    self.sources_signal.emit(update.get("data", {"count": 0, "sources": []}))
                elif update["type"] == "complete":
                    self.complete_signal.emit(update["confidence"])
                elif update["type"] == "error":
                    self.error_signal.emit(update["message"])
        except Exception as e:
            self.error_signal.emit(str(e))


class ChatWindow(QWidget):
    """
    Agent-first UI that shows system intelligence.
    
    Change: Agent-first design (not chat-first)
    Why:
    - Previous UI was standard chat
    - Users need to see what's happening
    - Transparency builds trust
    Impact:
    - System-aware interface
    - Visible intelligence
    - Better user experience
    """

    def __init__(self, agent: AgentController):
        super().__init__()
        self.agent = agent
        self.worker: Optional[StreamWorker] = None
        
        self.setWindowTitle("AIOS — Local AI Runtime")
        self.setMinimumSize(1000, 750)
        
        self._setup_styles()
        self._setup_ui()
        self._update_memory_panel()
        
        # Status timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(5000)
        
        log.info("ChatWindow initialized")

    def _setup_styles(self):
        """Configure dark theme styles."""
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0f1a;
                color: #e8ecf1;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 13px;
            }
            
            QFrame {
                border: none;
            }
            
            QTextEdit {
                background-color: #141b2d;
                color: #e8ecf1;
                border: 1px solid #2d3a5c;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.6;
            }
            
            QTextEdit:focus {
                border-color: #3b82f6;
            }
            
            QLineEdit {
                background-color: #141b2d;
                color: #e8ecf1;
                border: 1px solid #2d3a5c;
                border-radius: 8px;
                padding: 14px 18px;
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
                background-color: #1e293b;
                color: #64748b;
            }
            
            QPushButton#secondary {
                background-color: #1e293b;
                border: 1px solid #2d3a5c;
            }
            
            QPushButton#secondary:hover {
                background-color: #2d3a5c;
            }
            
            QPushButton#danger {
                background-color: #ef4444;
            }
            
            QPushButton#danger:hover {
                background-color: #dc2626;
            }
            
            QListWidget {
                background-color: #141b2d;
                border: 1px solid #2d3a5c;
                border-radius: 8px;
                padding: 8px;
            }
            
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 0;
                color: #94a3b8;
            }
            
            QListWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #1e293b;
            }
            
            QLabel {
                color: #94a3b8;
            }
            
            QLabel#header {
                color: #e8ecf1;
                font-size: 16px;
                font-weight: 700;
            }
            
            QLabel#status {
                color: #64748b;
                font-size: 11px;
            }
            
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #1e293b;
                height: 4px;
            }
            
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
            
            QSplitter::handle {
                background-color: #1e293b;
            }
        """)

    def _setup_ui(self):
        """Setup the agent-first UI layout."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Memory panel
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        splitter.setStretchFactor(0, 0)
        
        # Center: Main interaction
        center_panel = self._create_center_panel()
        splitter.addWidget(center_panel)
        splitter.setStretchFactor(1, 1)
        
        # Right: Intelligence panel
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(2, 0)
        
        splitter.setSizes([200, 600, 220])
        
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_left_panel(self) -> QWidget:
        """Create memory/conversation panel."""
        panel = QWidget()
        panel.setMaximumWidth(240)
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
        
        # Thread list
        self.thread_list = QListWidget()
        self.thread_list.itemClicked.connect(self._on_thread_selected)
        layout.addWidget(self.thread_list)
        
        # Stats
        self.memory_stats = QLabel("0 conversations")
        self.memory_stats.setObjectName("status")
        self.memory_stats.setWordWrap(True)
        layout.addWidget(self.memory_stats)
        
        panel.setLayout(layout)
        return panel

    def _create_center_panel(self) -> QWidget:
        """Create main interaction panel."""
        panel = QWidget()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = self._create_header()
        layout.addLayout(header)
        
        # Thinking indicator (shows processing steps)
        self.thinking_frame = QFrame()
        thinking_layout = QHBoxLayout()
        thinking_layout.setContentsMargins(12, 8, 12, 8)
        
        self.thinking_label = QLabel("")
        self.thinking_label.setStyleSheet("color: #3b82f6; font-size: 12px;")
        thinking_layout.addWidget(self.thinking_label)
        thinking_layout.addStretch()
        
        self.thinking_frame.setLayout(thinking_layout)
        self.thinking_frame.setStyleSheet("background-color: #1e293b; border-radius: 6px;")
        self.thinking_frame.hide()
        layout.addWidget(self.thinking_frame)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Show welcome
        self._show_welcome()
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask anything, research a topic, or execute a task...")
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(90)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Bottom toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        panel.setLayout(layout)
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create intelligence/sources panel."""
        panel = QWidget()
        panel.setMaximumWidth(240)
        panel.setMinimumWidth(180)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 16, 16, 16)
        layout.setSpacing(16)
        
        # Mode indicator
        mode_header = QLabel("🎯 Mode")
        mode_header.setObjectName("header")
        layout.addWidget(mode_header)
        
        self.mode_label = QLabel("💬 Chat")
        self.mode_label.setStyleSheet("color: #22c55e; font-size: 13px; padding: 8px;")
        layout.addWidget(self.mode_label)
        
        # Status section
        status_header = QLabel("📊 Status")
        status_header.setObjectName("header")
        layout.addWidget(status_header)
        
        self.model_status = QLabel(f"Model: {self.agent.llm.get_model()}")
        self.model_status.setObjectName("status")
        self.model_status.setWordWrap(True)
        layout.addWidget(self.model_status)
        
        self.confidence_status = QLabel("Confidence: —")
        self.confidence_status.setObjectName("status")
        layout.addWidget(self.confidence_status)
        
        self.emotion_status = QLabel("Emotion: neutral")
        self.emotion_status.setObjectName("status")
        layout.addWidget(self.emotion_status)
        
        # Sources section
        sources_header = QLabel("📚 Sources")
        sources_header.setObjectName("header")
        layout.addWidget(sources_header)
        
        self.sources_list = QListWidget()
        self.sources_list.setMaximumHeight(200)
        layout.addWidget(self.sources_list)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel

    def _create_header(self) -> QHBoxLayout:
        """Create header with system info."""
        layout = QHBoxLayout()
        
        # Title
        title = QLabel("🤖 AIOS")
        title.setObjectName("header")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Hardware badge
        hw = self.agent.llm.get_hardware_info()
        vram = hw.get("vram_gb", 0)
        gpu = hw.get("gpu_name", "CPU")
        
        if vram > 0:
            hw_text = f"🖥️ {gpu[:15]} • {vram:.0f}GB"
        else:
            hw_text = f"🖥️ {gpu[:20]}"
        
        hw_label = QLabel(hw_text)
        hw_label.setObjectName("status")
        layout.addWidget(hw_label)
        
        return layout

    def _create_toolbar(self) -> QHBoxLayout:
        """Create bottom toolbar."""
        layout = QHBoxLayout()
        
        # Commands hint
        hint = QLabel("Commands: /help /clear /status")
        hint.setObjectName("status")
        layout.addWidget(hint)
        
        layout.addStretch()
        
        # Settings
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("secondary")
        settings_btn.setFixedSize(40, 32)
        settings_btn.clicked.connect(self._on_settings)
        layout.addWidget(settings_btn)
        
        return layout

    def _show_welcome(self):
        """Show welcome message."""
        welcome_html = """
        <html>
        <head>
            <style>
                body { color: #94a3b8; font-family: 'Segoe UI', sans-serif; }
                h2 { color: #e8ecf1; margin-top: 0; }
                .feature { margin: 8px 0; }
                .highlight { color: #3b82f6; font-weight: 600; }
            </style>
        </head>
        <body>
            <h2>Welcome to AIOS v2.0</h2>
            <p>Your local AI runtime with <span class="highlight">reasoning</span>, 
            <span class="highlight">memory</span>, and <span class="highlight">research</span> capabilities.</p>
            
            <div class="feature">💬 <b>Chat</b> — Natural conversations with memory</div>
            <div class="feature">🔍 <b>Research</b> — Ask about latest information</div>
            <div class="feature">🔧 <b>Execute</b> — Run tools and calculations</div>
            <div class="feature">😊 <b>Adaptive</b> — Emotion-aware responses</div>
            
            <p style="margin-top: 16px;"><i>Type a message to begin...</i></p>
        </body>
        </html>
        """
        self.chat_display.setHtml(welcome_html)

    def _on_send(self):
        """Handle send button."""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Check commands
        if text.startswith("/"):
            self._handle_command(text)
            self.input_field.clear()
            return
        
        # Show user message
        self._append_message("user", text)
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Clear previous sources
        self.sources_list.clear()
        
        # Start worker
        self.worker = StreamWorker(self.agent, text)
        self.worker.token_signal.connect(self._on_token)
        self.worker.thinking_signal.connect(self._on_thinking)
        self.worker.mode_signal.connect(self._on_mode)
        self.worker.sources_signal.connect(self._on_sources)
        self.worker.complete_signal.connect(self._on_complete)
        self.worker.error_signal.connect(self._on_error)
        self.worker.start()

    def _on_token(self, token: str):
        """Handle streaming token."""
        self.thinking_frame.hide()
        
        # Check if we need to add assistant prefix
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Simple append (in production, track message state)
        cursor.insertText(token)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def _on_thinking(self, message: str):
        """Show thinking step."""
        self.thinking_label.setText(message)
        self.thinking_frame.show()

    def _on_mode(self, mode: str):
        """Update mode display."""
        mode_emoji = {
            "chat": "💬",
            "research": "🔍",
            "execute": "🔧",
            "reason": "🧠"
        }
        emoji = mode_emoji.get(mode, "💬")
        self.mode_label.setText(f"{emoji} {mode.title()}")

    def _on_sources(self, sources_data: dict):
        """Show sources found."""
        count = sources_data.get("count", 0)
        sources = sources_data.get("sources", [])
        
        self.sources_list.clear()
        self.sources_list.addItem(f"📄 {count} sources found")
        
        if sources:
            self.worker.current_sources = sources
            for source in sources[:5]:  # Show top 5
                title = source.get('title', 'Unknown')
                url = source.get('url', 'N/A')
                self.sources_list.addItem(f"• {title[:50]}...")
                self.sources_list.addItem(f"  🔗 {url}")

    def _on_source_details(self, source_data: Dict):
        """Show detailed source information."""
        if not source_data:
            return
            
        title = source_data.get('title', 'Unknown Source')
        url = source_data.get('url', 'N/A')
        snippet = source_data.get('snippet', 'No preview available')
        
        details = f"""
        <b>Source:</b> {title}<br>
        <b>URL:</b> <a href="{url}" style="color: #3b82f6;">{url}</a><br>
        <b>Preview:</b> {snippet[:200]}...
        """
        
        # Could show in a popup or dedicated panel
        self._append_message("system", f"Source details: {details}")

    def _on_complete(self, confidence: str):
        """Handle completion."""
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        self.thinking_frame.hide()
        
        self.confidence_status.setText(f"Confidence: {confidence.upper()}")
        
        self._update_memory_panel()
        self._update_status()

    def _on_error(self, error: str):
        """Handle error."""
        self._append_message("system", f"Error: {error}")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.thinking_frame.hide()

    def _append_message(self, role: str, content: str):
        """Append message to chat."""
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
        
        color = colors.get(role, "#e8ecf1")
        icon = icons.get(role, "💬")
        
        escaped = content.replace("<", "&lt;").replace(">", "&gt;")
        
        html = f"""
        <div style="margin: 12px 0; padding: 12px; border-left: 3px solid {color};">
            <span style="color: {color}; font-weight: 600;">{icon}</span>
            <span style="color: #e8ecf1;">{escaped}</span>
        </div>
        """
        self.chat_display.append(html)

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
        """Show help."""
        help_text = """
        <b>Available Commands:</b><br>
        <code>/help</code> — Show this help<br>
        <code>/clear</code> — Clear conversation<br>
        <code>/status</code> — System status<br>
        <code>/memory</code> — Memory stats<br>
        <br>
        <b>Modes:</b><br>
        💬 Chat — Natural conversation<br>
        🔍 Research — Web search + RAG<br>
        🔧 Execute — Tool execution<br>
        """
        self.chat_display.append(help_text)

    def _show_status(self):
        """Show system status."""
        status = self.agent.get_status()
        status_text = f"""
        <b>System Status</b><br>
        Model: {status['model']}<br>
        Emotion: {status['emotion']}<br>
        Memory: {status['memory_stats']['message_count']} messages<br>
        Knowledge: {status['rag_stats']['vector_store_size']} vectors<br>
        """
        self.chat_display.append(status_text)

    def _show_memory(self):
        """Show memory stats."""
        stats = self.agent.memory.get_stats()
        mem_text = f"""
        <b>Memory Statistics</b><br>
        Conversations: {stats['thread_count']}<br>
        Total Messages: {stats['message_count']}<br>
        User Messages: {stats['user_messages']}<br>
        Assistant: {stats['assistant_messages']}<br>
        """
        self.chat_display.append(mem_text)

    def _on_new_chat(self):
        """Create new chat."""
        thread_id = self.agent.memory.create_thread()
        self.agent.memory.switch_thread(thread_id)
        self.chat_display.clear()
        self._show_welcome()
        self._update_memory_panel()

    def _on_thread_selected(self, item: QListWidgetItem):
        """Switch thread."""
        thread_id = item.data(Qt.ItemDataRole.UserRole)
        self.agent.memory.switch_thread(thread_id)
        self._load_thread()

    def _load_thread(self):
        """Load thread messages."""
        self.chat_display.clear()
        messages = self.agent.memory.get_messages(limit=50)
        
        for msg in messages:
            if msg.role == "assistant":
                # For assistant, just show content (would reconstruct in production)
                self._append_message("assistant", msg.content[:200] + "...")
            else:
                self._append_message(msg.role, msg.content[:200])

    def _on_clear(self):
        """Clear conversation."""
        self.agent.clear_conversation()
        self.chat_display.clear()
        self._show_welcome()
        self._update_memory_panel()

    def _on_settings(self):
        """Settings placeholder."""
        self._append_message("system", "Settings panel coming in v2.1")

    def _update_memory_panel(self):
        """Update memory panel."""
        self.thread_list.clear()
        
        threads = self.agent.memory.get_threads()
        for thread in threads:
            item = QListWidgetItem(thread["title"])
            item.setData(Qt.ItemDataRole.UserRole, thread["id"])
            self.thread_list.addItem(item)
        
        stats = self.agent.memory.get_stats()
        self.memory_stats.setText(f"{stats['thread_count']} conversations")

    def _update_status(self):
        """Update status indicators."""
        context = self.agent.soulsync.get_context()
        emotion = context.get("emotion", {})
        self.emotion_status.setText(f"Emotion: {emotion.get('dominant', 'neutral')}")

    def closeEvent(self, event):
        """Handle close."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()
