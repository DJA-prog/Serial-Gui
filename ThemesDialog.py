"""
ThemesDialog - Dialog for selecting and applying pre-programmed color themes
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import Dict, Any, Callable, Optional


class ThemesDialog(QDialog):
    """Dialog window for selecting from pre-defined color themes"""
    
    # Pre-programmed themes
    THEMES = {
        "Default": {
            "accent_color": "#1E90FF",
            "hover_color": "#63B8FF",
            "font_color": "#FFFFFF",
            "background_color": "#121212",
            "description": "Clean and professional dark theme with electric blue accents. Best for general use and extended sessions."
        },
        "Hacker Mint": {
            "accent_color": "#0b3123",
            "hover_color": "#ff505e",
            "font_color": "#07fca2",
            "background_color": "#111111",
            "description": "Matrix-inspired green on black terminal aesthetic. Perfect for terminal enthusiasts and retro computing fans."
        },
        "Midnight Blue": {
            "accent_color": "#2C5F8D",
            "hover_color": "#4A90D9",
            "font_color": "#E0E0E0",
            "background_color": "#0A1628",
            "description": "Professional dark blue theme with subtle contrasts. Sophisticated and easy on the eyes."
        },
        "Sunset": {
            "accent_color": "#FF6B35",
            "hover_color": "#FFB347",
            "font_color": "#F7F7F7",
            "background_color": "#1A1A2E",
            "description": "Warm orange/red accents on deep navy. Vibrant and energetic color scheme."
        },
        "Monochrome": {
            "accent_color": "#555555",
            "hover_color": "#888888",
            "font_color": "#DDDDDD",
            "background_color": "#1C1C1C",
            "description": "Pure grayscale theme with minimal distraction. Perfect for focused work."
        },
        "Forest": {
            "accent_color": "#2D5016",
            "hover_color": "#4F7942",
            "font_color": "#C8E6C9",
            "background_color": "#0D1B0D",
            "description": "Natural green tones, easy on the eyes. Inspired by peaceful forest environments."
        },
        "Purple Haze": {
            "accent_color": "#6A0572",
            "hover_color": "#AB83A1",
            "font_color": "#E1BEE7",
            "background_color": "#1A0B1A",
            "description": "Rich purple theme for a unique and creative look. Stand out from the crowd."
        }
    }
    
    def __init__(self, parent=None, current_settings: Optional[Dict[str, Any]] = None, apply_callback: Optional[Callable] = None):
        """
        Initialize the themes dialog
        
        Args:
            parent: Parent widget
            current_settings: Current theme settings
            apply_callback: Callback function to apply the selected theme
        """
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.apply_callback = apply_callback
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI"""
        self.setWindowTitle("Theme Selection")
        self.setModal(True)
        self.resize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Select a Theme")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Content layout (list + preview)
        content_layout = QHBoxLayout()
        
        # Left side - themes list
        list_layout = QVBoxLayout()
        list_label = QLabel("Available Themes:")
        list_layout.addWidget(list_label)
        
        self.themes_list = QListWidget()
        
        # Populate themes list
        for theme_name in self.THEMES.keys():
            item = QListWidgetItem(theme_name)
            self.themes_list.addItem(item)
        
        # Select the first theme by default
        self.themes_list.setCurrentRow(0)
        self.themes_list.currentItemChanged.connect(self.on_theme_selected)
        
        list_layout.addWidget(self.themes_list)
        content_layout.addLayout(list_layout, 1)
        
        # Right side - theme preview
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Theme Details:")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        content_layout.addLayout(preview_layout, 2)
        main_layout.addLayout(content_layout)
        
        # Update preview with first theme
        self.update_preview(list(self.THEMES.keys())[0])
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply Theme")
        self.apply_button.clicked.connect(self.apply_theme)
        button_layout.addWidget(self.apply_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
    def on_theme_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle theme selection change"""
        if current:
            theme_name = current.text()
            self.update_preview(theme_name)
    
    def update_preview(self, theme_name: str) -> None:
        """Update the preview text with theme details"""
        if theme_name not in self.THEMES:
            return
            
        theme = self.THEMES[theme_name]
        
        preview_html = f"""
        <h3>{theme_name}</h3>
        <p><i>{theme['description']}</i></p>
        
        <h4>Color Values:</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 5px;">Accent Color:</td>
                <td style="padding: 5px; background-color: {theme['accent_color']};">&nbsp;&nbsp;&nbsp;&nbsp;</td>
                <td style="padding: 5px;">{theme['accent_color']}</td>
            </tr>
            <tr>
                <td style="padding: 5px;">Hover Color:</td>
                <td style="padding: 5px; background-color: {theme['hover_color']};">&nbsp;&nbsp;&nbsp;&nbsp;</td>
                <td style="padding: 5px;">{theme['hover_color']}</td>
            </tr>
            <tr>
                <td style="padding: 5px;">Font Color:</td>
                <td style="padding: 5px; background-color: {theme['font_color']};">&nbsp;&nbsp;&nbsp;&nbsp;</td>
                <td style="padding: 5px;">{theme['font_color']}</td>
            </tr>
            <tr>
                <td style="padding: 5px;">Background:</td>
                <td style="padding: 5px; background-color: {theme['background_color']};">&nbsp;&nbsp;&nbsp;&nbsp;</td>
                <td style="padding: 5px;">{theme['background_color']}</td>
            </tr>
        </table>
        """
        
        self.preview_text.setHtml(preview_html)
    
    def apply_theme(self) -> None:
        """Apply the selected theme"""
        current_item = self.themes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a theme to apply.")
            return
        
        theme_name = current_item.text()
        theme = self.THEMES[theme_name]
        
        # Call the callback if provided
        if self.apply_callback:
            # Extract only the color settings
            theme_settings = {
                "accent_color": theme["accent_color"],
                "hover_color": theme["hover_color"],
                "font_color": theme["font_color"],
                "background_color": theme["background_color"]
            }
            self.apply_callback(theme_settings)
        
        QMessageBox.information(
            self, 
            "Theme Applied", 
            f"The '{theme_name}' theme has been applied successfully!"
        )
        
        # Close the dialog
        self.accept()
