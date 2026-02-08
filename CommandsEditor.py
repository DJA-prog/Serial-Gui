"""
Commands Editor - Interface for managing command sets with two scrollable lists
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from StyleManager import StyleManager

# Import debug handler
try:
    from DebugHandler import get_debug_handler
    DEBUG_ENABLED = True
except:
    DEBUG_ENABLED = False
    def get_debug_handler():
        return None

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QLineEdit, QScrollArea, QMessageBox, QListWidget, QListWidgetItem,
    QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt


class CommandsEditor(QDialog):
    """Editor for managing command YAML files with two command lists"""
    
    def __init__(self, parent=None, config_path: Optional[Path] = None, style_manager: Optional['StyleManager'] = None):
        super().__init__(parent)
        
        debug = get_debug_handler()
        if debug and debug.enabled:
            debug.log("CommandsEditor: Initializing", "DEBUG")
        
        try:
            self.style_manager = style_manager
            self.config_path = config_path or Path.home() / ".config" / "SerialCommunicationMonitor"
            self.commands_dir = self.config_path / "commands"
            self.commands_dir.mkdir(parents=True, exist_ok=True)
            
            self.current_file: Optional[str] = None
            self.no_input_commands: Dict[str, str] = {}
            self.input_required_commands: Dict[str, str] = {}
            
            # Track unsaved changes
            self.has_unsaved_changes = False
            self.initial_state: Optional[Dict[str, Any]] = None
            
            self.setWindowTitle("Commands Editor")
            self.resize(900, 700)
            self.setup_ui()
            self.apply_style()
            
            # Store initial state after setup
            self.initial_state = self.get_current_state()
            
            if debug and debug.enabled:
                debug.log("CommandsEditor: Initialization complete", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Initialization error: {e}", "ERROR")
            raise
    
    def setup_ui(self):
        """Setup the main UI layout"""
        main_layout = QVBoxLayout(self)
        
        # Main content - Two lists side by side
        lists_layout = QHBoxLayout()
        
        # Left list - No Input Commands
        left_panel = QVBoxLayout()
        
        left_header = QHBoxLayout()
        left_label = QLabel("Commands (No Input Required)")
        left_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_header.addWidget(left_label)
        left_header.addStretch()
        
        add_no_input_btn = QPushButton("+ Add")
        add_no_input_btn.clicked.connect(self.add_no_input_command)
        left_header.addWidget(add_no_input_btn)
        
        left_panel.addLayout(left_header)
        
        self.no_input_list = QListWidget()
        self.no_input_list.setSelectionMode(QListWidget.SingleSelection)
        left_panel.addWidget(self.no_input_list)
        
        # Buttons for no input list
        no_input_btn_layout = QHBoxLayout()
        
        edit_no_input_btn = QPushButton("Edit")
        edit_no_input_btn.clicked.connect(self.edit_no_input_command)
        no_input_btn_layout.addWidget(edit_no_input_btn)
        
        remove_no_input_btn = QPushButton("Remove")
        remove_no_input_btn.clicked.connect(self.remove_no_input_command)
        no_input_btn_layout.addWidget(remove_no_input_btn)
        
        left_panel.addLayout(no_input_btn_layout)
        
        lists_layout.addLayout(left_panel)
        
        # Right list - Input Required Commands
        right_panel = QVBoxLayout()
        
        right_header = QHBoxLayout()
        right_label = QLabel("Commands (Input Required)")
        right_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_header.addWidget(right_label)
        right_header.addStretch()
        
        add_input_req_btn = QPushButton("+ Add")
        add_input_req_btn.clicked.connect(self.add_input_required_command)
        right_header.addWidget(add_input_req_btn)
        
        right_panel.addLayout(right_header)
        
        self.input_required_list = QListWidget()
        self.input_required_list.setSelectionMode(QListWidget.SingleSelection)
        right_panel.addWidget(self.input_required_list)
        
        # Buttons for input required list
        input_req_btn_layout = QHBoxLayout()
        
        edit_input_req_btn = QPushButton("Edit")
        edit_input_req_btn.clicked.connect(self.edit_input_required_command)
        input_req_btn_layout.addWidget(edit_input_req_btn)
        
        remove_input_req_btn = QPushButton("Remove")
        remove_input_req_btn.clicked.connect(self.remove_input_required_command)
        input_req_btn_layout.addWidget(remove_input_req_btn)
        
        right_panel.addLayout(input_req_btn_layout)
        
        lists_layout.addLayout(right_panel)
        
        main_layout.addLayout(lists_layout)
        
        # Bottom bar - File label, Save, and Close buttons
        bottom_bar = QHBoxLayout()
        
        self.file_label = QLabel("Unsaved changes")
        bottom_bar.addWidget(self.file_label)
        
        bottom_bar.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        bottom_bar.addWidget(save_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        bottom_bar.addWidget(close_btn)
        
        main_layout.addLayout(bottom_bar)
    
    def apply_style(self):
        """Apply dark theme styling using StyleManager"""
        if self.style_manager:
            style = self.style_manager.get_dialog_stylesheet()
            self.setStyleSheet(style)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state for change detection"""
        return {
            'file': self.current_file,
            'no_input': dict(self.no_input_commands),
            'input_required': dict(self.input_required_commands)
        }
    
    def mark_as_changed(self):
        """Mark the editor as having unsaved changes"""
        self.has_unsaved_changes = True
    
    def has_changes(self) -> bool:
        """Check if there are unsaved changes"""
        if not self.has_unsaved_changes:
            return False
        if self.initial_state is None:
            return False
        current_state = self.get_current_state()
        return current_state != self.initial_state
    
    def add_no_input_command(self):
        """Add a new command to the no input list"""
        debug = get_debug_handler()
        try:
            command, ok1 = QInputDialog.getText(
                self, "Add Command", "Enter command (e.g., AT, ATE0):"
            )
            if not ok1 or not command.strip():
                return
            
            description, ok2 = QInputDialog.getText(
                self, "Add Description", "Enter description:"
            )
            if not ok2:
                return
            
            self.no_input_commands[command.strip()] = description.strip()
            self.refresh_lists()
            self.mark_as_changed()
            
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Added no-input command '{command.strip()}'", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Error adding no-input command: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to add command:\n{e}")
    
    def edit_no_input_command(self):
        """Edit selected command in no input list"""
        debug = get_debug_handler()
        try:
            current_item = self.no_input_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a command to edit.")
                return
            
            # Parse current command and description
            item_text = current_item.text()
            if " - " in item_text:
                old_command, old_description = item_text.split(" - ", 1)
            else:
                old_command = item_text
                old_description = ""
            
            # Edit command
            command, ok1 = QInputDialog.getText(
                self, "Edit Command", "Edit command:", text=old_command
            )
            if not ok1 or not command.strip():
                return
            
            # Edit description
            description, ok2 = QInputDialog.getText(
                self, "Edit Description", "Edit description:", text=old_description
            )
            if not ok2:
                return
            
            # Remove old entry
            if old_command in self.no_input_commands:
                del self.no_input_commands[old_command]
            
            # Add updated entry
            self.no_input_commands[command.strip()] = description.strip()
            self.refresh_lists()
            self.mark_as_changed()
            
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Edited no-input command '{old_command}' -> '{command.strip()}'", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Error editing no-input command: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to edit command:\n{e}")
    
    def remove_no_input_command(self):
        """Remove selected command from no input list"""
        debug = get_debug_handler()
        try:
            current_item = self.no_input_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a command to remove.")
                return
            
            item_text = current_item.text()
            if " - " in item_text:
                command = item_text.split(" - ")[0]
            else:
                command = item_text
            
            if command in self.no_input_commands:
                del self.no_input_commands[command]
                self.refresh_lists()
                self.mark_as_changed()
                
                if debug and debug.enabled:
                    debug.log(f"CommandsEditor: Removed no-input command '{command}'", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Error removing command: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to remove command:\n{e}")
    
    def add_input_required_command(self):
        """Add a new command to the input required list"""
        debug = get_debug_handler()
        try:
            command, ok1 = QInputDialog.getText(
                self, "Add Command", "Enter command template (e.g., AT+CMGS=\"<number>\"):"
            )
            if not ok1 or not command.strip():
                return
            
            description, ok2 = QInputDialog.getText(
                self, "Add Description", "Enter description:"
            )
            if not ok2:
                return
            
            self.input_required_commands[command.strip()] = description.strip()
            self.refresh_lists()
            self.mark_as_changed()
            
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Added input-required command '{command.strip()}'", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Error adding input-required command: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to add command:\n{e}")
    
    def edit_input_required_command(self):
        """Edit selected command in input required list"""
        debug = get_debug_handler()
        try:
            current_item = self.input_required_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a command to edit.")
                return
            
            # Parse current command and description
            item_text = current_item.text()
            if " - " in item_text:
                old_command, old_description = item_text.split(" - ", 1)
            else:
                old_command = item_text
                old_description = ""
            
            # Edit command
            command, ok1 = QInputDialog.getText(
                self, "Edit Command", "Edit command:", text=old_command
            )
            if not ok1 or not command.strip():
                return
            
            # Edit description
            description, ok2 = QInputDialog.getText(
                self, "Edit Description", "Edit description:", text=old_description
            )
            if not ok2:
                return
            
            # Remove old entry
            if old_command in self.input_required_commands:
                del self.input_required_commands[old_command]
            
            # Add updated entry
            self.input_required_commands[command.strip()] = description.strip()
            self.refresh_lists()
            self.mark_as_changed()
            
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Edited input-required command '{old_command}' -> '{command.strip()}'", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Error editing input-required command: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to edit command:\n{e}")
    
    def remove_input_required_command(self):
        """Remove selected command from input required list"""
        debug = get_debug_handler()
        try:
            current_item = self.input_required_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a command to remove.")
                return
            
            item_text = current_item.text()
            if " - " in item_text:
                command = item_text.split(" - ")[0]
            else:
                command = item_text
            
            if command in self.input_required_commands:
                del self.input_required_commands[command]
                self.refresh_lists()
                self.mark_as_changed()
                
                if debug and debug.enabled:
                    debug.log(f"CommandsEditor: Removed input-required command '{command}'", "DEBUG")
        
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Error removing input-required command: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to remove command:\n{e}")
    
    def refresh_lists(self):
        """Refresh both list widgets with current data"""
        # Refresh no input list
        self.no_input_list.clear()
        for command, description in sorted(self.no_input_commands.items()):
            self.no_input_list.addItem(f"{command} - {description}")
        
        # Refresh input required list
        self.input_required_list.clear()
        for command, description in sorted(self.input_required_commands.items()):
            self.input_required_list.addItem(f"{command} - {description}")
    
    def save_file(self):
        """Save current commands to file"""
        debug = get_debug_handler()
        try:
            # If no current file, ask for filename
            if not self.current_file:
                filename, ok = QInputDialog.getText(
                    self, "Save As", "Enter filename (without .yaml):"
                )
                if not ok or not filename.strip():
                    return
                
                # Sanitize filename
                filename = filename.strip()
                if not filename.endswith('.yaml'):
                    filename += '.yaml'
                
                self.current_file = filename
            
            filepath = self.commands_dir / self.current_file
            
            data = {
                'no_input_commands': self.no_input_commands,
                'input_required_commands': self.input_required_commands
            }
            # Use allow_unicode and default_style for proper string handling
            # This ensures special characters like !, :, #, etc. are properly escaped
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, 
                         allow_unicode=True, default_style='"')
            
            self.file_label.setText(f"Saved: {self.current_file}")
            QMessageBox.information(self, "Success", f"Saved to {self.current_file}")
            
            # Reset change tracking after successful save
            self.has_unsaved_changes = False
            self.initial_state = self.get_current_state()
            
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Saved commands to {self.current_file}", "INFO")
        
        except yaml.YAMLError as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: YAML error saving file: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to save file (YAML error):\n{e}")
        except IOError as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: I/O error saving file: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to save file (I/O error):\n{e}")
        except Exception as e:
            if debug and debug.enabled:
                debug.log(f"CommandsEditor: Unexpected error saving file: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
