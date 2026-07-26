"""
AIOS -- Application Bootstrap (v4)

A floating desktop bubble that expands into a full workspace, wired to
the real orchestration pipeline:

    Natural language
        -> IntentEngine          (src/orchestrator/intent_engine.py)
        -> PlanningEngine        (src/orchestrator/planning_engine.py)
        -> PlanExecutor          (src/execution/plan_executor.py)
        -> ScrRuntimeAdapter     (src/adapters/scr_adapter.py)
        -> SCR Runtime           (Node subprocess, real terminal execution)
        -> VerificationEngine    (src/orchestrator/verification_engine.py)
        -> GUI (this file)

app.py only wires these together and renders them; it contains no
orchestration or execution logic of its own -- that lives in the
modules above, per the layering this project has settled on.

Known, honestly-stated limitation: PlanningEngine does not yet extract
a real shell command from natural language -- for the "terminal"
domain it currently carries the user's raw text forward as the
command (see planning_engine.py's TERMINAL branch). That means typing
an actual command ("pwd", "ls -la") works end-to-end; typing a
description of what you want ("show me the current directory") will
be sent to SCR Runtime literally and will fail as an unknown shell
command. PlanExecutor and the UI both surface that failure honestly
(a real, red, "command not found"-style error) rather than hiding or
faking success. Only the "terminal" plugin has an execution backend at
all right now (browser/git/docker/etc. plans are recognized and shown,
but PlanExecutor reports them as not-yet-implemented instead of
pretending to run them -- see PlanExecutor.SUPPORTED_PLUGINS).
"""

from __future__ import annotations

import asyncio
import json
import logging
import logging.handlers
import sys
import threading
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
    Property,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSplitter,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src import IntentEngine, PlanningEngine, VerificationEngine
from src.adapters import ScrRuntimeAdapter
from src.execution import PlanExecutor
from src.shared.types import Event

# --------------------------------------------------------------------------
# Paths & logging
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent
CONFIG_DIR = REPO_ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "settings.json"
LOG_DIR = REPO_ROOT / "logs"
LOG_PATH = LOG_DIR / "aios.log"

_ANSI_COLORS = {
    logging.DEBUG: "\033[36m",     # cyan
    logging.INFO: "\033[32m",      # green
    logging.WARNING: "\033[33m",   # yellow
    logging.ERROR: "\033[31m",     # red
    logging.CRITICAL: "\033[41m",  # red background
}
_ANSI_RESET = "\033[0m"


class ColorFormatter(logging.Formatter):
    """Console formatter with per-level ANSI color and a compact timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        color = _ANSI_COLORS.get(record.levelno, "")
        base = super().format(record)
        return f"{color}{base}{_ANSI_RESET}" if color else base


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("aios")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger  # already configured (e.g. re-entrant import)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColorFormatter("%(asctime)s %(name)-24s %(levelname)-8s %(message)s", "%H:%M:%S"))

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_PATH, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)-24s %(levelname)-8s %(message)s", "%Y-%m-%d %H:%M:%S")
    )

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


log = configure_logging()


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

@dataclass
class AiosConfig:
    """Persisted user/window preferences. Loaded once at startup, saved on change."""

    theme: str = "dark"
    bubble_x: int = 80
    bubble_y: int = 80
    workspace_x: int = 200
    workspace_y: int = 120
    workspace_width: int = 980
    workspace_height: int = 680
    last_goal: str = ""

    @classmethod
    def load(cls) -> "AiosConfig":
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                known = {f: data[f] for f in cls.__dataclass_fields__ if f in data}
                return cls(**known)
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Failed to load config (%s); using defaults", exc)
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError as exc:
            log.warning("Failed to save config: %s", exc)


# --------------------------------------------------------------------------
# Event bus
# --------------------------------------------------------------------------

class EventBus(QObject):
    """
    Process-wide pub/sub for Event objects (src.shared.types.Event).

    Any thread may call publish(); Qt's signal/slot machinery marshals
    the emission onto the thread that owns each connected slot's
    receiver (queued connection), so GUI widgets can connect safely
    even though events originate from the background runtime thread.
    """

    event = Signal(object)  # payload type: Event

    def publish(self, event_type: str, source: str, payload: Optional[dict[str, Any]] = None,
                severity: str = "info") -> None:
        evt = Event(type=event_type, source=source, payload=payload or {}, severity=severity)
        self.event.emit(evt)


# --------------------------------------------------------------------------
# Runtime controller -- owns the orchestration pipeline on a background
# thread with its own asyncio event loop, so the GUI thread never blocks.
# --------------------------------------------------------------------------

class RuntimeController(QObject):
    """
    Initializes IntentEngine / PlanningEngine / VerificationEngine /
    PlanExecutor / ScrRuntimeAdapter exactly once and keeps them alive
    for the process lifetime. Runs its own asyncio loop on a dedicated
    background thread; the GUI thread only ever calls submit_goal(),
    never awaits anything itself.
    """

    started = Signal()
    start_failed = Signal(str)
    goal_finished = Signal(str)  # goal_id

    def __init__(self, event_bus: EventBus, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._bus = event_bus
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()

        self.intent_engine = IntentEngine()
        self.planning_engine = PlanningEngine()
        self.verification_engine = VerificationEngine()
        self.scr_adapter = ScrRuntimeAdapter()
        self.plan_executor = PlanExecutor(self.scr_adapter, on_event=self._on_executor_event)

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        """Starts the background asyncio loop and SCR Runtime. Non-blocking."""
        self._thread = threading.Thread(target=self._run_loop, name="aios-runtime", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=10)
        if self._loop is None:
            self.start_failed.emit("Runtime event loop failed to start")
            return
        future = asyncio.run_coroutine_threadsafe(self._async_start(), self._loop)
        future.add_done_callback(self._handle_start_result)

    def shutdown(self) -> None:
        """Stops SCR Runtime and the background loop. Blocks briefly."""
        if self._loop is None:
            return
        future = asyncio.run_coroutine_threadsafe(self.scr_adapter.shutdown(), self._loop)
        try:
            future.result(timeout=8)
        except Exception as exc:  # noqa: BLE001 -- shutdown must never raise into caller
            log.warning("Error during SCR Runtime shutdown: %s", exc)
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=5)

    def submit_goal(self, goal_text: str) -> str:
        """
        Schedules a full Intent -> Plan -> Execute -> Verify run for the
        given natural-language goal. Returns a goal_id immediately; the
        GUI receives progress exclusively through EventBus events and
        the goal_finished signal.
        """
        goal_id = uuid.uuid4().hex[:8]
        if self._loop is None:
            self._bus.publish("Error", "runtime", {"goal_id": goal_id, "message": "Runtime not started"},
                               severity="error")
            return goal_id
        asyncio.run_coroutine_threadsafe(self._run_goal(goal_id, goal_text), self._loop)
        return goal_id

    # -- background-thread internals ---------------------------------------

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()

    async def _async_start(self) -> None:
        await self.scr_adapter.start()

    def _handle_start_result(self, future: "asyncio.Future[None]") -> None:
        exc = future.exception()
        if exc is not None:
            log.error("SCR Runtime failed to start: %s", exc)
            self._bus.publish("Error", "runtime", {"message": str(exc)}, severity="error")
            self.start_failed.emit(str(exc))
        else:
            log.info("SCR Runtime started")
            self._bus.publish("RuntimeStarted", "runtime", {})
            self.started.emit()

    async def _run_goal(self, goal_id: str, goal_text: str) -> None:
        try:
            intent = self.intent_engine.parse(goal_text)
            self._bus.publish("IntentCreated", "intent_engine", {
                "goal_id": goal_id,
                "goal": intent.goal,
                "domain": intent.domain.value,
                "confidence": intent.confidence,
                "requires_approval": intent.requires_approval,
            })

            plan = self.planning_engine.create_plan(intent)
            self._bus.publish("PlanCreated", "planning_engine", {
                "goal_id": goal_id,
                "step_count": len(plan.steps),
                "steps": [
                    {"id": s.id, "description": s.description, "plugin": s.plugin, "action": s.action}
                    for s in plan.steps
                ],
                "risk_level": plan.risk_level.value,
            })

            results = await self.plan_executor.execute(plan)

            for step, result in zip(plan.steps, results):
                verification = self.verification_engine.verify(result, expected={"exitCode": 0}, step=step)
                self._bus.publish(
                    "VerificationStarted", "verification_engine",
                    {"goal_id": goal_id, "step_id": step.id},
                )
                self._bus.publish(
                    "VerificationFinished", "verification_engine",
                    {
                        "goal_id": goal_id,
                        "step_id": step.id,
                        "success": verification.success,
                        "confidence": verification.confidence,
                        "failures": verification.failures,
                        "data": result.data if isinstance(result.data, dict) else None,
                        "error": result.error,
                    },
                )
        except Exception as exc:  # noqa: BLE001 -- surface to GUI instead of crashing the thread
            log.exception("Unhandled error while running goal %s", goal_id)
            self._bus.publish("Error", "runtime", {"goal_id": goal_id, "message": str(exc)}, severity="error")
        finally:
            self.goal_finished.emit(goal_id)

    def _on_executor_event(self, evt: Event) -> None:
        self._bus.publish(evt.type, evt.source, evt.payload, severity=evt.severity)


# --------------------------------------------------------------------------
# Bubble widget
# --------------------------------------------------------------------------

class BubbleState:
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"


_STATE_COLORS = {
    BubbleState.IDLE: QColor(90, 100, 240),
    BubbleState.THINKING: QColor(240, 190, 60),
    BubbleState.EXECUTING: QColor(60, 200, 220),
    BubbleState.SUCCESS: QColor(60, 200, 120),
    BubbleState.ERROR: QColor(230, 70, 70),
}

_DRAG_THRESHOLD_PX = 6


class BubbleWidget(QWidget):
    """
    Frameless, translucent, always-on-top floating bubble. Draggable
    with edge snapping, a color-coded state glow, and a soft pulsing
    animation while thinking/executing.

    True OS-compositor acrylic/blur-behind is not implemented here (Qt
    has no cross-platform API for it); the "glass" look is approximated
    with a translucent radial-style gradient fill, which is fully
    functional as written, just not a literal blur of what's behind it.
    """

    clicked = Signal()
    moved = Signal(int, int)

    SIZE = 64

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.SIZE, self.SIZE)

        self._state = BubbleState.IDLE
        self._glow = 0.55
        self._badge_count = 0
        self._drag_origin: Optional[QPoint] = None
        self._press_pos: Optional[QPoint] = None
        self._dragging = False

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        self._pulse = QPropertyAnimation(self, b"glow", self)
        self._pulse.setDuration(1100)
        self._pulse.setStartValue(0.35)
        self._pulse.setKeyValueAt(0.5, 1.0)
        self._pulse.setEndValue(0.35)
        self._pulse.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse.setLoopCount(-1)

    # -- animated "glow" property -------------------------------------------

    def _get_glow(self) -> float:
        return self._glow

    def _set_glow(self, value: float) -> None:
        self._glow = value
        self.update()

    glow = Property(float, _get_glow, _set_glow)

    # -- public API ----------------------------------------------------------

    def set_state(self, state: str) -> None:
        self._state = state
        if state in (BubbleState.THINKING, BubbleState.EXECUTING):
            if self._pulse.state() != QPropertyAnimation.Running:
                self._pulse.start()
        else:
            self._pulse.stop()
            self._glow = 0.55
        self.update()

    def set_badge(self, count: int) -> None:
        self._badge_count = count
        self.update()

    # -- painting --------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(4, 4, -4, -4)
        path = QPainterPath()
        path.addEllipse(rect)

        base_color = _STATE_COLORS[self._state]
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(255, 255, 255, 40))
        gradient.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 150))
        painter.fillPath(path, QBrush(gradient))

        glow_alpha = int(60 + self._glow * 120)
        glow_pen = QPen(QColor(base_color.red(), base_color.green(), base_color.blue(), glow_alpha))
        glow_pen.setWidth(3)
        painter.setPen(glow_pen)
        painter.drawPath(path)

        if self._badge_count > 0:
            badge_rect = QRect(rect.right() - 20, rect.top() - 2, 20, 20)
            painter.setBrush(QBrush(QColor(230, 70, 70)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(badge_rect)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(badge_rect, Qt.AlignCenter, str(min(self._badge_count, 9)))

        painter.end()

    # -- drag + click handling --------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self.pos()
            self._press_pos = event.globalPosition().toPoint()
            self._dragging = False
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is None:
            return
        current = event.globalPosition().toPoint()
        if self._press_pos is not None and (current - self._press_pos).manhattanLength() > _DRAG_THRESHOLD_PX:
            self._dragging = True
        if self._dragging:
            new_pos = current - self._drag_origin
            self.move(new_pos)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._snap_to_edge()
                self.moved.emit(self.x(), self.y())
            else:
                self.clicked.emit()
        self._drag_origin = None
        self._press_pos = None
        self._dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def _snap_to_edge(self) -> None:
        screen = QGuiApplication.screenAt(self.geometry().center()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        margin = 12
        x, y = self.x(), self.y()

        target_x = x
        if x < area.left() + margin + self.SIZE:
            target_x = area.left() + margin
        elif x > area.right() - margin - self.SIZE:
            target_x = area.right() - margin - self.SIZE

        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(self.pos())
        anim.setEndValue(QPoint(target_x, y))
        anim.start()
        self._edge_anim = anim  # keep a reference so it isn't garbage-collected mid-flight

    def _show_context_menu(self, global_pos: QPoint) -> None:
        menu = QMenu()
        open_action = menu.addAction("Open Workspace")
        hide_action = menu.addAction("Hide Bubble")
        quit_action = menu.addAction("Quit AIOS")
        chosen = menu.exec(global_pos)
        if chosen == open_action:
            self.clicked.emit()
        elif chosen == hide_action:
            self.hide()
        elif chosen == quit_action:
            QApplication.instance().quit()


# --------------------------------------------------------------------------
# Workspace window
# --------------------------------------------------------------------------

_WORKSPACE_STYLESHEET = """
QWidget#workspaceRoot {
    background-color: #14151a;
    border-radius: 14px;
}
QFrame#topBar, QFrame#bottomBar {
    background-color: #191a20;
    border-radius: 10px;
}
QLabel#logo {
    color: #8f8fff;
    font-size: 15px;
    font-weight: 600;
}
QLabel#title {
    color: #e6e6ef;
    font-size: 13px;
}
QLabel#status {
    color: #8a8a95;
    font-size: 11px;
}
QPushButton {
    background-color: #23242c;
    color: #e6e6ef;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #2d2f3a;
}
QPushButton#runButton {
    background-color: #5a64f0;
    font-weight: 600;
}
QPushButton#runButton:hover {
    background-color: #6d76f5;
}
QLineEdit {
    background-color: #1d1e25;
    color: #e6e6ef;
    border: 1px solid #2b2c36;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 13px;
}
QTextEdit, QListWidget {
    background-color: #17181d;
    color: #d6d6de;
    border: 1px solid #23242c;
    border-radius: 10px;
    font-size: 12px;
}
QLabel#sidebarHeader {
    color: #8f8fff;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 2px;
}
"""


class WorkspaceWindow(QWidget):
    """
    The expanded desktop workspace: streaming conversation in the
    middle, prompt input at the bottom, and a right sidebar reflecting
    Intent / Execution Plan / Running Tasks / Logs / Verification --
    all driven purely by EventBus events, never polled.
    """

    goal_submitted = Signal(str)
    closed = Signal()

    def __init__(self, config: AiosConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(760, 520)
        self.resize(config.workspace_width, config.workspace_height)
        self.move(config.workspace_x, config.workspace_y)

        self._drag_origin: Optional[QPoint] = None
        self._build_ui()
        self._current_status = "Idle"

    # -- UI construction -----------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("workspaceRoot")
        root.setStyleSheet(_WORKSPACE_STYLESHEET)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 180))
        root.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        main_layout.addWidget(self._build_top_bar())

        body = QSplitter(Qt.Horizontal)
        body.setChildrenCollapsible(False)
        body.setHandleWidth(8)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)
        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        center_layout.addWidget(self.conversation, stretch=1)
        center_layout.addWidget(self._build_bottom_bar())

        body.addWidget(center)
        body.addWidget(self._build_sidebar())
        body.setStretchFactor(0, 3)
        body.setStretchFactor(1, 1)

        main_layout.addWidget(body, stretch=1)

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 6, 10, 6)

        logo = QLabel("AIOS")
        logo.setObjectName("logo")
        self.title_label = QLabel("New Conversation")
        self.title_label.setObjectName("title")
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("status")

        settings_btn = QPushButton("Settings")
        minimize_btn = QPushButton("—")
        minimize_btn.setFixedWidth(32)
        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(32)
        minimize_btn.clicked.connect(self.hide)
        close_btn.clicked.connect(self.close)

        layout.addWidget(logo)
        layout.addSpacing(12)
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.status_label)
        layout.addSpacing(10)
        layout.addWidget(settings_btn)
        layout.addWidget(minimize_btn)
        layout.addWidget(close_btn)

        bar.installEventFilter(self)
        self._top_bar = bar
        return bar

    def _build_bottom_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("bottomBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)

        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Ask AIOS to do something...")
        self.prompt_input.setText(self._config.last_goal)
        self.prompt_input.returnPressed.connect(self._submit)

        attach_btn = QPushButton("📎")
        attach_btn.setFixedWidth(36)
        voice_btn = QPushButton("🎙")
        voice_btn.setFixedWidth(36)
        run_btn = QPushButton("Run")
        run_btn.setObjectName("runButton")
        run_btn.clicked.connect(self._submit)

        layout.addWidget(attach_btn)
        layout.addWidget(voice_btn)
        layout.addWidget(self.prompt_input, stretch=1)
        layout.addWidget(run_btn)
        return bar

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setMinimumWidth(260)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        def section(title: str) -> QListWidget:
            header = QLabel(title)
            header.setObjectName("sidebarHeader")
            layout.addWidget(header)
            listw = QListWidget()
            listw.setMaximumHeight(120)
            layout.addWidget(listw)
            return listw

        self.intent_list = section("Intent")
        self.plan_list = section("Execution Plan")
        self.tasks_list = section("Running Tasks")
        self.verification_list = section("Verification")
        self.logs_list = section("Logs")
        layout.addStretch(1)
        return sidebar

    # -- dragging the frameless window via its top bar ------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._top_bar:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag_origin = event.globalPosition().toPoint() - self.pos()
            elif event.type() == QEvent.MouseMove and self._drag_origin is not None:
                self.move(event.globalPosition().toPoint() - self._drag_origin)
            elif event.type() == QEvent.MouseButtonRelease:
                self._drag_origin = None
        return super().eventFilter(obj, event)

    # -- public API used by AiosApplication ------------------------------------

    def append_message(self, text: str, role: str = "system") -> None:
        color = {"user": "#8f8fff", "assistant": "#d6d6de", "system": "#8a8a95", "error": "#e64646"}.get(
            role, "#d6d6de"
        )
        self.conversation.append(f'<span style="color:{color};">[{role}]</span> {text}')

    def set_status(self, text: str) -> None:
        self._current_status = text
        self.status_label.setText(text)

    def set_intent(self, intent_payload: dict[str, Any]) -> None:
        self.intent_list.clear()
        for key in ("goal", "domain", "confidence", "requires_approval"):
            if key in intent_payload:
                self.intent_list.addItem(QListWidgetItem(f"{key}: {intent_payload[key]}"))

    def set_plan(self, plan_payload: dict[str, Any]) -> None:
        self.plan_list.clear()
        for step in plan_payload.get("steps", []):
            self.plan_list.addItem(
                QListWidgetItem(f"[{step['plugin']}] {step['description']}")
            )

    def add_running_task(self, description: str) -> None:
        self.tasks_list.addItem(QListWidgetItem(description))

    def clear_running_tasks(self) -> None:
        self.tasks_list.clear()

    def add_verification(self, text: str, ok: bool) -> None:
        item = QListWidgetItem(("✓ " if ok else "✗ ") + text)
        self.verification_list.addItem(item)

    def add_log(self, text: str) -> None:
        self.logs_list.addItem(QListWidgetItem(text))
        self.logs_list.scrollToBottom()

    # -- Qt overrides -----------------------------------------------------------

    def _submit(self) -> None:
        text = self.prompt_input.text().strip()
        if not text:
            return
        self._config.last_goal = text
        self._config.save()
        self.append_message(text, role="user")
        self.goal_submitted.emit(text)

    def closeEvent(self, event: QEvent) -> None:
        # Closing the workspace never terminates AIOS -- it minimizes to
        # the bubble/tray, matching the tray menu's "Hide" semantics.
        self._config.workspace_width = self.width()
        self._config.workspace_height = self.height()
        self._config.workspace_x = self.x()
        self._config.workspace_y = self.y()
        self._config.save()
        event.ignore()
        self.hide()
        self.closed.emit()


# --------------------------------------------------------------------------
# Application orchestration
# --------------------------------------------------------------------------

class AiosApplication(QObject):
    """
    Composition root. Owns the config, event bus, runtime controller,
    bubble, workspace, and tray icon, and wires them together. No
    business logic lives here -- only connections between the pieces
    above.
    """

    def __init__(self) -> None:
        super().__init__()
        self.config = AiosConfig.load()
        self.bus = EventBus()
        self.runtime = RuntimeController(self.bus)

        self.bubble = BubbleWidget()
        self.bubble.move(self.config.bubble_x, self.config.bubble_y)
        self.workspace = WorkspaceWindow(self.config)
        self.tray = self._build_tray()

        self._active_goal_id: Optional[str] = None
        self._pending_notifications = 0

        self._wire_signals()

    # -- construction ------------------------------------------------------

    def _build_tray(self) -> QSystemTrayIcon:
        icon = self._make_tray_icon()
        tray = QSystemTrayIcon(icon)
        tray.setToolTip("AIOS")

        menu = QMenu()
        open_action = QAction("Open Workspace", menu)
        hide_action = QAction("Hide Bubble", menu)
        settings_action = QAction("Settings", menu)
        restart_action = QAction("Restart Runtime", menu)
        quit_action = QAction("Quit", menu)

        open_action.triggered.connect(self.show_workspace)
        hide_action.triggered.connect(self.bubble.hide)
        settings_action.triggered.connect(self.show_workspace)
        restart_action.triggered.connect(self._restart_runtime)
        quit_action.triggered.connect(self.quit)

        menu.addAction(open_action)
        menu.addAction(hide_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(restart_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    @staticmethod
    def _make_tray_icon() -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(90, 100, 240)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        return QIcon(pixmap)

    # -- wiring ------------------------------------------------------------

    def _wire_signals(self) -> None:
        self.bubble.clicked.connect(self.show_workspace)
        self.bubble.moved.connect(self._on_bubble_moved)

        self.workspace.goal_submitted.connect(self._on_goal_submitted)
        self.workspace.closed.connect(self._on_workspace_closed)

        self.runtime.started.connect(self._on_runtime_started)
        self.runtime.start_failed.connect(self._on_runtime_start_failed)
        self.runtime.goal_finished.connect(self._on_goal_finished)

        self.bus.event.connect(self._on_event)

    # -- bubble / workspace / tray behavior --------------------------------

    def show_workspace(self) -> None:
        self.workspace.show()
        self.workspace.raise_()
        self.workspace.activateWindow()
        self._pending_notifications = 0
        self.bubble.set_badge(0)
        self.bus.publish("WorkspaceOpened", "gui", {})

    def _on_bubble_moved(self, x: int, y: int) -> None:
        self.config.bubble_x = x
        self.config.bubble_y = y
        self.config.save()
        self.bus.publish("BubbleMoved", "gui", {"x": x, "y": y})

    def _on_workspace_closed(self) -> None:
        self.bus.publish("WorkspaceClosed", "gui", {})

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_workspace()

    def _restart_runtime(self) -> None:
        self.workspace.append_message("Restarting SCR Runtime...", role="system")
        self.bubble.set_state(BubbleState.THINKING)
        self.runtime.shutdown()
        self.runtime.start()

    def quit(self) -> None:
        self.config.bubble_x, self.config.bubble_y = self.bubble.x(), self.bubble.y()
        self.config.save()
        self.runtime.shutdown()
        QApplication.instance().quit()

    # -- runtime lifecycle callbacks (delivered via Qt signals, GUI thread) --

    def _on_runtime_started(self) -> None:
        self.bubble.set_state(BubbleState.IDLE)
        self.workspace.set_status("Ready")
        self.workspace.append_message("SCR Runtime is ready.", role="system")

    def _on_runtime_start_failed(self, message: str) -> None:
        self.bubble.set_state(BubbleState.ERROR)
        self.workspace.set_status("Runtime unavailable")
        self.workspace.append_message(f"SCR Runtime failed to start: {message}", role="error")

    def _on_goal_submitted(self, goal_text: str) -> None:
        self.bubble.set_state(BubbleState.THINKING)
        self.workspace.set_status("Thinking...")
        self.workspace.clear_running_tasks()
        self._active_goal_id = self.runtime.submit_goal(goal_text)

    def _on_goal_finished(self, goal_id: str) -> None:
        self.bubble.set_state(BubbleState.IDLE)
        self.workspace.set_status("Ready")
        if not self.workspace.isVisible():
            self._pending_notifications += 1
            self.bubble.set_badge(self._pending_notifications)

    # -- event bus -> UI updates ---------------------------------------------

    def _on_event(self, evt: Event) -> None:
        self.workspace.add_log(f"{evt.timestamp:%H:%M:%S} [{evt.source}] {evt.type}")

        if evt.type == "IntentCreated":
            self.workspace.set_intent(evt.payload)
        elif evt.type == "PlanCreated":
            self.workspace.set_plan(evt.payload)
        elif evt.type == "ExecutionStarted":
            self.bubble.set_state(BubbleState.EXECUTING)
            self.workspace.set_status("Executing...")
        elif evt.type == "ExecutionProgress":
            self.workspace.add_running_task(
                f"{evt.payload.get('description', evt.payload.get('step_id'))} -> {evt.payload.get('status')}"
            )
        elif evt.type == "ExecutionFinished":
            failed = evt.payload.get("failed", 0)
            self.bubble.set_state(BubbleState.ERROR if failed else BubbleState.SUCCESS)
        elif evt.type == "VerificationFinished":
            ok = bool(evt.payload.get("success"))
            data = evt.payload.get("data") or {}
            summary = data.get("stdout", evt.payload.get("error", "")) or evt.payload.get("error", "")
            self.workspace.add_verification(str(summary).strip()[:200], ok)
            role = "assistant" if ok else "error"
            self.workspace.append_message(str(summary).strip() or "(no output)", role=role)
        elif evt.type == "Error":
            self.bubble.set_state(BubbleState.ERROR)
            self.workspace.append_message(evt.payload.get("message", "Unknown error"), role="error")


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    aios = AiosApplication()
    aios.bubble.show()
    aios.runtime.start()

    exit_code = app.exec()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
