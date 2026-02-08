"""
Debug Handler and Crash Reporter for Serial Communication Monitor
Captures exceptions and formats them for GitHub issue reporting
"""

import sys
import traceback
import platform
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import functools
import threading
import inspect


class DebugHandler:
    """
    Comprehensive debug and crash reporting handler.
    Captures exceptions with full context and formats for GitHub issues.
    """
    
    def __init__(self, app_version: str, enabled: bool = True, log_dir: Optional[Path] = None):
        """
        Initialize the debug handler.
        
        Args:
            app_version: Application version string
            enabled: Whether debugging is enabled
            log_dir: Directory to save crash logs (optional)
        """
        self.enabled = enabled
        self.app_version = app_version
        self.log_dir = log_dir
        self.crash_count = 0
        
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def install_exception_handler(self):
        """Install global exception handler to catch uncaught exceptions"""
        if self.enabled:
            sys.excepthook = self._exception_handler
            
            # Install handler for Qt exceptions (Qt5 version)
            try:
                from PyQt5.QtCore import qInstallMessageHandler
                # Note: qInstallMessageHandler in PyQt5 doesn't work the same way
                # It's mainly for Qt internal messages, not Python exceptions
                # We'll skip this for now as sys.excepthook handles Python exceptions
            except:
                pass
    
    def _exception_handler(self, exc_type, exc_value, exc_traceback):
        """
        Global exception handler that formats crashes for GitHub issues.
        """
        if not self.enabled:
            # If disabled, use default handler
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        self.crash_count += 1
        
        # Generate crash report
        report = self._generate_crash_report(exc_type, exc_value, exc_traceback)
        
        # Print to console
        print("\n" + "="*80)
        print("CRASH DETECTED - Debug Report Generated")
        print("="*80)
        print(report)
        print("="*80 + "\n")
        
        # Save to file if log directory is set
        if self.log_dir:
            self._save_crash_log(report)
        
        # Show GUI dialog if possible
        try:
            from PyQt5.QtWidgets import QApplication
            if QApplication.instance():
                # Import here to avoid circular dependency
                from CrashReportDialog import CrashReportDialog
                dialog = CrashReportDialog(report)
                dialog.exec_()
        except Exception as e:
            print(f"Could not show crash dialog: {e}")
        
        # Call original exception handler to maintain default behavior
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def _qt_message_handler(self, mode, context, message):
        """Handler for Qt messages (warnings, errors, etc.)"""
        if self.enabled:
            msg_type = {
                0: "DEBUG",
                1: "WARNING",
                2: "CRITICAL",
                3: "FATAL",
                4: "INFO"
            }.get(mode, "UNKNOWN")
            
            print(f"[Qt {msg_type}] {message}")
            if context.file:
                print(f"  at {context.file}:{context.line}")
    
    def _generate_crash_report(self, exc_type, exc_value, exc_traceback) -> str:
        """
        Generate a comprehensive crash report formatted for GitHub issues.
        """
        lines = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        lines.append("# Crash Report - Serial Communication Monitor")
        lines.append("")
        lines.append(f"**Timestamp:** {timestamp}")
        lines.append(f"**Version:** {self.app_version}")
        lines.append("")
        
        # Exception Information
        lines.append("## Exception Details")
        lines.append("")
        lines.append(f"**Type:** `{exc_type.__name__}`")
        lines.append(f"**Message:** {str(exc_value)}")
        lines.append("")
        
        # Traceback
        lines.append("## Stack Trace")
        lines.append("")
        lines.append("```python")
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        lines.extend([line.rstrip() for line in tb_lines])
        lines.append("```")
        lines.append("")
        
        # System Information
        lines.append("## System Information")
        lines.append("")
        lines.append(f"- **OS:** {platform.system()} {platform.release()}")
        lines.append(f"- **Architecture:** {platform.machine()}")
        lines.append(f"- **Python Version:** {platform.python_version()}")
        lines.append(f"- **Platform:** {platform.platform()}")
        
        # Try to get PyQt version
        try:
            from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
            lines.append(f"- **Qt Version:** {QT_VERSION_STR}")
            lines.append(f"- **PyQt Version:** {PYQT_VERSION_STR}")
        except:
            pass
        
        lines.append("")
        
        # Additional Context
        lines.append("## Additional Context")
        lines.append("")
        
        # Thread information
        current_thread = threading.current_thread()
        lines.append(f"- **Thread:** {current_thread.name} (ID: {current_thread.ident})")
        lines.append(f"- **Active Threads:** {threading.active_count()}")
        
        # Environment variables (selected)
        lines.append("")
        lines.append("### Relevant Environment")
        env_vars = ['PATH', 'PYTHONPATH', 'HOME', 'USER', 'DISPLAY']
        for var in env_vars:
            value = os.environ.get(var, 'Not Set')
            if var == 'PATH':
                value = value[:100] + '...' if len(value) > 100 else value
            lines.append(f"- `{var}`: {value}")
        
        lines.append("")
        
        # Installed packages (if we can get them)
        lines.append("### Installed Packages")
        lines.append("")
        try:
            # Use importlib.metadata (modern replacement for pkg_resources)
            try:
                from importlib.metadata import version as get_version
            except ImportError:
                # Fallback for Python < 3.8
                from importlib_metadata import version as get_version
            
            packages = ['pyserial', 'PyQt5', 'pyyaml']
            for pkg in packages:
                try:
                    pkg_version = get_version(pkg)
                    lines.append(f"- `{pkg}`: {pkg_version}")
                except:
                    lines.append(f"- `{pkg}`: Not found")
        except:
            lines.append("- Could not retrieve package information")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Steps to Reproduce")
        lines.append("")
        lines.append("1. ")
        lines.append("2. ")
        lines.append("3. ")
        lines.append("")
        lines.append("## Expected Behavior")
        lines.append("")
        lines.append("_Describe what should happen_")
        lines.append("")
        lines.append("## Actual Behavior")
        lines.append("")
        lines.append("_Describe what actually happened_")
        
        return "\n".join(lines)
    
    def _save_crash_log(self, report: str):
        """Save crash report to log file"""
        if not self.log_dir:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crash_report_{timestamp}_{self.crash_count}.md"
            filepath = self.log_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\nCrash report saved to: {filepath}")
        except Exception as e:
            print(f"Failed to save crash log: {e}")
    
    def debug_function(self, func: Callable) -> Callable:
        """
        Decorator to add debug logging to functions.
        Logs function entry, exit, arguments, and exceptions.
        
        Usage:
            @debug_handler.debug_function
            def my_function(arg1, arg2):
                pass
        """
        if not self.enabled:
            return func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            module_name = func.__module__
            
            # Log entry
            print(f"[DEBUG] Entering {module_name}.{func_name}")
            
            # Log arguments (be careful with sensitive data)
            if args:
                print(f"[DEBUG]   args: {self._safe_repr(args)}")
            if kwargs:
                print(f"[DEBUG]   kwargs: {self._safe_repr(kwargs)}")
            
            try:
                result = func(*args, **kwargs)
                print(f"[DEBUG] Exiting {module_name}.{func_name} -> {self._safe_repr(result)}")
                return result
            except Exception as e:
                print(f"[DEBUG] Exception in {module_name}.{func_name}: {type(e).__name__}: {e}")
                # Get call location
                frame = inspect.currentframe()
                if frame and frame.f_back:
                    caller_frame = frame.f_back
                    print(f"[DEBUG]   Called from: {caller_frame.f_code.co_filename}:{caller_frame.f_lineno}")
                raise
        
        return wrapper
    
    def debug_method(self, method: Callable) -> Callable:
        """
        Decorator specifically for class methods (includes self/cls information).
        
        Usage:
            @debug_handler.debug_method
            def my_method(self, arg):
                pass
        """
        if not self.enabled:
            return method
        
        @functools.wraps(method)
        def wrapper(instance, *args, **kwargs):
            class_name = instance.__class__.__name__
            method_name = method.__name__
            
            print(f"[DEBUG] {class_name}.{method_name} called")
            
            if args:
                print(f"[DEBUG]   args: {self._safe_repr(args)}")
            if kwargs:
                print(f"[DEBUG]   kwargs: {self._safe_repr(kwargs)}")
            
            try:
                result = method(instance, *args, **kwargs)
                print(f"[DEBUG] {class_name}.{method_name} completed")
                return result
            except Exception as e:
                print(f"[DEBUG] Exception in {class_name}.{method_name}: {type(e).__name__}: {e}")
                raise
        
        return wrapper
    
    def log(self, message: str, level: str = "INFO"):
        """
        Simple logging function.
        
        Args:
            message: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        if not self.enabled and level not in ["ERROR", "CRITICAL"]:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        thread_name = threading.current_thread().name
        print(f"[{timestamp}] [{level}] [{thread_name}] {message}")
    
    def _safe_repr(self, obj, max_length: int = 200) -> str:
        """
        Safe representation of objects that truncates long outputs.
        """
        try:
            repr_str = repr(obj)
            if len(repr_str) > max_length:
                return repr_str[:max_length] + "..."
            return repr_str
        except:
            return "<repr failed>"
    
    def capture_context(self, context_name: str = ""):
        """
        Context manager for capturing exceptions in specific code blocks.
        
        Usage:
            with debug_handler.capture_context("Serial Port Opening"):
                serial_port.open()
        """
        return DebugContext(self, context_name)


class DebugContext:
    """Context manager for debugging specific code blocks"""
    
    def __init__(self, handler: DebugHandler, context_name: str):
        self.handler = handler
        self.context_name = context_name
    
    def __enter__(self):
        if self.handler.enabled:
            self.handler.log(f"Entering context: {self.context_name}", "DEBUG")
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None and self.handler.enabled:
            self.handler.log(
                f"Exception in context '{self.context_name}': {exc_type.__name__}: {exc_value}",
                "ERROR"
            )
            # Return False to propagate the exception
            return False
        
        if self.handler.enabled:
            self.handler.log(f"Exiting context: {self.context_name}", "DEBUG")
        return True


# Singleton instance (will be initialized in App.py)
_debug_handler: Optional[DebugHandler] = None


def get_debug_handler() -> Optional[DebugHandler]:
    """Get the global debug handler instance"""
    return _debug_handler


def set_debug_handler(handler: DebugHandler):
    """Set the global debug handler instance"""
    global _debug_handler
    _debug_handler = handler
