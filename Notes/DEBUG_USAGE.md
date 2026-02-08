# Debug System Usage Guide

## Overview

The Serial Communication Monitor now includes a comprehensive debugging and crash reporting system that automatically captures exceptions, logs important operations, and generates GitHub-ready issue reports.

## Enabling/Disabling Debug Mode

Debug mode is controlled by a variable at the top of `App.py`:

```python
# Debug mode configuration
DEBUG_ENABLED = __version__.endswith('d')  # Auto-detect debug builds
```

### Automatic Detection
- **Debug builds** (version ending with 'd', e.g., "2.5.0d"): Debug mode is **ON**
- **Release builds** (normal version, e.g., "2.5.0"): Debug mode is **OFF**

### Manual Control
You can manually override the debug mode by editing `App.py`:

```python
# Force debug mode ON
DEBUG_ENABLED = True

# Force debug mode OFF  
DEBUG_ENABLED = False
```

## What Debug Mode Does

When `DEBUG_ENABLED = True`:

1. **Console Output Visible** (in debug builds)
   - Shows real-time debug messages
   - Logs function entry/exit
   - Reports errors with context

2. **Crash Reports Generated**
   - Saved to: `~/.config/SerialCommunicationMonitor/logs/` (Linux)
   - Saved to: `%APPDATA%\SerialCommunicationMonitor\logs\` (Windows)
   - Format: Markdown, ready to paste into GitHub issues

3. **Window Title Shows [DEBUG]**
   - Easy identification of debug mode

4. **Enhanced Error Context**
   - Full stack traces
   - System information
   - Thread information
   - Environment details

## Crash Reports

When an unhandled exception occurs, the debug system automatically:

### 1. Generates a Comprehensive Report

Example crash report structure:

```markdown
# Crash Report - Serial Communication Monitor

**Timestamp:** 2026-02-07 14:25:33
**Version:** 2.5.0d

## Exception Details

**Type:** `SerialException`
**Message:** Could not open port /dev/ttyUSB0

## Stack Trace

[Full Python traceback]

## System Information

- **OS:** Linux 6.1.0
- **Architecture:** x86_64
- **Python Version:** 3.11.2
- **Qt Version:** 5.15.9
- **PyQt Version:** 5.15.9

## Additional Context

- **Thread:** MainThread (ID: 139876543210)
- **Active Threads:** 3

### Installed Packages

- `pyserial`: 3.5
- `PyQt5`: 5.15.9
- `pyyaml`: 6.0

## Steps to Reproduce

1. 
2. 
3. 

## Expected Behavior

_Describe what should happen_

## Actual Behavior

_Describe what actually happened_
```

### 2. Saves to Log File

- Filename format: `crash_report_YYYYMMDD_HHMMSS_#.md`
- Location displayed in console output
- Can be directly attached to GitHub issues

### 3. Prints to Console

- Full report printed to console (visible in debug builds)
- Shows exact location of the saved report file

## Debug Logging Examples

The system logs critical operations. Here's what you'll see:

```
[14:25:33.123] [INFO] [MainThread] Starting Serial Communication Monitor v2.5.0d
[14:25:33.124] [INFO] [MainThread] Debug mode is ENABLED
[14:25:35.456] [INFO] [MainThread] Attempting to connect to /dev/ttyUSB0 at 115200 baud
[14:25:35.457] [DEBUG] [MainThread] Entering context: Serial Connection to /dev/ttyUSB0
[14:25:35.789] [INFO] [MainThread] Successfully connected to /dev/ttyUSB0
[14:25:35.790] [DEBUG] [SerialReaderThread] SerialReaderThread started
[14:25:40.123] [DEBUG] [MainThread] Sending command: 'AT'
[14:25:40.124] [DEBUG] [MainThread] Entering context: Send Command
```

## Adding Debug Logging to Custom Code

### Method 1: Using the Debug Handler Directly

```python
if DEBUG_ENABLED:
    self.debug_handler.log("My custom message", "INFO")
```

### Method 2: Using Context Managers

```python
with self.debug_handler.capture_context("MyOperation"):
    # Your code here
    # Any exceptions will be captured with context
    do_something()
```

### Method 3: Function Decorators (for new functions)

```python
@self.debug_handler.debug_function
def my_function(arg1, arg2):
    # Function will automatically log:
    # - Entry with arguments
    # - Exit with return value
    # - Any exceptions with context
    return result
```

### Method 4: Method Decorators (for class methods)

```python
@self.debug_handler.debug_method
def my_method(self, arg):
    # Same as debug_function but includes class name
    pass
```

## Debug Log Levels

Available log levels (in order of severity):

- `DEBUG`: Detailed debug information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error conditions
- `CRITICAL`: Critical errors

## Building with Debug Mode

### Windows
```powershell
# Release build (debug OFF)
.\build_windows.ps1 release

# Debug build (debug ON automatically)
.\build_windows.ps1 debug
```

### Linux
```bash
# Release build (debug OFF)
./build_linux.sh release

# Debug build (debug ON automatically)
./build_linux.sh debug
```

Debug builds:
- Have version suffix 'd' (e.g., 2.5.0d)
- Show console window for real-time logging
- Include PyInstaller debug output
- Automatically enable `DEBUG_ENABLED`

## Reporting Bugs

### If You're a User

1. **Build in debug mode** or **set `DEBUG_ENABLED = True`** in `App.py`
2. **Reproduce the crash**
3. **Find the crash report** in the logs directory
4. **Copy the entire crash report** to your clipboard
5. **Create a GitHub issue** and paste the report
6. **Fill in the "Steps to Reproduce" section**

### If You're a Developer

1. **Look in the logs directory** for recent crash reports
2. **Check the stack trace** for the error location
3. **Review debug logs** leading up to the crash
4. **Look at system information** for platform-specific issues

## Disabling Debug Mode for Release

When preparing a release build:

1. **Use the build script** with `release` parameter:
   ```bash
   ./build_linux.sh release
   # or
   .\build_windows.ps1 release
   ```

2. The version won't have 'd' suffix, so `DEBUG_ENABLED` will be `False`

3. No console window, no debug logging (except crashes still generate reports)

## Performance Impact

- **Debug ON**: Minor performance impact from logging
- **Debug OFF**: Minimal impact (only crash handling active)
- **Recommendation**: Use debug builds during development, release builds for distribution

## Troubleshooting

### "I don't see debug output"
- Check that `DEBUG_ENABLED = True` in App.py
- Run from terminal/console to see output
- Debug builds show console window automatically

### "Crash reports not generated"
- Check that logs directory exists and is writable
- On Linux: `~/.config/SerialCommunicationMonitor/logs/`
- On Windows: `%APPDATA%\SerialCommunicationMonitor\logs\`

### "Too much debug output"
- Use release build for normal use
- Or set `DEBUG_ENABLED = False` in App.py

## Example Debug Session

```
==========================================================
Starting Serial Communication Monitor v2.5.0d
Debug Mode: ENABLED
Crash reports will be saved to:
  /home/user/.config/SerialCommunicationMonitor/logs
==========================================================

[14:25:33.123] [INFO] [MainThread] Starting Serial Communication Monitor v2.5.0d
[14:25:33.124] [INFO] [MainThread] Debug mode is ENABLED
[14:25:35.456] [DEBUG] [MainThread] Loading settings from file
[14:25:35.457] [DEBUG] [MainThread] Entering context: Load Settings
[14:25:35.458] [DEBUG] [MainThread] Exiting context: Load Settings
...
```

## Files Involved

- **DebugHandler.py**: Core debugging system
- **App.py**: Integration and DEBUG_ENABLED variable
- **Crash logs**: `~/.config/SerialCommunicationMonitor/logs/*.md`
- **Build scripts**: Control debug vs release builds
