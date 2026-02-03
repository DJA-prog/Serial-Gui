# Serial Communication Monitor v2.3.0 Release Notes

**Release Date:** February 3, 2026

## What's New in v2.3.0

### 🎯 Macro System Enhancements

#### New Dialog Wait Block
- **Interactive macro control** - Pause macro execution with custom dialog messages
- **Continue/End options** - User can choose to proceed or terminate the macro
- **Continue pre-selected** - Default action is to continue for quick workflow
- **Custom messages** - Display specific instructions or confirmations at any point

#### Enhanced Output Block
- **Dialog for Command** - New fail action that prompts user for recovery command on-the-fly
- **Flexible error recovery** - Enter custom commands when expected output is not received
- **Four fail options**:
  - Continue - Proceed to next step
  - Exit Macro - Stop macro execution
  - Custom Command - Send predefined recovery command
  - Dialog for Command - Prompt user for command (NEW)

#### Improved Response Matching
- **Per-line matching** - Each line checked independently for expected output
- **Whitespace handling** - Leading and trailing spaces automatically stripped
- **Dedicated session buffer** - Isolated buffer for macro execution eliminates false positives
- **Zero lag detection** - Responses captured immediately, even before OutputBlock starts
- **Buffer clearing strategy** - Buffer cleared at start of InputBlock, DelayBlock, and DialogWaitBlock
- **Clean state** - Each OutputBlock sees only responses since last buffer clear

#### Macro Editor Improvements
- **Fail action persistence** - OutputBlock fail settings now correctly loaded when editing macros
- **Four fail actions supported** - All fail modes (Continue, Exit, Custom Command, Dialog) properly saved and restored
- **Custom command text** - Recovery commands preserved across edit sessions
- **Exit safety** - Prompts to save or discard changes when closing with unsaved work
- **Change tracking** - Detects modifications to macro name and blocks

### 🔧 Commands Editor Improvements
- **Exit safety** - Prompts to save or discard changes when closing with unsaved work
- **Change tracking** - Monitors all add, edit, and remove operations
- **Automatic state management** - Clears change flag after successful save

### 📚 Documentation Updates
- **MACROS.md expanded** - Complete documentation for Dialog Wait Block
- **Fail action examples** - New examples showing Dialog for Command usage
- **Interactive Configuration example** - Sample macro demonstrating dialog wait usage
- **Error Recovery example** - Flexible error recovery pattern with Dialog for Command

### 🐛 Bug Fixes
- **Fixed macro response detection** - Responses no longer missed when arriving before OutputBlock starts waiting
- **Fixed fail action loading** - OutputBlock fail selection now correctly displays saved value when editing
- **Eliminated false positives** - OutputBlocks no longer match responses from previous steps
- **Removed lag** - Session buffer approach eliminates delays from checking old data

### 🔧 Technical Improvements
- **Thread-safe dialog handling** - Queue-based communication for dialogs from macro thread
- **Session-based buffering** - Macro execution uses isolated buffer separate from main output
- **Automatic cleanup** - Session buffer cleared on macro completion, error, or cancellation
- **Lock optimization** - Efficient locking strategy prevents race conditions

## Upgrade Notes

- **No breaking changes** - All v2.2.0 macros fully compatible
- **Automatic fail action handling** - Old macros with fail actions work without modification
- **New fail option available** - "Dialog for Command" can be added to existing macros

## Known Issues

- None reported at this time

## System Requirements

- **Python 3.8+**
- **PyQt5**
- **pyserial**
- **PyYAML**

## Tested Platforms

- ✅ Debian 13
- ✅ Windows 10 (expected)
- 🔄 Should work on macOS and other Linux distributions

---

**Full Changelog:** [View on GitHub](https://github.com/DJA-prog/Serial-Gui/compare/v2.2.0...v2.2.1)
