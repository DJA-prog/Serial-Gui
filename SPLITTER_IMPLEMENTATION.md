# Serial Splitter Implementation Documentation

## Overview
This document outlines the comprehensive implementation plan for adding serial port splitting functionality to the Serial Communication Monitor application. The feature will allow the app to share a physical serial port with up to 2 additional virtual serial ports, enabling multiple applications/devices to communicate through the same physical connection.

---

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Application (GUI Thread)            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Serial Port  │  │   Splitter   │  │ Display Buffer  │  │
│  │   Controls   │  │   Tab UI     │  │   Manager UI    │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
    ┌───────────▼─────────┐  ┌─────────▼──────────┐
    │ SerialSplitter      │  │ DisplayBuffer      │
    │ Thread              │  │ Manager Thread     │
    │                     │  │                    │
    │ Priority Queues:    │  │ Batching Queue     │
    │ • Q0 (Virtual 1)    │  │ • Buffer incoming  │
    │ • Q1 (App)          │  │ • Throttle updates │
    │ • Q2 (Virtual 2)    │  │ • Update every     │
    │                     │  │   100ms            │
    │ Routes:             │  └────────────────────┘
    │ Physical→Virtuals   │
    │ Virtuals→Physical   │
    └─────────────────────┘
              │
    ┌─────────▼──────────┐
    │ Physical Serial    │
    │ Port (e.g., ttyUSB0)│
    └────────────────────┘
              │
    ┌─────────┴──────────┐
    │                    │
┌───▼────┐         ┌────▼────┐
│Virtual │         │Virtual  │
│Port 1  │         │Port 2   │
│(socat) │         │(socat)  │
└────────┘         └─────────┘
```

---

## 1. Threading Components

### 1.1 SerialSplitter Thread

**Location**: New file: `/opt/Serial Gui/SerialSplitter.py`

**Purpose**: Manages physical serial connection and routes data to/from virtual ports with priority-based queuing.

**Class Definition**:
```python
class SerialSplitter(threading.Thread):
    """
    Manages serial port splitting with priority-based routing.
    Creates up to 2 virtual serial ports using socat.
    """
```

**Attributes**:
- `physical_port: str` - Path to physical serial port (e.g., "/dev/ttyUSB0")
- `baud_rate: int` - Baud rate for serial connection
- `serial_settings: dict` - Contains data_bits, parity, stop_bits, flow_control
- `virtual_port_1: Optional[str]` - Path to first virtual port
- `virtual_port_2: Optional[str]` - Path to second virtual port
- `enabled: bool` - Whether splitter is active
- `running: bool` - Thread control flag
- `priority_queues: Dict[int, queue.PriorityQueue]` - Priority queues for outgoing data
  - Key: priority level (0, 1, 2)
  - Value: PriorityQueue containing (timestamp, data) tuples
- `broadcast_queue: queue.Queue` - Queue for incoming data to be broadcast
- `physical_serial: Optional[serial.Serial]` - Physical serial connection
- `virtual_serial_1: Optional[serial.Serial]` - First virtual port connection
- `virtual_serial_2: Optional[serial.Serial]` - Second virtual port connection
- `socat_process_1: Optional[subprocess.Popen]` - socat process for virtual port 1
- `socat_process_2: Optional[subprocess.Popen]` - socat process for virtual port 2
- `statistics: dict` - Data flow statistics
  - `bytes_in`: int
  - `bytes_out`: int
  - `bytes_virtual_1_in`: int
  - `bytes_virtual_1_out`: int
  - `bytes_virtual_2_in`: int
  - `bytes_virtual_2_out`: int
  - `start_time`: float

**Methods**:

1. `__init__(physical_port, baud_rate, serial_settings, priority_config)`
   - Initialize all attributes
   - Create priority queues for each priority level
   - Set up statistics dictionary

2. `run()` - Main thread loop
   - While running:
     - Read from physical serial → broadcast to app and virtual ports
     - Read from virtual ports → queue with their priority
     - Read from app queue → queue with app priority
     - Process priority queues → write to physical serial
     - Sleep briefly to prevent CPU spinning

3. `create_virtual_ports()` → bool
   - Check if socat is installed
   - Create 2 virtual port pairs using socat:
     ```bash
     socat -d -d pty,raw,echo=0,link=/tmp/serial_virtual_1 pty,raw,echo=0,link=/tmp/serial_virtual_1_slave
     socat -d -d pty,raw,echo=0,link=/tmp/serial_virtual_2 pty,raw,echo=0,link=/tmp/serial_virtual_2_slave
     ```
   - Store socat process handles
   - Open serial connections to the slave side
   - Return success/failure

4. `destroy_virtual_ports()`
   - Close virtual serial connections
   - Terminate socat processes
   - Clean up symlinks

5. `connect_physical()` → bool
   - Open physical serial port with settings
   - Apply DTR/RTS settings
   - Return success/failure

6. `disconnect_physical()`
   - Close physical serial connection

7. `broadcast_data(data: bytes)`
   - Put data in broadcast_queue
   - Increment statistics

8. `send_from_app(data: bytes, priority: int)`
   - Add to appropriate priority queue
   - Increment statistics

9. `send_from_virtual(port_num: int, data: bytes, priority: int)`
   - Add to appropriate priority queue
   - Increment statistics

10. `process_priority_queues()` → Optional[bytes]
    - Check queues in priority order (0, 1, 2)
    - Return next data to write to physical port
    - Implement fairness algorithm to prevent starvation

11. `get_statistics()` → dict
    - Return copy of statistics dictionary
    - Calculate data rates (bytes/sec)

12. `stop()`
    - Set running flag to False
    - Clean up all connections
    - Join thread

---

### 1.2 DisplayBufferManager Thread

**Location**: New file: `/opt/Serial Gui/DisplayBufferManager.py`

**Purpose**: Buffers incoming display data and throttles UI updates to prevent freezing during high-speed data streams.

**Class Definition**:
```python
class DisplayBufferManager(threading.Thread):
    """
    Manages buffering and throttled display updates for serial data.
    Prevents UI freezing during high-speed data bursts.
    """
```

**Attributes**:
- `input_queue: queue.Queue` - Receives data from serial/splitter
- `output_callback: Callable[[str], None]` - Callback to GUI update method
- `buffer: List[str]` - Temporary buffer for batching lines
- `running: bool` - Thread control flag
- `update_interval: float` - Seconds between GUI updates (default: 0.1)
- `max_buffer_size: int` - Max lines to buffer before forcing update
- `last_update_time: float` - Timestamp of last GUI update
- `statistics: dict` - Buffer statistics
  - `lines_buffered`: int
  - `lines_displayed`: int
  - `updates_throttled`: int

**Methods**:

1. `__init__(output_callback, update_interval=0.1, max_buffer_size=100)`
   - Initialize queue and buffer
   - Store callback reference

2. `run()` - Main thread loop
   - While running:
     - Get items from input_queue (non-blocking)
     - Add to buffer
     - Check if should update (time elapsed or buffer full)
     - If yes: call output_callback with batched data
     - Sleep briefly

3. `add_line(line: str)`
   - Put line into input_queue
   - Thread-safe

4. `should_update()` → bool
   - Check if update_interval elapsed
   - Check if buffer exceeds max_buffer_size
   - Return True if either condition met

5. `flush_buffer()`
   - Join all buffered lines
   - Call output_callback once with combined text
   - Clear buffer
   - Update statistics

6. `get_statistics()` → dict
   - Return copy of statistics

7. `stop()`
   - Set running flag to False
   - Flush any remaining buffer
   - Join thread

---

## 2. UI Components

### 2.1 Splitter Tab

**Location**: Add to `MainWindow.create_left_panel()` in `App.py`

**Layout Structure**:
```
┌─────────────────────────────────────────┐
│ Splitter Control                        │
├─────────────────────────────────────────┤
│ [✓] Enable Serial Splitter              │
│                                          │
│ Priority Configuration:                  │
│ ┌──────────────────────────────────┐   │
│ │ Virtual Port 1:    [0▼]          │   │
│ │ This App:          [1▼]          │   │
│ │ Virtual Port 2:    [2▼]          │   │
│ └──────────────────────────────────┘   │
│                                          │
│ Virtual Ports:                           │
│ ┌──────────────────────────────────┐   │
│ │ Port 1: /tmp/serial_virtual_1    │   │
│ │ Status: ● Connected              │   │
│ │ [Copy Path] [Test Connection]    │   │
│ └──────────────────────────────────┘   │
│ ┌──────────────────────────────────┐   │
│ │ Port 2: /tmp/serial_virtual_2    │   │
│ │ Status: ○ Disconnected           │   │
│ │ [Copy Path] [Test Connection]    │   │
│ └──────────────────────────────────┘   │
│                                          │
│ Data Flow Statistics:                    │
│ ┌──────────────────────────────────┐   │
│ │ Physical Port:                    │   │
│ │   ↓ In:  1.2 MB (24.5 KB/s)      │   │
│ │   ↑ Out: 345 KB (6.9 KB/s)       │   │
│ │                                   │   │
│ │ Virtual Port 1:                   │   │
│ │   ↓ In:  890 KB (17.8 KB/s)      │   │
│ │   ↑ Out: 125 KB (2.5 KB/s)       │   │
│ │                                   │   │
│ │ Virtual Port 2:                   │   │
│ │   ↓ In:  234 KB (4.7 KB/s)       │   │
│ │   ↑ Out: 89 KB (1.8 KB/s)        │   │
│ │                                   │   │
│ │ Queue Sizes:                      │   │
│ │   Priority 0: 0 items             │   │
│ │   Priority 1: 2 items             │   │
│ │   Priority 2: 0 items             │   │
│ └──────────────────────────────────┘   │
│                                          │
│ Buffer Statistics:                       │
│ ┌──────────────────────────────────┐   │
│ │ Lines Buffered: 1,234             │   │
│ │ Lines Displayed: 1,150            │   │
│ │ Updates Throttled: 45             │   │
│ │ Buffer Usage: 23/100 lines        │   │
│ └──────────────────────────────────┘   │
│                                          │
│ [Install socat] [Refresh Status]        │
└─────────────────────────────────────────┘
```

**Implementation Method**: `def tab_splitter(self) -> None:`

**Widgets to Create**:
1. `enable_splitter_checkbox: QCheckBox` - Enable/disable splitter
2. `priority_combos: Dict[str, QComboBox]` - Priority dropdowns (0-2)
   - "virtual_1"
   - "app"
   - "virtual_2"
3. `virtual_port_labels: Dict[int, QLabel]` - Display virtual port paths
4. `virtual_status_labels: Dict[int, QLabel]` - Connection status indicators
5. `copy_path_buttons: Dict[int, QPushButton]` - Copy path to clipboard
6. `test_connection_buttons: Dict[int, QPushButton]` - Test virtual port connectivity
7. `statistics_labels: Dict[str, QLabel]` - All statistics displays
8. `install_socat_button: QPushButton` - Install socat if missing
9. `refresh_button: QPushButton` - Refresh statistics

**Statistics Update Timer**:
- Create `QTimer` that fires every 1 second
- Calls `update_splitter_statistics()` method
- Only active when splitter tab is visible

---

### 2.2 Settings Integration

**Location**: `tab_settings()` in `App.py`

**New Settings to Add** (in settings table):
- Row 14: **Splitter Enabled** (bool)
- Row 15: **Splitter Virtual 1 Priority** (int: 0-2)
- Row 16: **Splitter App Priority** (int: 0-2)
- Row 17: **Splitter Virtual 2 Priority** (int: 0-2)
- Row 18: **Display Buffer Interval** (int: milliseconds)
- Row 19: **Display Buffer Max Size** (int: lines)

**Settings Dictionary Extension**:
```python
'general': {
    # ... existing settings ...
    'splitter_enabled': False,
    'splitter_virtual_1_priority': 0,
    'splitter_app_priority': 1,
    'splitter_virtual_2_priority': 2,
    'display_buffer_interval': 100,  # milliseconds
    'display_buffer_max_size': 100,  # lines
}
```

---

## 3. Integration Points

### 3.1 Serial Connection Logic

**Location**: `connect_serial()` method in `App.py` (around line 1850)

**Current Flow**:
```python
def connect_serial(self):
    # Create serial.Serial object
    # Open connection
    # Start timer for read_serial_data()
```

**Modified Flow**:
```python
def connect_serial(self):
    # Check if splitter is enabled
    if self.settings['general']['splitter_enabled']:
        # Create SerialSplitter thread
        # Create DisplayBufferManager thread
        # Start both threads
        # Connect splitter.broadcast_queue to buffer manager
        # Update UI to show splitter active
    else:
        # Original flow: direct serial connection
        # Create serial.Serial object
        # Open connection
        # Start timer for read_serial_data()
```

**Specific Changes Needed**:

1. Add instance variables to `__init__`:
   ```python
   self.serial_splitter: Optional[SerialSplitter] = None
   self.display_buffer: Optional[DisplayBufferManager] = None
   self.splitter_mode: bool = False
   ```

2. Modify `connect_serial()`:
   ```python
   def connect_serial(self) -> None:
       port = self.port_combo.currentText()
       baud_rate = int(self.baud_rate_combo.currentText())
       
       # Get splitter settings
       splitter_enabled = self.settings['general'].get('splitter_enabled', False)
       
       if splitter_enabled:
           self.connect_with_splitter(port, baud_rate)
       else:
           self.connect_direct(port, baud_rate)
   ```

3. Create new methods:
   - `connect_with_splitter(port, baud_rate)`
   - `connect_direct(port, baud_rate)` (existing logic)
   - `disconnect_with_splitter()`
   - `disconnect_direct()`

---

### 3.2 Data Reading Logic

**Location**: `read_serial_data()` method in `App.py` (around line 1990)

**Current Implementation**:
```python
def read_serial_data(self) -> None:
    if self.serial_port and self.serial_port.is_open:
        while self.serial_port.in_waiting > 0:
            response = self.serial_port.readline().decode('utf-8', errors='replace')
            if response:
                self.print_to_display('> ' + response)
```

**Modified Implementation**:
```python
def read_serial_data(self) -> None:
    if self.splitter_mode:
        # Data comes through DisplayBufferManager
        # This timer may not be needed in splitter mode
        pass
    else:
        # Original direct reading logic
        if self.serial_port and self.serial_port.is_open:
            while self.serial_port.in_waiting > 0:
                response = self.serial_port.readline().decode('utf-8', errors='replace')
                if response:
                    self.print_to_display('> ' + response)
```

---

### 3.3 Data Sending Logic

**Location**: `send_command()` method in `App.py` (around line 1950)

**Current Implementation**:
```python
def send_command(self) -> None:
    command = self.command_input.text().strip()
    if self.serial_port and self.serial_port.is_open:
        # ... encode and send ...
        self.serial_port.write((command + tx_value).encode())
```

**Modified Implementation**:
```python
def send_command(self) -> None:
    command = self.command_input.text().strip()
    
    if self.splitter_mode and self.serial_splitter:
        # Send through splitter with app priority
        app_priority = self.settings['general']['splitter_app_priority']
        data = (command + tx_value).encode()
        self.serial_splitter.send_from_app(data, app_priority)
        self.print_to_display(f"< {command}")
    elif self.serial_port and self.serial_port.is_open:
        # Original direct sending logic
        self.serial_port.write((command + tx_value).encode())
        self.print_to_display(f"< {command}")
```

---

## 4. File Structure Changes

### New Files to Create:

1. **`/opt/Serial Gui/SerialSplitter.py`**
   - SerialSplitter thread class
   - ~400 lines

2. **`/opt/Serial Gui/DisplayBufferManager.py`**
   - DisplayBufferManager thread class
   - ~200 lines

3. **`/opt/Serial Gui/SocatHelper.py`**
   - Utility functions for socat
   - Check installation
   - Install instructions
   - Create/destroy virtual ports
   - ~150 lines

### Modified Files:

1. **`/opt/Serial Gui/App.py`**
   - Add imports for new modules
   - Add `tab_splitter()` method
   - Modify `connect_serial()` and `disconnect_serial()`
   - Modify `send_command()`
   - Modify `read_serial_data()`
   - Add statistics update methods
   - ~300 lines of changes

2. **`/opt/Serial Gui/requirements.txt`**
   - No new Python packages needed
   - But note socat system dependency

---

## 5. Dependencies

### Python Packages (Already Available):
- `threading` - Thread management
- `queue` - Thread-safe queues
- `subprocess` - For socat process management
- `serial` (pyserial) - Already in use

### System Dependencies:

**socat** - Required for creating virtual serial ports

Installation detection and helper:
```python
def check_socat_installed() -> bool:
    try:
        result = subprocess.run(['which', 'socat'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def install_socat_instructions() -> str:
    system = platform.system()
    if system == 'Linux':
        # Detect distro
        if Path('/etc/debian_version').exists():
            return "sudo apt-get install socat"
        elif Path('/etc/redhat-release').exists():
            return "sudo yum install socat"
        elif Path('/etc/arch-release').exists():
            return "sudo pacman -S socat"
    return "Please install socat using your package manager"
```

---

## 6. Configuration & Settings

### Settings File Structure:

**`settings.yaml`** additions:
```yaml
general:
  # ... existing settings ...
  
  # Splitter settings
  splitter_enabled: false
  splitter_virtual_1_priority: 0  # Highest priority
  splitter_app_priority: 1        # Medium priority
  splitter_virtual_2_priority: 2  # Lowest priority
  
  # Buffer settings
  display_buffer_interval: 100    # milliseconds
  display_buffer_max_size: 100    # lines before forced update
  
  # Virtual port paths (auto-generated, saved for reference)
  splitter_virtual_1_path: "/tmp/serial_virtual_1"
  splitter_virtual_2_path: "/tmp/serial_virtual_2"
```

---

## 7. Error Handling

### Critical Error Scenarios:

1. **socat not installed**
   - Detect on splitter enable
   - Show dialog with installation instructions
   - Disable splitter checkbox
   - Log error

2. **Virtual port creation fails**
   - socat process crashes
   - Permission denied on /tmp
   - Ports already in use
   - Action: Show error dialog, disable splitter, cleanup

3. **Physical serial connection fails with splitter enabled**
   - Same as current behavior
   - Additionally cleanup virtual ports
   - Stop threads gracefully

4. **Thread crashes**
   - Implement try-except in thread run() loops
   - Log errors to console/file
   - Emit signal to GUI for notification
   - Attempt graceful shutdown

5. **Priority queue overflow**
   - Set max queue size (e.g., 10000 items)
   - Drop oldest items when full
   - Log warning
   - Show notification in UI

6. **Virtual port disconnection**
   - Detect in thread
   - Update UI status indicator
   - Continue operation (non-fatal)
   - Attempt reconnection after delay

### Error Recovery Strategies:

```python
# In SerialSplitter.run()
try:
    while self.running:
        # ... main loop ...
except Exception as e:
    self.error_callback(f"Splitter error: {e}")
    self.cleanup()
finally:
    self.cleanup()
```

---

## 8. Thread Safety Considerations

### Critical Sections:

1. **Statistics dictionary access**
   - Use threading.Lock
   - Lock when updating/reading stats

2. **Queue operations**
   - queue.Queue is already thread-safe
   - No additional locking needed

3. **GUI updates from threads**
   - Use Qt signals (already thread-safe)
   - Never call GUI methods directly from threads
   - DisplayBufferManager uses callback pattern

4. **Serial port access**
   - Only SerialSplitter thread touches physical port
   - App never directly accesses port in splitter mode
   - No locks needed (single writer)

### Signal/Slot Implementation:

```python
# In App.py
class MainWindow(QMainWindow):
    # Add new signals
    splitter_error_signal = pyqtSignal(str)
    splitter_status_signal = pyqtSignal(dict)
    
    def __init__(self):
        # ... existing code ...
        
        # Connect signals
        self.splitter_error_signal.connect(self.handle_splitter_error)
        self.splitter_status_signal.connect(self.update_splitter_ui)
```

---

## 9. Testing Strategy

### Unit Tests to Create:

1. **SerialSplitter Tests**:
   - Test priority queue ordering
   - Test virtual port creation/destruction
   - Test data routing logic
   - Test statistics tracking
   - Mock serial.Serial for testing

2. **DisplayBufferManager Tests**:
   - Test buffering logic
   - Test throttling timing
   - Test buffer overflow handling
   - Test flush on stop

3. **Integration Tests**:
   - Test full connection flow with splitter
   - Test data flow: physical → virtual → physical
   - Test priority enforcement
   - Test high-speed data handling

### Manual Testing Scenarios:

1. **Basic Functionality**:
   - Enable splitter → create virtual ports
   - Connect physical port → verify all connections
   - Send command from app → appears on physical
   - External device sends to virtual → appears on physical
   - Physical receives data → appears in app and virtual ports

2. **Priority Testing**:
   - Send simultaneous data from all 3 sources
   - Verify priority order on physical port
   - Verify no data loss

3. **High-Speed Data**:
   - Stream data at 921600 baud for 1 minute
   - Verify no app freezing
   - Verify statistics accuracy
   - Verify no dropped data

4. **Error Conditions**:
   - Disconnect virtual port during operation
   - Kill socat process during operation
   - Disconnect physical port
   - Verify graceful degradation

5. **Resource Cleanup**:
   - Enable/disable splitter multiple times
   - Connect/disconnect multiple times
   - Close app with splitter active
   - Verify no orphaned processes or ports

---

## 10. Performance Considerations

### Memory Usage:

- **Priority Queues**: Limit to 10,000 items each
- **Display Buffer**: Limit to 100 lines (configurable)
- **Statistics**: Fixed size dictionary
- **Estimated total**: < 50 MB even under heavy load

### CPU Usage:

- **Thread sleep intervals**:
  - SerialSplitter: 0.001s (1ms) - responsive but not spinning
  - DisplayBufferManager: 0.01s (10ms) - less critical
- **Expected CPU**: < 5% on modern hardware during normal operation
- **High-speed burst**: May spike to 15-20% temporarily

### Latency:

- **Without splitter**: Direct serial communication (~1ms)
- **With splitter**: Additional ~2-5ms due to queue processing
- **Display latency**: Up to 100ms (configurable buffer interval)
- **This is acceptable for most serial use cases**

---

## 11. Future Enhancements (Not in Initial Implementation)

1. **Data filtering per virtual port**:
   - Allow regex filtering
   - Only send matching data to specific virtual port

2. **Bidirectional routing rules**:
   - Virtual port 1 → only send to physical port if matches pattern
   - More complex routing logic

3. **Data logging per source**:
   - Separate logs for each virtual port
   - Log all data with source tagging

4. **Virtual port templates**:
   - Save/load priority configurations
   - Named profiles

5. **Network virtual ports**:
   - TCP/UDP instead of local Unix sockets
   - Remote devices can connect

6. **GUI for external apps**:
   - Show what's connected to each virtual port
   - Send test commands to virtual ports

---

## 12. Implementation Order

### Phase 1: Foundation (Core Threading)
1. Create `SocatHelper.py`
2. Create `SerialSplitter.py` (basic structure)
3. Create `DisplayBufferManager.py`
4. Unit tests for each

### Phase 2: UI Integration
1. Add `tab_splitter()` to App.py
2. Add settings entries
3. Add statistics display and update timer
4. Wire up enable/disable checkbox

### Phase 3: Connection Logic
1. Modify `connect_serial()` for dual mode
2. Modify `disconnect_serial()` for cleanup
3. Test basic connection flow

### Phase 4: Data Flow
1. Modify `send_command()` to route through splitter
2. Wire up broadcast queue to buffer manager
3. Wire up buffer manager to display
4. Test data flow end-to-end

### Phase 5: Priority & Routing
1. Implement priority queue logic
2. Add virtual port reading in SerialSplitter
3. Test priority enforcement
4. Performance testing

### Phase 6: Polish
1. Error handling throughout
2. Statistics accuracy
3. UI refinements
4. Documentation
5. Testing

---

## 13. Code Location Reference

### Files to Modify:

| File | Method/Section | Line Range (Approx) | Changes |
|------|---------------|---------------------|---------|
| `App.py` | Imports | 1-25 | Add SerialSplitter, DisplayBufferManager, SocatHelper |
| `App.py` | `__init__` | 100-180 | Add splitter/buffer instance variables |
| `App.py` | `set_style` | 230-400 | No changes |
| `App.py` | `create_left_panel` | 450-480 | Add splitter tab |
| `App.py` | After `tab_virtual_serial` | ~1200 | Add `tab_splitter()` (new ~200 lines) |
| `App.py` | `connect_serial` | ~1850 | Split into splitter/direct modes (~50 lines) |
| `App.py` | `disconnect_serial` | ~1900 | Add splitter cleanup (~20 lines) |
| `App.py` | `send_command` | ~1950 | Add splitter routing (~15 lines) |
| `App.py` | `read_serial_data` | ~1990 | Add splitter mode check (~10 lines) |
| `App.py` | `closeEvent` | ~2010 | Add thread cleanup (~10 lines) |
| `App.py` | End of class | ~2000+ | Add helper methods (~100 lines) |

### New Files to Create:

| File | Size (Est) | Purpose |
|------|------------|---------|
| `SerialSplitter.py` | ~400 lines | Main splitter thread |
| `DisplayBufferManager.py` | ~200 lines | Display buffering thread |
| `SocatHelper.py` | ~150 lines | socat utilities |

**Total New Code**: ~750 lines  
**Total Modified Code**: ~405 lines  
**Total Implementation**: ~1,155 lines

---

## 14. Testing Checklist

- [ ] socat installation check works
- [ ] Virtual ports created successfully
- [ ] Virtual ports accessible from external tools (minicom, screen, etc.)
- [ ] Physical port opens with splitter enabled
- [ ] Data from physical → appears in app display
- [ ] Data from physical → appears on virtual port 1
- [ ] Data from physical → appears on virtual port 2
- [ ] Data from app → goes to physical port
- [ ] Data from virtual port 1 → goes to physical port
- [ ] Data from virtual port 2 → goes to physical port
- [ ] Priority respected: 0 → 1 → 2
- [ ] Statistics update correctly
- [ ] High-speed data doesn't freeze UI
- [ ] Buffer throttling works
- [ ] Enable/disable splitter works
- [ ] Change priority while running works
- [ ] Disconnect cleans up all resources
- [ ] No orphaned socat processes
- [ ] Thread cleanup on app close
- [ ] Error messages displayed correctly
- [ ] Settings saved and restored

---

## 15. Documentation for Users

**User Guide Section** (to add to README.md):

```markdown
## Serial Splitter Feature

The Serial Splitter allows you to share a physical serial port with up to 2 additional 
virtual serial ports. This enables multiple applications or devices to communicate 
through the same physical connection simultaneously.

### Requirements
- Linux operating system
- `socat` package installed

### Setup
1. Go to the **Splitter** tab
2. Click "Install socat" if not already installed
3. Configure priorities (0 = highest, 2 = lowest)
4. Check "Enable Serial Splitter"
5. Connect to your serial port normally

### Using Virtual Ports
Once enabled, you'll see two virtual port paths displayed:
- `/tmp/serial_virtual_1` - First virtual port
- `/tmp/serial_virtual_2` - Second virtual port

External applications can connect to these ports as if they were physical ports.

### Priority System
The priority system ensures fair access when multiple sources send data simultaneously:
- **Priority 0**: Highest priority, data sent first
- **Priority 1**: Medium priority
- **Priority 2**: Lowest priority

Configure priorities based on your needs. For example:
- Critical control device → Priority 0
- This app → Priority 1  
- Logging device → Priority 2

### Statistics
The Splitter tab shows real-time statistics including:
- Data rates for all ports
- Queue sizes
- Buffer usage

### Troubleshooting
- **Virtual port not found**: Check that socat is running
- **Permission denied**: Run app with appropriate permissions
- **Data not flowing**: Check virtual port connection status in the Splitter tab
```

---

## Summary

This implementation adds approximately **1,155 lines of new code** across 3 new files and modifies ~405 lines in the existing `App.py`. The architecture uses two dedicated threads with priority-based queuing and display buffering to handle high-speed serial data while maintaining UI responsiveness.

The feature is optional and backward compatible - users can continue using the app without enabling the splitter. When enabled, it provides comprehensive control and visibility into the data flow through statistics and status indicators.

Key design decisions:
- **socat** for virtual ports (stable, well-tested, handles high traffic)
- **Priority queues** for fair, configurable routing
- **Display buffering** to prevent UI freezing
- **Comprehensive statistics** for debugging and monitoring
- **Graceful error handling** with recovery
- **Thread-safe** communication via queues and signals

Implementation time estimate: **8-12 hours** for experienced developer.
