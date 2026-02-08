# Debug System Quick Reference

## Toggle Debug Mode

**Location:** [App.py](App.py) (lines 22-25)

```python
# Debug mode configuration
DEBUG_ENABLED = __version__.endswith('d')  # Auto-detect debug builds
IS_DEBUG = DEBUG_ENABLED  # Alias for compatibility
```

**Quick Toggle:**
- `DEBUG_ENABLED = True` → Force debug ON
- `DEBUG_ENABLED = False` → Force debug OFF
- `DEBUG_ENABLED = __version__.endswith('d')` → Auto-detect (default)

## Build with Debug Mode

```bash
# Linux
./build_linux.sh debug    # Creates Serial_monitor_2.5.0d_x86-64
./build_linux.sh release  # Creates Serial_monitor_2.5.0_x86-64

# Windows
.\build_windows.ps1 debug    # Creates Serial_monitor_2.5.0d_x86-64.exe
.\build_windows.ps1 release  # Creates Serial_monitor_2.5.0_x86-64.exe
```

## Common Debug Patterns

### 1. Simple Logging
```python
if DEBUG_ENABLED:
    self.debug_handler.log("Operation started", "INFO")
```

### 2. Operation Context (Recommended)
```python
with self.debug_handler.capture_context("Port Opening"):
    self.serial_port.open()
    # Automatically logs entry, exit, and captures exceptions
```

### 3. Function Decorator
```python
@self.debug_handler.debug_function
def process_data(self, data):
    # Auto-logs: entry with args, exit with result, exceptions
    return processed_data
```

### 4. Method Decorator
```python
@self.debug_handler.debug_method
def handle_signal(self, value):
    # Same as debug_function but includes class name
    pass
```

## Log Levels

| Level | Use For | Example |
|-------|---------|---------|
| `DEBUG` | Detailed tracing | `"Entering function with args: {args}"` |
| `INFO` | General information | `"Connection established"` |
| `WARNING` | Potential issues | `"Port not responding, retrying..."` |
| `ERROR` | Error conditions | `"Failed to save file: {error}"` |

## Where Crash Reports Go

**Linux:** `~/.config/SerialCommunicationMonitor/logs/crash_report_*.md`  
**Windows:** `%APPDATA%\SerialCommunicationMonitor\logs\crash_report_*.md`

## Testing Debug System

```bash
cd "/opt/Serial Gui"
python3 test_debug_handler.py
```

## Files Overview

| File | Purpose |
|------|---------|
| [DebugHandler.py](DebugHandler.py) | Core debug & crash reporting system |
| [App.py](App.py) | Integration (DEBUG_ENABLED variable) |
| [DEBUG_USAGE.md](DEBUG_USAGE.md) | Comprehensive user guide |
| [DEBUG_BUILD_GUIDE.md](DEBUG_BUILD_GUIDE.md) | Build system guide |
| [test_debug_handler.py](test_debug_handler.py) | Test suite |

## Most Important Methods to Debug

Already instrumented with debug logging:
- ✅ `connect_serial()` - Serial connection
- ✅ `disconnect_serial()` - Serial disconnection  
- ✅ `send_command()` - Command transmission
- ✅ `load_settings()` - Settings loading
- ✅ `save_settings()` - Settings saving
- ✅ `SerialReaderThread.run()` - Serial reading thread

## Adding Debug to Your Code

**Step 1:** Check if debug is enabled
```python
if DEBUG_ENABLED:
    # Your debug code
```

**Step 2:** Use appropriate pattern
```python
# For critical operations - use context manager
with self.debug_handler.capture_context("MyOperation"):
    do_something()

# For status updates - use logging
if DEBUG_ENABLED:
    self.debug_handler.log(f"Status: {status}", "INFO")
```

## Crash Report Format

Generated reports are GitHub-ready Markdown including:
- ✅ Exception type and message
- ✅ Full stack trace with code context
- ✅ System information (OS, Python, Qt versions)
- ✅ Installed package versions
- ✅ Thread information
- ✅ Environment variables
- ✅ Template for user to fill "Steps to Reproduce"

## Example Console Output

```
=============================================================
Starting Serial Communication Monitor v2.5.0d
Debug Mode: ENABLED
Crash reports will be saved to:
  /home/user/.config/SerialCommunicationMonitor/logs
=============================================================

[14:25:33.123] [INFO] [MainThread] Starting Serial Communication Monitor v2.5.0d
[14:25:33.124] [INFO] [MainThread] Debug mode is ENABLED
[14:25:35.456] [INFO] [MainThread] Attempting to connect to /dev/ttyUSB0
[14:25:35.789] [INFO] [MainThread] Successfully connected to /dev/ttyUSB0
[14:25:35.790] [DEBUG] [SerialReaderThread] SerialReaderThread started
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No debug output | Set `DEBUG_ENABLED = True` in App.py |
| Crash reports not saved | Check logs directory permissions |
| Too much output | Use release build or set `DEBUG_ENABLED = False` |
| Missing logs directory | Will be auto-created on first crash |

## Performance

- **Debug ON:** ~5-10% overhead from logging
- **Debug OFF:** <1% overhead (only crash handler active)
- 💡 Use debug builds for development, release for production

## Quick Commands

```bash
# Check debug status
grep "DEBUG_ENABLED" App.py

# View recent crashes
ls -lt ~/.config/SerialCommunicationMonitor/logs/

# Test debug system
python3 test_debug_handler.py

# Build debug version
./build_linux.sh debug
```
