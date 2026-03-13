<div align="center">

# Serial Communication Monitor

![Version](https://img.shields.io/badge/version-2.6.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A modern, cross-platform serial monitor application built with PyQt5. This tool provides a powerful and user-friendly interface for interacting with serial devices, managing commands, executing macros, and viewing responses in real time.

![Preview](images/V2.5.0_preview.png)

</div>

## Tested Platforms

- ✅ **Windows 10**
- ✅ **Debian 13** (Trixie)
- Should work on macOS and other Linux distributions

## Features

### Core Functionality
- **Cross-platform support** (Windows 10+, Linux, macOS) using PyQt5
- **Serial port management** with auto-detection and reconnection
- **Flexible baud rate configuration** including custom rates
- **Real-time data transmission** with configurable line endings (CR, LF, CRLF)
- **Threaded serial reader** prevents UI freezing during data bursts
- **Command history** with quick access (single-click to insert, double-click to send)
- **Output display** with optional hex conversion and hidden character visualization
- **Output filtering** with empty line removal and custom line filters
- **Blank line indicators** for improved readability

### Command Management
- **Command sets** loaded from YAML files with two categories:
  - Commands requiring no input (click to send)
  - Commands requiring input (click to insert template)
- **Commands Editor** for creating and managing command sets
- **Exit safety** prevents accidental loss of unsaved command sets
- **Last selected command set** is remembered across sessions

### Macro System
- **Drag-and-drop macro editor** with Scratch-like interface
- **Four block types**:
  - Input blocks: Send commands
  - Delay blocks: Wait for specified duration
  - Output blocks: Expect response with timeout and fail actions
  - Dialog Wait blocks: Pause macro for user decision
- **Advanced fail actions**: Continue, End macro, or Dialog for custom command
- **Improved response detection** with per-line matching and session buffer
- **Macro execution** with visual feedback
- **Exit safety** prevents accidental loss of unsaved macros

### Customization
- **Centralized theming** with StyleManager
- **Configurable colors**: Accent, hover, font, and background
- **Automatic color derivation** for secondary/tertiary backgrounds
- **Pre-made color themes** with gallery (see THEMES.md)
- **Font size adjustment** for accessibility
- **Customizable quick-access buttons** (10 configurable buttons)
- **Tooltips** with enable/disable option
- **Settings persistence** across sessions

### Serial Configuration
- **DTR/RTS control** via settings
- **Configurable serial parameters**: Data bits, parity, stop bits, flow control
- **Open mode selection**: Read/Write, Read-only, Write-only
- **Auto-clear output** option
- **Maximum output lines** limit to prevent memory issues

## Getting Started

### Prerequisites

- Python 3.7+
- [PyQt5](https://pypi.org/project/PyQt5/)
- [pyserial](https://pypi.org/project/pyserial/)
- [PyYAML](https://pypi.org/project/PyYAML/)

Install dependencies:

```sh
pip install -r requirements.txt
```

### Running the Application

```sh
python App.py
```

### Windows Executable

Pre-built single-file executables for Windows will be available in the [Releases](https://github.com/DJA-prog/Serial-Gui/releases) section. No Python installation required—just download and run.

## Usage

### Basic Operation
1. Select the serial port and baud rate from the dropdowns
2. Click **Connect** to establish connection
3. Enter commands in the input field and press **Send** or Enter
4. Use **Send** button with empty input to repeat last command
5. Press Enter twice quickly to resend last command

### Command Tab
- Select a command set from the dropdown
- Click commands in "No Input Required" list to send immediately
- Click commands in "Require Input" list to insert template into input field
- Use **New Command List** to create custom command sets
- Use **Edit Selected List** to modify existing sets

### History Tab
- Single-click an entry to insert into input field
- Double-click an entry to send immediately
- View all previously sent commands
- Clear history with the button at bottom

### Macros Tab
- Create drag-and-drop automation sequences
- Add Input, Delay, Output, and Dialog Wait blocks
- Configure fail actions: Continue, End, or Dialog for custom command
- Save macros for repeated use (exit safety prevents accidental loss)
- Execute macros with visual status updates
- See MACROS.md for complete documentation and examples

### Settings Tab
- **Colors**: Click to change accent, hover, font, and background colors (see THEMES.md for theme gallery)
- **Serial Settings**: Configure DTR, RTS, data bits, parity, stop bits, flow control
- **Display Options**: Toggle tooltips, hidden characters, auto-clear output
- **Output Filtering**: Filter empty lines, set custom line filter for noise reduction
- **Line Endings**: Choose CR, LF, or CRLF for transmitted data
- **Maximum Output Lines**: Set buffer limit (default: 10000)

### About Tab
- View application version
- Access GitHub repository
- Read application description

## Configuration

### Configuration Directory
Settings are stored in OS-specific locations:
- **Windows**: `%APPDATA%\SerialCommunicationMonitor\`
- **macOS**: `~/Library/Application Support/SerialCommunicationMonitor/`
- **Linux**: `~/.config/SerialCommunicationMonitor/`

### Files
- `settings.yaml`: Application settings and preferences
- `command_history.txt`: Command history log
- `commands/*.yaml`: Command set definitions
- `macros/*.yaml`: Saved macro sequences

### Documentation
- `README.md`: Main application documentation
- `MACROS.md`: Complete macro system guide with examples
- `THEMES.md`: Custom color theme gallery and creation guide
- `release_notes/`: Version history and changelogs

### Command Set Format
```yaml
no_input_commands:
  AT: "Check if module is ready"
  ATE0: "Disable command echo"

input_required_commands:
  AT+CMGS: "Send SMS message"
  AT+CMGR: "Read SMS message"
```

## Keyboard Shortcuts

- **Enter**: Send command
- **Enter + Enter** (double-press): Resend last command
- **Up/Down arrows**: Navigate command history in input field

## Architecture

### Key Components
- **App.py**: Main application window and logic (v2.3.0)
- **StyleManager.py**: Centralized theming and stylesheet management
- **MacroEditor.py**: Drag-and-drop macro creation interface with exit safety
- **CommandsEditor.py**: Command set editor with dual-list layout and exit safety
- **SerialReaderThread**: Background thread for non-blocking serial I/O

### Design Patterns
- **Thread safety**: Qt signals/slots for cross-thread communication
- **Settings management**: YAML-based persistent storage
- **Style centralization**: Single source of truth for UI theming
- **Type hints**: Full type annotations for maintainability

## Directory Structure

```
App.py                      # Main application (v2.3.0)
StyleManager.py            # Centralized styling
MacroEditor.py             # Macro creation interface
CommandsEditor.py          # Command set editor
README.md                  # Main documentation
MACROS.md                  # Macro system guide
THEMES.md                  # Color theme gallery
requirements.txt
commands/
    sim800l.yaml          # SIM800L AT commands
    sim808.yaml           # SIM808 AT commands
images/
    default_theme.png     # Default theme screenshot
    hacker_mint_theme.png # Hacker theme screenshot
logs/
release_notes/            # Version changelogs
```

## Similar Software

- CuteCom (Linux serial terminal)
- Arduino IDE Serial Monitor
- PuTTY (with serial support)
- RealTerm (Windows)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License

## Acknowledgments

Inspired by CuteCom and Arduino IDE Serial Monitor. This project is not affiliated with these applications. All trademarks are property of their respective owners.

<a href="https://www.flaticon.com/free-icons/computer" title="computer icons">Computer icons created by Freepik - Flaticon</a>
