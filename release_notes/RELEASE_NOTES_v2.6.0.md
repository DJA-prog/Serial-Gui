# Serial Communication Monitor v2.6.0 Release Notes

**Release Date:** February 15, 2026

## What's New in v2.6.0

### 🎯 Macro Improvements

#### Silent Macro Stop (NEW)
- **Clean termination** - Stopping a macro no longer outputs additional messages
- **Immediate exit** - Macro stops at the current step without printing step results
- **No residual output** - Failed output blocks, dialogs, and other step-related messages suppressed
- **Professional appearance** - Clean macro termination with just the initial stop message
- **Responsive stop** - Stop checks at strategic points: between steps, during delays, and during response waits

#### Improved Auto-Reconnect Control
- **User-controlled reconnection** - Auto-reconnect now respects manual disconnect operations
- **Pause on disconnect** - Clicking disconnect pauses auto-reconnect functionality
- **Resume on connect** - Clicking connect re-enables auto-reconnect
- **Flexible workflow** - App can run with auto-reconnect disabled, ready for manual connection
- **Better device management** - Prevents reconnection attempts when user intentionally disconnects
- **Unchanged connected behavior** - Auto-reconnect still activates automatically when connected and port is lost

#### Macro Stability Fixes
- **Fixed deadlock issue** - Resolved nested lock acquisition that caused app freezing when running consecutive macros
- **Better thread safety** - Improved lock handling in stop signal detection
- **Smooth macro execution** - Sequential macro runs no longer cause app hangs
- **Reliable resumption** - Can now run multiple macros in succession without issues

#### How It Works
1. **When you connect** - Auto-reconnect becomes active
2. **Device disconnects** - If device is physically unplugged/reconnected, app automatically reconnects
3. **When you click disconnect** - Auto-reconnect is paused
4. **App waits** - Serial port stays disconnected, auto-reconnect disabled
5. **When you click connect** - Auto-reconnect is re-enabled for future accidental disconnections
6. **Stop macro** - Halts execution silently, leaves app in consistent state

#### New Menu Blocks (NEW)
- **Interactive command selection** - Allow user to select and execute commands during macro execution
- **Two menu types** - Single selection and multi-selection modes
- **Single Menu Block** - User selects one command from list, then macro continues
- **Multi Menu Block** - User can select multiple commands, each executed immediately, then clicks continue
- **Pause and resume** - Macros pause at menu blocks waiting for user input
- **Command execution** - Selected commands sent directly to serial port
- **Flexible workflows** - Create conditional macros where user choices determine execution path

##### Menu Single Block (NEW)
- **One-time selection** - User picks a single command from the available list
- **Immediate execution** - Selected command sent to serial port right away
- **Automatic advancement** - Macro continues to next step after command execution
- **Dropdown-like behavior** - Click menu to see options, pick one, macro proceeds
- **Perfect for** - Simple choices, selecting one of several recovery options

##### Menu Multi Block (NEW)
- **Multiple selections** - User can select and execute multiple commands in sequence
- **Repeat selection** - "Continue" button allows selecting more commands
- **Manual advancement** - User clicks "Continue Macro" when ready to proceed
- **Flexible execution** - Send as many commands as needed before advancing
- **Perfect for** - Complex initialization, testing sequences, user-guided diagnostics

### 🐛 Bug Fixes

#### Auto-Reconnect Behavior
- **Respects user intent** - Disconnect now prevents auto-reconnect attempts
- **Clean initialization** - New flag properly initialized and managed throughout app lifecycle
- **No interference** - Manual reconnect operations no longer interfere with auto-reconnect logic

## Technical Details

### New Variables
- `auto_reconnect_disabled` - Flag to track if auto-reconnect should be paused
- Initialized to `False` on app startup
- Set to `True` when user disconnects
- Set to `False` when user connects

### Modified Functions
- **`disconnect_serial()`** - Sets `auto_reconnect_disabled = True`
- **`connect_serial()`** - Sets `auto_reconnect_disabled = False`
- **`refresh_serial_ports()`** - Checks both `auto_reconnect_checkbox.isChecked()` and `not auto_reconnect_disabled`
- **`_execute_macro_steps()`** - Improved lock handling, removed nested acquisitions, added menu block support
- **`stop_macro()`** - Silent exit, no output messages

### Menu Block Handling
- **Menu Single** - Uses a `Queue[Optional[str]]` to receive the user's selected command
- **Menu Multi** - Uses a `Queue[Optional[str]]` to handle multiple selections with a continue button
- **Signal emission** - `macro_menu_signal` emits to main thread for safe UI interaction
- **Queue-based communication** - Thread-safe command passing from UI back to macro thread
- **Separate lists** - Each menu type maintains its own command list configuration
- **Immediate execution** - Selected commands sent to serial port immediately upon selection

## Known Issues
None reported

## Installation & Updating
Users are encouraged to update to v2.6.0 for improved macro stability and better auto-reconnect control.
