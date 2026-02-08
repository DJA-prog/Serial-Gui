"""
Crash Report Dialog for Serial Communication Monitor
Displays crash reports with options to copy, save, and open GitHub issues
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont
import platform
from pathlib import Path
from datetime import datetime


class CrashReportDialog(QDialog):
    """Dialog to display crash reports with copy/save/report options"""
    
    GITHUB_ISSUES_URL = "https://github.com/DJA-prog/SerialCommunicationMonitor/issues/new"
    
    def __init__(self, crash_report: str, parent=None):
        super().__init__(parent)
        self.crash_report = crash_report
        self.setWindowTitle("Crash Report - Serial Communication Monitor")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title and explanation
        title_label = QLabel("Application Crash Detected")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF6B6B;")
        layout.addWidget(title_label)
        
        explanation = QLabel(
            "The application has encountered an error. Below is a detailed crash report.\n"
            "You can copy this report to your clipboard, save it to a file, or report it on GitHub."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Crash report text area
        self.text_area = QTextEdit()
        self.text_area.setPlainText(self.crash_report)
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Courier", 9))
        layout.addWidget(self.text_area)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.setToolTip("Copy the crash report to clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        buttons_layout.addWidget(copy_btn)
        
        # Save button
        save_btn = QPushButton("💾 Save to File")
        save_btn.setToolTip("Save the crash report to a file")
        save_btn.clicked.connect(self.save_to_file)
        buttons_layout.addWidget(save_btn)
        
        # GitHub button
        github_btn = QPushButton("🐛 Report on GitHub")
        github_btn.setToolTip("Open GitHub to create a new issue")
        github_btn.clicked.connect(self.open_github_issues)
        buttons_layout.addWidget(github_btn)
        
        buttons_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Footer with auto-save info
        footer = QLabel("Note: Crash reports are automatically saved to the logs directory.")
        footer.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(footer)
    
    def copy_to_clipboard(self):
        """Copy crash report to clipboard"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.crash_report)
        
        # Show confirmation
        QMessageBox.information(
            self, 
            "Copied", 
            "Crash report copied to clipboard!\n\nYou can now paste it into a GitHub issue or email."
        )
    
    def save_to_file(self):
        """Save crash report to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"crash_report_{timestamp}.md"
        
        # Determine default directory based on platform
        if platform.system() == 'Windows':
            default_dir = str(Path.home() / "Desktop")
        else:
            default_dir = str(Path.home())
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Crash Report",
            str(Path(default_dir) / default_name),
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.crash_report)
                
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Crash report saved to:\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Failed to save crash report:\n{e}"
                )
    
    def open_github_issues(self):
        """Open GitHub issues page in browser"""
        # Try to open the URL
        if QDesktopServices.openUrl(QUrl(self.GITHUB_ISSUES_URL)):
            QMessageBox.information(
                self,
                "GitHub Issues",
                "Opening GitHub in your browser...\n\n"
                "Please paste the crash report (use the Copy button) when creating your issue."
            )
        else:
            # Fallback: show URL for manual copy
            QMessageBox.information(
                self,
                "GitHub Issues",
                f"Could not open browser automatically.\n\n"
                f"Please visit:\n{self.GITHUB_ISSUES_URL}\n\n"
                f"Then paste the crash report when creating your issue."
            )
