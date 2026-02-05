"""
ManualDialog - Dialog for displaying application manual and documentation
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QTextBrowser, QSplitter
)
from PyQt5.QtCore import Qt
from typing import Dict


class ManualDialog(QDialog):
    """Dialog window for displaying user manual and documentation"""
    
    # Manual sections organized by topic
    MANUAL_SECTIONS = {
        "Overview": """<h2>Serial Communication Monitor - User Manual</h2>
<p>A powerful serial communication tool for monitoring, debugging, and automating serial device communication.</p>

<h3>Key Features:</h3>
<ul>
<li>Real-time serial port monitoring</li>
<li>Command history and quick buttons</li>
<li>Macro automation system</li>
<li>Custom command lists</li>
<li>Theme customization</li>
<li>Output filtering and formatting</li>
</ul>
""",

        "Commands Tab": """<h2>Commands Tab</h2>
<p>The Commands tab allows you to organize and execute predefined serial commands.</p>

<h3>Command Lists:</h3>
<ul>
<li><b>Dropdown:</b> Select from available YAML command files</li>
<li><b>No Input Commands:</b> Commands that execute immediately when clicked</li>
<li><b>Input Required Commands:</b> Commands that insert text into the input field for modification</li>
<li><b>Flat Commands:</b> Simple command list without arguments</li>
</ul>

<h3>Managing Command Lists:</h3>
<ul>
<li><b>New Command List:</b> Create a new YAML command file</li>
<li><b>Edit Selected List:</b> Opens the Commands Editor to modify commands</li>
<li><b>Duplicate Selected List:</b> Create a copy of the current command list</li>
<li><b>Refresh Command Lists:</b> Reload all YAML files from disk</li>
</ul>

<h3>Commands Editor:</h3>
<p>Edit command definitions with a dual-list interface:</p>
<ul>
<li><b>No Input Commands:</b> Execute immediately (command: description format)</li>
<li><b>Input Required Commands:</b> Insert into input field for editing</li>
<li><b>Save:</b> Save changes to the YAML file</li>
<li><b>Exit Safety:</b> Prompts to save unsaved changes</li>
</ul>
""",

        "Macros Tab": """<h2>Macros Tab</h2>
<p>Create automated sequences of commands with conditional logic and validation.</p>

<h3>Block Types:</h3>
<ul>
<li><b>Input Block (Blue):</b> Send commands to the serial port</li>
<li><b>Delay Block (Orange):</b> Add delays between commands (0-60000 ms)</li>
<li><b>Dialog Wait Block (Purple):</b> Pause for user confirmation</li>
<li><b>Output Block (Green):</b> Wait for expected responses with timeout and substring/full line matching</li>
</ul>

<h3>Output Block Matching:</h3>
<ul>
<li><b>Substring Match (checked):</b> Expected text can appear anywhere in the line</li>
<li><b>Full Line Match (unchecked):</b> Entire line must match expected text exactly</li>
<li><b>Timeout:</b> Maximum wait time in milliseconds (0-60000)</li>
</ul>

<h3>Output Block Actions:</h3>
<p><b>On Success:</b></p>
<ul>
<li>Ignore - Continue without action</li>
<li>Continue - Proceed to next step (default)</li>
<li>Exit Macro - Stop execution</li>
<li>Custom Command - Send specific command</li>
<li>Dialog for Command - Ask user for recovery command</li>
<li>Dialog and Wait - Show confirmation dialog</li>
</ul>

<p><b>On Fail:</b></p>
<ul>
<li>Continue - Proceed despite failure</li>
<li>Exit Macro - Stop execution (default)</li>
<li>Custom Command - Send recovery command</li>
<li>Dialog for Command - Ask user for recovery command</li>
</ul>

<h3>Creating Macros:</h3>
<ol>
<li>Click "Create New Macro"</li>
<li>Drag blocks from the palette to the canvas</li>
<li>Configure each block's parameters</li>
<li>Enter a macro name</li>
<li>Click "Save Macro"</li>
</ol>

<h3>Running Macros:</h3>
<ul>
<li>Must be connected to a serial port first</li>
<li>Click any macro button to execute</li>
<li>Watch output display for execution progress</li>
<li>Macros use a dedicated session buffer for response matching</li>
</ul>
""",

        "Settings Tab": """<h2>Settings Tab</h2>
<p>Double-click any value to edit. Boolean values toggle, others show input dialogs.</p>

<h3>Display Settings:</h3>
<ul>
<li><b>Auto Clear Output:</b> Clear output when connecting/disconnecting</li>
<li><b>Enable Tooltips:</b> Show/hide all tooltips</li>
<li><b>Reveal Hidden Char:</b> Display whitespace and special characters as symbols</li>
<li><b>Show Flow Indicators:</b> Display &lt; and &gt; symbols for data direction</li>
</ul>

<h3>Theme Settings:</h3>
<ul>
<li><b>Colors:</b> Use the "Select Theme" button in the About tab to change colors</li>
<li><b>Custom themes:</b> Edit settings.yaml directly for fine-tuned color control</li>
</ul>

<h3>Serial Port Settings:</h3>
<ul>
<li><b>DTR:</b> Data Terminal Ready state</li>
<li><b>RTS:</b> Request To Send state</li>
<li><b>Tx Line Ending:</b> Line ending for transmitted data (LN, CR, CRLN, NUL)</li>
<li><b>Data Bits:</b> Number of data bits (5, 6, 7, 8)</li>
<li><b>Parity:</b> Parity checking (None, Even, Odd, Space, Mark)</li>
<li><b>Stop Bits:</b> Number of stop bits (1, 1.5, 2)</li>
<li><b>Flow Control:</b> Flow control method (None, Hardware, Software)</li>
<li><b>Open Mode:</b> Port access mode (R/W, RO, WO)</li>
<li><b>Custom Baud Rate:</b> Custom baud rate value</li>
</ul>

<h3>Output Display Settings:</h3>
<ul>
<li><b>Max Output Lines:</b> Maximum lines to keep in buffer (prevents unlimited memory growth)</li>
<li><b>Filter Empty Lines:</b> Hide lines with no content from display</li>
<li><b>Custom Line Filter:</b> Filter specific lines by exact text match (stripped)</li>
</ul>

<h3>Window Settings:</h3>
<ul>
<li><b>Maximized:</b> Start application maximized</li>
<li><b>Disconnect On Inactive:</b> Auto-disconnect when app loses focus, auto-reconnect when regaining focus (! warning on Connect button when enabled)</li>
</ul>

<h3>Configuration Directory:</h3>
<p>Click "Open Configurations Directory" to access:</p>
<ul>
<li>settings.yaml - Application settings</li>
<li>command_history.txt - Command history</li>
<li>commands/ - YAML command files</li>
<li>macros/ - Saved macro files</li>
</ul>
""",

        "Main Window": """<h2>Main Window Interface</h2>

<h3>Top Ribbon:</h3>
<ul>
<li><b>Serial Port:</b> Select COM/TTY port to connect to</li>
<li><b>Baud Rate:</b> Select communication speed (9600-921600 or Custom)</li>
<li><b>Connect/Disconnect:</b> Toggle serial connection (shows ! when Disconnect On Inactive is enabled)</li>
<li><b>Command Input:</b> Enter commands to send</li>
<li><b>Send Button:</b> Send command or repeat last command if input is blank</li>
<li><b>Auto Reconnect:</b> Automatically reconnect if connection is lost</li>
</ul>

<h3>Output Display:</h3>
<ul>
<li><b>&lt; symbol:</b> Data sent to device (if flow indicators enabled)</li>
<li><b>&gt; symbol:</b> Data received from device (if flow indicators enabled)</li>
<li><b>Right-click menu:</b> Toggle display format (Text/Hex) and timestamps</li>
<li><b>Timestamps:</b> Show [HH:MM:SS.mmm] with each message</li>
<li><b>Hex Mode:</b> Display data as hexadecimal values</li>
</ul>

<h3>Quick Buttons (A-E):</h3>
<ul>
<li><b>Left-click:</b> Execute assigned command</li>
<li><b>Right-click:</b> Edit button (set label, command, tooltip) or clear</li>
<li>Use for frequently-used commands</li>
<li>Settings saved automatically</li>
</ul>

<h3>Action Buttons:</h3>
<ul>
<li><b>Save Output:</b> Export output display to a text file</li>
<li><b>Clear Output:</b> Clear all text from output display</li>
</ul>

<h3>Status Bar:</h3>
<ul>
<li><b>Serial Status:</b> Connection state (red=disconnected, green=connected)</li>
<li><b>Connected Time:</b> Duration of current connection (HH:MM:SS)</li>
<li><b>Macro Status:</b> Current macro execution state</li>
<li><b>Lines:</b> Output line count and percentage of max buffer</li>
</ul>
""",

        "Keyboard Shortcuts": """<h2>Keyboard Shortcuts</h2>

<h3>Command Input:</h3>
<ul>
<li><b>Enter:</b> Send command</li>
<li><b>Enter + Enter:</b> Double-press to resend last command</li>
<li><b>Up/Down Arrows:</b> Navigate command history</li>
</ul>

<h3>History Tab:</h3>
<ul>
<li><b>Double-click:</b> Send command from history immediately</li>
<li><b>Clear History:</b> Remove all saved commands</li>
</ul>
""",

        "Tips & Best Practices": """<h2>Tips & Best Practices</h2>

<h3>Performance:</h3>
<ul>
<li>Use "Max Output Lines" to prevent memory issues with long sessions</li>
<li>Enable "Filter Empty Lines" to reduce noise</li>
<li>Use "Custom Line Filter" to hide repetitive status messages</li>
</ul>

<h3>Macros:</h3>
<ul>
<li>Test macros with verbose output first</li>
<li>Use Dialog Wait blocks for manual intervention points</li>
<li>Add delays after commands that take time to process</li>
<li>Use Output blocks to validate responses</li>
<li>Macro responses are captured in a dedicated buffer (unaffected by filters)</li>
</ul>

<h3>Command Organization:</h3>
<ul>
<li>Create separate YAML files for different devices</li>
<li>Use descriptive names for commands</li>
<li>Duplicate and modify existing lists rather than starting from scratch</li>
</ul>

<h3>Themes:</h3>
<ul>
<li>Choose high-contrast themes for better readability</li>
<li>Test custom colors before committing</li>
<li>See THEMES.md in the repository for theme gallery</li>
</ul>

<h3>Serial Port Management:</h3>
<ul>
<li>Enable "Disconnect On Inactive" to release ports when switching applications</li>
<li>Use "Auto Reconnect" for unstable connections</li>
<li>Check DTR/RTS settings if device doesn't respond</li>
</ul>
""",

        "Troubleshooting": """<h2>Troubleshooting</h2>

<h3>Connection Issues:</h3>
<ul>
<li><b>Port not listed:</b> Check device drivers, try different USB cable</li>
<li><b>Access denied:</b> Close other applications using the port</li>
<li><b>No response:</b> Verify baud rate, parity, stop bits, and flow control</li>
<li><b>Garbled text:</b> Wrong baud rate or data bits settings</li>
</ul>

<h3>Display Issues:</h3>
<ul>
<li><b>Missing characters:</b> Disable "Filter Empty Lines" if needed</li>
<li><b>Can't see spaces:</b> Enable "Reveal Hidden Char"</li>
<li><b>Too much output:</b> Reduce "Max Output Lines" or use filtering</li>
</ul>

<h3>Macro Issues:</h3>
<ul>
<li><b>Responses not detected:</b> Check for extra whitespace, adjust timeout</li>
<li><b>Macro fails silently:</b> Check output display for error messages</li>
<li><b>Timing issues:</b> Increase delay blocks between commands</li>
</ul>

<h3>Performance Issues:</h3>
<ul>
<li><b>Slow display:</b> Reduce "Max Output Lines"</li>
<li><b>High memory:</b> Enable "Auto Clear Output" or clear manually</li>
<li><b>UI freezing:</b> Check for very high baud rates or continuous data streams</li>
</ul>
""",

        "File Formats": """<h2>File Formats</h2>

<h3>settings.yaml:</h3>
<p>Stores all application settings including colors, serial configuration, and UI state.</p>

<h3>Command Files (.yaml):</h3>
<pre>
commands:
  no_input:
    AT: "Test command"
    AT+CPIN?: "Check SIM PIN"
  input_required:
    AT+CMGS=: "Send SMS"
  flat_commands:
    - AT
    - ATI
    - AT+CSQ
</pre>

<h3>Macro Files (.yaml):</h3>
<pre>
name: Macro Name
steps:
  - input: "AT"
  - delay: 1000
  - output:
      expected: "OK"
      timeout: 1000
      fail: EXIT
      success: CONTINUE
  - dialog_wait:
      message: "Continue?"
</pre>

<h3>Output Save Format:</h3>
<p>Plain text with timestamps and flow indicators (if enabled).</p>
""",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Manual")
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the manual dialog UI"""
        layout = QVBoxLayout(self)
        
        # # Title
        # title = QLabel("<h1>Serial Communication Monitor - User Manual</h1>")
        # title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(title)
        
        # Create splitter for list and content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - section list
        self.section_list = QListWidget()
        self.section_list.setMaximumWidth(200)
        for section in self.MANUAL_SECTIONS.keys():
            self.section_list.addItem(section)
        self.section_list.currentItemChanged.connect(self.on_section_changed)
        splitter.addWidget(self.section_list)
        
        # Right side - content display
        self.content_display = QTextBrowser()
        self.content_display.setOpenExternalLinks(True)
        splitter.addWidget(self.content_display)
        
        # Set splitter sizes
        splitter.setSizes([200, 700])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # Select first section by default
        if self.section_list.count() > 0:
            self.section_list.setCurrentRow(0)
    
    def on_section_changed(self, current, previous):
        """Update content display when section selection changes"""
        if current:
            section_name = current.text()
            content = self.MANUAL_SECTIONS.get(section_name, "")
            self.content_display.setHtml(content)
