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

    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        try:
            resolved = path.resolve()
            for allowed in self.allowed_dirs:
                try:
                    if resolved.is_relative_to(allowed.resolve()):
                        return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    def get_tools_dict(self) -> Dict[str, callable]:
        """Get all tools as a dictionary for registration."""
        return {
            "think": self.think,
            "calculator": self.calculator,
            "file_read": self.file_read,
            "file_write": self.file_write,
            "list_directory": self.list_directory,
            "system_info": self.system_info,
        }
