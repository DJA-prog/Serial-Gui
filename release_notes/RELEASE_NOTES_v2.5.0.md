# Serial Communication Monitor v2.5.0 Release Notes

**Release Date:** February 6, 2026  
**Updated:** February 8, 2026

## What's New in v2.5.0

### 🎨 Collapsible Left Panel with Animation

#### Slide-In/Slide-Out Panel Toggle
- **Space optimization** - Hide the left panel to maximize output display area
- **Smooth animation** - 300ms slide animation with easing curve for professional look
- **Dynamic resizing** - Output display automatically adjusts as panel slides
- **Visual feedback** - Button text changes to show current state:
  - **"◀ Hide Panel"** when panel is visible
  - **"▶ Show Panel"** when panel is hidden
- **Default state** - Panel starts visible when app launches
- **Easy access** - Toggle button conveniently located in bottom button row
- **Preserves functionality** - All panel features remain accessible when shown
- **Responsive layout** - Content smoothly reflows as panel width changes

#### Use Cases
- **Focus mode** - Hide panel when monitoring output exclusively
- **Screen space** - Maximize output area on smaller displays
- **Presentation mode** - Clean interface when demonstrating or sharing screen
- **Flexible workflow** - Toggle panel visibility as needed during use

### �️ Debug and Crash Reporting System (NEW)

#### Comprehensive Debugging Infrastructure
- **Automatic crash detection** - Captures unhandled exceptions with full context
- **GitHub-ready reports** - Crash reports formatted as Markdown for easy issue reporting
- **Auto-detection** - Debug mode automatically enabled for debug builds (version ending with 'd')
- **Manual override** - Can be manually enabled/disabled via `DEBUG_ENABLED` variable
- **Zero overhead in release** - Minimal performance impact when disabled

#### Crash Report Features
- **Detailed exception information** - Type, message, and full stack trace
- **System information** - OS, architecture, Python version, Qt/PyQt versions
- **Package inventory** - Automatically lists installed package versions
- **Thread context** - Current thread and active thread count
- **Environment details** - Relevant environment variables for troubleshooting
- **Auto-save** - Reports automatically saved to logs directory
- **Interactive dialog** - Copy, save, or report directly to GitHub

#### Debug Logging Capabilities
- **Context managers** - Wrap critical operations for automatic entry/exit logging
- **Function decorators** - Add debug logging to any function with a single line
- **Method decorators** - Special decorator for class methods with instance info
- **Log levels** - DEBUG, INFO, WARNING, ERROR with timestamps and thread names
- **Strategic instrumentation** - Key operations already instrumented:
  - Serial port connection/disconnection
  - Command transmission
  - Settings load/save
  - Serial reader thread lifecycle
  - Macro editor operations
  - Commands editor operations

#### Developer Benefits
- **Faster debugging** - Detailed logs show exactly what's happening
- **Better error reports** - Users can provide comprehensive crash information
- **Production-safe** - Debug features cleanly disabled in release builds
- **Easy to extend** - Simple APIs for adding debug logging to new code

#### User Benefits
- **Better support** - Crash reports include all needed troubleshooting info
- **One-click reporting** - Copy crash info and open GitHub issues directly
- **Transparent operation** - See exactly what the app is doing in debug mode
- **Confidence** - Know that crashes are captured and can be reported

#### Files Included
- **DebugHandler.py** - Core debug and crash reporting system
- **CrashReportDialog.py** - GUI for viewing and sharing crash reports
- **Notes/DEBUG_USAGE.md** - Comprehensive guide for users and developers
- **Notes/DEBUG_QUICKREF.md** - Quick reference for common debug tasks
- **Notes/DEBUG_BUILD_GUIDE.md** - Guide for building debug vs release versions

### �🐛 Bug Fixes and Stability Improvements

#### Line Filter Fixes
- **Fixed blank line printing** - Custom line filter no longer prints empty lines when filtering lines
- **Proper empty line handling** - Empty lines now display correctly when filter is disabled
- **Improved filter logic** - Trailing empty strings from data splits properly removed only when filtering is active
- **Consistent behavior** - Filter settings now work as expected in all scenarios

#### Windows Compatibility Improvements
- **Signal blocking during initialization** - Prevents combo box signals from firing during widget setup
- **RuntimeError protection** - All widget access now handles Qt C++ object deletion gracefully
- **Enhanced OutputBlock stability** - Fixed crashes on Windows 11 and updated Windows 10 systems
- **Comprehensive error handling** - Added RuntimeError catching for Qt widget operations
- **Initialization safety** - Combo boxes now block signals until fully initialized
- **Cross-platform reliability** - Works consistently across different Windows versions and PyQt5 builds

#### OutputBlock Crash Prevention
- **Signal connection safety** - Verifies widgets exist before connecting signals
- **Immediate visibility updates** - Sets command input visibility directly during initialization
- **Protected serialization** - All widget access in `to_dict()` wrapped in RuntimeError handlers
- **Graceful degradation** - Returns valid fallback data if widgets are deleted
- **Prevents cascade failures** - Stops crashes from propagating through application

### 🔧 Technical Improvements

#### UI Architecture Enhancements
- **Container-based panel** - Left panel wrapped in QWidget container for animation support
- **Property animations** - Uses QPropertyAnimation for smooth width transitions
- **Dual animation** - Animates both minimum and maximum width for consistent resizing
- **InOutQuad easing** - Professional animation curve for natural motion
- **State tracking** - Internal flag tracks panel visibility for reliable toggling

#### Error Recovery
- **Widget lifecycle handling** - Properly handles Qt widget deletion scenarios
- **Signal handler protection** - All handlers check initialization state before executing
- **Debug logging** - Error messages logged to console for troubleshooting
- **Fault tolerance** - Application continues operating despite widget errors

## Technical Details

### New Files
- **DebugHandler.py** - Comprehensive debug and crash reporting system with exception handler
- **CrashReportDialog.py** - Interactive dialog for viewing, copying, and reporting crashes
- **Notes/DEBUG_USAGE.md** - Complete debug system usage guide (290 lines)
- **Notes/DEBUG_QUICKREF.md** - Quick reference for common debug patterns (178 lines)
- **Notes/DEBUG_BUILD_GUIDE.md** - Guide for building debug vs release executables (110 lines)
- **Notes/MACROS.md** - Macro system documentation (moved from root)
- **Notes/THEMES.md** - Theme customization guide (moved from root)

### Modified Files
- **App.py** - Added debug handler integration, collapsible panel, animation support, filter fixes, error handling, and version bump to 2.5.0
- **MacroEditor.py** - Enhanced error handling for OutputBlock with signal blocking, RuntimeError protection, and debug logging
- **CommandsEditor.py** - Added comprehensive debug logging and error handling for all operations

### New Imports in App.py
- **traceback** - For capturing detailed exception information in debug mode
- **QPropertyAnimation** - Enables smooth width animations for panel toggle
- **QEasingCurve** - Provides animation easing for professional transitions
- **DebugHandler, set_debug_handler, get_debug_handler** - Debug system integration
- **CrashReportDialog** - Crash report display and management

### New Methods in App.py
- `toggle_left_panel()` - Handles panel visibility toggle with animated transitions

### Enhanced Methods in App.py
- `__init__()` - Added debug handler initialization and exception handler installation
- `create_left_panel()` - Updated to use container widget for animation support
- `handle_serial_data()` - Fixed filtering logic to preserve empty lines when appropriate
- `connect_serial()` - Wrapped in debug context manager with comprehensive logging
- `disconnect_serial()` - Added debug context and error logging
- `send_command()` - Added debug context wrapper and command logging
- `load_settings()` - Wrapped in debug context for error tracking
- `save_settings()` - Added debug logging and error handling

### New Methods in DebugHandler.py
- `install_exception_handler()` - Installs global exception handler
- `log()` - Simple logging with timestamps and thread info
- `capture_context()` - Context manager for wrapping critical operations
- `debug_function()` - Decorator for adding debug logging to functions
- `debug_method()` - Decorator for adding debug logging to methods
- `_generate_crash_report()` - Creates GitHub-ready Markdown crash reports
- `_save_crash_log()` - Saves crash reports to disk

### New Methods in CrashReportDialog.py
- `copy_to_clipboard()` - Copies crash report to system clipboard
- `save_to_file()` - Saves crash report to user-selected file
- `open_github_issues()` - Opens GitHub issues page in browser

### Enhanced Methods in MacroEditor.py
- `OutputBlock.__init__()` - Added signal blocking and immediate visibility updates
- `OutputBlock.setup_block_content()` - Enhanced signal connection with RuntimeError protection
- `OutputBlock.on_success_action_changed()` - Added RuntimeError handling for widget access
- `OutputBlock.on_fail_action_changed()` - Added RuntimeError handling for widget access
- `OutputBlock.to_dict()` - Comprehensive RuntimeError protection for all widget access
- `MacroCanvas.add_block()` - Added debug logging and comprehensive error handling
- `MacroCanvas.remove_block()` - Added debug logging for block removal
- `MacroEditor.load_macro()` - Added debug logging for macro loading and per-step error handling
- `MacroEditor.save_macro()` - Added debug context and error type handling (YAML, IOError)

### Enhanced Methods in CommandsEditor.py
- `__init__()` - Added debug logging and comprehensive error handling
- `add_no_input_command()` - Added debug logging and error handling
- `edit_no_input_command()` - Added debug logging and error handling
- `remove_no_input_command()` - Added debug logging and error handling
- `add_input_required_command()` - Added debug logging and error handling
- `edit_input_required_command()` - Added debug logging and error handling
- `remove_input_required_command()` - Added debug logging and error handling
- `save_file()` - Enhanced with specific error type handling (YAML, IOError) and debug logging

## Upgrade Notes

- **No breaking changes** - All v2.4.0 settings and configurations fully compatible
- **Seamless upgrade** - Panel visibility state not persisted, always starts visible
- **Backward compatible** - All existing features continue to work unchanged
- **Windows users** - Significant stability improvements for macro editor on Windows 11 and updated Windows 10 systems
- **Filter behavior** - Line filters now work correctly; may notice improved filtering behavior
- **Debug builds** - Debug mode automatically enabled for versions ending with 'd' (e.g., 2.5.0d)
- **Release builds** - Debug mode disabled by default for optimal performance
- **Documentation reorganized** - User guides moved to Notes/ directory for better organization
- **Crash reporting** - Automatic crash detection and reporting now available (opt-in via debug builds)
- **Performance** - Debug mode adds ~5-10% overhead; release mode has <1% overhead from crash handler

## Debug Mode

### Automatic Detection
- **Debug builds** (version ending with 'd', e.g., "2.5.0d"): Debug mode is **ON**
- **Release builds** (normal version, e.g., "2.5.0"): Debug mode is **OFF**

### Building with Debug Mode

**Linux:**
```bash
./build_linux.sh debug    # Creates Serial_monitor_2.5.0d_x86-64
./build_linux.sh release  # Creates Serial_monitor_2.5.0_x86-64
```

**Windows:**
```powershell
.\build_windows.ps1 debug    # Creates Serial_monitor_2.5.0d_x86-64.exe
.\build_windows.ps1 release  # Creates Serial_monitor_2.5.0_x86-64.exe
```

### What Debug Mode Provides
- **Console output** - Real-time logging visible in terminal/console window
- **Crash reports** - Automatic generation and saving of detailed crash information
- **GitHub integration** - One-click copy/save/report functionality
- **Enhanced logging** - Function entry/exit, arguments, and return values
- **Error context** - Full stack traces with system and package information

### Manual Override
Edit `DEBUG_ENABLED` in [App.py](../App.py):
```python
DEBUG_ENABLED = True   # Force debug ON
DEBUG_ENABLED = False  # Force debug OFF
```

### Crash Report Location
- **Linux:** `~/.config/SerialCommunicationMonitor/logs/`
- **Windows:** `%APPDATA%\SerialCommunicationMonitor\logs\`
- **macOS:** `~/Library/Application Support/SerialCommunicationMonitor/logs/`

## Documentation

All documentation has been reorganized into the `Notes/` directory:

- **[DEBUG_USAGE.md](../Notes/DEBUG_USAGE.md)** - Comprehensive debug system guide (290 lines)
- **[DEBUG_QUICKREF.md](../Notes/DEBUG_QUICKREF.md)** - Quick reference for debug patterns (178 lines)
- **[DEBUG_BUILD_GUIDE.md](../Notes/DEBUG_BUILD_GUIDE.md)** - Build system configuration (110 lines)
- **[MACROS.md](../Notes/MACROS.md)** - Macro system documentation (180 lines)
- **[THEMES.md](../Notes/THEMES.md)** - Color theme customization guide (236 lines)

## Known Issues

- None reported at this time

## System Requirements

- **Python 3.8+**
- **PyQt5**
- **pyserial**
- **PyYAML**

## Tested Platforms

- ✅ Debian 13
- ✅ Windows 10 (Version 22H2)
- ✅ Windows 11 (all updates)
- 🔄 Should work on macOS and other Linux distributions

---

**Full Changelog:** [View on GitHub](https://github.com/DJA-prog/Serial-Gui/compare/v2.4.0...v2.5.0)
