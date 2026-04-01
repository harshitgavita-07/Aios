"""
System Tools — Built-in tools for system interaction
"""

import os
import platform
import shutil
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

log = logging.getLogger("aios.tools.system")


class SystemTools:
    """
    Collection of system-level tools.
    
    Tools:
    - think: Reasoning tool
    - calculator: Math evaluation
    - file_read: Read file contents
    - file_write: Write to file
    - system_info: Get system information
    - list_directory: List directory contents
    
    Change: Sandboxed system tools
    Why:
    - Previous system had limited tool support
    - Needed safe file/system access
    Impact:
    - Expanded capabilities
    - Safe system interaction
    """

    def __init__(self, allowed_dirs: Optional[list] = None):
        # Restrict file operations to these directories
        self.allowed_dirs = allowed_dirs or [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
        ]
        
        # Ensure directories exist
        for d in self.allowed_dirs:
            d.mkdir(parents=True, exist_ok=True)

    def think(self, payload: Any) -> str:
        """
        Thought/reasoning tool.
        
        Change: Structured thinking tool
        Why:
        - LLM benefits from explicit reasoning step
        - Improves complex task handling
        Impact:
        - Better problem-solving
        - Observable reasoning process
        """
        thought = ""
        if isinstance(payload, dict):
            thought = payload.get("thought", "")
        elif isinstance(payload, str):
            thought = payload
        
        if not thought:
            return json.dumps({"error": "No thought provided"})
        
        return json.dumps({
            "status": "ok",
            "thought": thought,
            "timestamp": datetime.now().isoformat()
        })

    def calculator(self, payload: Any) -> str:
        """
        Safe calculator tool.
        
        Change: Safe math evaluation
        Why:
        - Users need calculation support
        - eval() is dangerous, use safe parser
        Impact:
        - Safe mathematical operations
        - No code injection risk
        """
        expression = ""
        if isinstance(payload, dict):
            expression = payload.get("expression", "")
        elif isinstance(payload, str):
            expression = payload
        
        if not expression:
            return json.dumps({"error": "No expression provided"})
        
        try:
            # Safe evaluation: only allow basic math
            allowed_chars = set("0123456789+-*/().^% ")
            if not all(c in allowed_chars for c in expression):
                return json.dumps({"error": "Invalid characters in expression"})
            
            # Replace ^ with ** for Python
            expression = expression.replace("^", "**")
            
            # Evaluate safely
            result = eval(expression, {"__builtins__": {}}, {})
            
            return json.dumps({
                "expression": expression,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return json.dumps({"error": f"Calculation error: {str(e)}"})

    def file_read(self, payload: Any) -> str:
        """
        Read file contents (restricted to allowed directories).
        
        Change: Sandboxed file reading
        Why:
        - Security: prevent access to sensitive files
        - Users need file access for AI assistance
        Impact:
        - Safe file reading
        - Controlled access scope
        """
        filepath = ""
        if isinstance(payload, dict):
            filepath = payload.get("path", "")
        elif isinstance(payload, str):
            filepath = payload
        
        if not filepath:
            return json.dumps({"error": "No file path provided"})
        
        try:
            path = Path(filepath).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return json.dumps({"error": "Access denied: path outside allowed directories"})
            
            if not path.exists():
                return json.dumps({"error": f"File not found: {filepath}"})
            
            if not path.is_file():
                return json.dumps({"error": f"Not a file: {filepath}"})
            
            # Size limit: 1MB
            if path.stat().st_size > 1024 * 1024:
                return json.dumps({"error": "File too large (max 1MB)"})
            
            content = path.read_text(encoding="utf-8", errors="replace")
            
            return json.dumps({
                "path": str(path),
                "content": content,
                "size": len(content),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return json.dumps({"error": f"Read error: {str(e)}"})

    def file_write(self, payload: Any) -> str:
        """
        Write to file (restricted to allowed directories).
        
        Change: Sandboxed file writing
        Why:
        - Security: prevent writing to system files
        - Users need to save AI-generated content
        Impact:
        - Safe file writing
        - Controlled write scope
        """
        filepath = ""
        content = ""
        
        if isinstance(payload, dict):
            filepath = payload.get("path", "")
            content = payload.get("content", "")
        elif isinstance(payload, str):
            return json.dumps({"error": "Payload must be dict with 'path' and 'content'"})
        
        if not filepath:
            return json.dumps({"error": "No file path provided"})
        
        try:
            path = Path(filepath).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return json.dumps({"error": "Access denied: path outside allowed directories"})
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding="utf-8")
            
            return json.dumps({
                "path": str(path),
                "bytes_written": len(content.encode("utf-8")),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return json.dumps({"error": f"Write error: {str(e)}"})

    def list_directory(self, payload: Any) -> str:
        """
        List directory contents.
        
        Change: Sandboxed directory listing
        Why:
        - Users need to browse files
        - Security requires path restrictions
        Impact:
        - Safe directory browsing
        - File system exploration
        """
        dirpath = ""
        if isinstance(payload, dict):
            dirpath = payload.get("path", ".")
        elif isinstance(payload, str):
            dirpath = payload or "."
        
        try:
            path = Path(dirpath).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return json.dumps({"error": "Access denied: path outside allowed directories"})
            
            if not path.exists():
                return json.dumps({"error": f"Directory not found: {dirpath}"})
            
            if not path.is_dir():
                return json.dumps({"error": f"Not a directory: {dirpath}"})
            
            items = []
            for item in path.iterdir():
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort: directories first, then alphabetically
            items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
            
            return json.dumps({
                "path": str(path),
                "items": items,
                "count": len(items),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return json.dumps({"error": f"List error: {str(e)}"})

    def system_info(self, payload: Any = None) -> str:
        """
        Get system information.
        
        Change: System information gathering
        Why:
        - Users ask about system status
        - Hardware context helps with assistance
        Impact:
        - System awareness
        - Better contextual responses
        """
        info = {
            "platform": platform.platform(),
            "processor": platform.processor() or "Unknown",
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
        
        if PSUTIL_AVAILABLE:
            try:
                info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                info["cpu_count"] = psutil.cpu_count()
                
                memory = psutil.virtual_memory()
                info["memory"] = {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                }
                
                disk = psutil.disk_usage("/")
                info["disk"] = {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 1)
                }
            except Exception as e:
                info["psutil_error"] = str(e)
        else:
            info["psutil"] = "not installed"
        
        return json.dumps(info, indent=2)

    def run_command(self, payload: Any) -> str:
        """
        Run a system command safely.
        
        Change: Safe command execution
        Why:
        - Users need to run system commands
        - Must prevent dangerous operations
        Impact:
        - Controlled system access
        - Safe command execution
        """
        command = ""
        if isinstance(payload, dict):
            command = payload.get("command", "")
        elif isinstance(payload, str):
            command = payload
        
        if not command:
            return json.dumps({"error": "No command provided"})
        
        # Dangerous commands blacklist
        dangerous = [
            "rm ", "del ", "format ", "fdisk", "mkfs", "dd ", "shutdown",
            "reboot", "halt", "poweroff", "sudo ", "su ", "chmod 777",
            "chown root", "passwd", "usermod", "userdel", "groupmod"
        ]
        
        command_lower = command.lower()
        for bad in dangerous:
            if bad in command_lower:
                return json.dumps({"error": f"Dangerous command blocked: {bad.strip()}"})
        
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path.home())
            )
            
            return json.dumps({
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Command timed out after 30 seconds"})
        except Exception as e:
            return json.dumps({"error": f"Command execution error: {str(e)}"})

    def open_application(self, payload: Any) -> str:
        """
        Open an application or file.
        
        Change: Application launching
        Why:
        - Users want to open programs/files
        - Convenient computer control
        Impact:
        - Application management
        - File opening capability
        """
        target = ""
        if isinstance(payload, dict):
            target = payload.get("target", "")
        elif isinstance(payload, str):
            target = payload
        
        if not target:
            return json.dumps({"error": "No target provided"})
        
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # Windows
                result = subprocess.run(
                    ["start", target],
                    shell=True,
                    capture_output=True,
                    text=True
                )
            elif platform.system() == "Darwin":
                # macOS
                result = subprocess.run(
                    ["open", target],
                    capture_output=True,
                    text=True
                )
            else:
                # Linux
                result = subprocess.run(
                    ["xdg-open", target],
                    capture_output=True,
                    text=True
                )
            
            return json.dumps({
                "action": "open_application",
                "target": target,
                "success": result.returncode == 0,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return json.dumps({"error": f"Application open error: {str(e)}"})

    def take_screenshot(self, payload: Any) -> str:
        """
        Take a screenshot and save it.
        
        Change: Screenshot capability
        Why:
        - Users need visual capture
        - Helpful for documentation
        Impact:
        - Visual capture tool
        - Screen recording capability
        """
        filename = ""
        if isinstance(payload, dict):
            filename = payload.get("filename", "")
        elif isinstance(payload, str):
            filename = payload or "screenshot.png"
        
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            from PIL import ImageGrab
            import platform
            
            # Take screenshot
            screenshot = ImageGrab.grab()
            
            # Save to allowed directory
            save_path = self.allowed_dirs[0] / filename
            screenshot.save(str(save_path))
            
            return json.dumps({
                "action": "screenshot",
                "filename": filename,
                "path": str(save_path),
                "size": screenshot.size,
                "timestamp": datetime.now().isoformat()
            })
            
        except ImportError:
            return json.dumps({"error": "PIL not installed. Install with: pip install pillow"})
        except Exception as e:
            return json.dumps({"error": f"Screenshot error: {str(e)}"})

    def get_running_processes(self, payload: Any) -> str:
        """
        Get list of running processes.
        
        Change: Process monitoring
        Why:
        - Users need system monitoring
        - Process management capability
        Impact:
        - System monitoring tool
        - Process visibility
        """
        try:
            if not PSUTIL_AVAILABLE:
                return json.dumps({"error": "psutil not installed"})
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu_percent": round(info['cpu_percent'], 1),
                        "memory_percent": round(info['memory_percent'], 1)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return json.dumps({
                "processes": processes[:20],  # Top 20
                "total_count": len(processes),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return json.dumps({"error": f"Process list error: {str(e)}"})

    def control_window(self, payload: Any) -> str:
        """
        Control application windows (minimize, maximize, close).
        
        Change: Window management
        Why:
        - Users need window control
        - Computer automation capability
        Impact:
        - Window management tool
        - Desktop automation
        """
        action = ""
        window_title = ""
        
        if isinstance(payload, dict):
            action = payload.get("action", "")
            window_title = payload.get("window_title", "")
        else:
            return json.dumps({"error": "Payload must be dict with 'action' and 'window_title'"})
        
        if not action or not window_title:
            return json.dumps({"error": "Both 'action' and 'window_title' required"})
        
        try:
            import pygetwindow as gw
            
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                return json.dumps({"error": f"No window found with title: {window_title}"})
            
            window = windows[0]  # Take first match
            
            if action == "minimize":
                window.minimize()
            elif action == "maximize":
                window.maximize()
            elif action == "restore":
                window.restore()
            elif action == "close":
                window.close()
            elif action == "focus":
                window.activate()
            else:
                return json.dumps({"error": f"Unknown action: {action}"})
            
            return json.dumps({
                "action": action,
                "window_title": window_title,
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
            
        except ImportError:
            return json.dumps({"error": "pygetwindow not installed. Install with: pip install pygetwindow"})
        except Exception as e:
            return json.dumps({"error": f"Window control error: {str(e)}"})

    def get_tools_dict(self) -> Dict[str, callable]:
        """Get all tools as a dictionary for registration."""
        return {
            "think": self.think,
            "calculator": self.calculator,
            "file_read": self.file_read,
            "file_write": self.file_write,
            "list_directory": self.list_directory,
            "system_info": self.system_info,
            "run_command": self.run_command,
            "open_application": self.open_application,
            "take_screenshot": self.take_screenshot,
            "get_running_processes": self.get_running_processes,
            "control_window": self.control_window,
        }
