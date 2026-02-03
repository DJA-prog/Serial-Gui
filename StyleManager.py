"""
StyleManager - Centralized stylesheet management for consistent theming across the application
"""
from typing import Dict, Any


class StyleManager:
    """Manages application-wide styling and theming"""
    
    def __init__(self, settings: Dict[str, Any]):
        """
        Initialize StyleManager with settings
        
        Args:
            settings: Dictionary containing theme settings
        """
        self.accent_color = settings.get('accent_color', '#1E90FF')
        self.hover_color = settings.get('hover_color', '#63B8FF')
        self.font_color = settings.get('font_color', '#FFFFFF')
        self.bg_primary = settings.get('background_color', '#121212')
        self.bg_secondary = self._lighten_color(self.bg_primary, 10)
        self.bg_tertiary = self._lighten_color(self.bg_primary, 20)
        self.font_size = settings.get('font_size', 10)
    
    def _lighten_color(self, hex_color: str, amount: int) -> str:
        """Lighten a hex color by adding an amount to each RGB component"""
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Add amount and clamp to 255
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_main_window_stylesheet(self) -> str:
        """Get stylesheet for the main application window"""
        return f"""
            QMainWindow {{
                background-color: {self.bg_primary};
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QLabel {{
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QLineEdit, QTextEdit, QTableWidget {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                font-size: {self.font_size}pt;
            }}
            QHeaderView::section {{
                background-color: {self.accent_color};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                padding: 4px;
                font-size: {self.font_size}pt;
            }}
            QComboBox {{
                background-color: {self.bg_tertiary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                padding: 2px;
                font-size: {self.font_size}pt;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.bg_tertiary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                selection-background-color: {self.accent_color};
                selection-color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QCheckBox {{
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QCheckBox::indicator {{
                border: 1px solid {self.accent_color};
                width: 15px;
                height: 15px;
                border-radius: 3px;
                background-color: {self.bg_secondary};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.accent_color};
            }}
            QTableWidget::item {{
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QTableWidget::item:selected {{
                background-color: {self.accent_color};
                color: {self.font_color};
            }}
            QScrollBar:vertical, QScrollBar:horizontal {{
                background-color: {self.bg_secondary};
                border: none;
                width: 10px;
                height: 10px;
            }}
            QScrollBar::handle {{
                background-color: {self.accent_color};
                border-radius: 5px;
            }}
            QScrollBar::handle:hover {{
                background-color: {self.hover_color};
            }}
            QMessageBox {{
                background-color: {self.bg_primary};
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QInputDialog {{
                background-color: {self.bg_primary};
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QDialog {{
                background-color: {self.bg_primary};
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QWidget {{
                background-color: {self.bg_primary};
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QListWidget {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                font-size: {self.font_size}pt;
            }}
            QListWidget::item {{
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QListWidget::item:selected {{
                background-color: {self.accent_color};
                color: {self.font_color};
            }}
            QListWidget::item:hover {{
                background-color: {self.hover_color};
                color: {self.font_color};
            }}
            QTabWidget::pane {{
                border: 1px solid {self.accent_color};
                border-bottom: none;
                background: {self.bg_primary};
            }}
            QTabBar::tab {{
                background: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 6px;
                min-width: 100px;
                font-size: {self.font_size}pt;
            }}
            QTabBar::tab:selected {{
                background: {self.accent_color};
                color: {self.font_color};
            }}
            QTabBar::tab:hover {{
                background: {self.hover_color};
                color: {self.font_color};
            }}
            QPushButton {{
                background-color: {self.accent_color};
                color: {self.font_color};
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: {self.font_size}pt;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color};
            }}
            QSpinBox {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                font-size: {self.font_size}pt;
            }}
        """
    
    def get_dialog_stylesheet(self) -> str:
        """Get stylesheet for dialog windows (MacroEditor, CommandsEditor, etc.)"""
        return f"""
            QDialog {{
                background-color: {self.bg_primary};
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QLabel {{
                color: {self.font_color};
                font-size: {self.font_size}pt;
                border: none;
                background: transparent;
            }}
            QLineEdit {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                padding: 5px;
                font-size: {self.font_size}pt;
            }}
            QListWidget {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                font-size: {self.font_size}pt;
            }}
            QListWidget::item {{
                color: {self.font_color};
                padding: 5px;
                font-size: {self.font_size}pt;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {self.accent_color};
                color: {self.font_color};
            }}
            QListWidget::item:hover {{
                background-color: {self.hover_color};
                color: {self.font_color};
            }}
            QPushButton {{
                background-color: {self.accent_color};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                padding: 5px;
                font-size: {self.font_size}pt;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color};
                border: 1px solid {self.hover_color};
            }}
            QPushButton:pressed {{
                background-color: {self.accent_color};
                border: 1px solid {self.accent_color};
            }}
            QSpinBox {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                padding: 2px;
                font-size: {self.font_size}pt;
            }}
            QComboBox {{
                background-color: {self.bg_tertiary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                border-radius: 5px;
                padding: 2px;
                font-size: {self.font_size}pt;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.bg_tertiary};
                color: {self.font_color};
                border: 1px solid {self.accent_color};
                selection-background-color: {self.accent_color};
                selection-color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
            QFrame {{
                background-color: {self.bg_primary};
                border: none;
                border-radius: 5px;
                font-size: {self.font_size}pt;
            }}
            QListWidget {{
                background-color: {self.bg_secondary};
                color: {self.font_color};
                border: 1px solid {self.accent_color} !important;
                border-radius: 5px;
                font-size: {self.font_size}pt;
            }}
            QScrollArea {{
                background-color: {self.bg_primary};
                border: none;
                font-size: {self.font_size}pt;
            }}
            QWidget {{
                color: {self.font_color};
                font-size: {self.font_size}pt;
            }}
        """
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update style settings and refresh colors"""
        self.accent_color = settings.get('accent_color', self.accent_color)
        self.hover_color = settings.get('hover_color', self.hover_color)
        self.font_color = settings.get('font_color', self.font_color)
        self.bg_primary = settings.get('background_color', self.bg_primary)
        # Automatically derive secondary and tertiary from primary
        self.bg_secondary = self._lighten_color(self.bg_primary, 10)
        self.bg_tertiary = self._lighten_color(self.bg_primary, 20)
        self.font_size = settings.get('font_size', self.font_size)
