import subprocess
import sys
import os
import serial
import serial.tools.list_ports
import platform
from pathlib import Path
import yaml
from datetime import datetime
import time
import threading
import traceback
from typing import Optional, Dict, Any, List
from queue import Queue

from MacroEditor import MacroEditor, MenuDialog
from CommandsEditor import CommandsEditor
from StyleManager import StyleManager
from ThemesDialog import ThemesDialog
from ManualDialog import ManualDialog
from DebugHandler import DebugHandler, set_debug_handler, get_debug_handler
from CrashReportDialog import CrashReportDialog

# Application version
__version__ = "2.6.0"

# Debug mode configuration
# Set to True to enable comprehensive debugging and crash reporting
# Debug builds (version ending with 'd') will show console output
DEBUG_ENABLED = __version__.endswith('d')  # Auto-detect debug builds
IS_DEBUG = DEBUG_ENABLED  # Alias for compatibility

# sip is uncommented in windows pyinstaller build
# import sip

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidgetItem,
    QTextEdit, QLineEdit, QLabel, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QInputDialog, QDialog, QListWidget, QCheckBox,
    QSpinBox, QTabWidget, QFileDialog, QMenu, QAction, QScrollArea
)

from PyQt5.QtCore import QTimer, Qt, QPoint, pyqtSignal, pyqtSlot, QThread, QEvent, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QMouseEvent, QCloseEvent, QKeyEvent, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QColorDialog, QAbstractItemView

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_config_dir(app_name: str) -> Path:
    """
    Returns the path to the application config directory for the current user.
    Creates the directory if it doesn't exist.
    """
    system = platform.system()

    if system == 'Windows':
        base_dir = os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')
    elif system == 'Darwin':
        base_dir = Path.home() / 'Library' / 'Application Support'
    else:  # Assume Linux or other Unix
        base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))

    config_dir = Path(base_dir) / app_name
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir

class SerialReaderThread(QThread):
    """Thread for reading serial data to prevent UI blocking"""
    data_received = pyqtSignal(str)  # Signal to send data back to main thread
    error_occurred = pyqtSignal(str)  # Signal for error handling
    
    def __init__(self, serial_port: serial.Serial) -> None:
        super().__init__()
        self.serial_port = serial_port
        self.running = True
        self.buffer = ""  # Buffer to accumulate partial lines
        
    def run(self) -> None:
        """Main thread loop for reading serial data"""
        debug = get_debug_handler()
        if debug and debug.enabled:
            debug.log("SerialReaderThread started", "DEBUG")
            
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    # Read available data in chunks
                    chunk_size = min(self.serial_port.in_waiting, 4096)  # Read up to 4KB at a time
                    data = self.serial_port.read(chunk_size)
                    
                    # Decode with error handling
                    decoded = data.decode('utf-8', errors='replace')
                    
                    # Add to buffer
                    self.buffer += decoded
                    
                    # Process complete lines (lines ending with \n or \r\n)
                    while '\n' in self.buffer or '\r' in self.buffer:
                        # Find the first line ending
                        newline_pos = len(self.buffer)
                        line_ending = '\n'  # Default line ending
                        for delim in ['\r\n', '\n', '\r']:
                            pos = self.buffer.find(delim)
                            if pos != -1 and pos < newline_pos:
                                newline_pos = pos
                                line_ending = delim
                        
                        if newline_pos < len(self.buffer):
                            # Extract the complete line
                            line = self.buffer[:newline_pos]
                            # Remove the line and its ending from buffer
                            self.buffer = self.buffer[newline_pos + len(line_ending):]
                            
                            # Emit the line (preserve the line ending for display)
                            if line or line_ending:  # Emit if there's content or just a line ending
                                self.data_received.emit(line + line_ending.replace('\r\n', '\n').replace('\r', '\n'))
                        else:
                            break
                else:
                    # Small sleep to prevent CPU spinning
                    time.sleep(0.01)
            except Exception as e:
                debug = get_debug_handler()
                if debug and debug.enabled:
                    debug.log(f"Exception in serial reader thread: {e}", "ERROR")
                self.error_occurred.emit(str(e))
                break
    
    def stop(self) -> None:
        """Stop the thread gracefully"""
        debug = get_debug_handler()
        if debug and debug.enabled:
            debug.log("Stopping SerialReaderThread", "DEBUG")
        self.running = False
        self.wait()  # Wait for thread to finish

class HistoryLineEdit(QLineEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent_window = parent  # so we can access parent's history list
        self.last_enter_time = 0  # Track time of last enter press for double-enter detection
        self.double_enter_threshold = 500  # milliseconds

    def keyPressEvent(self, a0: QKeyEvent) -> None:  # type: ignore[override]
        if self.parent_window is not None:
            if a0.key() == Qt.Key.Key_Up:
                # Limit navigation to last 10 history entries
                history_length = len(self.parent_window.history)
                start_index = max(0, history_length - 10)
                
                if self.parent_window.history_index > start_index:
                    if self.parent_window.history_index == history_length:
                        self.parent_window.current_text = self.text()
                    self.parent_window.history_index -= 1
                    self.setText(self.parent_window.history[self.parent_window.history_index])
            elif a0.key() == Qt.Key.Key_Down:
                if self.parent_window.history_index < len(self.parent_window.history) - 1:
                    self.parent_window.history_index += 1
                    self.setText(self.parent_window.history[self.parent_window.history_index])
                elif self.parent_window.history_index == len(self.parent_window.history) - 1:
                    self.parent_window.history_index += 1
                    self.setText(self.parent_window.current_text)
            elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Check for double-enter on empty input
                import time
                current_time = int(time.time() * 1000)  # milliseconds
                
                if not self.text().strip():
                    # Input is empty
                    if current_time - self.last_enter_time < self.double_enter_threshold:
                        # Double enter detected - get and send last command
                        if self.parent_window.history:
                            last_command = self.parent_window.history[-1]
                            self.setText(last_command)
                            # Let the parent handle the send
                            super().keyPressEvent(a0)
                            self.last_enter_time = 0  # Reset to prevent triple-enter issues
                        else:
                            # No history, do nothing
                            self.last_enter_time = 0
                    else:
                        # First enter on empty input - just record time, don't send
                        self.last_enter_time = current_time
                else:
                    # Input has text - send normally
                    self.last_enter_time = 0
                    super().keyPressEvent(a0)
            else:
                super().keyPressEvent(a0)
        else:
            super().keyPressEvent(a0)

class MainWindow(QMainWindow):
    # Qt signals for thread-safe communication
    macro_print_signal = pyqtSignal(str)
    macro_set_input_signal = pyqtSignal(str)
    macro_send_command_signal = pyqtSignal()
    macro_status_signal = pyqtSignal(str)
    macro_dialog_signal = pyqtSignal(str, object)  # (message, result_queue)
    macro_input_dialog_signal = pyqtSignal(str, object)  # (prompt, result_queue)
    macro_menu_signal = pyqtSignal(list, bool, object)  # (commands, is_multi, result_queue)
    
    # Hard-coded options that should not be saved to settings.yaml
    OPTIONS = {
        'auto_clear_output': [[False, 0], [True, 1]],
        'data_bits': [8, 7, 6, 5],
        'flow_control': [['None', 0], ['Hardware', 1], ['Software', 2]],
        'maximized': [[True, True], [False, False]],
        'open_mode': [['R/W', 0], ['RO', 1], ['WO', 2]],
        'parity': [['None', 0], ['Even', 1], ['Odd', 2], ['Space', 3], ['Mark', 4]],
        'stop_bits': [1, 1.5, 2],
        'tx_line_ending': [['LN', '\\n'], ['CR', '\\r'], ['CRLN', '\\r\\n'], ['NUL', '\\0']]
    }
    
    def __init__(self) -> None:
        """
        Initializes the main window of the Serial monitor application.
        Sets up the GUI with a dark theme and electric blue accents, initializes serial port controls,
        timers for refreshing serial ports and tracking connection time, and arranges the main layout
        including configuration and routing tables, response display, predefined command buttons, and
        status indicators for serial connections.
        Also prepares widgets for serial port selection, baud rate, connect/disconnect, AT command input,
        DTR/RTS toggles, and log count tracking. Disables certain controls until a serial connection is established.
        """
        super().__init__()
        
        # Initialize debug handler
        log_dir = get_config_dir("SerialCommunicationMonitor") / "logs"
        self.debug_handler = DebugHandler(
            app_version=__version__,
            enabled=DEBUG_ENABLED,
            log_dir=log_dir
        )
        self.debug_handler.install_exception_handler()
        set_debug_handler(self.debug_handler)
        
        if DEBUG_ENABLED:
            self.debug_handler.log(f"Starting Serial Communication Monitor v{__version__}", "INFO")
            self.debug_handler.log(f"Debug mode is ENABLED", "INFO")
            self.setWindowTitle(f"Serial Communication Monitor v{__version__} [DEBUG]")
        else:
            self.setWindowTitle("Serial Communication Monitor")
        
        self.resize(800, 600)
        
        # Set window icon for taskbar and title bar
        icon_path = get_resource_path("images/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.history = []  # copy so we don't modify the original list
        self.history_index = len(self.history)  # start at "end" (new command)
        self.current_text = ""  # stores what user was typing before navigating history
        self.last_connected: bool = False # Keeps if there was a last connection since start, used with auto reconnect

        self.app_configs_path = get_config_dir("SerialCommunicationMonitor")
        
        self.settings = {
            'quick_buttons': {
                'A': {'command': '', 'label': '', 'tooltip': ''}, 
                'B': {'command': '', 'label': '', 'tooltip': ''}, 
                'C': {'command': '', 'label': '', 'tooltip': ''}, 
                'D': {'command': '', 'label': '', 'tooltip': ''}, 
                'E': {'command': '', 'label': '', 'tooltip': ''}
                }, 
            'general': {
                'accent_color': '#1E90FF', 
                'auto_clear_output': False,
                'auto_reconnect': False,
                'background_color': '#121212',
                'background_secondary': '#1E1E1E',
                'background_tertiary': '#2A2A2A',
                'data_bits': 8,
                'display_format': 'text',
                'dtr_state': False,
                'flow_control': 'None', 
                'font_color': '#FFFFFF',
                'font_size': 10,
                'hover_color': '#63B8FF',
                'last_serial_port': '',
                'last_tab_index': 0,
                'maximized': True,
                'max_output_lines': 10000,
                'open_mode': 'R/W', 
                'parity': 'None',
                'rts_state': False,
                'show_timestamps': False,
                'stop_bits': 1, 
                'tx_line_ending': 'LN',
                'reveal-hidden-char': False,
                'last-baudrate': 115200,
                'custom-baudrate': 115200,
                'filter_empty_lines': False,
                'custom_line_filter': '',
                'show_flow_indicators': True,
                'disconnect_on_inactive': False
            }
        }
        self.default_settings = self.settings.copy()
        self.load_settings()  # Load settings from YAML file
        
        # Initialize StyleManager
        self.style_manager = StyleManager(self.settings['general'])


        if self.settings['general'].get('maximized', False):
            self.showMaximized()

        # print(self.settings)

        history_file = os.path.join(self.app_configs_path, "command_history.txt")
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                self.history = f.read().splitlines()
        else:
            self.history = []
        self.history_index = len(self.history)
        self.current_text = ""

        self.set_style()

        # Serial connection
        self.serial_port = None
        self.serial_reader_thread: Optional[SerialReaderThread] = None
        self.available_ports = self.get_serial_ports()
        
        # Track disconnection due to focus loss for auto-reconnect
        self.disconnected_by_focus_loss = False
        self.reconnect_port: Optional[str] = None
        self.reconnect_baud_rate: Optional[int] = None
        
        # Macro session buffer - only active during macro execution
        self.macro_session_active = False
        self.macro_session_buffer: List[str] = []  # Dedicated buffer for macro OutputBlock checking
        self.macro_session_lock = threading.Lock()

        # Timer for refreshing serial ports
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_serial_ports)
        self.refresh_timer.start(1000)  # Refresh every 1 second

        # Timer for connected time
        self.connected_time_seconds = 0
        self.connected_time_timer = QTimer()
        self.connected_time_timer.timeout.connect(self.update_connected_time)

        # Store button references for later updates
        self.custom_buttons = {}

        # Main layout
        self.main_layout = QVBoxLayout()

        self.create_top_ribbon()  # Create the top ribbon with serial controls

        
        self.middle_layout = QHBoxLayout() # Middle layout: Split into left (tables) and right (output)
        
        # Create a container widget for the left panel to enable animation
        self.left_panel_container = QWidget()
        self.left_panel_layout = QVBoxLayout(self.left_panel_container)
        self.left_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.left_panel_visible = True  # Track visibility state
        
        self.create_left_panel()  # Create the left panel with configuration and routing tables
        self.middle_layout.addWidget(self.left_panel_container)
        
        self.create_right_panel()  # Create the right panel with response display
        self.main_layout.addLayout(self.middle_layout)

        self.create_bottom_panel()  # Create the bottom panel with status indicators

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)
        
        # Connect macro signals for thread-safe GUI updates
        self.macro_print_signal.connect(self.print_to_display)
        self.macro_set_input_signal.connect(self.command_input.setText)
        self.macro_send_command_signal.connect(self.send_command)
        self.macro_status_signal.connect(self.macro_status_label.setText)
        self.macro_dialog_signal.connect(self._show_macro_dialog)
        self.macro_input_dialog_signal.connect(self._show_macro_input_dialog)
        self.macro_menu_signal.connect(self._show_macro_menu)
        
        # Update connect button appearance based on settings
        self.update_connect_button_appearance()

    def set_style(self) -> None:
        """Apply stylesheet using StyleManager"""
        # Update StyleManager with current settings
        self.style_manager.update_settings(self.settings['general'])
        style = self.style_manager.get_main_window_stylesheet()
        self.setStyleSheet(style)
    
    def set_tooltip(self, widget: QWidget, text: str) -> None:
        """Set tooltip on widget if tooltips are enabled"""
        if self.settings.get('general', {}).get('enable_tooltips', True):
            widget.setToolTip(text)
        else:
            widget.setToolTip("")
    
    def update_tooltips_visibility(self) -> None:
        """Update all tooltips based on current setting"""
        enabled = self.settings.get('general', {}).get('enable_tooltips', True)
        
        # Update all widgets with tooltips
        for widget in self.findChildren(QWidget):
            if widget.toolTip():
                if not enabled:
                    widget.setProperty("_original_tooltip", widget.toolTip())
                    widget.setToolTip("")
            elif enabled and widget.property("_original_tooltip"):
                widget.setToolTip(widget.property("_original_tooltip"))

    def create_top_ribbon(self) -> None:
        """
        Creates the top ribbon of the main window, which includes the serial port selection,
        baud rate selection, connect/disconnect button, command input field, send button,
        and DTR/RTS checkboxes.
        """
        # Top layout: Serial port, baud rate, connect, input field, send button, and DTR/RTS checkboxes
        top_layout = QHBoxLayout()
        port_label = QLabel("Serial Port:")
        self.port_combo = QComboBox()
        self.populate_port_combo()  # Populate with color-coded availability
        self.port_combo.setFixedWidth(150)  # Set fixed width for the port dropdown
        self.port_combo.setToolTip("Select the serial port to connect to. Hover over ports to see availability.")

        baud_rate_label = QLabel("Baud Rate:")
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600", "Custom"])
        self.baud_rate_combo.setCurrentText(str(self.settings.get("general", {}).get("last-baudrate", 115200)))  # Default baud rate
        self.baud_rate_combo.setFixedWidth(100)  # Set fixed width for the baud rate dropdown
        self.baud_rate_combo.setToolTip("Select the baud rate for serial communication")

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setToolTip("Connect to or disconnect from the selected serial port")

        self.command_input = HistoryLineEdit(self)
        self.command_input.setPlaceholderText("Enter command here...")
        self.command_input.returnPressed.connect(self.send_command)
        self.command_input.setFixedHeight(self.command_input.sizeHint().height() + 2)
        self.command_input.setToolTip("Enter a command to send. Press Enter to send, or double-Enter to repeat last command")

        self.send_button = QPushButton("Send")  # Add Send button
        self.send_button.clicked.connect(self.send_command)  # Connect to send_command method
        self.send_button.setDisabled(True)
        self.send_button.setToolTip("Send command, or Repeat last command if input is blank")

        # Add Auto Reconnect checkbox
        self.auto_reconnect_checkbox = QCheckBox("Auto Reconnect")
        self.auto_reconnect_checkbox.setChecked(self.settings.get('general', {}).get('auto_reconnect', False))
        self.auto_reconnect_checkbox.setToolTip("Automatically reconnect if the serial connection is lost")
        
        # Connect state change handler to save settings
        self.auto_reconnect_checkbox.stateChanged.connect(lambda: self.save_checkbox_state('auto_reconnect', self.auto_reconnect_checkbox.isChecked()))

        top_layout.addWidget(port_label)
        top_layout.addWidget(self.port_combo)
        top_layout.addWidget(baud_rate_label)
        top_layout.addWidget(self.baud_rate_combo)  # Add baud rate dropdown
        top_layout.addWidget(self.connect_button)
        top_layout.addWidget(self.command_input)
        top_layout.addWidget(self.send_button)  # Add Send button to layout
        top_layout.addWidget(self.auto_reconnect_checkbox)
        self.main_layout.addLayout(top_layout)

    def create_left_panel(self) -> None:
        # Left layout: Tabbed panel for Configuration and Routing tables

        self.left_panel_width = 350

        self.tab_widget = QTabWidget()
        self.tab_widget.setFixedWidth(self.left_panel_width)

        self.tab_commands()  # Create the commands tab
        self.tab_input_history()  # Create the command history tab
        self.tab_macros()  # Create the macros tab
        self.tab_settings()
        self.tab_about()

        # Add tables to tabs
        self.tab_widget.addTab(self.commands_tab, "Commands")
        self.tab_widget.addTab(self.command_history_tab, "History")
        self.tab_widget.addTab(self.macros_tab, "Macros")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        self.tab_widget.addTab(self.about_tab, "About")
        
        # Restore last active tab
        last_tab = self.settings.get('general', {}).get('last_tab_index', 0)
        self.tab_widget.setCurrentIndex(last_tab)
        
        # Connect tab change handler to save current tab
        self.tab_widget.currentChanged.connect(self.save_current_tab)

        self.left_panel_layout.addWidget(self.tab_widget)
        self.left_panel_container.setFixedWidth(self.left_panel_width)
        
        # Restore last serial port if it exists
        last_port = self.settings.get('general', {}).get('last_serial_port', '')
        if last_port:
            index = self.port_combo.findText(last_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def toggle_left_panel(self) -> None:
        """Toggle the visibility of the left panel with slide animation"""
        # Calculate the target width
        if self.left_panel_visible:
            # Hide panel
            start_width = self.left_panel_width
            end_width = 0
            self.toggle_panel_button.setText("▶ Show Panel")
        else:
            # Show panel
            start_width = 0
            end_width = self.left_panel_width
            self.toggle_panel_button.setText("◀ Hide Panel")
        
        # Create animation for smooth sliding
        self.panel_animation = QPropertyAnimation(self.left_panel_container, b"maximumWidth")
        self.panel_animation.setDuration(300)  # 300ms animation
        self.panel_animation.setStartValue(start_width)
        self.panel_animation.setEndValue(end_width)
        self.panel_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Also animate minimum width to ensure smooth resizing
        self.panel_animation_min = QPropertyAnimation(self.left_panel_container, b"minimumWidth")
        self.panel_animation_min.setDuration(300)
        self.panel_animation_min.setStartValue(start_width)
        self.panel_animation_min.setEndValue(end_width)
        self.panel_animation_min.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Start both animations
        self.panel_animation.start()
        self.panel_animation_min.start()
        
        # Toggle the visibility state
        self.left_panel_visible = not self.left_panel_visible

    def load_yaml_commands(self, filepath: str) -> dict:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("Invalid YAML format")

        if 'no_input_commands' in data or 'input_required_commands' in data:
            return {
                'no_input_commands': data.get('no_input_commands', {}),
                'input_required_commands': data.get('input_required_commands', {})
            }

        return {
            'no_input_commands': {},
            'input_required_commands': {},
            'commands': data  # fallback if flat dict
        }

    def tab_commands(self) -> None:
        self.commands_tab = QWidget()
        self.commands_layout = QVBoxLayout(self.commands_tab)

        # --- YAML file dropdown ---
        self.yaml_dropdown = QComboBox()
        self.yaml_dropdown.setToolTip("Select a command set to load predefined commands")
        self.commands_layout.addWidget(QLabel("Select Command Set:"))
        self.commands_layout.addWidget(self.yaml_dropdown)

        commands_dir = os.path.join(self.app_configs_path, "commands")
        
        if not os.path.exists(commands_dir):
            os.makedirs(commands_dir, exist_ok=True)

        yaml_files = [f for f in os.listdir(commands_dir) 
                      if f.endswith(".yaml") and os.path.isfile(os.path.join(commands_dir, f))]
        yaml_files.sort()
        self.yaml_dropdown.addItems(yaml_files)

        # Restore last selected command list
        last_command_list = self.settings.get('general', {}).get('last_command_list', '')
        if last_command_list and last_command_list in yaml_files:
            self.yaml_dropdown.setCurrentText(last_command_list)

        selected_file = self.yaml_dropdown.currentText()

        # --- Command lists ---
        self.no_input_list = QListWidget()
        self.no_input_list.setToolTip("Click to send a command that doesn't require additional input")
        self.input_required_list = QListWidget()
        self.input_required_list.setToolTip("Click to insert a command template into the input field")
        self.flat_command_list = QListWidget()  # For flat (non-sectioned) YAMLs
        self.flat_command_list.setToolTip("Click to send a command")

        self.no_input_label = QLabel("Commands (No Input Required):")
        self.input_required_label = QLabel("Commands (Require Input):")

        self.commands_layout.addWidget(self.no_input_label)
        self.commands_layout.addWidget(self.no_input_list)
        self.commands_layout.addWidget(self.input_required_label)
        self.commands_layout.addWidget(self.input_required_list)
        self.commands_layout.addWidget(self.flat_command_list)
        
        # Initially hide the flat command list
        self.flat_command_list.hide()

        # --- Handlers ---
        def send_no_input_command(item: QListWidgetItem) -> None:
            cmd = item.text().split(" - ")[0]
            self.send_predefined_command(cmd)

        def insert_input_command(item: QListWidgetItem) -> None:
            cmd = item.text().split(" - ")[0]
            self.command_input.setText(cmd)

        def handle_flat_command(item: QListWidgetItem) -> None:
            cmd = item.text().split(" - ")[0]
            self.send_predefined_command(cmd)

        self.no_input_list.itemClicked.connect(send_no_input_command)
        self.input_required_list.itemClicked.connect(insert_input_command)
        self.flat_command_list.itemClicked.connect(handle_flat_command)

        # --- Load and populate ---
        def populate_command_lists(yaml_filename: str) -> None:
            full_path = os.path.join(commands_dir, yaml_filename)
            if not os.path.exists(full_path):
                return
            
            # Skip if it's a directory
            if os.path.isdir(full_path):
                return

            self.no_input_list.clear()
            self.input_required_list.clear()
            self.flat_command_list.clear()

            try:
                data = self.load_yaml_commands(full_path)
            except Exception as e:
                print(f"Failed to load {yaml_filename}: {e}")
                return

            if 'commands' in data:
                # Flat YAML (no sections)
                self.no_input_list.hide()
                self.input_required_list.hide()
                self.no_input_label.hide()
                self.input_required_label.hide()

                self.flat_command_list.show()
                for cmd, desc in data['commands'].items():
                    self.flat_command_list.addItem(f"{cmd} - {desc}")
            else:
                # Sectioned YAML
                self.flat_command_list.hide()
                self.no_input_list.show()
                self.input_required_list.show()
                self.no_input_label.show()
                self.input_required_label.show()

                for cmd, desc in data.get('no_input_commands', {}).items():
                    self.no_input_list.addItem(f"{cmd} - {desc}")
                for cmd, desc in data.get('input_required_commands', {}).items():
                    self.input_required_list.addItem(f"{cmd} - {desc}")

        # Initial load
        populate_command_lists(selected_file)

        # Reload on change and save selection
        def on_command_list_changed(filename: str) -> None:
            populate_command_lists(filename)
            # Save the selected command list
            self.settings['general']['last_command_list'] = filename
            self.save_settings()
        
        self.yaml_dropdown.currentTextChanged.connect(on_command_list_changed)
        
        # --- Bottom buttons ---
        bottom_buttons_layout = QHBoxLayout()
        
        new_list_btn = QPushButton("New Command List")
        new_list_btn.setToolTip("Create a new command list")
        new_list_btn.clicked.connect(self.create_new_command_list)
        bottom_buttons_layout.addWidget(new_list_btn)
        
        edit_list_btn = QPushButton("Edit Selected List")
        edit_list_btn.setToolTip("Edit the currently selected command list")
        edit_list_btn.clicked.connect(self.edit_selected_command_list)
        bottom_buttons_layout.addWidget(edit_list_btn)
        
        self.commands_layout.addLayout(bottom_buttons_layout)

    def tab_input_history(self) -> None:
        # Create a tab widget for command history
        self.command_history_tab = QWidget()
        self.command_history_layout = QVBoxLayout(self.command_history_tab)

        self.command_history_list = QListWidget()
        self.command_history_list.setToolTip("Single-click to insert command into input field. Double-click to send immediately.")
        self.update_tab_input_history()

        # Click to insert command into input field
        self.command_history_list.itemClicked.connect(
            lambda item: self.command_input.setText(item.text())
        )
        
        # Double-click to send command immediately
        self.command_history_list.itemDoubleClicked.connect(
            lambda item: self.send_history_command(item.text())
        )

        self.command_history_layout.addWidget(QLabel("Command History:"))
        self.command_history_layout.addWidget(self.command_history_list)

        # Add clear history button at the bottom
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.setToolTip("Clear all command history")
        clear_history_btn.clicked.connect(self.confirm_clear_history)
        self.command_history_layout.addWidget(clear_history_btn)

    def tab_macros(self) -> None:
        """Create the macros tab with scrollable button list and create button"""
        self.macros_tab = QWidget()
        self.macros_layout = QVBoxLayout(self.macros_tab)
        
        # Create macros directory
        self.macros_dir = Path(self.app_configs_path) / "macros"
        self.macros_dir.mkdir(parents=True, exist_ok=True)
        
        # Title
        self.macros_layout.addWidget(QLabel("Macros"))
        
        # Scrollable area for macro buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.macro_buttons_layout = QVBoxLayout(scroll_widget)
        self.macro_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(scroll_widget)
        self.macros_layout.addWidget(scroll_area)
        
        # Dictionary to track macro buttons
        self.macro_buttons = {}
        
        # Create macro button at bottom
        create_macro_btn = QPushButton("Create New Macro")
        create_macro_btn.setToolTip("Create a new macro")
        create_macro_btn.clicked.connect(self.create_new_macro)
        self.macros_layout.addWidget(create_macro_btn)
        
        # Load existing macros
        self.refresh_macro_list()
    
    def refresh_macro_list(self) -> None:
        """Refresh the list of macro buttons"""
        # Clear existing buttons
        for button in self.macro_buttons.values():
            button.deleteLater()
        self.macro_buttons.clear()
        
        # Load macros from directory
        if self.macros_dir.exists():
            macro_files = sorted(self.macros_dir.glob("*.yaml"))
            
            for macro_file in macro_files:
                try:
                    with open(macro_file, 'r') as f:
                        macro_data = yaml.safe_load(f)
                    
                    macro_name = macro_data.get('name', macro_file.stem)
                    
                    # Create button
                    btn = QPushButton(macro_name)
                    btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                    btn.customContextMenuRequested.connect(
                        lambda pos, path=macro_file: self.show_macro_context_menu(pos, path)
                    )
                    btn.clicked.connect(
                        lambda _, path=macro_file: self.execute_macro(path)
                    )
                    
                    self.macro_buttons_layout.addWidget(btn)
                    self.macro_buttons[str(macro_file)] = btn
                    
                except Exception as e:
                    print(f"Failed to load macro {macro_file}: {e}")
    
    def create_new_macro(self) -> None:
        """Open the macro editor to create a new macro"""
        try:
            editor = MacroEditor(self, style_manager=self.style_manager)
            if editor.exec_() == QDialog.Accepted:
                # Save the new macro
                macro_name = editor.macro_name
                if macro_name:
                    # Sanitize filename
                    safe_name = "".join(c for c in macro_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    macro_path = self.macros_dir / f"{safe_name}.yaml"
                    
                    try:
                        with open(macro_path, 'w') as f:
                            yaml.dump(editor.macro_data, f, default_flow_style=False, sort_keys=False)
                        QMessageBox.information(self, "Success", f"Macro '{macro_name}' created successfully!")
                        self.refresh_macro_list()
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to save macro: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open macro editor: {e}")

    def show_macro_context_menu(self, pos: QPoint, macro_path: Path) -> None:
        """Show context menu for a macro button"""
        menu = QMenu(self)
        
        edit_action = QAction("Edit Macro", self)
        edit_action.triggered.connect(lambda: self.edit_macro(macro_path))
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete Macro", self)
        delete_action.triggered.connect(lambda: self.delete_macro(macro_path))
        menu.addAction(delete_action)
        
        # Show menu at cursor position
        sender = self.sender()
        if sender and isinstance(sender, QWidget):
            menu.exec_(sender.mapToGlobal(pos))
    
    def edit_macro(self, macro_path: Path) -> None:
        """Open the macro editor to edit an existing macro"""
        editor = MacroEditor(self, macro_path, style_manager=self.style_manager)
        if editor.exec_() == QDialog.Accepted:
            self.refresh_macro_list()
    
    def delete_macro(self, macro_path: Path) -> None:
        """Delete a macro file"""
        reply = QMessageBox.question(
            self,
            "Delete Macro",
            f"Are you sure you want to delete '{macro_path.stem}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                macro_path.unlink()
                QMessageBox.information(self, "Success", "Macro deleted successfully!")
                self.refresh_macro_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete macro: {e}")
    
    def open_commands_editor(self) -> None:
        """Open the commands editor"""
        editor = CommandsEditor(self, self.app_configs_path, self.style_manager)
        editor.exec_()
        
        # Refresh the commands dropdown after editor closes
        self.refresh_commands_dropdown()
    
    def refresh_commands_dropdown(self) -> None:
        """Refresh the commands dropdown with available YAML files"""
        commands_dir = os.path.join(self.app_configs_path, "commands")
        
        # Store current selection
        current_selection = self.yaml_dropdown.currentText()
        
        # Clear and repopulate
        self.yaml_dropdown.clear()
        yaml_files = [f for f in os.listdir(commands_dir) 
                      if f.endswith(".yaml") and os.path.isfile(os.path.join(commands_dir, f))]
        yaml_files.sort()
        self.yaml_dropdown.addItems(yaml_files)
        
        # Restore selection if it still exists
        if current_selection in yaml_files:
            self.yaml_dropdown.setCurrentText(current_selection)
    
    def create_new_command_list(self) -> None:
        """Create a new command list using the commands editor"""
        editor = CommandsEditor(self, self.app_configs_path, self.style_manager)
        # Start with empty lists - filename will be requested on save
        editor.exec_()
        
        # Refresh the commands dropdown after editor closes
        self.refresh_commands_dropdown()
    
    def edit_selected_command_list(self) -> None:
        """Edit the currently selected command list"""
        current_file = self.yaml_dropdown.currentText()
        if not current_file:
            QMessageBox.warning(self, "No Selection", "No command list selected. Please select a list or create a new one.")
            return
        
        editor = CommandsEditor(self, self.app_configs_path, self.style_manager)
        
        # Load the selected file
        filepath = self.app_configs_path / "commands" / current_file
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                raise ValueError("Invalid YAML format")
            
            editor.no_input_commands = data.get('no_input_commands', {})
            editor.input_required_commands = data.get('input_required_commands', {})
            editor.current_file = current_file
            editor.refresh_lists()
            editor.file_label.setText(f"File: {current_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
            return
        
        editor.exec_()
        
        # Refresh the commands dropdown after editor closes
        self.refresh_commands_dropdown()
    
    def execute_macro(self, macro_path: Path) -> None:
        """Execute a macro file"""
        if not hasattr(self, 'serial_port') or not self.serial_port:
            QMessageBox.warning(self, "Not Connected", "Please connect to a serial port first.")
            return
        
        try:
            with open(macro_path, 'r') as f:
                macro_data = yaml.safe_load(f)
            
            macro_name = macro_data.get('name', macro_path.stem)
            steps = macro_data.get('steps', [])
            
            if not steps:
                QMessageBox.warning(self, "Empty Macro", "This macro has no steps.")
                return
            
            # Execute macro in a separate thread to avoid blocking UI
            thread = threading.Thread(target=self._execute_macro_steps, args=(macro_name, steps))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Execution Error", f"Failed to execute macro: {e}")
    
    def _print_to_display_threadsafe(self, message: str) -> None:
        """Thread-safe wrapper for print_to_display using signal"""
        self.macro_print_signal.emit(message)
    
    def _set_command_input_threadsafe(self, text: str) -> None:
        """Thread-safe wrapper for setting command input using signal"""
        self.macro_set_input_signal.emit(text)
    
    def _send_command_threadsafe(self) -> None:
        """Thread-safe wrapper for send_command using signal"""
        self.macro_send_command_signal.emit()
    
    def _send_macro_command_direct(self, command: str) -> None:
        """Send a command directly from macro menu (thread-safe)"""
        self._set_command_input_threadsafe(command)
        time.sleep(0.05)
        self._send_command_threadsafe()
        time.sleep(0.05)
    
    def _update_macro_status_threadsafe(self, status: str) -> None:
        """Thread-safe wrapper for updating macro status using signal"""
        self.macro_status_signal.emit(status)
    
    def _show_macro_dialog(self, message: str, result_queue: Queue) -> None:
        """Show a dialog with Continue/End Macro options (called in main thread)"""
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Macro Dialog")
        msgBox.setText(message)
        msgBox.setIcon(QMessageBox.Question)
        
        continue_btn = msgBox.addButton("Continue", QMessageBox.AcceptRole)
        end_btn = msgBox.addButton("End Macro", QMessageBox.RejectRole)
        msgBox.setDefaultButton(continue_btn)
        
        msgBox.exec_()
        
        # Put result in queue (True for Continue, False for End Macro)
        result_queue.put(msgBox.clickedButton() == continue_btn)
    
    def _show_macro_input_dialog(self, prompt: str, result_queue: Queue) -> None:
        """Show an input dialog to get custom command from user (called in main thread)"""
        text, ok = QInputDialog.getText(
            self,
            "Custom Command",
            prompt,
            QLineEdit.Normal,
            ""
        )
        
        # Put result in queue (command string if ok, None if cancelled)
        result_queue.put(text if ok else None)
    
    def _show_macro_menu(self, commands: List[str], is_multi: bool, result_queue: Queue) -> None:
        """Show a menu dialog with command buttons (called in main thread)"""
        # Define callback for immediate command execution in multi mode
        def on_command_execute(command: str):
            self._send_macro_command_direct(command)
        
        dialog = MenuDialog(
            self, 
            commands=commands, 
            is_multi=is_multi,
            accent_color=self.style_manager.accent_color if self.style_manager else "#1E90FF",
            font_color=self.style_manager.font_color if self.style_manager else "#FFFFFF",
            background_color=self.style_manager.bg_secondary if self.style_manager else "#1E1E1E",
            on_command_execute=on_command_execute if is_multi else None
        )
        
        dialog.exec_()
        
        # Put result in queue
        if is_multi:
            # For multi mode, commands already executed via callback, just signal completion
            result_queue.put(None)
        else:
            # For single mode, return the selected command or None
            result_queue.put(dialog.selected_command)
    
    def _execute_macro_steps(self, macro_name: str, steps: list) -> None:
        """Execute macro steps in sequence"""
        # Initialize macro session buffer
        with self.macro_session_lock:
            self.macro_session_active = True
            self.macro_session_buffer.clear()
        
        self._update_macro_status_threadsafe(f"Macro: Running '{macro_name}'")
        self._print_to_display_threadsafe(f"══════════════════════════════════════")
        self._print_to_display_threadsafe(f"  Executing Macro: {macro_name}")
        self._print_to_display_threadsafe(f"══════════════════════════════════════")
        
        for i, step in enumerate(steps, 1):
            try:
                if 'input' in step:
                    # Clear session buffer before sending command
                    # This ensures OutputBlock only sees responses to this command
                    with self.macro_session_lock:
                        self.macro_session_buffer.clear()
                    
                    # Send command
                    command = step['input']
                    self._print_to_display_threadsafe(f"Step {i}: Send command '{command}'")
                    self._set_command_input_threadsafe(command)
                    time.sleep(0.05)  # Small delay to ensure setText completes
                    self._send_command_threadsafe()
                    time.sleep(0.1)  # Small delay for command to be sent
                    
                elif 'delay' in step:
                    # Clear session buffer before delay
                    with self.macro_session_lock:
                        self.macro_session_buffer.clear()
                    
                    # Wait for specified time
                    delay_ms = step['delay']
                    self._print_to_display_threadsafe(f"Step {i}: Delay {delay_ms}ms")
                    time.sleep(delay_ms / 1000.0)
                    
                elif 'dialog_wait' in step:
                    # Clear session buffer before dialog
                    with self.macro_session_lock:
                        self.macro_session_buffer.clear()
                    
                    # Show dialog and wait for user response
                    dialog_config = step['dialog_wait']
                    message = dialog_config.get('message', 'Continue macro execution?')
                    self._print_to_display_threadsafe(f"Step {i}: Dialog wait")
                    
                    # Create a queue to receive the result
                    result_queue: Queue[bool] = Queue()
                    
                    # Show dialog in main thread and wait for response
                    self.macro_dialog_signal.emit(message, result_queue)
                    
                    # Wait for user response (blocking)
                    user_choice = result_queue.get()
                    
                    if not user_choice:
                        # User clicked End
                        self._print_to_display_threadsafe(f"Step {i}: User ended macro")
                        self._print_to_display_threadsafe(f"══════════════════════════════════════")
                        self._print_to_display_threadsafe(f"Macro ENDED by user")
                        self._print_to_display_threadsafe(f"══════════════════════════════════════")
                        self._update_macro_status_threadsafe("Macro: Idle")
                        # Deactivate macro session
                        with self.macro_session_lock:
                            self.macro_session_active = False
                            self.macro_session_buffer.clear()
                        return
                    else:
                        self._print_to_display_threadsafe(f"Step {i}: User continued macro")
                    
                elif 'output' in step:
                    # Expect output
                    output_config = step['output']
                    expected = output_config.get('expected', '')
                    timeout_ms = output_config.get('timeout', 1000)
                    fail_action = output_config.get('fail')
                    success_action = output_config.get('success')
                    substring_match = output_config.get('substring_match', True)
                    
                    match_type = "substring" if substring_match else "full line"
                    self._print_to_display_threadsafe(f"Step {i}: Expect '{expected}' ({match_type}, timeout {timeout_ms}ms)")
                    
                    # Wait and check for expected output
                    received = self._wait_for_response(expected, timeout_ms / 1000.0, substring_match)
                    
                    if not received:
                        self._print_to_display_threadsafe(f"Step {i}: ✗ FAILED - Expected output not received")
                        
                        # Handle fail action
                        if fail_action == "IGNORE":
                            self._print_to_display_threadsafe(f"Step {i}: Ignoring fail, continuing")
                        elif fail_action == "EXIT":
                            self._print_to_display_threadsafe(f"══════════════════════════════════════")
                            self._print_to_display_threadsafe(f"Macro EXITED (fail condition)")
                            self._print_to_display_threadsafe(f"══════════════════════════════════════")
                            self._update_macro_status_threadsafe("Macro: Idle")
                            # Deactivate macro session
                            with self.macro_session_lock:
                                self.macro_session_active = False
                                self.macro_session_buffer.clear()
                            return
                        elif fail_action == "DIALOG":
                            # Show dialog to get custom command from user
                            self._print_to_display_threadsafe(f"Step {i}: Requesting custom command from user")
                            input_queue: Queue[Optional[str]] = Queue()
                            self.macro_input_dialog_signal.emit("Expected output not received. Enter recovery command:", input_queue)
                            
                            # Wait for user input
                            user_command = input_queue.get()
                            
                            if user_command:
                                self._print_to_display_threadsafe(f"Step {i}: User provided command '{user_command}'")
                                self._set_command_input_threadsafe(user_command)
                                time.sleep(0.05)
                                self._send_command_threadsafe()
                                time.sleep(0.1)
                            else:
                                self._print_to_display_threadsafe(f"Step {i}: User cancelled - continuing without action")
                        elif fail_action == "DIALOG_WAIT":
                            # Show dialog and wait for user to continue or end
                            self._print_to_display_threadsafe(f"Step {i}: Waiting for user decision")
                            result_queue: Queue[bool] = Queue()
                            self.macro_dialog_signal.emit("Expected output not received. Do you want to continue?", result_queue)
                            
                            user_choice = result_queue.get()
                            
                            if not user_choice:
                                self._print_to_display_threadsafe(f"Step {i}: User ended macro")
                                self._print_to_display_threadsafe(f"══════════════════════════════════════")
                                self._print_to_display_threadsafe(f"Macro ENDED by user")
                                self._print_to_display_threadsafe(f"══════════════════════════════════════")
                                self._update_macro_status_threadsafe("Macro: Idle")
                                with self.macro_session_lock:
                                    self.macro_session_active = False
                                    self.macro_session_buffer.clear()
                                return
                            else:
                                self._print_to_display_threadsafe(f"Step {i}: User continued macro")
                        elif isinstance(fail_action, dict) and 'input' in fail_action:
                            # Send fail command
                            fail_cmd = fail_action['input']
                            self._print_to_display_threadsafe(f"Step {i}: Send recovery command '{fail_cmd}'")
                            self._set_command_input_threadsafe(fail_cmd)
                            time.sleep(0.05)
                            self._send_command_threadsafe()
                            time.sleep(0.1)
                    else:
                        self._print_to_display_threadsafe(f"Step {i}: ✓ SUCCESS - Received expected output")
                        
                        # Handle success action
                        if success_action == "IGNORE":
                            self._print_to_display_threadsafe(f"Step {i}: Ignoring success, continuing")
                        elif success_action == "EXIT":
                            self._print_to_display_threadsafe(f"══════════════════════════════════════")
                            self._print_to_display_threadsafe(f"Macro EXITED (success condition)")
                            self._print_to_display_threadsafe(f"══════════════════════════════════════")
                            self._update_macro_status_threadsafe("Macro: Idle")
                            with self.macro_session_lock:
                                self.macro_session_active = False
                                self.macro_session_buffer.clear()
                            return
                        elif success_action == "DIALOG":
                            # Show dialog to get custom command from user
                            self._print_to_display_threadsafe(f"Step {i}: Requesting custom command from user")
                            input_queue_success: Queue[Optional[str]] = Queue()
                            self.macro_input_dialog_signal.emit("Expected output received. Enter command:", input_queue_success)
                            
                            user_command_success = input_queue_success.get()
                            
                            if user_command_success:
                                self._print_to_display_threadsafe(f"Step {i}: User provided command '{user_command_success}'")
                                self._set_command_input_threadsafe(user_command_success)
                                time.sleep(0.05)
                                self._send_command_threadsafe()
                                time.sleep(0.1)
                            else:
                                self._print_to_display_threadsafe(f"Step {i}: User cancelled - continuing without action")
                        elif success_action == "DIALOG_WAIT":
                            # Show dialog and wait for user to continue or end
                            self._print_to_display_threadsafe(f"Step {i}: Waiting for user decision")
                            result_queue_success: Queue[bool] = Queue()
                            self.macro_dialog_signal.emit("Expected output received. Do you want to continue?", result_queue_success)
                            
                            user_choice_success = result_queue_success.get()
                            
                            if not user_choice_success:
                                self._print_to_display_threadsafe(f"Step {i}: User ended macro")
                                self._print_to_display_threadsafe(f"══════════════════════════════════════")
                                self._print_to_display_threadsafe(f"Macro ENDED by user")
                                self._print_to_display_threadsafe(f"══════════════════════════════════════")
                                self._update_macro_status_threadsafe("Macro: Idle")
                                with self.macro_session_lock:
                                    self.macro_session_active = False
                                    self.macro_session_buffer.clear()
                                return
                            else:
                                self._print_to_display_threadsafe(f"Step {i}: User continued macro")
                        elif isinstance(success_action, dict) and 'input' in success_action:
                            # Send success command
                            success_cmd = success_action['input']
                            self._print_to_display_threadsafe(f"Step {i}: Send success command '{success_cmd}'")
                            self._set_command_input_threadsafe(success_cmd)
                            time.sleep(0.05)
                            self._send_command_threadsafe()
                            time.sleep(0.1)
                
                elif 'menu_multi' in step:
                    # Menu with multiple command selections
                    menu_config = step['menu_multi']
                    commands = menu_config.get('commands', [])
                    
                    if not commands:
                        self._print_to_display_threadsafe(f"Step {i}: Warning - Menu has no commands")
                        continue
                    
                    self._print_to_display_threadsafe(f"Step {i}: Menu (Multi) - {len(commands)} commands available")
                    
                    # Create a queue to signal when dialog closes
                    command_queue: Queue[Optional[str]] = Queue()
                    
                    # Show menu dialog (commands execute immediately via callback)
                    self.macro_menu_signal.emit(commands, True, command_queue)
                    
                    # Wait for user to click Continue
                    command_queue.get()
                    self._print_to_display_threadsafe(f"Step {i}: Menu (Multi) - User clicked Continue")
                            
                    # # Show menu again for next selection
                    # self.macro_menu_signal.emit(commands, True, command_queue)
                
                elif 'menu_single' in step:
                    # Menu with single command selection
                    menu_config = step['menu_single']
                    commands = menu_config.get('commands', [])
                    
                    if not commands:
                        self._print_to_display_threadsafe(f"Step {i}: Warning - Menu has no commands")
                        continue
                    
                    self._print_to_display_threadsafe(f"Step {i}: Menu (Single) - {len(commands)} commands available")
                    
                    # Create a queue to receive the selected command
                    command_queue: Queue[Optional[str]] = Queue()
                    
                    # Show menu dialog
                    self.macro_menu_signal.emit(commands, False, command_queue)
                    
                    # Wait for user to select a command
                    selected = command_queue.get()
                    
                    if selected:
                        # User selected a command
                        self._print_to_display_threadsafe(f"Step {i}: Menu (Single) - Executing '{selected}'")
                        
                        # Clear session buffer before sending command
                        with self.macro_session_lock:
                            self.macro_session_buffer.clear()
                        
                        self._set_command_input_threadsafe(selected)
                        time.sleep(0.05)
                        self._send_command_threadsafe()
                        time.sleep(0.1)
                    else:
                        self._print_to_display_threadsafe(f"Step {i}: Menu (Single) - User cancelled")
                        
            except Exception as e:
                self._print_to_display_threadsafe(f"Step {i}: ✗ ERROR - {e}")
                self._update_macro_status_threadsafe("Macro: Idle")
                # Deactivate macro session
                with self.macro_session_lock:
                    self.macro_session_active = False
                    self.macro_session_buffer.clear()
                return
        
        self._print_to_display_threadsafe(f"══════════════════════════════════════")
        self._print_to_display_threadsafe(f"Macro '{macro_name}' COMPLETED")
        self._print_to_display_threadsafe(f"══════════════════════════════════════")
        self._update_macro_status_threadsafe("Macro: Idle")
        
        # Deactivate macro session
        with self.macro_session_lock:
            self.macro_session_active = False
            self.macro_session_buffer.clear()
    
    def _wait_for_response(self, expected: str, timeout: float, substring_match: bool = True) -> bool:
        """Wait for expected response from serial port
        
        Args:
            expected: The text to search for
            timeout: Maximum time to wait in seconds
            substring_match: If True, match if expected is found anywhere in line.
                           If False, entire line must match expected exactly.
        """
        start_time = time.time()
        expected_stripped = expected.strip()
        
        # Check if the response is already in the session buffer
        with self.macro_session_lock:
            for line in self.macro_session_buffer:
                line_stripped = line.strip()
                if substring_match:
                    if expected_stripped in line_stripped:
                        return True
                else:
                    if expected_stripped == line_stripped:
                        return True
        
        # If not found in buffer, wait for new data to arrive in the session buffer
        while time.time() - start_time < timeout:
            with self.macro_session_lock:
                # Check entire session buffer for the expected response
                for line in self.macro_session_buffer:
                    line_stripped = line.strip()
                    if substring_match:
                        if expected_stripped in line_stripped:
                            return True
                    else:
                        if expected_stripped == line_stripped:
                            return True
            
            time.sleep(0.01)  # Small sleep to avoid busy waiting
        
        return False

    def tab_settings_set(self) -> None:
        settings = self.settings.get("general", {})

        auto_clear_item = QTableWidgetItem(str(settings.get("auto_clear_output", False)))
        self.settings_table.setItem(0, 1, auto_clear_item)
        # Row 1: DTR (bool)
        dtr_item = QTableWidgetItem(str(settings.get("dtr_state", False)))
        self.settings_table.setItem(1, 1, dtr_item)
        # Row 2: RTS (bool)
        rts_item = QTableWidgetItem(str(settings.get("rts_state", False)))
        self.settings_table.setItem(2, 1, rts_item)
        # Row 3: maximized (bool)
        maximized_item = QTableWidgetItem(str(settings.get("maximized", False)))
        self.settings_table.setItem(3, 1, maximized_item)
        # Row 4: tx line ending
        tx_line_ending_item = QTableWidgetItem(str(settings.get("tx_line_ending", "CRLN")))
        self.settings_table.setItem(4, 1, tx_line_ending_item)
        # Row 5: Data bits: 8,7,6,5
        data_bits = QTableWidgetItem(str(settings.get("data_bits", "8")))
        self.settings_table.setItem(5, 1, data_bits)
        # Row 6: parity: None, Even, Odd, Space, Mark
        parity = QTableWidgetItem(str(settings.get("parity", "None")))
        self.settings_table.setItem(6, 1, parity)
        # Row 7: Stop bits: 1, 2
        stop_bits = QTableWidgetItem(str(settings.get("stop_bits", "1")))
        self.settings_table.setItem(7, 1, stop_bits)
        # Row 8: Flow Control: None, Hardware, Software
        flow_control = QTableWidgetItem(str(settings.get("flow_control", "None")))
        self.settings_table.setItem(8, 1, flow_control)
        # Row 9: Open mode: Read/Write, Read only, Write only
        open_mode = QTableWidgetItem(str(settings.get("open_mode", "Read/Write")))
        self.settings_table.setItem(9, 1, open_mode)
        # Row 10: reveal_hidden_char (bool)
        reveal_hidden_char_item = QTableWidgetItem(str(settings.get("reveal_hidden_char", False)))
        self.settings_table.setItem(10, 1, reveal_hidden_char_item)
        # Row 11: max_output_lines (int)
        max_output_lines_item = QTableWidgetItem(str(settings.get("max_output_lines", 10000)))
        self.settings_table.setItem(11, 1, max_output_lines_item)
        # Row 12: custom-baudrate (int)
        custom_baud_rate_item = QTableWidgetItem(str(settings.get("custom-baudrate", 115200)))
        self.settings_table.setItem(12, 1, custom_baud_rate_item)
        # Row 13: enable_tooltips (bool)
        enable_tooltips_item = QTableWidgetItem(str(settings.get("enable_tooltips", True)))
        self.settings_table.setItem(13, 1, enable_tooltips_item)
        # Row 14: filter_empty_lines (bool)
        filter_empty_lines_item = QTableWidgetItem(str(settings.get("filter_empty_lines", False)))
        self.settings_table.setItem(14, 1, filter_empty_lines_item)
        # Row 15: custom_line_filter (string)
        custom_line_filter_item = QTableWidgetItem(str(settings.get("custom_line_filter", "")))
        self.settings_table.setItem(15, 1, custom_line_filter_item)
        # Row 16: show_flow_indicators (bool)
        show_flow_indicators_item = QTableWidgetItem(str(settings.get("show_flow_indicators", True)))
        self.settings_table.setItem(16, 1, show_flow_indicators_item)
        # Row 17: disconnect_on_inactive (bool)
        disconnect_on_inactive_item = QTableWidgetItem(str(settings.get("disconnect_on_inactive", False)))
        self.settings_table.setItem(17, 1, disconnect_on_inactive_item)

    def tab_settings(self) -> None:

        self.settings_tab: QWidget = QWidget()
        self.settings_layout: QVBoxLayout = QVBoxLayout(self.settings_tab)

        # Settings table
        self.settings_table = QTableWidget()
        self.settings_table.setToolTip("Double-click a value to edit.")
        self.settings_table.setRowCount(18)
        self.settings_table.setColumnCount(2)
        self.settings_table.setHorizontalHeaderLabels(["Setting", "Value"])
        v_header = self.settings_table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        self.settings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.settings_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        h_header = self.settings_table.horizontalHeader()
        if h_header:
            h_header.setStretchLastSection(True)
        self.settings_table.setColumnWidth(0, int(self.left_panel_width * 0.5))

        # Populate settings
        settings = self.settings.get("general", {})
        
        self.settings_table.setItem(0, 0, QTableWidgetItem("Auto Clear Output"))
        self.settings_table.setItem(1, 0, QTableWidgetItem("DTR"))
        self.settings_table.setItem(2, 0, QTableWidgetItem("RTS"))
        self.settings_table.setItem(3, 0, QTableWidgetItem("Maximized"))
        self.settings_table.setItem(4, 0, QTableWidgetItem("Tx line Ending"))
        self.settings_table.setItem(5, 0, QTableWidgetItem("Data Bits"))
        self.settings_table.setItem(6, 0, QTableWidgetItem("Parity"))
        self.settings_table.setItem(7, 0, QTableWidgetItem("Stop Bits"))
        self.settings_table.setItem(8, 0, QTableWidgetItem("Flow Control"))
        self.settings_table.setItem(9, 0, QTableWidgetItem("Open Mode"))
        self.settings_table.setItem(10, 0, QTableWidgetItem("Reveal Hidden Char"))
        self.settings_table.setItem(11, 0, QTableWidgetItem("Max Output Lines"))
        self.settings_table.setItem(12, 0, QTableWidgetItem("Custom Baud Rate"))
        self.settings_table.setItem(13, 0, QTableWidgetItem("Enable Tooltips"))
        self.settings_table.setItem(14, 0, QTableWidgetItem("Filter Empty Lines"))
        self.settings_table.setItem(15, 0, QTableWidgetItem("Custom Line Filter"))
        self.settings_table.setItem(16, 0, QTableWidgetItem("Show Flow Indicators"))
        self.settings_table.setItem(17, 0, QTableWidgetItem("Disconnect On Inactive"))

        self.tab_settings_set()

        self.settings_layout.addWidget(self.settings_table)

        # Handle editing
        def edit_setting(row: int, column: int) -> None:
            item = self.settings_table.item(row, 0)
            if item is None:
                return
            key = item.text()
            
            general = self.settings["general"]

            # Boolean options
            if key in ("Auto Clear Output", "Maximized", "Reveal Hidden Char", "DTR", "RTS", "Enable Tooltips", "Filter Empty Lines", "Show Flow Indicators", "Disconnect On Inactive"):
                value_item = self.settings_table.item(row, 1)
                if value_item is None:
                    return
                current = str(value_item.text()).lower() == "true"
                new_value = not current
                self.settings_table.setItem(row, 1, QTableWidgetItem(str(new_value)))
                # Update corresponding key in settings
                if key == "Auto Clear Output":
                    general["auto_clear_output"] = new_value
                elif key == "Maximized":
                    general["maximized"] = new_value
                elif key == "Reveal Hidden Char":
                    general["reveal_hidden_char"] = new_value
                elif key == "Filter Empty Lines":
                    general["filter_empty_lines"] = new_value
                elif key == "Show Flow Indicators":
                    general["show_flow_indicators"] = new_value
                elif key == "Disconnect On Inactive":
                    general["disconnect_on_inactive"] = new_value
                    self.update_connect_button_appearance()
                elif key == "DTR":
                    general["dtr_state"] = new_value
                    # Update serial port if connected
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.dtr = new_value
                elif key == "RTS":
                    general["rts_state"] = new_value
                    # Update serial port if connected
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.rts = new_value
                elif key == "Enable Tooltips":
                    general["enable_tooltips"] = new_value
                    self.update_tooltips_visibility()
                    # Update serial port if connected
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.rts = new_value
                self.save_settings()

            # Drop-down / list options
            elif key == "Tx line Ending":
                items = [opt[0] for opt in self.OPTIONS['tx_line_ending']]
                value_item = self.settings_table.item(row, 1)
                if value_item is None:
                    return
                current_value = value_item.text()
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit TX Line Ending", "Select new line ending:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["tx_line_ending"] = new_value
                    self.save_settings()

            elif key == "Data Bits":
                items = [str(x) for x in self.OPTIONS['data_bits']]
                current_value = str(general.get("data_bits", 8))
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit Data Bits", "Select data bits:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["data_bits"] = int(new_value)
                    self.save_settings()

            elif key == "Parity":
                items = [x[0] for x in self.OPTIONS['parity']]
                current_value = general.get("parity", "None")
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit Parity", "Select parity:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["parity"] = new_value
                    self.save_settings()

            elif key == "Stop Bits":
                items = [str(x) for x in self.OPTIONS['stop_bits']]
                current_value = str(general.get("stop_bits", 1))
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit Stop Bits", "Select stop bits:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["stop_bits"] = int(new_value)
                    self.save_settings()

            elif key == "Flow Control":
                items = [x[0] for x in self.OPTIONS['flow_control']]
                current_value = general.get("flow_control", "None")
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit Flow Control", "Select flow control:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["flow_control"] = new_value
                    self.save_settings()

            elif key == "Open Mode":
                items = [x[0] for x in self.OPTIONS['open_mode']]
                current_value = general.get("open_mode", "R/W")
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit Open Mode", "Select open mode:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["open_mode"] = new_value
                    self.save_settings()

            elif key == "Custom Baud Rate":
                current_value = str(general.get("custom-baudrate", 115200))
                new_value, ok = QInputDialog.getText(self, "Edit Custom Baud Rate", "Enter custom baud rate:", text=current_value)
                if ok and new_value:
                    new_value = abs(int(new_value))
                    self.settings_table.setItem(row, 1, QTableWidgetItem(str(new_value)))
                    general["custom-baudrate"] = new_value
                    self.save_settings()

            elif key == "Max Output Lines":
                current_value = str(general.get("max_output_lines", 10000))
                new_value, ok = QInputDialog.getText(self, "Edit Max Output Lines", "Enter maximum number of lines to keep in output display:\n(Prevents unlimited memory growth)", text=current_value)
                if ok and new_value:
                    new_value = max(100, abs(int(new_value)))  # Minimum 100 lines
                    self.settings_table.setItem(row, 1, QTableWidgetItem(str(new_value)))
                    general["max_output_lines"] = new_value
                    doc = self.response_display.document()
                    if doc:
                        doc.setMaximumBlockCount(new_value)
                    self.save_settings()
            
            elif key == "Custom Line Filter":
                current_value = str(general.get("custom_line_filter", ""))
                new_value, ok = QInputDialog.getText(self, "Edit Custom Line Filter", "Enter line to filter (exact match, stripped):\n(Leave blank to disable)", text=current_value)
                if ok:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["custom_line_filter"] = new_value
                    self.save_settings()

        self.settings_table.cellDoubleClicked.connect(edit_setting)

        # Add a button to open a file manager to select a custom commands directory
        commands_button = QPushButton("Open Configurations Directory")
        commands_button.setToolTip("Open the directory where command YAML files are stored")
        commands_button.clicked.connect(self.open_configurations_directory)
        self.settings_layout.addWidget(commands_button)

        # Add a reset to defaults button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.setToolTip("Restore all settings to their default values")
        self.settings_layout.addWidget(reset_button)

        def reset_to_defaults() -> None:
            # First confirmation
            reply = QMessageBox.question(
                self,
                "Reset to Defaults",
                "Are you sure you want to reset all settings to default values?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Ask about backup
                backup_reply = QMessageBox.question(
                    self,
                    "Backup Current Settings",
                    "Would you like to backup your current settings before resetting?\n\nNote: Only one backup can be stored. This will overwrite any previous backup.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if backup_reply == QMessageBox.Yes:
                    # Save backup
                    backup_file = os.path.join(self.app_configs_path, "settings_backup.yaml")
                    try:
                        with open(backup_file, "w") as f:
                            yaml.dump(self.settings, f, default_flow_style=False)
                        QMessageBox.information(self, "Backup Saved", "Current settings have been backed up to settings_backup.yaml")
                    except Exception as e:
                        QMessageBox.critical(self, "Backup Error", f"Failed to backup settings: {e}")
                        return
                
                # Reset to defaults
                self.settings = self.default_settings.copy()
                self.save_settings()
                self.set_style()
                self.tab_settings_set()
                QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")

        reset_button.clicked.connect(reset_to_defaults)

    def tab_about(self) -> None:
        """Create the About tab with application information"""
        self.about_tab: QWidget = QWidget()
        about_layout: QVBoxLayout = QVBoxLayout(self.about_tab)
        about_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Application title
        title_label = QLabel("Serial Communication Monitor")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(title_label)
        
        about_layout.addSpacing(20)
        
        # Version info
        version_label = QLabel(f"Version: {__version__}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(version_label)
        
        about_layout.addSpacing(10)
        
        # Description
        description = QLabel(
            "A powerful serial communication tool for monitoring and debugging "
            "serial devices. Features include command history, macros, and "
            "customizable settings."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(description)
        
        about_layout.addSpacing(20)
        
        # GitHub link (if applicable)
        github_label = QLabel('<a href="https://github.com/DJA-prog/Serial-Gui">GitHub Repository</a>')
        github_label.setOpenExternalLinks(True)
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(github_label)
        
        about_layout.addStretch()
        
        # Manual button
        manual_button = QPushButton("User Manual")
        manual_button.clicked.connect(self.open_manual_dialog)
        about_layout.addWidget(manual_button)
        
        # Themes button at the bottom
        themes_button = QPushButton("Select Theme")
        themes_button.clicked.connect(self.open_themes_dialog)
        about_layout.addWidget(themes_button)

    def open_configurations_directory(self, config_path: Path) -> None:
        """Opens the configuration directory in the system's file manager."""
        if not self.app_configs_path:
            QMessageBox.warning(self, "Error", "Configuration directory path is not set.")
            return

        try:
            system = platform.system()
            if system == "Windows":
                # Avoid linter error by checking attribute existence
                if hasattr(os, "startfile"):
                    os.startfile(self.app_configs_path)  # type: ignore[attr-defined]
                else:
                    print("os.startfile is not available on this platform.")
            elif system == "Darwin":
                subprocess.run(["open", self.app_configs_path], check=False)
            else:  # Linux / Unix
                subprocess.run(["xdg-open", self.app_configs_path], check=False)
        except Exception as e:
            print(f"Failed to open configuration directory: {e}")

    def open_manual_dialog(self) -> None:
        """Opens the user manual dialog"""
        dialog = ManualDialog(parent=self)
        dialog.exec_()
    
    def open_themes_dialog(self) -> None:
        """Opens the themes selection dialog"""
        dialog = ThemesDialog(
            parent=self,
            current_settings=self.settings.get('general', {}),
            apply_callback=self.apply_theme_settings
        )
        dialog.exec_()
    
    def apply_theme_settings(self, theme_settings: Dict[str, str]) -> None:
        """
        Apply theme settings and update the UI
        
        Args:
            theme_settings: Dictionary containing color settings
        """
        # Update settings
        for key, value in theme_settings.items():
            self.settings['general'][key] = value
        
        # Save settings to file
        self.save_settings()
        
        # Apply the new style
        self.set_style()

    def save_settings(self) -> None:
        if DEBUG_ENABLED:
            self.debug_handler.log("Saving settings to file", "DEBUG")
            
        # Always update the version to track which app version last edited the settings
        self.settings['general']['app_version'] = __version__
        
        settings_file = os.path.join(self.app_configs_path, "settings.yaml")
        try:
            with self.debug_handler.capture_context("Save Settings"):
                with open(settings_file, "w") as f:
                    yaml.dump(self.settings, f, default_flow_style=False)
        except Exception as e:
            if DEBUG_ENABLED:
                self.debug_handler.log(f"Failed to save settings: {e}", "ERROR")
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")

    def confirm_clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Command History",
            "Are you sure you want to clear all command history? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            history_file = os.path.join(self.app_configs_path, "command_history.txt")
            try:
                if os.path.exists(history_file):
                    os.remove(history_file)
                self.command_history_list.clear()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear history: {e}")

    def send_history_command(self, command: str) -> None:
        """Send a command from history immediately"""
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "Not Connected", "Please connect to a serial port first.")
            return
        
        # Set the command in the input field
        self.command_input.setText(command)
        # Trigger the send
        self.send_command()

    def create_right_panel(self) -> None:
        """
        Creates the right panel of the main window, which includes the response display area,
        predefined command buttons, and status indicators for serial connections.
        """
        # Right layout: Response display
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setToolTip("Serial communication output display. Right-click for options.")
        max_lines = self.settings.get('general', {}).get('max_output_lines', 10000)
        doc = self.response_display.document()
        if doc:
            doc.setMaximumBlockCount(max_lines)
        self.response_display.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.response_display.customContextMenuRequested.connect(self.show_output_context_menu)
        self.middle_layout.addWidget(self.response_display)

    def create_bottom_panel(self) -> None:
        """
        Creates the bottom panel of the main window, which includes the status indicators for
        serial connections, and connected time.
        """
        # Bottom layout: Predefined commands and status indicators
        bottom_layout = QVBoxLayout()

        # Predefined commands
        predefined_layout = QHBoxLayout()

        self.toggle_panel_button = QPushButton("◀ Hide Panel")
        self.toggle_panel_button.clicked.connect(self.toggle_left_panel)
        self.toggle_panel_button.setToolTip("Show/hide the left panel")
        predefined_layout.addWidget(self.toggle_panel_button)

        for key, button in self.settings["quick_buttons"].items():
            if isinstance(button, dict):
                label = button.get('label', '')
                tooltip = button.get('tooltip', '')
                command = button.get('command', '')

                btn = QPushButton(label if label else "---")
                btn.setToolTip(tooltip)
                btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                btn.customContextMenuRequested.connect(lambda pos, k=key: self.show_button_context_menu(pos, k))
                
                # Always keep button enabled so context menu works, but connect handler that checks for command
                btn.clicked.connect(lambda _, k=key: self.execute_button_command(k))
                
                self.custom_buttons[key] = btn
                predefined_layout.addWidget(btn)


        self.save_output_button = QPushButton("Save output")
        self.save_output_button.clicked.connect(self.save_output)
        self.save_output_button.setToolTip("Save the content of the response display to a file")

        self.clear_button = QPushButton("Clear output")
        self.clear_button.clicked.connect(self.clear_output)
        self.clear_button.setToolTip("Clear all text from the output display")
        

        predefined_layout.addWidget(self.save_output_button)
        predefined_layout.addWidget(self.clear_button)
        bottom_layout.addLayout(predefined_layout)

        # Status indicators
        status_layout = QHBoxLayout()

        # Serial status
        self.serial_status_label = QLabel("Serial: Disconnected")
        self.serial_status_light = QLabel()
        self.serial_status_light.setFixedSize(10, 10)
        self.serial_status_light.setStyleSheet("background-color: red; border: 1px solid black; border-radius: 5px;")
        serial_status_container = QHBoxLayout()
        serial_status_container.addWidget(self.serial_status_label)
        serial_status_container.addWidget(self.serial_status_light)
        serial_status_container.addStretch()
        status_layout.addLayout(serial_status_container)

        # Connected time
        self.connected_time_label = QLabel("Connected Time: 00:00:00")
        connected_time_container = QHBoxLayout()
        connected_time_container.addWidget(self.connected_time_label)
        connected_time_container.addStretch()
        status_layout.addLayout(connected_time_container)

        # Macro status
        self.macro_status_label = QLabel("Macro: Idle")
        macro_status_container = QHBoxLayout()
        macro_status_container.addWidget(self.macro_status_label)
        macro_status_container.addStretch()
        status_layout.addLayout(macro_status_container)

        # Line count percentage
        self.line_count_label = QLabel("Lines: 0 / 10000 (0%)")
        line_count_container = QHBoxLayout()
        line_count_container.addWidget(self.line_count_label)
        line_count_container.addStretch()
        status_layout.addLayout(line_count_container)

        bottom_layout.addLayout(status_layout)

        self.main_layout.addLayout(bottom_layout)

    def update_line_count_display(self) -> None:
        """
        Updates the line count percentage display in the status bar.
        """
        doc = self.response_display.document()
        if doc:
            current_lines = doc.blockCount()
            max_lines = self.settings.get('general', {}).get('max_output_lines', 10000)
            percentage = (current_lines / max_lines * 100) if max_lines > 0 else 0
            self.line_count_label.setText(f"Lines: {current_lines} / {max_lines} ({percentage:.1f}%)")

    def save_checkbox_state(self, setting_name: str, value: bool) -> None:
        """
        Saves checkbox state to settings.
        """
        self.settings['general'][setting_name] = value
        self.save_settings()

    def save_current_tab(self, index: int) -> None:
        """
        Saves the current tab index to settings.
        """
        self.settings['general']['last_tab_index'] = index
        self.save_settings()

    def show_output_context_menu(self, pos) -> None:
        """
        Shows a context menu for the output display with options to toggle hex/text and timestamps.
        """
        menu = QMenu(self)
        
        # Copy and Select All actions
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.response_display.copy)
        copy_action.setEnabled(self.response_display.textCursor().hasSelection())
        
        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.response_display.selectAll)
        
        menu.addAction(copy_action)
        menu.addAction(select_all_action)
        menu.addSeparator()
        
        # Display format toggle
        current_format = self.settings.get('general', {}).get('display_format', 'text')
        if current_format == 'text':
            format_action = QAction("Switch to Hex Display", self)
            format_action.triggered.connect(lambda: self.toggle_display_format('hex'))
        else:
            format_action = QAction("Switch to Text Display", self)
            format_action.triggered.connect(lambda: self.toggle_display_format('text'))
        
        # Timestamp toggle
        show_timestamps = self.settings.get('general', {}).get('show_timestamps', False)
        if show_timestamps:
            timestamp_action = QAction("Hide Timestamps", self)
            timestamp_action.triggered.connect(lambda: self.toggle_timestamps(False))
        else:
            timestamp_action = QAction("Show Timestamps", self)
            timestamp_action.triggered.connect(lambda: self.toggle_timestamps(True))
        
        menu.addAction(format_action)
        menu.addAction(timestamp_action)
        
        menu.exec_(self.response_display.mapToGlobal(pos))

    def toggle_display_format(self, new_format: str) -> None:
        """
        Toggles between text and hex display format.
        """
        self.settings['general']['display_format'] = new_format
        self.save_settings()
        QMessageBox.information(
            self,
            "Display Format Changed",
            f"Display format changed to {new_format.upper()}.\nNew messages will be displayed in {new_format.upper()} format."
        )

    def toggle_timestamps(self, show: bool) -> None:
        """
        Toggles timestamp display for output messages.
        """
        self.settings['general']['show_timestamps'] = show
        self.save_settings()
        status = "enabled" if show else "disabled"
        QMessageBox.information(
            self,
            "Timestamp Display Changed",
            f"Timestamps have been {status}.\nNew messages will {'include' if show else 'not include'} timestamps."
        )

    def execute_button_command(self, key: str) -> None:
        """
        Executes the command associated with a quick button key, if it exists.
        """
        button_settings = self.settings['quick_buttons'].get(key, {})
        command = button_settings.get('command', '')
        if command:
            self.send_predefined_command(command)

    def show_button_context_menu(self, pos, key: str) -> None:
        """
        Shows a context menu for the custom buttons with Edit and Clear options.
        """
        btn = self.custom_buttons.get(key)
        if not btn:
            return
            
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        clear_action = QAction("Clear", self)
        
        edit_action.triggered.connect(lambda: self.edit_button(key))
        clear_action.triggered.connect(lambda: self.clear_button_functionality(key))
        
        menu.addAction(edit_action)
        menu.addAction(clear_action)
        
        menu.exec_(btn.mapToGlobal(pos))

    def edit_button(self, key: str) -> None:
        """
        Opens a dialog to edit the quick button's name and command.
        """
        current_settings = self.settings['quick_buttons'].get(key, {})
        current_label = current_settings.get('label', '')
        current_command = current_settings.get('command', '')
        
        # Create a custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Quick Button")
        dialog.setModal(True)
        dialog_layout = QVBoxLayout(dialog)
        
        # Name field
        name_label = QLabel("Button Name:")
        name_label.setToolTip("The text to display on the button")
        name_input = QLineEdit(current_label)
        name_input.setPlaceholderText("Enter button text (e.g., 'Status', 'Reset')")
        name_input.setToolTip("The text to display on the button")
        dialog_layout.addWidget(name_label)
        dialog_layout.addWidget(name_input)
        
        # Command field
        command_label = QLabel("Command:")
        command_label.setToolTip("The command to execute when the button is clicked")
        command_input = QLineEdit(current_command)
        command_input.setPlaceholderText("Enter command (e.g., 'AT+CSQ', 'AT+CPIN?')")
        command_input.setToolTip("The command to execute when the button is clicked")
        dialog_layout.addWidget(command_label)
        dialog_layout.addWidget(command_input)
        
        # Tooltip field
        current_tooltip = current_settings.get('tooltip', '')
        tooltip_label = QLabel("Tooltip:")
        tooltip_label.setToolTip("The tooltip to show when hovering over the button")
        tooltip_input = QLineEdit(current_tooltip)
        tooltip_input.setPlaceholderText("Enter tooltip description (optional)")
        tooltip_input.setToolTip("The tooltip to show when hovering over the button")
        dialog_layout.addWidget(tooltip_label)
        dialog_layout.addWidget(tooltip_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)
        
        def on_ok():
            new_label = name_input.text().strip()
            new_command = command_input.text().strip()
            new_tooltip = tooltip_input.text().strip()
            
            # Update settings
            self.settings['quick_buttons'][key] = {
                'label': new_label,
                'command': new_command,
                'tooltip': new_tooltip
            }
            self.save_settings()
            
            # Update button
            btn = self.custom_buttons.get(key)
            if btn:
                if new_label and new_command:
                    btn.setText(new_label)
                else:
                    btn.setText("---")
                btn.setToolTip(new_tooltip)
            
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
        
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)
        
        dialog.exec_()

    def clear_button_functionality(self, key: str) -> None:
        """
        Clears the quick button functionality, sets text to '---'.
        """
        # Update settings
        self.settings['quick_buttons'][key] = {
            'label': '',
            'command': '',
            'tooltip': ''
        }
        self.save_settings()
        
        # Update button
        btn = self.custom_buttons.get(key)
        if btn:
            btn.setText("---")

    def save_output(self) -> None:
        """
        Saves the content of the response display to a file.
        Opens a file dialog to choose the save location and filename.
        Suggests a filename as "output_save_<date>_<time>.txt".
        """
        if len(self.response_display.toPlainText()) == 0:
            QMessageBox.warning(self, "No Output", "There is no output to save.")
            return
        # print("save_output called")
        now = datetime.now()
        suggested_name = f"output_save_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output",
            suggested_name,
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        if file_name:
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(self.response_display.toPlainText())
                QMessageBox.information(self, "Success", "Output saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save output: {e}")

    def update_tab_input_history(self) -> None:
        history: list[str] = []
        history_file = os.path.join(self.app_configs_path, "command_history.txt")
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = f.read().splitlines()
        self.history = history.copy()
        self.history_index = len(self.history)
        self.command_history_list.clear()
        self.command_history_list.addItems(reversed(history))

    def load_settings(self) -> None:
        """
        Loads settings from a YAML file and populates the configuration table.
        If the file does not exist, it initializes with default values.
        """
        if DEBUG_ENABLED:
            self.debug_handler.log("Loading settings from file", "DEBUG")
            
        settings_file = os.path.join(self.app_configs_path, "settings.yaml")
        if os.path.exists(settings_file):
            try:
                with self.debug_handler.capture_context("Load Settings"):
                    with open(settings_file, "r") as f:
                        settings = yaml.safe_load(f)
                        # print(f"Loaded settings: {settings}")
            except Exception as e:
                if DEBUG_ENABLED:
                    self.debug_handler.log(f"Failed to load settings: {e}", "ERROR")
                raise
                
            if settings:
                # Migrate from old 'buttons' to 'quick_buttons' format
                if 'buttons' in settings and 'quick_buttons' not in settings:
                    settings['quick_buttons'] = settings.pop('buttons')
                
                # Remove hard-coded options from settings if they exist
                if 'general' in settings:
                    options_to_remove = [
                        'options-auto_clear_output',
                        'options-data_bits',
                        'options-flow_control',
                        'options-maximized',
                        'options-open_mode',
                        'options-parity',
                        'options-stop_bits',
                        'options-tx_line_ending'
                    ]
                    for option in options_to_remove:
                        settings['general'].pop(option, None)
                
                self.settings = settings
                # print(f"Settings loaded: {self.settings}")
            
            self.save_settings()

    def get_serial_ports(self) -> list[str]:
        ports = serial.tools.list_ports.comports()
        # Filter out unwanted devices (ttyS on Linux, which are typically built-in ports that don't work well)
        # On Windows, this filter won't match anything (COM ports don't contain "ttyS")
        return [port.device for port in ports if "ttyS" not in port.device]
    
    def is_port_in_use(self, port_name: str) -> bool:
        """Check if a serial port is currently in use by attempting to open it."""
        # Skip check if this is our currently connected port
        if self.serial_port and self.serial_port.is_open and self.serial_port.port == port_name:
            return False  # Our own port is available to us
        
        try:
            # Try to open the port briefly
            test_port = serial.Serial(port_name, timeout=0)
            test_port.close()
            return False  # Port is available
        except (serial.SerialException, OSError):
            return True  # Port is in use or inaccessible
    
    def populate_port_combo(self) -> None:
        """Populate the port combo box with availability tooltips."""
        # Save current selection
        current_text = self.port_combo.currentText()
        
        # Create a new model
        model = QStandardItemModel()
        
        # Add items with tooltips
        for port in self.available_ports:
            item = QStandardItem(port)
            
            # Check if port is in use and set tooltip
            if self.is_port_in_use(port):
                item.setToolTip(f"{port} - Currently in use")
            else:
                item.setToolTip(f"{port} - Available")
            
            model.appendRow(item)
        
        # Set the model on the combo box
        self.port_combo.setModel(model)
        
        # Restore previous selection if it still exists
        if current_text:
            index = self.port_combo.findText(current_text)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def print_to_display(self, message: str) -> None:
        # Store original message for processing
        original_message = message
        timestamp_prefix = ""
        flow_indicator = ""
        
        # Add timestamp if enabled
        if self.settings.get("general", {}).get("show_timestamps", False):
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # milliseconds
            timestamp_prefix = f"[{timestamp}] "
        
        # Extract flow indicator (< or >) if present
        has_flow_indicator = False
        if original_message.startswith("< "):
            flow_indicator = "< "
            original_message = original_message[2:]
            has_flow_indicator = True
        elif original_message.startswith("> "):
            flow_indicator = "> "
            original_message = original_message[2:]
            has_flow_indicator = True
        
        # Convert to hex if enabled - but ONLY for actual serial data (messages with flow indicators)
        display_format = self.settings.get("general", {}).get("display_format", "text")
        if display_format == "hex" and has_flow_indicator:
            # Convert only the message content to hex
            try:
                hex_representation = ' '.join(f'{ord(c):02X}' for c in original_message.strip())
                message = f"{timestamp_prefix}{flow_indicator}{hex_representation}"
            except:
                # If conversion fails, keep original with timestamp and flow indicator
                message = f"{timestamp_prefix}{flow_indicator}{original_message}"
        else:
            # Text mode - apply reveal hidden characters if enabled (only for serial data)
            if self.settings.get("general", {}).get("reveal_hidden_char", False) and has_flow_indicator:
                original_message = self.reveal_hidden_characters(flow_indicator + original_message)
                # Remove flow indicator as it was added back by reveal_hidden_characters
                if original_message.startswith(flow_indicator):
                    original_message = original_message[len(flow_indicator):]
            message = f"{timestamp_prefix}{flow_indicator}{original_message}"
        
        self.response_display.append(message.strip())
        self.update_line_count_display()

    def reveal_hidden_characters(self, message: str) -> str:
        """
        Replace hidden/whitespace characters with visible symbols
        so the user can see them in the QTextEdit.
        Exceptions:
            - If the string starts with '> ' or '< ', the first space is preserved.
        """
        # Check for special cases
        preserve_prefixes = ("> ", "< ")
        preserve_first_space = message.startswith(preserve_prefixes)

        replacements = {
            " ": "·",     # middle dot for space
            "\t": "→   ", # arrow for tab (plus spacing)
            "\n": "⏎\n",  # return symbol for newline
            "\r": "␍",    # carriage return
        }

        if preserve_first_space:
            # Keep prefix as-is, process the rest
            prefix = message[:2]   # either "> " or "< "
            rest = message[2:]
            for hidden, symbol in replacements.items():
                rest = rest.replace(hidden, symbol)
            return prefix + rest
        else:
            # Normal case — replace everything
            for hidden, symbol in replacements.items():
                message = message.replace(hidden, symbol)
            return message

    def refresh_serial_ports(self) -> None:
        current_ports = self.get_serial_ports()

        # Always repopulate to update colors, even if port list hasn't changed
        if current_ports != self.available_ports:
            self.available_ports = current_ports
        
        # Repopulate with color-coded entries
        self.populate_port_combo()

        # Auto-reconnect if needed
        if self.auto_reconnect_checkbox.isChecked():
            # Use the last connected port from settings, not the current combo selection
            last_port = self.settings.get('general', {}).get('last_serial_port', '')
            
            # Only attempt reconnect if:
            # 1. We have a saved port
            # 2. The saved port is available in current ports
            # 3. Serial port is not already open
            if last_port and last_port in current_ports and (not self.serial_port or not self.serial_port.is_open):
                # Set the combo box to the correct port before reconnecting
                index = self.port_combo.findText(last_port)
                if index >= 0:
                    self.port_combo.setCurrentIndex(index)
                    self.print_to_display(f"Attempting auto-reconnect to {last_port}...")
                    try:
                        self.connect_serial()
                    except Exception as e:
                        self.print_to_display(f"Auto-reconnect failed: {e}")

    def toggle_connection(self) -> None:
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def apply_serial_settings(self) -> None:
        """Apply settings from self.settings to the serial port if it's open."""
        if not self.serial_port or not self.serial_port.is_open:
            return

        general = self.settings.get("general", {})

        # Data bits
        data_bits = general.get("data_bits", 8)
        self.serial_port.bytesize = {
            5: serial.FIVEBITS,
            6: serial.SIXBITS,
            7: serial.SEVENBITS,
            8: serial.EIGHTBITS
        }.get(data_bits, serial.EIGHTBITS)

        # Parity
        parity = general.get("parity", "None")
        self.serial_port.parity = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD,
            "Mark": serial.PARITY_MARK,
            "Space": serial.PARITY_SPACE
        }.get(parity, serial.PARITY_NONE)

        # Stop bits
        stop_bits = general.get("stop_bits", 1)
        self.serial_port.stopbits = {
            1: serial.STOPBITS_ONE,
            1.5: serial.STOPBITS_ONE_POINT_FIVE,
            2: serial.STOPBITS_TWO
        }.get(stop_bits, serial.STOPBITS_ONE)

        # Flow control (pyserial handles RTS/CTS and XON/XOFF)
        flow = general.get("flow_control", "None")
        self.serial_port.xonxoff = flow.lower() == "software"
        self.serial_port.rtscts = flow.lower() == "hardware"
        self.serial_port.dsrdtr = False  # Not using DSR/DTR hardware flow by default

    def connect_serial(self) -> None:
        port = self.port_combo.currentText()
        baud_rate = self.baud_rate_combo.currentText()
        
        if DEBUG_ENABLED:
            self.debug_handler.log(f"Attempting to connect to {port} at {baud_rate} baud", "INFO")

        if self.settings.get("general", {}).get("last-baudrate", 115200) != baud_rate:
            self.settings["general"]["last-baudrate"] = baud_rate
            self.save_settings()
        
        # Save last connected serial port
        self.settings["general"]["last_serial_port"] = port
        self.save_settings()

        if baud_rate == "Custom":
            baud_rate = self.settings.get("general", {}).get("custom-baudrate", 115200)

        baud_rate = int(baud_rate)

        try:
            with self.debug_handler.capture_context(f"Serial Connection to {port}"):
                if os.name == "posix":
                    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_EXCL)
                    self.serial_port = serial.Serial()
                    self.serial_port.port = port
                    self.serial_port.baudrate = baud_rate
                    self.serial_port.timeout = 1
                    self.serial_port.open()
                    os.close(fd)
                else:
                    self.serial_port = serial.Serial(port, baudrate=baud_rate, timeout=1)

                # Apply additional serial settings
                self.apply_serial_settings()

                # Set DTR/RTS from settings
                self.serial_port.dtr = self.settings.get('general', {}).get('dtr_state', False)
                self.serial_port.rts = self.settings.get('general', {}).get('rts_state', False)

                # Start the serial reader thread
                self.serial_reader_thread = SerialReaderThread(self.serial_port)
                self.serial_reader_thread.data_received.connect(self.handle_serial_data)
                self.serial_reader_thread.error_occurred.connect(self.handle_serial_error)
                self.serial_reader_thread.start()

                # Stop refreshing ports when connected
                self.refresh_timer.stop()
                self.update_connect_button_appearance()
                self.update_serial_status("green", "Connected")

                self.send_button.setDisabled(False)

                self.connected_time_seconds = 0
                self.connected_time_timer.start(1000)
                
                # Display connection message
                self.print_to_display(f"Serial connection established: {port} @ {baud_rate} baud")
                
                if DEBUG_ENABLED:
                    self.debug_handler.log(f"Successfully connected to {port}", "INFO")

        except Exception as e:
            if DEBUG_ENABLED:
                self.debug_handler.log(f"Connection failed: {e}", "ERROR")
            QMessageBox.critical(self, "Connection Error", str(e))
            self.update_serial_status("red", "Disconnected")
            self.send_button.setDisabled(True)
            if self.settings.get("general", {}).get("auto_clear_output", False):
                self.response_display.clear()

    def disconnect_serial(self) -> None:
        if DEBUG_ENABLED:
            self.debug_handler.log("Disconnecting serial port", "INFO")
            
        if self.serial_port:
            try:
                with self.debug_handler.capture_context("Serial Disconnection"):
                    # Stop the serial reader thread first
                    if self.serial_reader_thread:
                        self.serial_reader_thread.stop()
                        self.serial_reader_thread = None
                    
                    # Stop timers
                    self.connected_time_timer.stop()

                    # Close the serial port
                    self.serial_port.close()
                    self.serial_port = None
                    
                    if DEBUG_ENABLED:
                        self.debug_handler.log("Serial port closed successfully", "INFO")
            except Exception as e:
                if DEBUG_ENABLED:
                    self.debug_handler.log(f"Error during disconnect: {e}", "ERROR")
                raise

            # Resume refreshing ports when disconnected
            self.refresh_timer.start(1000)

            # Reset UI elements
            self.update_connect_button_appearance()
            self.update_serial_status("red", "Disconnected")
            self.connected_time_label.setText("Connected Time: 00:00:00")

            # Disable buttons
            self.send_button.setDisabled(True)
            if self.settings.get("general", {}).get("auto_clear_output", False):
                self.response_display.clear()

            # Close any open popup windows
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QDialog):
                    widget.close()

            # Clear any ongoing processes or states
            self.route_dump = False
            self.print_to_display("Serial connection disconnected.")

    def save_command(self, command: str) -> None:
        """
        Saves a command to the command input field and sends it.
        Prevents duplicate entries by removing old entry and appending the new one.
        """
        history_file: str = os.path.join(self.app_configs_path, "command_history.txt")
        try:
            # Read existing history
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    lines: list[str] = f.read().splitlines()
            else:
                lines: list[str] = []
            # Remove old entry if it exists
            if command in lines:
                lines.remove(command)
            # Append new command
            lines.append(command)
            # Limit to last 100 commands
            lines = lines[-100:]
            # Write back
            with open(history_file, "w") as f:
                f.write("\n".join(lines) + "\n")
            
            self.update_tab_input_history()  # Update command history display
        except Exception as e:
            print(f"Failed to save command history: {e}")
        
    def send_command(self) -> None:
        command = self.command_input.text().strip()
        
        if DEBUG_ENABLED:
            self.debug_handler.log(f"Sending command: '{command}'", "DEBUG")
            
        if self.serial_port and self.serial_port.is_open:
            try:
                with self.debug_handler.capture_context("Send Command"):
                    # Get the current line ending key
                    tx_key = self.settings['general']['tx_line_ending']

                    # Find the matching value from options
                    tx_value = next(
                        value for key, value in self.OPTIONS['tx_line_ending'] 
                        if key == tx_key
                    )
                    tx_value = tx_value.encode().decode("unicode_escape")
                    
                    if command:
                        self.save_command(command)  # Save command to history
                        self.serial_port.write((command + str(tx_value)).encode())
                        # Show flow indicator if enabled
                        show_flow = self.settings.get("general", {}).get("show_flow_indicators", True)
                        if show_flow:
                            self.print_to_display(f"< {command}")
                    else:
                        # Send just the line ending when input is empty
                        self.serial_port.write(tx_value.encode())
                        # Only display empty line indicator if filter is disabled and flow indicators enabled
                        filter_empty = self.settings.get("general", {}).get("filter_empty_lines", False)
                        show_flow = self.settings.get("general", {}).get("show_flow_indicators", True)
                        if not filter_empty and show_flow:
                            self.print_to_display("<")
            except Exception as e:
                if DEBUG_ENABLED:
                    self.debug_handler.log(f"Failed to send command: {e}", "ERROR")
                raise
            
            self.command_input.clear()

    def send_predefined_command(self, command: str) -> None:
        self.command_input.setText(command)
        self.send_command()

    def handle_serial_data(self, data: str) -> None:
        """Handle data received from the serial reader thread"""
        # Get filter settings
        filter_empty = self.settings.get("general", {}).get("filter_empty_lines", False)
        custom_filter = self.settings.get("general", {}).get("custom_line_filter", "").strip()
        
        # Split data into lines for filtering
        lines = data.split('\n')
        filtered_lines = []

        if lines[-1] == '':
            lines = lines[:-1]  # Remove the last empty line caused by split if it exists
        
        for line in lines:
            # Filter empty lines if enabled
            if filter_empty and not line.strip():
                continue
            
            # Filter lines matching custom filter (exact match after stripping)
            if custom_filter and line.strip() == custom_filter:
                continue
            
            filtered_lines.append(line)
        
        # Only display if there are non-empty lines left after filtering
        if filtered_lines:
            # Remove trailing empty strings from split (only if filter is enabled)
            if filter_empty:
                while filtered_lines and not filtered_lines[-1].strip():
                    filtered_lines.pop()
            
            # Only display if we still have content
            if filtered_lines or not filter_empty:
                filtered_data = '\n'.join(filtered_lines)
                # Only check for content if filter is enabled, otherwise show all data including blanks
                if not filter_empty or filtered_data.strip():
                    # Show flow indicator if enabled
                    show_flow = self.settings.get("general", {}).get("show_flow_indicators", True)
                    if show_flow:
                        self.print_to_display('> ' + filtered_data)
                    else:
                        self.print_to_display(filtered_data)
        
        # Add to macro session buffer if a macro is running (unfiltered)
        if self.macro_session_active:
            with self.macro_session_lock:
                # Split into lines and add each line to session buffer
                for line in data.split('\n'):
                    if line.strip():  # Don't add empty lines
                        self.macro_session_buffer.append(line)
    
    def handle_serial_error(self, error: str) -> None:
        """Handle errors from the serial reader thread"""
        QMessageBox.critical(self, "Read Error", error)
        self.disconnect_serial()

    def update_serial_status(self, color: str, status_text: str) -> None:
        self.serial_status_light.setStyleSheet(f"background-color: {color}; border: 1px solid black; border-radius: 5px;")
        self.serial_status_label.setText(f"Serial: {status_text}")

    def clear_output(self) -> None:
        """Clear the response display."""
        self.response_display.clear()
        self.update_line_count_display()

    def changeEvent(self, event: QEvent) -> None:  # type: ignore[override]
        """Handle window state changes including focus (activation) changes"""
        if event.type() == QEvent.Type.ActivationChange:  # type: ignore[attr-defined]
            if self.isActiveWindow():
                # Window became active (focused)
                self.on_window_activated()
            else:
                # Window became inactive (unfocused)
                self.on_window_deactivated()
        super().changeEvent(event)
    
    def update_connect_button_appearance(self) -> None:
        """Update the connect button text and tooltip based on connection state and settings"""
        disconnect_on_inactive = self.settings.get("general", {}).get("disconnect_on_inactive", False)
        is_connected = self.serial_port and self.serial_port.is_open
        
        if is_connected:
            if disconnect_on_inactive:
                self.connect_button.setText("Disconnect !")
                self.connect_button.setToolTip(
                    "Disconnect from serial port\n\n"
                    "! Warning: 'Disconnect On Inactive' is enabled.\n"
                    "Serial port will auto-disconnect when app loses focus\n"
                    "and auto-reconnect when app regains focus."
                )
            else:
                self.connect_button.setText("Disconnect")
                self.connect_button.setToolTip("Disconnect from the serial port")
        else:
            if disconnect_on_inactive:
                self.connect_button.setText("Connect !")
                self.connect_button.setToolTip(
                    "Connect to the selected serial port\n\n"
                    "! Warning: 'Disconnect On Inactive' is enabled.\n"
                    "Serial port will auto-disconnect when app loses focus\n"
                    "and auto-reconnect when app regains focus."
                )
            else:
                self.connect_button.setText("Connect")
                self.connect_button.setToolTip("Connect to the selected serial port")
    
    def on_window_activated(self) -> None:
        """Called when the application window becomes active (focused)"""
        disconnect_on_inactive = self.settings.get("general", {}).get("disconnect_on_inactive", False)
        
        # Auto-reconnect if we disconnected due to focus loss
        if disconnect_on_inactive and self.disconnected_by_focus_loss and self.reconnect_port:
            self.disconnected_by_focus_loss = False
            # Set the port and baud rate in the UI
            port_index = self.port_combo.findText(self.reconnect_port)
            if port_index >= 0:
                self.port_combo.setCurrentIndex(port_index)
            
            if self.reconnect_baud_rate:
                baud_index = self.baud_rate_combo.findText(str(self.reconnect_baud_rate))
                if baud_index >= 0:
                    self.baud_rate_combo.setCurrentIndex(baud_index)
                elif self.reconnect_baud_rate == self.settings.get("general", {}).get("custom-baudrate", 115200):
                    # Use custom baud rate
                    custom_index = self.baud_rate_combo.findText("Custom")
                    if custom_index >= 0:
                        self.baud_rate_combo.setCurrentIndex(custom_index)
            
            # Reconnect
            self.connect_serial()
            self.reconnect_port = None
            self.reconnect_baud_rate = None
    
    def on_window_deactivated(self) -> None:
        """Called when the application window becomes inactive (unfocused)"""
        disconnect_on_inactive = self.settings.get("general", {}).get("disconnect_on_inactive", False)
        
        # Disconnect serial if setting is enabled and save connection info for reconnect
        if disconnect_on_inactive and self.serial_port and self.serial_port.is_open:
            # Save connection details for auto-reconnect
            self.reconnect_port = self.serial_port.port
            self.reconnect_baud_rate = self.serial_port.baudrate
            self.disconnected_by_focus_loss = True
            
            # Disconnect
            self.disconnect_serial()

    def closeEvent(self, a0: QCloseEvent | None) -> None:  # type: ignore[override]
        if a0 is not None:
            self.disconnect_serial()
            a0.accept()

    def update_connected_time(self) -> None:
        self.connected_time_seconds += 1
        hours, remainder = divmod(self.connected_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.connected_time_label.setText(f"Connected Time: {hours:02}:{minutes:02}:{seconds:02}")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        
        # Set application icon for taskbar
        icon_path = get_resource_path("images/icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        if DEBUG_ENABLED:
            print(f"="*60)
            print(f"Starting Serial Communication Monitor v{__version__}")
            print(f"Debug Mode: ENABLED")
            print(f"Crash reports will be saved to: {get_config_dir('SerialCommunicationMonitor') / 'logs'}")
            print(f"="*60)
            print()
        
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
        
    except Exception as e:
        # This catches any exceptions during startup
        print(f"\nFATAL ERROR during application startup:")
        print(f"Exception: {type(e).__name__}: {e}")
        print(f"\nTraceback:")
        traceback.print_exc()
        
        if DEBUG_ENABLED:
            print(f"\nPlease report this issue with the above information.")
        
        sys.exit(1)
