"""
Macro Editor - A Scratch-like drag-and-drop interface for creating serial communication macros
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from StyleManager import StyleManager

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QLineEdit, QScrollArea, QMessageBox, QSpinBox, QComboBox, QFrame,
    QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPalette, QColor, QMouseEvent, QDragEnterEvent, QDropEvent


class MacroBlock(QFrame):
    """Base class for draggable macro blocks"""
    
    def __init__(self, block_type: str, label: str, parent=None, accent_color: str = "#1E90FF", hover_color: str = "#63B8FF", background_color: str = "#1E1E1E"):
        super().__init__(parent)
        self.block_type = block_type
        self.label_text = label
        self.accent_color = accent_color
        self.hover_color = hover_color
        self.background_color = background_color
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setMinimumHeight(60)
        # self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMaximumHeight(240)
        
        # Set background color based on type
        self.set_block_color()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title label
        # title = QLabel(f"{label}")
        # layout.addWidget(title)
        
        # Add specific widgets based on block type
        self.setup_block_content(layout)
        
    def set_block_color(self):
        """Set background color based on block type"""

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.background_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            QCheckBox {{
                background: transparent;
            }}
        """)
    
    
    def setup_block_content(self, layout: QHBoxLayout):
        """Setup block-specific content - override in subclasses"""
        pass
    
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:  # type: ignore[override]
        """Enable dragging"""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = a0.pos()
    
    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:  # type: ignore[override]
        """Start drag operation"""
        if not a0:
            return
        buttons = a0.buttons()
        if (buttons & Qt.MouseButton.LeftButton) == 0:
            return
        if (a0.pos() - self.drag_start_position).manhattanLength() < 10:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.block_type)
        
        # Store reference to this block for reordering detection
        drag.source_block = self  # type: ignore[attr-defined]
        
        drag.setMimeData(mime_data)
        drag.exec_(Qt.DropAction.CopyAction)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for YAML serialization"""
        return {"type": self.block_type}


class InputBlock(MacroBlock):
    """Block for sending input commands"""
    
    def __init__(self, parent=None, command: str = "", accent_color: str = "#1E90FF", hover_color: str = "#63B8FF", background_color: str = "#1E1E1E"):
        super().__init__("input", "Send Command", parent, accent_color, hover_color, background_color)
        try:
            if hasattr(self, 'command_input') and self.command_input is not None:
                self.command_input.setText(command)
        except Exception as e:
            print(f"InputBlock initialization error: {e}")
    
    def setup_block_content(self, layout: QHBoxLayout):
        layout_last = QVBoxLayout()
        label = QLabel("Send Command")
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        layout_last.addWidget(label)
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command (e.g., AT)")
        self.command_input.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        layout_last.addWidget(self.command_input)
        layout.addLayout(layout_last)
    
    def to_dict(self) -> Dict[str, Any]:
        try:
            return {"input": self.command_input.text() if hasattr(self, 'command_input') and self.command_input else ""}
        except Exception as e:
            print(f"Error in InputBlock.to_dict: {e}")
            return {"input": ""}


class DelayBlock(MacroBlock):
    """Block for adding delays"""
    
    def __init__(self, parent=None, delay_ms: int = 1000, accent_color: str = "#1E90FF", hover_color: str = "#63B8FF", background_color: str = "#1E1E1E"):
        super().__init__("delay", "Delay", parent, accent_color, hover_color, background_color)
        try:
            if hasattr(self, 'delay_spinbox') and self.delay_spinbox is not None:
                self.delay_spinbox.setValue(delay_ms)
        except Exception as e:
            print(f"DelayBlock initialization error: {e}")
    
    def setup_block_content(self, layout: QHBoxLayout):
        layout_last = QVBoxLayout()
        label = QLabel("Delay")
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        layout_last.addWidget(label)
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Wait:"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 60000)
        self.delay_spinbox.setValue(1000)
        self.delay_spinbox.setSuffix(" ms")
        self.delay_spinbox.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        h_layout.addWidget(self.delay_spinbox)
        layout_last.addLayout(h_layout)
        layout.addLayout(layout_last)
    
    def to_dict(self) -> Dict[str, Any]:
        try:
            return {"delay": self.delay_spinbox.value() if hasattr(self, 'delay_spinbox') and self.delay_spinbox else 1000}
        except Exception as e:
            print(f"Error in DelayBlock.to_dict: {e}")
            return {"delay": 1000}


class DialogWaitBlock(MacroBlock):
    """Block for displaying a dialog with custom message and continue/end options"""
    
    def __init__(self, parent=None, message: str = "", accent_color: str = "#1E90FF", hover_color: str = "#63B8FF", background_color: str = "#1E1E1E"):
        super().__init__("dialog_wait", "Dialog Wait", parent, accent_color, hover_color, background_color)
        try:
            if hasattr(self, 'message_input') and self.message_input is not None:
                self.message_input.setText(message)
        except Exception as e:
            print(f"DialogWaitBlock initialization error: {e}")
    
    def setup_block_content(self, layout: QHBoxLayout):
        layout_last = QVBoxLayout()
        label = QLabel("Dialog Wait")
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        layout_last.addWidget(label)
        
        # Message input
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Message:"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter dialog message")
        self.message_input.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        h_layout.addWidget(self.message_input)
        layout_last.addLayout(h_layout)
        
        # Info label
        info_label = QLabel("Pauses macro and shows dialog with Continue/End")
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout_last.addWidget(info_label)
        
        layout.addLayout(layout_last)
    
    def to_dict(self) -> Dict[str, Any]:
        try:
            return {"dialog_wait": {"message": self.message_input.text() if hasattr(self, 'message_input') and self.message_input else ""}}
        except Exception as e:
            print(f"Error in DialogWaitBlock.to_dict: {e}")
            return {"dialog_wait": {"message": ""}}


class OutputBlock(MacroBlock):
    """Block for expecting output with conditional logic"""
    
    def __init__(self, parent=None, expected: str = "", timeout: int = 1000, 
                 fail_action: str = "Continue", fail_command: str = "",
                 success_action: str = "Continue", success_command: str = "",
                 substring_match: bool = True,
                 accent_color: str = "#1E90FF", hover_color: str = "#63B8FF", background_color: str = "#1E1E1E"):
        # Initialize flag to prevent signal handling during setup
        self._initializing = True
        
        super().__init__("output", "Expect Output", parent, accent_color, hover_color, background_color)
        
        # Set values after all widgets are created (no signal blocking needed since signals aren't connected yet)
        try:
            # Set values for all widgets
            if hasattr(self, 'expected_input') and self.expected_input is not None:
                self.expected_input.setText(expected)
            if hasattr(self, 'timeout_spinbox') and self.timeout_spinbox is not None:
                self.timeout_spinbox.setValue(timeout)
            
            # Set fail action and update visibility
            if hasattr(self, 'fail_action_combo') and self.fail_action_combo is not None:
                if fail_action in ["Ignore", "Continue", "Exit Macro", "Custom Command", "Dialog for Command", "Dialog and Wait"]:
                    self.fail_action_combo.setCurrentText(fail_action)
                    # Update visibility immediately (no signal to trigger it yet)
                    if hasattr(self, 'fail_command_input') and self.fail_command_input is not None:
                        self.fail_command_input.setVisible(fail_action == "Custom Command")
            
            if hasattr(self, 'fail_command_input') and self.fail_command_input is not None and fail_command:
                self.fail_command_input.setText(fail_command)
            
            # Set success action and update visibility
            if hasattr(self, 'success_action_combo') and self.success_action_combo is not None:
                if success_action in ["Ignore", "Continue", "Exit Macro", "Custom Command", "Dialog for Command", "Dialog and Wait"]:
                    self.success_action_combo.setCurrentText(success_action)
                    # Update visibility immediately (no signal to trigger it yet)
                    if hasattr(self, 'success_command_input') and self.success_command_input is not None:
                        self.success_command_input.setVisible(success_action == "Custom Command")
            
            if hasattr(self, 'success_command_input') and self.success_command_input is not None and success_command:
                self.success_command_input.setText(success_command)
            
            # Set substring match checkbox
            if hasattr(self, 'substring_match_checkbox') and self.substring_match_checkbox is not None:
                self.substring_match_checkbox.setChecked(substring_match)
        except Exception as e:
            print(f"OutputBlock initialization error: {e}")
        finally:
            # Initialization complete - now connect signals safely
            self._initializing = False
            self._connect_signals()
    
    def setup_block_content(self, layout: QHBoxLayout):
        layout_last = QVBoxLayout()
        label = QLabel("Expect Output")
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)
        layout_last.addWidget(label)
        # Expected output
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(QLabel("Expected:"))
        self.expected_input = QLineEdit()
        self.expected_input.setPlaceholderText("OK")
        self.expected_input.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        h_layout1.addWidget(self.expected_input)
        layout_last.addLayout(h_layout1)
        
        # Timeout
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(QLabel("Timeout:"))
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(100, 60000)
        self.timeout_spinbox.setValue(1000)
        self.timeout_spinbox.setSuffix(" ms")
        self.timeout_spinbox.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        h_layout2.addWidget(self.timeout_spinbox)
        layout_last.addLayout(h_layout2)
        
        # Substring match checkbox
        h_layout_match = QHBoxLayout()
        self.substring_match_checkbox = QCheckBox("Substring Match")
        self.substring_match_checkbox.setChecked(True)
        self.substring_match_checkbox.setToolTip("When checked: match if expected text is found anywhere in line.\nWhen unchecked: entire line must match expected text exactly.")
        self.substring_match_checkbox.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        h_layout_match.addWidget(self.substring_match_checkbox)
        layout_last.addLayout(h_layout_match)
        
        # Success action
        self.success_action_combo = QComboBox()
        self.success_action_combo.addItems(["Ignore", "Continue", "Exit Macro", "Custom Command", "Dialog for Command", "Dialog and Wait"])
        self.success_action_combo.setCurrentText("Continue")
        self.success_action_combo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        layout_last.addWidget(QLabel("On Success:"))
        layout_last.addWidget(self.success_action_combo)
        
        # Custom success command (hidden by default)
        self.success_command_input = QLineEdit()
        self.success_command_input.setPlaceholderText("Success command")
        self.success_command_input.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.success_command_input.setVisible(False)
        layout_last.addWidget(self.success_command_input)
        
        # Fail action
        self.fail_action_combo = QComboBox()
        self.fail_action_combo.addItems(["Ignore", "Continue", "Exit Macro", "Custom Command", "Dialog for Command", "Dialog and Wait"])
        self.fail_action_combo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        layout_last.addWidget(QLabel("On Fail:"))
        layout_last.addWidget(self.fail_action_combo)
        
        # Custom fail command (hidden by default)
        self.fail_command_input = QLineEdit()
        self.fail_command_input.setPlaceholderText("Fail command")
        self.fail_command_input.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.fail_command_input.setVisible(False)
        layout_last.addWidget(self.fail_command_input)

        layout.addLayout(layout_last)
        
        # DO NOT connect signals here - they will be connected after initialization completes
        # This prevents race conditions on Windows where signals can fire during initialization
    
    def _connect_signals(self):
        """Connect signals after widget initialization is complete to prevent Windows race conditions"""
        try:
            if hasattr(self, 'success_action_combo') and self.success_action_combo is not None:
                # Verify the widget is fully initialized before connecting
                if hasattr(self.success_action_combo, 'currentTextChanged'):
                    try:
                        self.success_action_combo.currentTextChanged.connect(self.on_success_action_changed)
                    except RuntimeError as e:
                        print(f"OutputBlock success_action_combo signal connection RuntimeError: {e}")
                        
            if hasattr(self, 'fail_action_combo') and self.fail_action_combo is not None:
                # Verify the widget is fully initialized before connecting
                if hasattr(self.fail_action_combo, 'currentTextChanged'):
                    try:
                        self.fail_action_combo.currentTextChanged.connect(self.on_fail_action_changed)
                    except RuntimeError as e:
                        print(f"OutputBlock fail_action_combo signal connection RuntimeError: {e}")
        except Exception as e:
            print(f"OutputBlock _connect_signals error: {e}")
    
    def on_success_action_changed(self, text: str):
        """Handle success action combo box changes with error protection"""
        # Skip if still initializing
        if hasattr(self, '_initializing') and self._initializing:
            return
        
        try:
            if hasattr(self, 'success_command_input') and self.success_command_input is not None:
                # Verify widget still exists (not deleted by Qt)
                try:
                    # Check if C++ object is still valid before accessing
                    if not hasattr(self.success_command_input, 'setVisible'):
                        return
                    self.success_command_input.setVisible(text == "Custom Command")
                except RuntimeError as e:
                    # Widget was deleted by Qt (C++ object no longer exists)
                    print(f"OutputBlock on_success_action_changed RuntimeError: {e}")
        except AttributeError as e:
            # Attribute doesn't exist
            print(f"OutputBlock on_success_action_changed AttributeError: {e}")
        except Exception as e:
            print(f"Error in on_success_action_changed: {e}")
    
    def on_fail_action_changed(self, text: str):
        """Handle fail action combo box changes with error protection"""
        # Skip if still initializing
        if hasattr(self, '_initializing') and self._initializing:
            return
        
        try:
            if hasattr(self, 'fail_command_input') and self.fail_command_input is not None:
                # Verify widget still exists (not deleted by Qt)
                try:
                    # Check if C++ object is still valid before accessing
                    if not hasattr(self.fail_command_input, 'setVisible'):
                        return
                    self.fail_command_input.setVisible(text == "Custom Command")
                except RuntimeError as e:
                    # Widget was deleted by Qt (C++ object no longer exists)
                    print(f"OutputBlock on_fail_action_changed RuntimeError: {e}")
        except AttributeError as e:
            # Attribute doesn't exist
            print(f"OutputBlock on_fail_action_changed AttributeError: {e}")
        except Exception as e:
            print(f"Error in on_fail_action_changed: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary with error handling"""
        try:
            result: Dict[str, Any] = {
                "output": {
                    "expected": "",
                    "timeout": 1000,
                    "substring_match": True
                }
            }
            
            # Safely get values with RuntimeError protection
            try:
                if hasattr(self, 'expected_input') and self.expected_input is not None:
                    result["output"]["expected"] = self.expected_input.text()
            except RuntimeError:
                pass  # Widget deleted
            
            try:
                if hasattr(self, 'timeout_spinbox') and self.timeout_spinbox is not None:
                    result["output"]["timeout"] = self.timeout_spinbox.value()
            except RuntimeError:
                pass  # Widget deleted
            
            try:
                if hasattr(self, 'substring_match_checkbox') and self.substring_match_checkbox is not None:
                    result["output"]["substring_match"] = self.substring_match_checkbox.isChecked()
            except RuntimeError:
                pass  # Widget deleted
            
            # Handle success action
            try:
                if hasattr(self, 'success_action_combo') and self.success_action_combo is not None:
                    success_action = self.success_action_combo.currentText()
                    if success_action == "Ignore":
                        result["output"]["success"] = "IGNORE"
                    elif success_action == "Exit Macro":
                        result["output"]["success"] = "EXIT"
                    elif success_action == "Custom Command":
                        if hasattr(self, 'success_command_input') and self.success_command_input is not None:
                            try:
                                cmd = self.success_command_input.text()
                                if cmd:
                                    result["output"]["success"] = {"input": cmd}
                            except RuntimeError:
                                pass  # Widget deleted
                    elif success_action == "Dialog for Command":
                        result["output"]["success"] = "DIALOG"
                    elif success_action == "Dialog and Wait":
                        result["output"]["success"] = "DIALOG_WAIT"
                    # Continue is default, no need to add it
            except RuntimeError:
                pass  # Widget deleted
            
            # Handle fail action
            try:
                if hasattr(self, 'fail_action_combo') and self.fail_action_combo is not None:
                    fail_action = self.fail_action_combo.currentText()
                    if fail_action == "Ignore":
                        result["output"]["fail"] = "IGNORE"
                    elif fail_action == "Exit Macro":
                        result["output"]["fail"] = "EXIT"
                    elif fail_action == "Custom Command":
                        if hasattr(self, 'fail_command_input') and self.fail_command_input is not None:
                            try:
                                cmd = self.fail_command_input.text()
                                if cmd:
                                    result["output"]["fail"] = {"input": cmd}
                            except RuntimeError:
                                pass  # Widget deleted
                    elif fail_action == "Dialog for Command":
                        result["output"]["fail"] = "DIALOG"
                    elif fail_action == "Dialog and Wait":
                        result["output"]["fail"] = "DIALOG_WAIT"
                    # Continue is default, no need to add it
            except RuntimeError:
                pass  # Widget deleted
            
            return result
        except Exception as e:
            print(f"Error in OutputBlock.to_dict: {e}")
            # Return minimal valid structure
            return {
                "output": {
                    "expected": "",
                    "timeout": 1000
                }
            }


class MacroCanvas(QWidget):
    """Canvas where macro blocks are dropped and arranged"""
    
    def __init__(self, parent=None, accent_color: str = "#1E90FF", hover_color: str = "#63B8FF", background_color: str = "#1E1E1E", font_color: str = "#FFFFFF"):
        super().__init__(parent)
        self.accent_color = accent_color
        self.hover_color = hover_color
        self.background_color = background_color
        self.font_color = font_color
        # self.setAcceptDrops(True)
        self.setFixedWidth(600)

        # Create internal container for blocks
        from PyQt5.QtWidgets import QSizePolicy
        self.container = QWidget(self)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.container_layout.setContentsMargins(5, 5, 5, 5)
        self.container_layout.setSpacing(5)
        self.setStyleSheet(f"""
            border: 1px solid {self.accent_color};
            border-radius: 5px;
        """)
        self.container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.blocks: List[MacroBlock] = []
    
    def add_block(self, block_type: str, **kwargs):
        """Add a new block to the canvas"""
        block: Optional[MacroBlock] = None

        if block_type == "input":
            block = InputBlock(self.container, kwargs.get('command', ''), self.accent_color, self.hover_color, self.background_color)
        elif block_type == "delay":
            block = DelayBlock(self.container, kwargs.get('delay', 1000), self.accent_color, self.hover_color, self.background_color)
        elif block_type == "dialog_wait":
            block = DialogWaitBlock(self.container, kwargs.get('message', ''), self.accent_color, self.hover_color, self.background_color)
        elif block_type == "output":
            block = OutputBlock(self.container, 
                              kwargs.get('expected', ''), 
                              kwargs.get('timeout', 1000),
                              kwargs.get('fail_action', 'Continue'),
                              kwargs.get('fail_command', ''),
                              kwargs.get('success_action', 'Continue'),
                              kwargs.get('success_command', ''),
                              kwargs.get('substring_match', True),
                              self.accent_color, 
                              self.hover_color, 
                              self.background_color)
            
        if block:
            # Add vertical button group (Up, Close, Down)
            sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            btn_col = QVBoxLayout()
            btn_col.setSpacing(0)
            btn_col.setContentsMargins(0, 0, 0, 0)
            
            up_btn = QPushButton("↑")
            up_btn.setSizePolicy(sizePolicy)
            up_btn.setFixedWidth(20)
            up_btn.setStyleSheet(f"border-radius: 0; background-color: {self.accent_color}; color: {self.font_color};")
            up_btn.clicked.connect(lambda _, b=block: self.move_block_up(b))
            btn_col.addWidget(up_btn, 1)

            close_btn = QPushButton("✕")
            close_btn.setSizePolicy(sizePolicy)
            close_btn.setFixedWidth(20)
            close_btn.setStyleSheet(f"border-radius: 0; background-color: {self.accent_color}; color: {self.font_color};")
            close_btn.clicked.connect(lambda _, b=block: self.remove_block(b))
            btn_col.addWidget(close_btn, 1)

            down_btn = QPushButton("↓")
            down_btn.setSizePolicy(sizePolicy)
            down_btn.setFixedWidth(20)
            down_btn.setStyleSheet(f"border-radius: 0; background-color: {self.accent_color}; color: {self.font_color};")
            down_btn.clicked.connect(lambda _, b=block: self.move_block_down(b))
            btn_col.addWidget(down_btn, 1)

            # Add button column to block layout
            block_layout = block.layout()
            if block_layout:
                block_layout.setSpacing(5)
                block_layout.setContentsMargins(5, 5, 0, 5)
                block_layout.addLayout(btn_col, 0)

            self.blocks.append(block)
            self.container_layout.addWidget(block)
            self.container.updateGeometry()
            self.updateGeometry()
            scroll_width = self.parent().width() if self.parent() else 450
            self.container.setMinimumWidth(scroll_width)
            self.container.setMaximumWidth(scroll_width)
            self.container.resize(scroll_width, self.container.height())
    
    def remove_block(self, block: MacroBlock):
        if block in self.blocks:
            self.blocks.remove(block)
            block.deleteLater()
            self.container.updateGeometry()
            self.updateGeometry()
            # print(f"\n=== Block Removed ===")
            # print(f"Remaining blocks: {len(self.blocks)}")
            # print(f"Container size after removal: {self.container.size().width()}x{self.container.size().height()}")
    
    def clear_blocks(self):
        for block in self.blocks[:]:
            self.remove_block(block)
    
    def get_drop_index(self, pos: QPoint) -> int:
        y = pos.y()
        for i, block in enumerate(self.blocks):
            block_y = block.pos().y()
            block_height = block.height()
            block_center = block_y + block_height / 2
            if y < block_center:
                return i
        return len(self.blocks)
    
    def to_yaml_list(self) -> List[Dict[str, Any]]:
        return [block.to_dict() for block in self.blocks]
    
    def resizeEvent(self, a0):
        """Debug resize events"""
        super().resizeEvent(a0)
        # print(f"\n=== Canvas Resized ===")
        # print(f"New size: {self.size().width()}x{self.size().height()}")
        # print(f"Old size: {a0.oldSize().width()}x{a0.oldSize().height()}")


    def move_block_up(self, block):
        idx = self.blocks.index(block)
        if idx > 0:
            self.blocks[idx], self.blocks[idx-1] = self.blocks[idx-1], self.blocks[idx]
            self.container_layout.removeWidget(block)
            self.container_layout.insertWidget(idx-1, block)

    def move_block_down(self, block):
        idx = self.blocks.index(block)
        if idx < len(self.blocks)-1:
            self.blocks[idx], self.blocks[idx+1] = self.blocks[idx+1], self.blocks[idx]
            self.container_layout.removeWidget(block)
            self.container_layout.insertWidget(idx+1, block)


class MacroEditor(QDialog):
    """Main macro editor dialog"""
    
    def __init__(self, parent=None, macro_path: Optional[Path] = None, macro_name: str = "", style_manager: Optional['StyleManager'] = None):
        super().__init__(parent)
        self.macro_path = macro_path
        self.macro_name = macro_name
        self.style_manager = style_manager
        
        # Get colors from style_manager if available
        if style_manager:
            self.accent_color = style_manager.accent_color
            self.hover_color = style_manager.hover_color
        else:
            self.accent_color = "#1E90FF"
            self.hover_color = "#63B8FF"
        
        self.setWindowTitle("Macro Editor")
        self.resize(750, 600)
        
        # Track unsaved changes
        self.has_unsaved_changes = False
        self.initial_state = None  # Will store initial macro state for comparison
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Top: Macro name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Macro Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(macro_name)
        self.name_input.setPlaceholderText("Enter macro name")
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)
        
        # Middle: Split view (blocks palette + canvas)
        content_layout = QHBoxLayout()
        
        # Left: Block palette
        palette_widget = self.create_block_palette()
        content_layout.addWidget(palette_widget, 1)
        
        # Right: Macro canvas (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Get background and font colors from style_manager if available
        background_color = self.style_manager.bg_secondary if self.style_manager else "#1E1E1E"
        font_color = self.style_manager.font_color if self.style_manager else "#FFFFFF"
        self.canvas = MacroCanvas(accent_color=self.accent_color, hover_color=self.hover_color, background_color=background_color, font_color=font_color)
        scroll_area.setWidget(self.canvas.container)
        content_layout.addWidget(scroll_area, 2)
        
        main_layout.addLayout(content_layout)
        
        # Bottom: Action buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_macro)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Macro")
        save_btn.clicked.connect(self.save_macro)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
        
        # Load existing macro if provided
        if macro_path and macro_path.exists():
            self.load_macro(macro_path)
        
        # Store initial state for change detection
        self.initial_state = self.get_current_state()
        
        # Connect change signals
        self.name_input.textChanged.connect(self.mark_as_changed)
        
        # Apply styling
        self.apply_style()
    
    def apply_style(self):
        """Apply stylesheet from style manager"""
        if self.style_manager:
            self.setStyleSheet(self.style_manager.get_dialog_stylesheet())
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state of the macro for comparison"""
        return {
            'name': self.name_input.text().strip(),
            'blocks': len(self.canvas.blocks),
            'steps': self.canvas.to_yaml_list() if self.canvas.blocks else []
        }
    
    def mark_as_changed(self):
        """Mark the editor as having unsaved changes"""
        self.has_unsaved_changes = True
    
    def has_changes(self) -> bool:
        """Check if there are unsaved changes"""
        if not self.has_unsaved_changes:
            return False
        current_state = self.get_current_state()
        return current_state != self.initial_state
    
    def create_block_palette(self) -> QWidget:
        """Create the left panel with block type buttons"""
        palette_widget = QWidget()
        palette_layout = QVBoxLayout(palette_widget)
        palette_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        palette_layout.addWidget(QLabel("Block Palette"))
        # Block types and labels
        block_types = [
            ("input", "Add Send Command"),
            ("delay", "Add Delay"),
            ("dialog_wait", "Add Dialog Wait"),
            ("output", "Add Expect Output")
        ]
        for block_type, label in block_types:
            row = QHBoxLayout()
            # row.addWidget(QLabel(label))
            add_btn = QPushButton(label)
            # add_btn.setMaximumWidth(120)
            add_btn.clicked.connect(lambda _, t=block_type: self.on_add_block(t))
            row.addWidget(add_btn)
            palette_layout.addLayout(row)
        palette_layout.addStretch()
        return palette_widget
    
    def on_add_block(self, block_type: str):
        """Handle adding a block and mark as changed"""
        self.canvas.add_block(block_type)
        self.mark_as_changed()
    
    def reject(self):
        """Override reject to check for unsaved changes"""
        if self.has_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_macro()
                # Only close if save was successful (save_macro calls accept)
                return
            elif reply == QMessageBox.Cancel:
                return
            # If Discard, continue to close
        
        super().reject()
    
    def load_macro(self, macro_path: Path):
        """Load an existing macro from YAML file"""
        try:
            with open(macro_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                return
            
            # Get macro name
            self.name_input.setText(data.get('name', macro_path.stem))
            
            # Get steps
            steps = data.get('steps', [])
            
            for step in steps:
                if 'input' in step:
                    self.canvas.add_block('input', command=step['input'])
                elif 'delay' in step:
                    self.canvas.add_block('delay', delay=step['delay'])
                elif 'dialog_wait' in step:
                    dialog_data = step['dialog_wait']
                    self.canvas.add_block('dialog_wait', message=dialog_data.get('message', ''))
                elif 'output' in step:
                    output_data = step['output']
                    fail_data = output_data.get('fail')
                    success_data = output_data.get('success')
                    
                    # Determine fail action and fail command
                    fail_action = "Continue"  # default
                    fail_command = ""
                    
                    if fail_data == "IGNORE":
                        fail_action = "Ignore"
                    elif fail_data == "EXIT":
                        fail_action = "Exit Macro"
                    elif fail_data == "DIALOG":
                        fail_action = "Dialog for Command"
                    elif fail_data == "DIALOG_WAIT":
                        fail_action = "Dialog and Wait"
                    elif isinstance(fail_data, dict) and 'input' in fail_data:
                        fail_action = "Custom Command"
                        fail_command = fail_data['input']
                    
                    # Determine success action and success command
                    success_action = "Continue"  # default
                    success_command = ""
                    
                    if success_data == "IGNORE":
                        success_action = "Ignore"
                    elif success_data == "EXIT":
                        success_action = "Exit Macro"
                    elif success_data == "DIALOG":
                        success_action = "Dialog for Command"
                    elif success_data == "DIALOG_WAIT":
                        success_action = "Dialog and Wait"
                    elif isinstance(success_data, dict) and 'input' in success_data:
                        success_action = "Custom Command"
                        success_command = success_data['input']
                    
                    self.canvas.add_block('output', 
                                        expected=output_data.get('expected', ''),
                                        timeout=output_data.get('timeout', 1000),
                                        fail_action=fail_action,
                                        fail_command=fail_command,
                                        success_action=success_action,
                                        success_command=success_command,
                                        substring_match=output_data.get('substring_match', True))
        
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load macro: {e}")
    
    def save_macro(self):
        """Save the macro to YAML file"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a macro name.")
            return
        
        if not self.canvas.blocks:
            QMessageBox.warning(self, "Empty Macro", "Please add at least one block to the macro.")
            return
        
        # Convert blocks to YAML structure
        steps = self.canvas.to_yaml_list()
        
        macro_data = {
            'name': name,
            'steps': steps
        }
        
        # Save to file
        if not self.macro_path:
            # New macro - parent should provide the path
            self.macro_name = name
            self.macro_data = macro_data
            self.accept()
        else:
            try:
                with open(self.macro_path, 'w') as f:
                    yaml.dump(macro_data, f, default_flow_style=False, sort_keys=False)
                QMessageBox.information(self, "Success", f"Macro '{name}' saved successfully!")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save macro: {e}")
    
    def clear_macro(self):
        """Clear all blocks from the canvas"""
        reply = QMessageBox.question(
            self,
            "Clear Macro",
            "Are you sure you want to clear all blocks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.canvas.clear_blocks()
            self.mark_as_changed()
