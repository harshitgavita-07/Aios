"""
AIOS Workspace Manager — AI-Native Desktop Environment

The workspace where agents are the fundamental "applications" and workflows
are the primary interaction paradigm. This replaces traditional windows/apps
with an agent-centric interface.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSplitter, QListWidget,
    QListWidgetItem, QTextEdit, QProgressBar, QTabWidget,
    QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QAction

from runtime.aios_runtime import AIOSRuntime, Agent, Workflow, Intent

log = logging.getLogger("aios.workspace")


class AgentWidget(QFrame):
    """
    Visual representation of an AI agent in the workspace.
    """

    clicked = Signal(str)  # agent_id

    def __init__(self, agent: Agent):
        super().__init__()
        self.agent = agent
        self._setup_ui()

    def _setup_ui(self):
        """Setup the agent widget UI."""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)

        # Agent name
        name_label = QLabel(self.agent.name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(name_label)

        # Agent description
        desc_label = QLabel(self.agent.description)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Arial", 10))
        layout.addWidget(desc_label)

        # Status indicator
        self.status_label = QLabel(f"Status: {self.agent.state.value}")
        self.status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.status_label)

        # Capabilities
        caps_text = ", ".join(self.agent.capabilities)
        caps_label = QLabel(f"Capabilities: {caps_text}")
        caps_label.setWordWrap(True)
        caps_label.setFont(QFont("Arial", 8))
        layout.addWidget(caps_label)

        # Click handler
        self.mousePressEvent = self._on_click

        # Styling based on state
        self._update_styling()

    def _on_click(self, event):
        """Handle mouse click."""
        self.clicked.emit(self.agent.agent_id)

    def _update_styling(self):
        """Update visual styling based on agent state."""
        if self.agent.state.value == "ready":
            self.setStyleSheet("background-color: #e8f5e8; border: 2px solid #4caf50;")
        elif self.agent.state.value == "active":
            self.setStyleSheet("background-color: #fff3e0; border: 2px solid #ff9800;")
        elif self.agent.state.value == "busy":
            self.setStyleSheet("background-color: #fff8e1; border: 2px solid #ffc107;")
        elif self.agent.state.value == "error":
            self.setStyleSheet("background-color: #ffebee; border: 2px solid #f44336;")
        else:
            self.setStyleSheet("background-color: #f5f5f5; border: 2px solid #9e9e9e;")

    def update_agent(self, agent: Agent):
        """Update the widget with new agent data."""
        self.agent = agent
        self.status_label.setText(f"Status: {self.agent.state.value}")
        self._update_styling()


class WorkflowWidget(QFrame):
    """
    Visual representation of a workflow in the workspace.
    """

    clicked = Signal(str)  # workflow_id

    def __init__(self, workflow: Workflow):
        super().__init__()
        self.workflow = workflow
        self._setup_ui()

    def _setup_ui(self):
        """Setup the workflow widget UI."""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)

        # Workflow name
        name_label = QLabel(self.workflow.name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(name_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self._update_progress()
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel(f"Status: {self.workflow.state.value}")
        self.status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.status_label)

        # Current step
        self.step_label = QLabel(f"Step: {self.workflow.current_step}/{len(self.workflow.steps)}")
        self.step_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.step_label)

        # Click handler
        self.mousePressEvent = self._on_click

        # Styling
        self._update_styling()

    def _on_click(self, event):
        """Handle mouse click."""
        self.clicked.emit(self.workflow.workflow_id)

    def _update_progress(self):
        """Update progress bar."""
        if self.workflow.steps:
            progress = int((self.workflow.current_step / len(self.workflow.steps)) * 100)
        else:
            progress = 100 if self.workflow.state == "completed" else 0
        self.progress_bar.setValue(progress)

    def _update_styling(self):
        """Update visual styling based on workflow state."""
        if self.workflow.state == "running":
            self.setStyleSheet("background-color: #e3f2fd; border: 2px solid #2196f3;")
        elif self.workflow.state == "completed":
            self.setStyleSheet("background-color: #e8f5e8; border: 2px solid #4caf50;")
        elif self.workflow.state == "failed":
            self.setStyleSheet("background-color: #ffebee; border: 2px solid #f44336;")
        elif self.workflow.state == "paused":
            self.setStyleSheet("background-color: #fff3e0; border: 2px solid #ff9800;")
        else:
            self.setStyleSheet("background-color: #f5f5f5; border: 2px solid #9e9e9e;")

    def update_workflow(self, workflow: Workflow):
        """Update the widget with new workflow data."""
        self.workflow = workflow
        self.status_label.setText(f"Status: {self.workflow.state.value}")
        self.step_label.setText(f"Step: {self.workflow.current_step}/{len(self.workflow.steps)}")
        self._update_progress()
        self._update_styling()


class IntentPanel(QWidget):
    """
    Panel for displaying and interacting with user intents.
    """

    intent_selected = Signal(dict)  # intent data

    def __init__(self):
        super().__init__()
        self.intents: List[Dict[str, Any]] = []
        self._setup_ui()

    def _setup_ui(self):
        """Setup the intent panel UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Active Intents")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header)

        # Intent list
        self.intent_list = QListWidget()
        self.intent_list.itemClicked.connect(self._on_intent_clicked)
        layout.addWidget(self.intent_list)

        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_intents)
        layout.addWidget(clear_btn)

    def add_intent(self, intent_data: Dict[str, Any]):
        """Add a new intent to the panel."""
        self.intents.append(intent_data)

        intent_type = intent_data.get("intent_type", "unknown")
        description = intent_data.get("description", "")[:50]

        item_text = f"{intent_type}: {description}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, intent_data)
        self.intent_list.addItem(item)

    def clear_intents(self):
        """Clear all intents."""
        self.intents.clear()
        self.intent_list.clear()

    def _on_intent_clicked(self, item):
        """Handle intent selection."""
        intent_data = item.data(Qt.UserRole)
        self.intent_selected.emit(intent_data)


class ContextPanel(QWidget):
    """
    Panel displaying current runtime context and environment.
    """

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the context panel UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Runtime Context")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header)

        # Context info
        self.context_text = QTextEdit()
        self.context_text.setReadOnly(True)
        self.context_text.setMaximumHeight(200)
        layout.addWidget(self.context_text)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_context)
        layout.addWidget(refresh_btn)

    def update_context(self, context_data: Dict[str, Any]):
        """Update the context display."""
        context_str = "Current Runtime Context:\n\n"

        for key, value in context_data.items():
            if isinstance(value, list):
                context_str += f"{key}:\n"
                for item in value:
                    context_str += f"  - {item}\n"
            else:
                context_str += f"{key}: {value}\n"
            context_str += "\n"

        self.context_text.setPlainText(context_str)

    def _refresh_context(self):
        """Refresh context display."""
        # This would trigger a context update in the real implementation
        pass


class AIOSWorkspace(QWidget):
    """
    The main AI-native workspace where agents and workflows are the primary interface.
    """

    def __init__(self, runtime: AIOSRuntime):
        super().__init__()
        self.runtime = runtime
        self.agent_widgets: Dict[str, AgentWidget] = {}
        self.workflow_widgets: Dict[str, WorkflowWidget] = {}

        self._setup_ui()
        self._setup_system_tray()
        self._connect_signals()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_workspace)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _setup_ui(self):
        """Setup the main workspace UI."""
        self.setWindowTitle("AIOS — AI-Native Workspace")
        self.setGeometry(100, 100, 1400, 900)

        # Main layout
        main_layout = QHBoxLayout(self)

        # Left sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar, 1)

        # Main content area
        content_splitter = QSplitter(Qt.Vertical)

        # Top: Agents and Workflows
        agent_workflow_area = self._create_agent_workflow_area()
        content_splitter.addWidget(agent_workflow_area)

        # Bottom: Intent and Context panels
        bottom_splitter = QSplitter(Qt.Horizontal)

        self.intent_panel = IntentPanel()
        bottom_splitter.addWidget(self.intent_panel)

        self.context_panel = ContextPanel()
        bottom_splitter.addWidget(self.context_panel)

        content_splitter.addWidget(bottom_splitter)
        content_splitter.setSizes([600, 300])

        main_layout.addWidget(content_splitter, 4)

    def _create_sidebar(self) -> QWidget:
        """Create the sidebar with quick actions."""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)

        # Title
        title = QLabel("AIOS Runtime")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Quick actions
        actions_group = QFrame()
        actions_group.setFrameStyle(QFrame.Box)
        actions_layout = QVBoxLayout(actions_group)

        actions_title = QLabel("Quick Actions")
        actions_title.setFont(QFont("Arial", 12, QFont.Bold))
        actions_layout.addWidget(actions_title)

        # Action buttons
        create_agent_btn = QPushButton("Create Agent")
        create_agent_btn.clicked.connect(self._create_agent)
        actions_layout.addWidget(create_agent_btn)

        create_workflow_btn = QPushButton("Create Workflow")
        create_workflow_btn.clicked.connect(self._create_workflow)
        actions_layout.addWidget(create_workflow_btn)

        system_status_btn = QPushButton("System Status")
        system_status_btn.clicked.connect(self._show_system_status)
        actions_layout.addWidget(system_status_btn)

        layout.addWidget(actions_group)

        # System info
        system_group = QFrame()
        system_group.setFrameStyle(QFrame.Box)
        system_layout = QVBoxLayout(system_group)

        system_title = QLabel("System Info")
        system_title.setFont(QFont("Arial", 12, QFont.Bold))
        system_layout.addWidget(system_title)

        self.system_info_label = QLabel("Loading...")
        self.system_info_label.setWordWrap(True)
        system_layout.addWidget(self.system_info_label)

        layout.addWidget(system_group)

        # Spacer
        layout.addStretch()

        return sidebar

    def _create_agent_workflow_area(self) -> QWidget:
        """Create the main area for agents and workflows."""
        area = QWidget()
        layout = QVBoxLayout(area)

        # Tabs for Agents and Workflows
        self.tab_widget = QTabWidget()

        # Agents tab
        agents_tab = QWidget()
        agents_layout = QVBoxLayout(agents_tab)

        agents_label = QLabel("Available Agents")
        agents_label.setFont(QFont("Arial", 14, QFont.Bold))
        agents_layout.addWidget(agents_label)

        self.agents_scroll = QScrollArea()
        self.agents_container = QWidget()
        self.agents_layout = QGridLayout(self.agents_container)

        self.agents_scroll.setWidget(self.agents_container)
        self.agents_scroll.setWidgetResizable(True)
        agents_layout.addWidget(self.agents_scroll)

        self.tab_widget.addTab(agents_tab, "Agents")

        # Workflows tab
        workflows_tab = QWidget()
        workflows_layout = QVBoxLayout(workflows_tab)

        workflows_label = QLabel("Active Workflows")
        workflows_label.setFont(QFont("Arial", 14, QFont.Bold))
        workflows_layout.addWidget(workflows_label)

        self.workflows_scroll = QScrollArea()
        self.workflows_container = QWidget()
        self.workflows_layout = QGridLayout(self.workflows_container)

        self.workflows_scroll.setWidget(self.workflows_container)
        self.workflows_scroll.setWidgetResizable(True)
        workflows_layout.addWidget(self.workflows_scroll)

        self.tab_widget.addTab(workflows_tab, "Workflows")

        layout.addWidget(self.tab_widget)

        return area

    def _setup_system_tray(self):
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon())  # Would set actual icon

        # Tray menu
        tray_menu = QMenu()

        show_action = QAction("Show Workspace", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit AIOS", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _connect_signals(self):
        """Connect widget signals."""
        # Agent widget clicks
        for widget in self.agent_widgets.values():
            widget.clicked.connect(self._on_agent_clicked)

        # Workflow widget clicks
        for widget in self.workflow_widgets.values():
            widget.clicked.connect(self._on_workflow_clicked)

        # Intent selection
        self.intent_panel.intent_selected.connect(self._on_intent_selected)

    def _update_workspace(self):
        """Update the workspace with current runtime state."""
        try:
            # Update agents
            current_agents = self.runtime.agent_mesh.agents
            self._update_agents(current_agents)

            # Update workflows
            current_workflows = self.runtime.workflow_engine.workflows
            self._update_workflows(current_workflows)

            # Update context
            context = self.runtime.context_engine.get_context()
            context_data = {
                "active_workflows": context.active_workflows,
                "active_agents": context.active_agents,
                "environment": context.environment
            }
            self.context_panel.update_context(context_data)

            # Update system info
            self._update_system_info()

        except Exception as e:
            log.error(f"Error updating workspace: {e}")

    def _update_agents(self, agents: Dict[str, Agent]):
        """Update agent widgets."""
        # Remove widgets for agents that no longer exist
        existing_ids = set(agents.keys())
        widget_ids = set(self.agent_widgets.keys())

        to_remove = widget_ids - existing_ids
        for agent_id in to_remove:
            widget = self.agent_widgets[agent_id]
            self.agents_layout.removeWidget(widget)
            widget.deleteLater()
            del self.agent_widgets[agent_id]

        # Add or update agent widgets
        row, col = 0, 0
        max_cols = 3

        for agent in agents.values():
            if agent.agent_id in self.agent_widgets:
                # Update existing widget
                self.agent_widgets[agent.agent_id].update_agent(agent)
            else:
                # Create new widget
                widget = AgentWidget(agent)
                widget.clicked.connect(self._on_agent_clicked)
                self.agent_widgets[agent.agent_id] = widget
                self.agents_layout.addWidget(widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _update_workflows(self, workflows: Dict[str, Workflow]):
        """Update workflow widgets."""
        # Remove widgets for workflows that no longer exist
        existing_ids = set(workflows.keys())
        widget_ids = set(self.workflow_widgets.keys())

        to_remove = widget_ids - existing_ids
        for wf_id in to_remove:
            widget = self.workflow_widgets[wf_id]
            self.workflows_layout.removeWidget(widget)
            widget.deleteLater()
            del self.workflow_widgets[wf_id]

        # Add or update workflow widgets
        row, col = 0, 0
        max_cols = 2

        for workflow in workflows.values():
            if workflow.workflow_id in self.workflow_widgets:
                # Update existing widget
                self.workflow_widgets[workflow.workflow_id].update_workflow(workflow)
            else:
                # Create new widget
                widget = WorkflowWidget(workflow)
                widget.clicked.connect(self._on_workflow_clicked)
                self.workflow_widgets[workflow.workflow_id] = widget
                self.workflows_layout.addWidget(widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _update_system_info(self):
        """Update system information display."""
        try:
            status = self.runtime.get_system_status()
            runtime_status = status.get("runtime_status", "unknown")
            agent_count = len(status.get("agents", {}))
            workflow_count = len(status.get("workflows", {}))

            info_text = f"Status: {runtime_status}\nAgents: {agent_count}\nWorkflows: {workflow_count}"
            self.system_info_label.setText(info_text)

        except Exception as e:
            self.system_info_label.setText(f"Error: {e}")

    def _on_agent_clicked(self, agent_id: str):
        """Handle agent widget click."""
        log.info(f"Agent clicked: {agent_id}")
        # Would open agent interaction dialog

    def _on_workflow_clicked(self, workflow_id: str):
        """Handle workflow widget click."""
        log.info(f"Workflow clicked: {workflow_id}")
        # Would open workflow monitoring dialog

    def _on_intent_selected(self, intent_data: Dict[str, Any]):
        """Handle intent selection."""
        log.info(f"Intent selected: {intent_data}")
        # Would process the selected intent

    def _create_agent(self):
        """Create a new agent."""
        log.info("Creating new agent...")
        # Would open agent creation dialog

    def _create_workflow(self):
        """Create a new workflow."""
        log.info("Creating new workflow...")
        # Would open workflow creation dialog

    def _show_system_status(self):
        """Show detailed system status."""
        try:
            status = self.runtime.get_system_status()
            # Would open detailed status dialog
            log.info(f"System status: {status}")
        except Exception as e:
            log.error(f"Error getting system status: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        # Hide to tray instead of closing
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "AIOS Workspace",
            "AIOS is running in the background. Click the tray icon to restore.",
            QSystemTrayIcon.Information,
            3000
        )


class WorkspaceManager:
    """
    Manages the AI-native workspace environment.
    """

    def __init__(self, runtime: AIOSRuntime):
        self.runtime = runtime
        self.workspace: Optional[AIOSWorkspace] = None

    def create_workspace(self) -> AIOSWorkspace:
        """Create the main workspace."""
        self.workspace = AIOSWorkspace(self.runtime)
        return self.workspace

    def show_workspace(self):
        """Show the workspace window."""
        if self.workspace:
            self.workspace.show()
            self.workspace.raise_()
            self.workspace.activateWindow()

    def hide_workspace(self):
        """Hide the workspace window."""
        if self.workspace:
            self.workspace.hide()

    def get_workspace(self) -> Optional[AIOSWorkspace]:
        """Get the workspace instance."""
        return self.workspace