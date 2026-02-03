# Serial Communication Monitor v2.2.0 Release Notes

**Release Date:** February 2, 2026

## What's New in v2.2.0

### 🎨 Centralized Style Management
- **New StyleManager class** - All stylesheets extracted into a single, centralized style manager
- **Dynamic theme customization** - Change background colors, accent colors, and font sizes from Settings
- **Consistent styling** - Main app, Macro Editor, and Commands Editor now share unified styling
- **Auto-derived colors** - Secondary and tertiary background colors automatically calculated from primary background

### 🎯 Commands Tab Enhancements
- **Command Set Editor** - New dedicated editor for creating and managing command YAML files
- **Two-list organization** - Separate lists for commands requiring input vs. no-input commands
- **In-app creation** - Create new command sets without leaving the application
- **Edit existing sets** - Modify command lists with a user-friendly interface
- **Persistent selection** - Last selected command list is remembered across sessions
- **Protected YAML handling** - Automatic string quoting prevents YAML parsing failures from special characters

### 🔧 Macro System
- **Visual macro editor** - Drag-and-drop canvas for building command sequences
- **Multiple step types**:
  - Send commands
  - Add delays
  - Wait for expected responses with timeout handling
- **Macro management** - Create, edit, delete, and organize macros from the Macros tab
- **Thread-safe execution** - Macros run in background threads without freezing the UI
- **Status indicators** - Real-time macro execution status display

### ⚡ Performance & Reliability
- **Threaded serial reading** - Serial data processing moved to dedicated thread
- **Buffered input** - Handles large data bursts without UI freezes
- **Smart line handling** - Accumulates partial data until complete lines are received
- **Up to 4KB chunks** - Efficient processing of high-volume serial data

### 📋 Command History Improvements
- **Double-click to send** - Quickly resend commands from history with double-click
- **Visual history list** - Commands displayed in reverse chronological order
- **Clear history option** - Remove all history with confirmation dialog
- **Persistent storage** - History saved between sessions

### ⚙️ Enhanced Settings
- **DTR/RTS control** - Moved from ribbon to Settings tab for cleaner UI
- **Background color picker** - Customize the entire app's color scheme
- **Tooltip toggle** - Enable/disable tooltips application-wide
- **Max output lines** - Configure buffer size to prevent memory issues
- **Settings backup** - Optional backup when resetting to defaults
- **Color settings** - Customize accent, hover, font, and background colors

### 📖 About Tab
- **New About tab** - Replaces Virtual Serial tab (removed)
- **Version information** - Displays current version number
- **GitHub link** - Direct link to project repository
- **Application description** - Quick overview of features

### 🎮 User Experience
- **Enhanced tooltips** - Comprehensive tooltips throughout the application
- **Hex display mode** - Toggle between text and hex display for serial data
- **Timestamp display** - Optional timestamps on received data
- **Reveal hidden characters** - Option to visualize whitespace and control characters
- **Smart command input** - Double-enter on empty input repeats last command
- **Send blank entries** - Send button can send newline when input is empty

### 🔧 Technical Improvements
- **Cross-platform compatibility** - Verified on Windows 10 and Debian 13
- **Type hints** - Improved code quality with comprehensive type annotations
- **Error handling** - Better error messages and recovery mechanisms
- **YAML safety** - Protected against special characters breaking configuration files
- **Memory management** - Configurable output line limits prevent unbounded growth

## Upgrade Notes

- **No breaking changes** - All settings and command files from v2.1.0 are fully compatible
- **Automatic migration** - Old 'buttons' format automatically converted to 'quick_buttons'
- **Settings preservation** - User preferences maintained during upgrade
- **Config location unchanged** - All configuration files remain in the same directory

## Known Issues

- None reported at this time

## System Requirements

- **Python 3.8+**
- **PyQt5**
- **pyserial**
- **PyYAML**

## Tested Platforms

- ✅ Windows 10
- ✅ Debian 13
- 🔄 Should work on macOS and other Linux distributions

---

**Full Changelog:** [View on GitHub](https://github.com/DJA-prog/Serial-Gui/compare/v2.1.0...v2.2.0)
