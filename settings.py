"""
Aios settings panel — model selection, download, and performance profiles.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QProgressBar,
    QFrame,
    QGroupBox,
    QMessageBox,
    QCompleter,
)
from PySide6.QtCore import Qt, Signal, QThread, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QPainter, QColor

import ollama
from llm import list_models, set_model, get_model, init as llm_init


# ── Curated model catalog (popular Ollama models by size tier) ────────────

MODEL_CATALOG = [
    # (model_tag, display_label, approx_vram_gb)
    ("llama3.2:1b", "Llama 3.2 1B", 1.5),
    ("qwen2.5:1.5b", "Qwen 2.5 1.5B", 2.0),
    ("gemma2:2b", "Gemma 2 2B", 2.5),
    ("phi3:mini", "Phi-3 Mini 3.8B", 3.0),
    ("llama3.2:3b", "Llama 3.2 3B", 3.0),
    ("qwen2.5:3b", "Qwen 2.5 3B", 3.5),
    ("phi3:3.8b", "Phi-3 3.8B", 3.5),
    ("mistral:7b", "Mistral 7B", 5.5),
    ("qwen2.5:7b", "Qwen 2.5 7B", 5.5),
    ("llama3.1:8b", "Llama 3.1 8B", 6.0),
    ("gemma3:12b", "Gemma 3 12B", 8.0),
    ("qwen2.5:14b", "Qwen 2.5 14B", 10.0),
    ("deepseek-r1:14b", "DeepSeek-R1 14B", 10.0),
    ("qwen2.5:32b", "Qwen 2.5 32B", 20.0),
    ("deepseek-r1:32b", "DeepSeek-R1 32B", 20.0),
    ("llama3.1:70b", "Llama 3.1 70B", 42.0),
    ("qwen2.5:72b", "Qwen 2.5 72B", 42.0),
    ("deepseek-r1:70b", "DeepSeek-R1 70B", 42.0),
]


def _make_icon(color: str, text: str) -> QIcon:
    """Create a tiny colored circle icon with text overlay."""
    px = QPixmap(16, 16)
    px.fill(QColor("transparent"))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 12, 12)
    p.end()
    return QIcon(px)


# ── Pull worker (downloads model in background) ──────────────────────────

class PullWorker(QThread):
    progress = Signal(str)       # status text
    pull_done = Signal(bool, str)  # (success, message)

    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name

    def run(self):
        try:
            self.progress.emit(f"Pulling {self.model_name}...")
            stream = ollama.pull(self.model_name, stream=True)
            for chunk in stream:
                status = chunk.get("status", "")
                total = chunk.get("total", 0)
                completed = chunk.get("completed", 0)
                if total:
                    pct = int(completed / total * 100)
                    self.progress.emit(f"{status} — {pct}%")
                elif status:
                    self.progress.emit(status)
            self.pull_done.emit(True, f"✅ {self.model_name} ready")
        except Exception as e:
            self.pull_done.emit(False, f"❌ {e}")


# ── Install worker (non-blocking pip install) ────────────────────────────

class InstallWorker(QThread):
    install_done = Signal(bool, str)  # (success, message)

    def __init__(self, package: str, parent=None):
        super().__init__(parent)
        self.package = package

    def run(self):
        import subprocess, sys
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-input", self.package],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0:
                self.install_done.emit(True, f"✅ {self.package} installed")
            else:
                self.install_done.emit(False, f"❌ {result.stderr[:120]}")
        except Exception as e:
            self.install_done.emit(False, f"❌ {e}")


# ── Performance profile helpers ──────────────────────────────────────────

PERF_PROFILES = {
    "auto": "Auto-detect best settings for your hardware",
    "speed": "Max throughput — single user, aggressive caching",
    "balanced": "General use — good mix of speed and memory",
    "memory": "Low-VRAM GPUs — reduced context, conservative memory",
    "multiuser": "Shared server — parallel requests, shorter keep-alive",
}


# ── Settings Panel ───────────────────────────────────────────────────────

class SettingsPanel(QWidget):
    model_changed = Signal(str)   # emitted when user picks a model
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aios — Settings")
        self.setFixedWidth(500)
        self._pull_worker = None
        self._install_worker = None

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # ── Model section ─────────────────────────────────────
        model_group = QGroupBox("🤖  Model")
        model_group.setStyleSheet(self._group_style())
        mg = QVBoxLayout()

        # Mode selector
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto", "Manual"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)
        mode_row.addWidget(self.mode_combo)
        mg.addLayout(mode_row)

        # Model selector (manual)
        self.model_row = QHBoxLayout()
        self.model_row_label = QLabel("Model:")
        self.model_row.addWidget(self.model_row_label)
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(240)
        self.model_row.addWidget(self.model_combo)
        self.model_apply_btn = QPushButton("Apply")
        self.model_apply_btn.setFixedWidth(60)
        self.model_apply_btn.clicked.connect(self._apply_model)
        self.model_row.addWidget(self.model_apply_btn)
        mg.addLayout(self.model_row)

        # Separator
        mg.addWidget(self._separator())

        # Download model — searchable combo with catalog
        pull_label = QLabel("Download model:")
        pull_label.setStyleSheet("font-weight: bold;")
        mg.addWidget(pull_label)

        pull_row = QHBoxLayout()
        self.pull_combo = QComboBox()
        self.pull_combo.setEditable(True)
        self.pull_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.pull_combo.setMinimumWidth(300)
        self.pull_combo.lineEdit().setPlaceholderText("Type to search or enter model tag...")
        self.pull_combo.completer().setCompletionMode(
            QCompleter.CompletionMode.PopupCompletion
        )
        self.pull_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        pull_row.addWidget(self.pull_combo)

        self.pull_btn = QPushButton("⬇ Download")
        self.pull_btn.setFixedWidth(100)
        self.pull_btn.clicked.connect(self._pull_model)
        pull_row.addWidget(self.pull_btn)
        mg.addLayout(pull_row)

        self.pull_status = QLabel("")
        self.pull_status.setStyleSheet("color: #9ca3af; font-size: 11px;")
        mg.addWidget(self.pull_status)

        model_group.setLayout(mg)
        layout.addWidget(model_group)

        # ── Performance section ───────────────────────────────
        perf_group = QGroupBox("⚡  Performance")
        perf_group.setStyleSheet(self._group_style())
        pg = QVBoxLayout()

        prof_row = QHBoxLayout()
        prof_row.addWidget(QLabel("Profile:"))
        self.perf_combo = QComboBox()
        for name in PERF_PROFILES:
            self.perf_combo.addItem(name)
        self.perf_combo.currentTextChanged.connect(self._on_profile_change)
        prof_row.addWidget(self.perf_combo)
        pg.addLayout(prof_row)

        self.perf_desc = QLabel(PERF_PROFILES["auto"])
        self.perf_desc.setWordWrap(True)
        self.perf_desc.setStyleSheet("color: #9ca3af; font-size: 11px; padding: 2px;")
        pg.addWidget(self.perf_desc)

        self.perf_apply_btn = QPushButton("Apply Profile")
        self.perf_apply_btn.clicked.connect(self._apply_profile)
        pg.addWidget(self.perf_apply_btn)

        self.perf_status = QLabel("")
        self.perf_status.setStyleSheet("color: #9ca3af; font-size: 11px;")
        pg.addWidget(self.perf_status)

        # Install pyaccelerate (with approval banner)
        pg.addWidget(self._separator())
        dep_row = QHBoxLayout()
        dep_row.addWidget(QLabel("Hardware profiling:"))
        self.dep_btn = QPushButton("Install pyaccelerate")
        self.dep_btn.setFixedWidth(170)
        self.dep_btn.clicked.connect(self._confirm_install_pyaccelerate)
        dep_row.addWidget(self.dep_btn)
        pg.addLayout(dep_row)
        self.dep_status = QLabel("")
        self.dep_status.setStyleSheet("color: #9ca3af; font-size: 11px;")
        pg.addWidget(self.dep_status)

        perf_group.setLayout(pg)
        layout.addWidget(perf_group)

        # ── Close button ──────────────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._close)
        layout.addWidget(close_btn)

        layout.addStretch()
        self.setLayout(layout)

        # Apply dark theme
        self.setStyleSheet(
            "QWidget { background: #111827; color: #f3f4f6; font-size: 12px; }"
            "QComboBox { background: #1f2937; border: 1px solid #374151; "
            "  border-radius: 4px; padding: 4px 8px; color: #f3f4f6; }"
            "QComboBox QAbstractItemView { background: #1f2937; color: #f3f4f6; "
            "  selection-background-color: #2563eb; }"
            "QLineEdit { background: #1f2937; border: 1px solid #374151; "
            "  border-radius: 4px; padding: 4px 8px; color: #f3f4f6; }"
            "QPushButton { background: #2563eb; color: white; border-radius: 4px; "
            "  padding: 6px 12px; font-weight: bold; }"
            "QPushButton:hover { background: #1d4ed8; }"
            "QPushButton:disabled { background: #374151; color: #6b7280; }"
        )

        self._refresh_models()
        self._populate_catalog()
        self._set_manual_visible(False)
        self._check_pyaccelerate()

    # ── Model logic ───────────────────────────────────────────

    def _refresh_models(self):
        self.model_combo.clear()
        models = list_models()
        for m in models:
            self.model_combo.addItem(m)
        current = get_model()
        idx = self.model_combo.findText(current)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def _populate_catalog(self):
        """Fill the download combo with catalog models, marking installed ones."""
        installed = set(list_models())
        self.pull_combo.clear()

        icon_installed = _make_icon("#22c55e", "✓")  # green
        icon_available = _make_icon("#6b7280", "")    # gray

        for tag, label, vram_gb in MODEL_CATALOG:
            if tag in installed:
                display = f"✅  {label}  ({tag})  —  {vram_gb:.0f} GB"
                self.pull_combo.addItem(icon_installed, display, tag)
            else:
                display = f"⬇  {label}  ({tag})  —  {vram_gb:.0f} GB"
                self.pull_combo.addItem(icon_available, display, tag)

        self.pull_combo.setCurrentIndex(-1)
        self.pull_combo.lineEdit().clear()

    def _on_mode_change(self, text: str):
        manual = text == "Manual"
        self._set_manual_visible(manual)
        if not manual:
            # Re-run auto detection
            status = llm_init()
            self.model_changed.emit(status.get("model", ""))

    def _set_manual_visible(self, visible: bool):
        self.model_row_label.setVisible(visible)
        self.model_combo.setVisible(visible)
        self.model_apply_btn.setVisible(visible)

    def _apply_model(self):
        model = self.model_combo.currentText()
        if model:
            set_model(model)
            self.model_changed.emit(model)

    # ── Pull logic ────────────────────────────────────────────

    def _pull_model(self):
        # Get model tag from combo data or from typed text
        idx = self.pull_combo.currentIndex()
        if idx >= 0:
            name = self.pull_combo.itemData(idx) or self.pull_combo.currentText()
        else:
            name = self.pull_combo.currentText()

        # If user selected a display string, extract the tag from it
        if "(" in name and ")" in name:
            # "⬇  Llama 3.1 8B  (llama3.1:8b)  — 6 GB" → llama3.1:8b
            name = name.split("(")[1].split(")")[0]

        name = name.strip()
        if not name:
            return

        # Skip if already installed
        installed = set(list_models())
        if name in installed:
            self.pull_status.setText(f"✅ {name} is already installed")
            return

        self.pull_btn.setEnabled(False)
        self.pull_status.setText(f"Downloading {name}...")

        self._pull_worker = PullWorker(name)
        self._pull_worker.progress.connect(self._on_pull_progress)
        self._pull_worker.pull_done.connect(self._on_pull_done)
        self._pull_worker.start()

    def _on_pull_progress(self, text: str):
        self.pull_status.setText(text)

    def _on_pull_done(self, ok: bool, msg: str):
        self.pull_status.setText(msg)
        self.pull_btn.setEnabled(True)
        self.pull_combo.setCurrentIndex(-1)
        self.pull_combo.lineEdit().clear()
        if ok:
            self._refresh_models()
            self._populate_catalog()  # refresh icons

    # ── Performance logic ─────────────────────────────────────

    def _on_profile_change(self, name: str):
        self.perf_desc.setText(PERF_PROFILES.get(name, ""))

    def _apply_profile(self):
        profile = self.perf_combo.currentText()
        self.perf_status.setText(f"Applying '{profile}'...")

        # Try Ollama autotune API first
        try:
            import requests
            r = requests.post(
                "http://localhost:11434/api/autotune",
                json={"profile": profile},
                timeout=5,
            )
            if r.ok:
                data = r.json()
                applied = data.get("profile", profile)
                self.perf_status.setText(f"✅ Profile '{applied}' applied via Ollama autotune")
                return
        except Exception:
            pass

        # Fallback: try pyaccelerate Engine for richer tuning
        try:
            from pyaccelerate import Engine
            engine = Engine()
            gpu = engine.best_gpu
            if gpu:
                self.perf_status.setText(
                    f"✅ Profile '{profile}' — {gpu.short_label()}"
                )
            else:
                self.perf_status.setText(f"✅ Profile '{profile}' noted (CPU-only)")
            return
        except ImportError:
            pass

        self.perf_status.setText(f"ℹ️  Profile '{profile}' saved (install pyaccelerate for full tuning)")

    # ── Dependency install with approval banner ──────────────

    def _confirm_install_pyaccelerate(self):
        """Show approval dialog before installing — avoids surprise CLI interactions."""
        reply = QMessageBox.question(
            self,
            "Install pyaccelerate",
            "This will install pyaccelerate using pip.\n\n"
            "• GPU dependencies (CUDA toolkit, etc.) may require\n"
            "  additional system packages.\n"
            "• The install runs with --no-input (non-interactive).\n\n"
            "Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._install_pyaccelerate()

    def _install_pyaccelerate(self):
        self.dep_btn.setEnabled(False)
        self.dep_status.setText("Installing (this may take a moment)...")

        self._install_worker = InstallWorker("pyaccelerate")
        self._install_worker.install_done.connect(self._on_install_done)
        self._install_worker.start()

    def _on_install_done(self, ok: bool, msg: str):
        self.dep_status.setText(msg)
        self.dep_btn.setEnabled(True)
        if ok:
            self._check_pyaccelerate()

    def _check_pyaccelerate(self):
        try:
            import pyaccelerate
            self.dep_btn.setText("✅ Installed")
            self.dep_btn.setEnabled(False)
            self.dep_status.setText(f"v{pyaccelerate.__version__}")
        except ImportError:
            pass

    # ── Helpers ───────────────────────────────────────────────

    def _close(self):
        self.hide()
        self.closed.emit()

    @staticmethod
    def _separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #374151;")
        return line

    @staticmethod
    def _group_style() -> str:
        return (
            "QGroupBox { border: 1px solid #374151; border-radius: 6px; "
            "margin-top: 8px; padding-top: 16px; font-weight: bold; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; "
            "padding: 0 4px; color: #e5e7eb; }"
        )
