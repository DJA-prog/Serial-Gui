import subprocess
import sys
import os
import serial
import serial.tools.list_ports
import platform
from pathlib import Path
import yaml
from datetime import datetime

# import sip

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidgetItem,
    QTextEdit, QLineEdit, QLabel, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QInputDialog, QDialog, QListWidget, QCheckBox,
    QSpinBox, QTabWidget, QFileDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QMouseEvent, QCloseEvent
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QColorDialog, QAbstractItemView

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

class HistoryLineEdit(QLineEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent_window = parent  # so we can access parent's history list

    def keyPressEvent(self, a0) -> None:
        if self.parent_window is not None:
            if a0.key() == Qt.Key.Key_Up:
                if self.parent_window.history_index > 0:
                    if self.parent_window.history_index == len(self.parent_window.history):
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
            else:
                super().keyPressEvent(a0)

class MainWindow(QMainWindow):
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
        self.setWindowTitle("Serial Communication Monitor")
        self.resize(800, 600)

        self.history = []  # copy so we don't modify the original list
        self.history_index = len(self.history)  # start at "end" (new command)
        self.current_text = ""  # stores what user was typing before navigating history
        self.last_connected: bool = False # Keeps if there was a last connection since start, used with auto reconnect

        self.app_configs_path = get_config_dir("SerialCommunicationMonitor")
        
        self.settings = {
            'buttons': {
                'A': {'command': '', 'label': '', 'tooltip': ''}, 
                'B': {'command': '', 'label': '', 'tooltip': ''}, 
                'C': {'command': '', 'label': '', 'tooltip': ''}, 
                'D': {'command': '', 'label': '', 'tooltip': ''}, 
                'E': {'command': '', 'label': '', 'tooltip': ''}
                }, 
            'general': {'accent_color': '#1E90FF', 
                        'auto_clear_output': False, 
                        'data_bits': 8, 
                        'flow_control': 'None', 
                        'hover_color': '#63B8FF', 
                        'maximized': True, 
                        'open_mode': 'R/W', 
                        'options-auto_clear_output': [[False, 0], [True, 1]], 
                        'options-data_bits': [8, 7, 6, 5], 
                        'options-flow_control': [['None', 0], ['Hardware', 1], ['Software', 2]], 
                        'options-maximized': [[True, True], [False, False]], 
                        'options-open_mode': [['R/W', 0], ['RO', 1], ['WO', 2]], 
                        'options-parity': [['None', 0], ['Even', 1], ['Odd', 2], ['Space', 3], ['Mark', 4]], 
                        'options-stop_bits': [1, 1.5, 2], 
                        'options-tx_line_ending': [['LN', '\\n'], ['CR', '\\r'], ['CRLN', '\\r\\n'], ['NUL', '\\0']], 
                        'parity': 'None', 
                        'stop_bits': 1, 
                        'tx_line_ending': 'LN',
                        'reveal-hidden-char': False,
                        'last-baudrate': 115200,
                        'custom-baudrate': 115200}
            }
        self.default_settings = self.settings.copy()
        self.load_settings()  # Load settings from YAML file


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
        self.available_ports = self.get_serial_ports()

        # Timer for refreshing serial ports
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_serial_ports)
        self.refresh_timer.start(1000)  # Refresh every 1 second

        # Timer for connected time
        self.connected_time_seconds = 0
        self.connected_time_timer = QTimer()
        self.connected_time_timer.timeout.connect(self.update_connected_time)

        # Main layout
        self.main_layout = QVBoxLayout()

        self.create_top_ribbon()  # Create the top ribbon with serial controls

        
        self.middle_layout = QHBoxLayout() # Middle layout: Split into left (tables) and right (output)
        self.create_left_panel()  # Create the left panel with configuration and routing tables
        self.create_right_panel()  # Create the right panel with response display
        self.main_layout.addLayout(self.middle_layout)

        self.create_bottom_panel()  # Create the bottom panel with status indicators

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # Timer for reading serial data
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)

    def set_style(self) -> None:

        style: str = """
            QMainWindow {
            background-color: #121212;  /* Dark background */
            color: #FFFFFF;  /* White text */
            }
            QLabel {
            color: #FFFFFF;  /* White text */
            }
            QLineEdit, QTextEdit, QTableWidget {
            background-color: #1E1E1E;  /* Slightly lighter dark background */
            color: #FFFFFF;  /* White text */
            border: 1px solid #1E90FF;  /* Electric blue border */
            border-radius: 5px;
            }
            QHeaderView::section {
            background-color: #1E90FF;  /* Electric blue header */
            color: #FFFFFF;  /* White text */
            border: 1px solid #1E90FF;
            font-weight: bold;
            padding: 4px;
            }
            QComboBox {
            background-color: #2A2A2A;  /* Slightly lighter background for better visibility */
            color: #FFFFFF;  /* White text */
            border: 1px solid #1E90FF;  /* Electric blue border */
            border-radius: 5px;
            padding: 2px;
            }
            QComboBox QAbstractItemView {
            background-color: #2A2A2A;  /* Dropdown background */
            color: #FFFFFF;  /* Dropdown text color */
            border: 1px solid #1E90FF;  /* Electric blue border */
            selection-background-color: #1E90FF;  /* Electric blue selection */
            selection-color: #FFFFFF;  /* White text for selection */
            }
            QCheckBox {
            color: #FFFFFF;  /* White text */
            }
            QCheckBox::indicator {
            border: 1px solid #1E90FF;  /* Electric blue border */
            width: 15px;
            height: 15px;
            border-radius: 3px;
            background-color: #1E1E1E;  /* Dark background */
            }
            QCheckBox::indicator:checked {
            background-color: #1E90FF;  /* Electric blue when checked */
            }
            QTableWidget::item {
            color: #FFFFFF;  /* White text */
            }
            QTableWidget::item:selected {
            background-color: #1E90FF;  /* Electric blue selection */
            color: #FFFFFF;  /* White text */
            }
            QScrollBar:vertical, QScrollBar:horizontal {
            background-color: #1E1E1E;  /* Dark scrollbar background */
            border: none;
            width: 10px;
            height: 10px;
            }
            QScrollBar::handle {
            background-color: #1E90FF;  /* Electric blue scrollbar handle */
            border-radius: 5px;
            }
            QScrollBar::handle:hover {
            background-color: #63B8FF;  /* Lighter blue on hover */
            }
            QMessageBox {
            background-color: #121212;  /* Dark background for popups */
            color: #FFFFFF;  /* White text */
            }
            QInputDialog {
            background-color: #121212;  /* Dark background for input dialogs */
            color: #FFFFFF;  /* White text */
            }
            QDialog {
            background-color: #121212;  /* Dark background for dialogs */
            color: #FFFFFF;  /* White text */
            }
            QWidget {
            background-color: #121212;
            color: #FFFFFF;
            }
            QListWidget {
            background-color: #1E1E1E;
            color: #FFFFFF;
            border: 1px solid #1E90FF;
            border-radius: 5px;
            }
            QListWidget::item {
            color: #FFFFFF;
            }
            QListWidget::item:selected {
            background-color: #1E90FF;
            color: #FFFFFF;
            }
            QListWidget::item:hover {
            background-color: #1E90FF;
            color: #FFFFFF;
            }
            QTabWidget::pane {
            border: 1px solid #1E90FF;
            border-bottom: none;
            background: #121212;
            }
            QTabBar::tab {
            background: #1E1E1E;
            color: #FFFFFF;
            border: 1px solid #1E90FF;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            padding: 6px;
            min-width: 100px;
            }
            QTabBar::tab:selected {
            background: #1E90FF;
            color: #FFFFFF;
            }
            QTabBar::tab:hover {
            background: #63B8FF;
            color: #FFFFFF;
            }

            QPushButton {
            background-color: #1E90FF;  /* Electric blue background */
            color: #FFFFFF;  /* White text */
            border: none;
            border-radius: 5px;
            padding: 5px;
            }
            QPushButton:hover {
            background-color: #63B8FF;  /* Lighter blue on hover */
            }
        """
        style = style.replace("#1E90FF", str(self.settings['general']['accent_color']))
        style = style.replace("#63B8FF", str(self.settings['general']['hover_color']))

        self.setStyleSheet(style)

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
        self.port_combo.addItems(self.available_ports)
        self.port_combo.setFixedWidth(150)  # Set fixed width for the port dropdown

        baud_rate_label = QLabel("Baud Rate:")
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600", "Custom"])
        self.baud_rate_combo.setCurrentText(str(self.settings.get("general", {}).get("last-baudrate", 115200)))  # Default baud rate
        self.baud_rate_combo.setFixedWidth(100)  # Set fixed width for the baud rate dropdown

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)

        self.command_input = HistoryLineEdit(self)
        self.command_input.setPlaceholderText("Enter AT command...")
        self.command_input.returnPressed.connect(self.send_command)
        self.command_input.setFixedHeight(self.command_input.sizeHint().height() + 2) 

        self.send_button = QPushButton("Send")  # Add Send button
        self.send_button.clicked.connect(self.send_command)  # Connect to send_command method
        self.send_button.setDisabled(True)
        self.send_button.setToolTip("Send command, or Repeat last command if input is blank")

        # Add DTR and RTS checkboxes
        self.dtr_checkbox = QCheckBox("DTR")
        self.dtr_checkbox.setChecked(False)  # Default selected
        self.rts_checkbox = QCheckBox("RTS")
        self.rts_checkbox.setChecked(False)  # Default selected
        self.auto_reconnect_checkbox = QCheckBox("Auto Reconnect")
        self.auto_reconnect_checkbox.setChecked(False)  # Default selected

        top_layout.addWidget(port_label)
        top_layout.addWidget(self.port_combo)
        top_layout.addWidget(baud_rate_label)
        top_layout.addWidget(self.baud_rate_combo)  # Add baud rate dropdown
        top_layout.addWidget(self.connect_button)
        top_layout.addWidget(self.command_input)
        top_layout.addWidget(self.send_button)  # Add Send button to layout
        top_layout.addWidget(self.dtr_checkbox)
        top_layout.addWidget(self.rts_checkbox)
        top_layout.addWidget(self.auto_reconnect_checkbox)
        self.main_layout.addLayout(top_layout)

    def create_left_panel(self) -> None:
        # Left layout: Tabbed panel for Configuration and Routing tables

        self.left_panel_width = 400

        left_layout = QVBoxLayout()

        tab_widget = QTabWidget()
        tab_widget.setFixedWidth(self.left_panel_width)

        self.tab_commands()  # Create the commands tab
        self.tab_input_history()  # Create the command history tab
        self.tab_settings()
        self.tab_virtual_serial()

        # Add tables to tabs
        tab_widget.addTab(self.commands_tab, "Commands")
        tab_widget.addTab(self.command_history_tab, "History")
        tab_widget.addTab(self.settings_tab, "Settings")
        tab_widget.addTab(self.virtual_serial_tab, "Virtual Serial")

        left_layout.addWidget(tab_widget)
        self.middle_layout.addLayout(left_layout)

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
        self.commands_layout.addWidget(QLabel("Select Command Set:"))
        self.commands_layout.addWidget(self.yaml_dropdown)

        commands_dir = os.path.join(self.app_configs_path, "commands")
        
        if not os.path.exists(commands_dir):
            os.makedirs(commands_dir)

        yaml_files = [f for f in os.listdir(commands_dir) if f.endswith(".yaml")]
        yaml_files.sort()
        self.yaml_dropdown.addItems(yaml_files)

        selected_file = self.yaml_dropdown.currentText()

        # --- Command lists ---
        self.no_input_list = QListWidget()
        self.input_required_list = QListWidget()
        self.flat_command_list = QListWidget()  # For flat (non-sectioned) YAMLs

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

        # Reload on change
        self.yaml_dropdown.currentTextChanged.connect(populate_command_lists)

    def tab_input_history(self) -> None:
        # Create a tab widget for command history
        self.command_history_tab = QWidget()
        self.command_history_layout = QVBoxLayout(self.command_history_tab)

        self.command_history_list = QListWidget()
        self.command_history_list.setToolTip("Click to insert command into input field")
        self.update_tab_input_history()

        # Click to insert command into input field
        self.command_history_list.itemClicked.connect(
            lambda item: self.command_input.setText(item.text())
        )

        self.command_history_layout.addWidget(QLabel("Command History:"))
        self.command_history_layout.addWidget(self.command_history_list)

        # Add clear history button at the bottom
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.setToolTip("Clear all command history")
        clear_history_btn.clicked.connect(self.confirm_clear_history)
        self.command_history_layout.addWidget(clear_history_btn)

    def tab_settings_set(self) -> None:
        settings = self.settings.get("general", {})

        auto_clear_item = QTableWidgetItem(str(settings.get("auto_clear_output", False)))
        self.settings_table.setItem(0, 1, auto_clear_item)
        # Row 1: accent_color (color)
        accent_color_item = QTableWidgetItem(str(settings.get("accent_color", "#1E90FF")))
        self.settings_table.setItem(1, 1, accent_color_item)
        # Row 2: hover_color (color)
        hover_color_item = QTableWidgetItem(str(settings.get("hover_color", "#63B8FF")))
        self.settings_table.setItem(2, 1, hover_color_item)
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
        # Row 11: custom-baudrate (int)
        custom_baud_rate_item = QTableWidgetItem(str(settings.get("custom-baudrate", 115200)))
        self.settings_table.setItem(11, 1, custom_baud_rate_item)

    def tab_settings(self) -> None:

        self.settings_tab: QWidget = QWidget()
        self.settings_layout: QVBoxLayout = QVBoxLayout(self.settings_tab)

        # Settings table
        self.settings_table = QTableWidget()
        self.settings_table.setToolTip("Double-click a value to edit. For colors, a color picker will appear.")
        self.settings_table.setRowCount(12)
        self.settings_table.setColumnCount(2)
        self.settings_table.setHorizontalHeaderLabels(["Setting", "Value"])
        self.settings_table.verticalHeader().setVisible(False)
        self.settings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.settings_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.settings_table.setColumnWidth(0, int(self.left_panel_width * 0.45))
        self.settings_table.setColumnWidth(1, int(self.left_panel_width * 0.48))

        # Populate settings
        settings = self.settings.get("general", {})
        
        self.settings_table.setItem(0, 0, QTableWidgetItem("Auto Clear Output"))
        self.settings_table.setItem(1, 0, QTableWidgetItem("Accent Color"))
        self.settings_table.setItem(2, 0, QTableWidgetItem("Hover Color"))
        self.settings_table.setItem(3, 0, QTableWidgetItem("Maximized"))
        self.settings_table.setItem(4, 0, QTableWidgetItem("Tx line Ending"))
        self.settings_table.setItem(5, 0, QTableWidgetItem("Data Bits"))
        self.settings_table.setItem(6, 0, QTableWidgetItem("Parity"))
        self.settings_table.setItem(7, 0, QTableWidgetItem("Stop Bits"))
        self.settings_table.setItem(8, 0, QTableWidgetItem("Flow Control"))
        self.settings_table.setItem(9, 0, QTableWidgetItem("Open Mode"))
        self.settings_table.setItem(10, 0, QTableWidgetItem("Reveal Hidden Char"))
        self.settings_table.setItem(11, 0, QTableWidgetItem("Custom Baud Rate"))

        self.tab_settings_set()

        self.settings_layout.addWidget(self.settings_table)

        # Handle editing
        def edit_setting(row: int, column: int) -> None:
            key = self.settings_table.item(row, 0).text()
            general = self.settings["general"]

            # Boolean options
            if key in ("Auto Clear Output", "Maximized", "Reveal Hidden Char"):
                current = str(self.settings_table.item(row, 1).text()).lower() == "true"
                new_value = not current
                self.settings_table.setItem(row, 1, QTableWidgetItem(str(new_value)))
                # Update corresponding key in settings
                if key == "Auto Clear Output":
                    general["auto_clear_output"] = new_value
                elif key == "Maximized":
                    general["maximized"] = new_value
                elif key == "Reveal Hidden Char":
                    general["reveal_hidden_char"] = new_value
                self.save_settings()

            # Color options
            elif key in ("Accent Color", "Hover Color"):
                color = QColorDialog.getColor()
                if color.isValid():
                    hex_color = color.name()
                    self.settings_table.setItem(row, 1, QTableWidgetItem(hex_color))
                    if key == "Accent Color":
                        general["accent_color"] = hex_color
                    else:
                        general["hover_color"] = hex_color
                    self.save_settings()
                    self.set_style()

            # Drop-down / list options
            elif key == "Tx line Ending":
                items = [opt[0] for opt in general["options-tx_line_ending"]]
                current_value = self.settings_table.item(row, 1).text()
                current_index = items.index(current_value) if current_value in items else 0
                new_value, ok = QInputDialog.getItem(
                    self, "Edit TX Line Ending", "Select new line ending:", items, current_index, False
                )
                if ok and new_value:
                    self.settings_table.setItem(row, 1, QTableWidgetItem(new_value))
                    general["tx_line_ending"] = new_value
                    self.save_settings()

            elif key == "Data Bits":
                items = [str(x) for x in general["options-data_bits"]]
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
                items = [x[0] for x in general["options-parity"]]
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
                items = [str(x) for x in general["options-stop_bits"]]
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
                items = [x[0] for x in general["options-flow_control"]]
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
                items = [x[0] for x in general["options-open_mode"]]
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

        self.settings_table.cellDoubleClicked.connect(edit_setting)

        custom_buttons_title = QLabel("Custom Bottom Bar Butttons")
        self.settings_layout.addWidget(custom_buttons_title)

        custom_buttons_table = QTableWidget()
        custom_buttons_table.setRowCount(0)
        custom_buttons_table.setColumnCount(2)
        custom_buttons_table.setHorizontalHeaderLabels(["Label", "Command"])
        custom_buttons_table.verticalHeader().setVisible(False)
        custom_buttons_table.setEditTriggers(QTableWidget.NoEditTriggers)
        custom_buttons_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        custom_buttons_table.setColumnWidth(0, int(self.left_panel_width * 0.45))
        custom_buttons_table.setColumnWidth(1, int(self.left_panel_width * 0.50))

        self.settings_layout.addWidget(custom_buttons_table)

        # Populate custom buttons from settings
        if 'buttons' in self.settings:
            for key, button in self.settings['buttons'].items():
                if isinstance(button, dict):
                    label = button.get('label', '')
                    command = button.get('command', '')
                    custom_buttons_table.insertRow(custom_buttons_table.rowCount())
                    custom_buttons_table.setItem(custom_buttons_table.rowCount() - 1, 0, QTableWidgetItem(label))
                    custom_buttons_table.setItem(custom_buttons_table.rowCount() - 1, 1, QTableWidgetItem(command))
        
        def edit_custom_button(row: int, column: int) -> None:
            keys = ['A', 'B', 'C', 'D', 'E']
            if column == 0:
                # Edit label
                current_label = custom_buttons_table.item(row, 0).text()
                new_label, ok = QInputDialog.getText(self, "Edit Button Label", "Enter new label:", text=current_label)
                if ok and new_label:
                    custom_buttons_table.setItem(row, 0, QTableWidgetItem(new_label))
                    # Update settings
                    command = custom_buttons_table.item(row, 1).text()
                    key = keys[row]
                    if key in self.settings['buttons']:
                        self.settings['buttons'][key] = {'label': new_label, 'command': command}
                        self.save_settings()
                        print(self.settings['buttons'])
            elif column == 1:
                # Edit command
                current_command = custom_buttons_table.item(row, 1).text()
                new_command, ok = QInputDialog.getText(self, "Edit Button Command", "Enter new command:", text=current_command)
                if ok and new_command:
                    custom_buttons_table.setItem(row, 1, QTableWidgetItem(new_command))
                    # Update settings
                    label = custom_buttons_table.item(row, 0).text()
                    key = keys[row]
                    if key in self.settings['buttons']:
                        self.settings['buttons'][key] = {'label': label, 'command': new_command}
                        self.save_settings()
                        print(self.settings['buttons'])

        custom_buttons_table.cellDoubleClicked.connect(edit_custom_button)

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
            self.settings = self.default_settings.copy()
            # Update table
            self.save_settings()
            self.set_style()
            self.tab_settings_set()
            # QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults. Please restart the application for all changes to take effect.")

        reset_button.clicked.connect(reset_to_defaults)

    def tab_virtual_serial(self) -> None:
        self.virtual_serial_tab: QWidget = QWidget()
        self.virtual_serial_layout: QVBoxLayout = QVBoxLayout(self.virtual_serial_tab)

        self.virtual_serial_table = QTableWidget()
        self.virtual_serial_table.setRowCount(0)
        self.virtual_serial_table.setColumnCount(2)
        self.virtual_serial_table.setHorizontalHeaderLabels(["Virtual Serial Path", "Baud Rate"])
        self.virtual_serial_table.verticalHeader().setVisible(False)
        self.virtual_serial_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.virtual_serial_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.virtual_serial_table.setColumnWidth(0, int(self.left_panel_width * 0.45))
        self.virtual_serial_table.setColumnWidth(1, int(self.left_panel_width * 0.50))

        self.virtual_serial_layout.addWidget(self.virtual_serial_table)

        # Load saved virtual serials from YAML
        yaml_path = os.path.join(self.app_configs_path, "virtual_serials.yaml")
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r") as f:
                    entries = yaml.safe_load(f)
                if isinstance(entries, list):
                    for entry in entries:
                        path = entry.get("path", "")
                        baud_rate = entry.get("baud_rate", "")
                        row = self.virtual_serial_table.rowCount()
                        self.virtual_serial_table.insertRow(row)
                        self.virtual_serial_table.setItem(row, 0, QTableWidgetItem(str(path)))
                        self.virtual_serial_table.setItem(row, 1, QTableWidgetItem(str(baud_rate)))
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load virtual serials: {e}")

       
        # Add a clear all button
        add_virtual_serial_button = QPushButton("Add Virtual Serial")
        add_virtual_serial_button.setToolTip("Add a new virtual_serial entry")
        add_virtual_serial_button.clicked.connect(self.add_virtual_serial)
        self.virtual_serial_layout.addWidget(add_virtual_serial_button)

        clear_button = QPushButton("Clear All Virtual Serials")
        clear_button.setToolTip("Remove all virtual_serial entries")
        clear_button.clicked.connect(self.clear_virtual_serials)
        self.virtual_serial_layout.addWidget(clear_button)


    def add_virtual_serial(self) -> None:
        path, ok = QInputDialog.getText(self, "Add Virtual Serial", "Enter virtual serial path (e.g., /dev/pts/3 or COM5):")
        if not ok or not path:
            return

        baud_rate, ok = QInputDialog.getText(self, "Add Virtual Serial", "Enter baud rate (e.g., 115200):")
        if not ok or not baud_rate:
            return

        baud_rate = abs(int(baud_rate))

        # Update table
        self.virtual_serial_table.insertRow(self.virtual_serial_table.rowCount())
        self.virtual_serial_table.setItem(self.virtual_serial_table.rowCount() - 1, 0, QTableWidgetItem(path))
        self.virtual_serial_table.setItem(self.virtual_serial_table.rowCount() - 1, 1, QTableWidgetItem(str(baud_rate)))

        # Save to YAML file
        yaml_path = os.path.join(self.app_configs_path, "virtual_serials.yaml")
        entries = []
        # Read existing entries from table
        for row in range(self.virtual_serial_table.rowCount()):
            entry_path = self.virtual_serial_table.item(row, 0).text()
            entry_baud = int(self.virtual_serial_table.item(row, 1).text())
            entries.append({'path': entry_path, 'baud_rate': entry_baud})
        try:
            with open(yaml_path, "w") as f:
                yaml.dump(entries, f, default_flow_style=False)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save virtual serials: {e}")

    def clear_virtual_serials(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear All Virtual Serials",
            "Are you sure you want to clear all virtual serial entries? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.virtual_serial_table.setRowCount(0)
            yaml_path = os.path.join(self.app_configs_path, "virtual_serials.yaml")
            try:
                with open(yaml_path, "w") as f:
                    yaml.dump([], f, default_flow_style=False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear virtual serials file: {e}")

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

    def save_settings(self) -> None:
        settings_file = os.path.join(self.app_configs_path, "settings.yaml")
        try:
            with open(settings_file, "w") as f:
                yaml.dump(self.settings, f, default_flow_style=False)
        except Exception as e:
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

    def create_right_panel(self) -> None:
        """
        Creates the right panel of the main window, which includes the response display area,
        predefined command buttons, and status indicators for serial connections.
        """
        # Right layout: Response display
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
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

        for key, button in self.settings["buttons"].items():
            if isinstance(button, dict):
                label = button.get('label', '')
                tooltip = button.get('tooltip', '')
                command = button.get('command', '')

                btn = QPushButton(label)
                btn.setToolTip(tooltip)
                if not label:
                    btn.setDisabled(True)
                btn.clicked.connect(lambda _, cmd=command: self.send_predefined_command(cmd))
                predefined_layout.addWidget(btn)


        self.save_output_button = QPushButton("Save output")
        self.save_output_button.clicked.connect(self.save_output)
        self.save_output_button.setToolTip("Save the content of the response display to a file")

        self.clear_button = QPushButton("Clear output")
        self.clear_button.clicked.connect(self.clear_output)

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

        bottom_layout.addLayout(status_layout)

        self.main_layout.addLayout(bottom_layout)

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
        settings_file = os.path.join(self.app_configs_path, "settings.yaml")
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = yaml.safe_load(f)
                # print(f"Loaded settings: {settings}")
            if settings:
                self.settings = settings
                # print(f"Settings loaded: {self.settings}")
            
            self.save_settings()

    def get_serial_ports(self) -> list[str]:
        ports = serial.tools.list_ports.comports()
        # Filter out devices containing "ttyS"
        return [port.device for port in ports if "ttyS" not in port.device]

    def print_to_display(self, message: str) -> None:
        if self.settings.get("general", {}).get("reveal_hidden_char", False):
            message = self.reveal_hidden_characters(message)
        self.response_display.append(message.strip())

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

        # Update port list if it has changed
        if current_ports != self.available_ports:
            self.available_ports = current_ports
            self.port_combo.clear()
            self.port_combo.addItems(self.available_ports)

        # Auto-reconnect if needed
        if self.auto_reconnect_checkbox.isChecked():
            port = self.port_combo.currentText()
            if port in current_ports and (not self.serial_port or not self.serial_port.is_open):
                self.print_to_display("Attempting auto-reconnect...")
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

        if self.settings.get("general", {}).get("last-baudrate", 115200) != baud_rate:
            self.settings["general"]["last-baudrate"] = baud_rate
            self.save_settings()

        if baud_rate == "Custom":
            baud_rate = self.settings.get("general", {}).get("custom-baudrate", 115200)

        baud_rate = int(baud_rate)

        try:
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

            # Set DTR/RTS
            self.serial_port.dtr = self.dtr_checkbox.isChecked()
            self.serial_port.rts = self.rts_checkbox.isChecked()

            # Timers and UI
            self.timer.start(100)
            self.refresh_timer.stop()
            self.connect_button.setText("Disconnect")
            self.update_serial_status("green", "Connected")

            self.send_button.setDisabled(False)

            self.connected_time_seconds = 0
            self.connected_time_timer.start(1000)

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))
            self.update_serial_status("red", "Disconnected")
            self.send_button.setDisabled(True)
            if self.settings.get("general", {}).get("auto_clear_output", False):
                self.response_display.clear()

    def disconnect_serial(self) -> None:
        if self.serial_port:
            # Stop timers
            self.timer.stop()
            self.connected_time_timer.stop()

            # Close the serial port
            self.serial_port.close()
            self.serial_port = None

            # Resume refreshing ports when disconnected
            self.refresh_timer.start(1000)

            # Reset UI elements
            self.connect_button.setText("Connect")
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
        if self.serial_port and self.serial_port.is_open:
            if command:
                self.save_command(command)  # Save command to history
                # Get the current line ending key
                tx_key = self.settings['general']['tx_line_ending']

                # Find the matching value from options
                tx_value = next(
                    value for key, value in self.settings['general']['options-tx_line_ending'] 
                    if key == tx_key
                )
                tx_value = tx_value.encode().decode("unicode_escape")
                self.serial_port.write((command + str(tx_value)).encode())
                self.print_to_display(f"< {command}")
                self.command_input.clear()
            else:
                # If command input is blank, get the last command from history and send it
                history_file = os.path.expanduser("~/.command_history.txt")
                if os.path.exists(history_file):
                    with open(history_file, "r") as f:
                        lines = f.read().splitlines()
                    if lines:
                        last_command = lines[-1]
                        self.command_input.setText(last_command)
                        self.send_command()
                    else:
                        QMessageBox.information(self, "No History", "No previous command found in history.")
                else:
                    QMessageBox.information(self, "No History", "No previous command found in history.")

    def send_predefined_command(self, command: str) -> None:
        self.command_input.setText(command)
        self.send_command()

    def read_serial_data(self) -> None:
        if self.serial_port and self.serial_port.is_open:
            try:
                while self.serial_port.in_waiting > 0:
                    # Decode with error handling
                    response = self.serial_port.readline().decode('utf-8', errors='replace')

                    if response:
                        self.print_to_display('> ' + response)


            except Exception as e:
                QMessageBox.critical(self, "Read Error", str(e))
                self.disconnect_serial()

    def update_serial_status(self, color: str, status_text: str) -> None:
        self.serial_status_light.setStyleSheet(f"background-color: {color}; border: 1px solid black; border-radius: 5px;")
        self.serial_status_label.setText(f"Serial: {status_text}")

    def clear_output(self) -> None:
        """Clear the response display."""
        self.response_display.clear()

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.disconnect_serial()
        a0.accept()

    def update_connected_time(self) -> None:
        self.connected_time_seconds += 1
        hours, remainder = divmod(self.connected_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.connected_time_label.setText(f"Connected Time: {hours:02}:{minutes:02}:{seconds:02}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
