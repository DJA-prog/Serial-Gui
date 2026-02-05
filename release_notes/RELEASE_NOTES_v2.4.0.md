# Serial Communication Monitor v2.4.0 Release Notes

**Release Date:** February 4, 2026

## What's New in v2.4.0

### 🎨 Theme Selection Dialog

#### New Themes Dialog
- **Quick theme switching** - Select from pre-programmed themes with a single click
- **Theme preview** - Visual color swatches and descriptions for each theme
- **Seven pre-defined themes**:
  - Default - Clean and professional dark theme with electric blue accents
  - Hacker Mint - Matrix-inspired green on black terminal aesthetic
  - Midnight Blue - Professional dark blue theme with subtle contrasts
  - Sunset - Warm orange/red accents on deep navy
  - Monochrome - Pure grayscale, minimal distraction
  - Forest - Natural green tones, easy on the eyes
  - Purple Haze - Rich purple for a unique look
- **Instant application** - Themes apply immediately with automatic settings save
- **Easy access** - New "Select Theme" button in About tab

#### ThemesDialog Module
- **Standalone component** - New ThemesDialog.py module for theme management
- **Reusable design** - Callback-based architecture for easy integration
- **Theme metadata** - Each theme includes description and color specifications
- **User-friendly interface** - List selection with detailed preview pane

### 🎯 Macro System Enhancements

#### Enhanced OutputBlock - Success Checks
- **Success actions** - Define what happens when expected output IS received
- **Symmetric control** - Both success and fail conditions now have identical capabilities
- **Six action options** for both success and fail:
  - **Ignore** - Silently continue without any action (NEW)
  - **Continue** - Proceed to next step (default)
  - **Exit Macro** - Terminate macro execution
  - **Custom Command** - Send a predefined command
  - **Dialog for Command** - Prompt user to enter a command
  - **Dialog and Wait** - Show dialog asking user to Continue or End Macro (NEW)

#### Dialog and Wait Feature
- **User decision points** - Pause macro execution for user confirmation
- **Available in OutputBlock** - Use on both success and fail conditions
- **Clear options** - User chooses to Continue or End Macro
- **Flexible control** - React to success/fail states with interactive dialogs

#### Ignore Option
- **Silent continuation** - No action taken, macro proceeds to next step
- **Available for both** - Success and fail conditions can both ignore results
- **Streamlined workflows** - Skip unnecessary actions when result doesn't matter

#### Improved Dialog Clarity
- **Better button labels** - Changed from confusing "OK/Cancel" to clear "Continue/End Macro"
- **Consistent across dialogs** - All macro-related dialogs use the same button labels
- **Pre-selected default** - "Continue" is always the default for quick workflows
- **User-friendly** - Buttons clearly communicate what will happen

### � User Manual Dialog

#### Comprehensive In-App Documentation
- **Built-in manual** - Complete user guide accessible from About tab
- **Eight organized sections**:
  - Overview - Key features and introduction
  - Commands Tab - Command list management and editor
  - Macros Tab - Macro creation and execution guide
  - Settings Tab - All settings explained
  - Main Window - Interface overview and status bar
  - Keyboard Shortcuts - Quick reference
  - Tips & Best Practices - Performance and usage tips
  - Troubleshooting - Common issues and solutions
  - File Formats - YAML structure reference
- **Split-view interface** - Section list with HTML content display
- **External links support** - Clickable GitHub repository links
- **Always accessible** - No internet connection required

### 🎯 Window Focus Management

#### Auto-Disconnect on Inactive
- **Smart port management** - Automatically disconnect serial port when app loses focus
- **Auto-reconnect** - Seamlessly reconnects when app regains focus
- **Visual indicator** - Connect/Disconnect button shows ! when feature is enabled
- **Informative tooltips** - Button tooltip explains current behavior
- **Settings integration** - Toggle via "Disconnect On Inactive" setting
- **Port memory** - Remembers port and baud rate for reconnection
- **Use cases** - Free up serial port for other applications temporarily

### 🎨 Enhanced Macro System - Substring Matching

#### Flexible Output Validation
- **Substring match option** - OutputBlock now supports partial line matching
- **Two matching modes**:
  - **Substring Match (default)** - Find expected text anywhere in the line
  - **Full Line Match** - Entire line must match exactly
- **Checkbox control** - Easy toggle in OutputBlock UI
- **YAML persistence** - Matching mode saved with macro
- **Better compatibility** - Handle verbose device responses more easily
- **Tooltip guidance** - Clear explanation of each mode

### 🔧 User Interface Refinements

#### Settings Tab Cleanup
- **Streamlined display** - Removed color settings from Settings table
- **Theme-focused** - Colors now exclusively managed via Themes dialog
- **Reduced clutter** - From 23 rows to 18 focused settings
- **Removed read-only fields** - App version no longer displayed in settings
- **Cleaner interface** - Focus on actionable settings only

#### Flow Indicators Toggle
- **Show Flow Indicators** - New setting to hide/show < and > symbols
- **User preference** - Some users prefer clean output without direction indicators
- **Full control** - Affects both sent and received data display

#### Visual Polish
- **Consistent styling** - Themes dialog inherits application styling
- **Improved button sizing** - Buttons use default heights for consistency
- **Clean list displays** - Removed alternating row colors for better theme compatibility
- **CheckBox backgrounds** - OutputBlock substring checkbox blends with block color

### � Bug Fixes and Stability Improvements

#### Macro Editor Crash Prevention
- **Initialization protection** - Added flag to prevent signal handling during widget creation
- **Defensive widget access** - All widget accesses now verify existence before use
- **Comprehensive error handling** - Try-except blocks added to all critical operations
- **Signal handler safety** - Handlers check initialization state before execution
- **Graceful degradation** - Errors are logged and app continues with fallback values

#### Cross-Platform Compatibility
- **Windows build stability** - Prevents crashes on systems with different PyQt5 versions
- **DPI scaling protection** - Handles various screen resolutions and DPI settings
- **Error logging** - Debug messages help identify system-specific issues
- **Robust serialization** - YAML operations protected with error recovery

#### Protected Components
- **OutputBlock** - Full error handling for success/fail action changes
- **InputBlock** - Protected initialization and serialization
- **DelayBlock** - Safe value setting and retrieval
- **DialogWaitBlock** - Error-tolerant message handling
- **All signal handlers** - Protected against race conditions and null references

### �📚 Enhanced Documentation
- **THEMES.md reference** - Complete guide to available themes and customization
- **Color specifications** - Hex codes and usage guidelines for all themes
- **Theme descriptions** - Detailed explanations of each theme's purpose and best use cases

## Technical Details

### New Files
- **ThemesDialog.py** - Theme selection dialog implementation
- **ManualDialog.py** - In-app user manual with comprehensive documentation
- **build_windows.ps1** - PowerShell script for building Windows .exe with PyInstaller

### Modified Files
- **App.py** - Added theme dialog integration, manual dialog, window focus detection, flow indicator toggle, callback methods, and enhanced macro execution logic
- **MacroEditor.py** - Expanded OutputBlock with success/fail actions, substring matching, and serialization improvements
- **THEMES.md** - Theme documentation and gallery

### New Methods in App.py
- `open_themes_dialog()` - Opens the theme selection dialog
- `open_manual_dialog()` - Opens the user manual dialog
- `apply_theme_settings()` - Applies selected theme colors and updates UI
- `changeEvent()` - Detects window activation/deactivation for focus management
- `on_window_activated()` - Handles window gaining focus with auto-reconnect
- `on_window_deactivated()` - Handles window losing focus with auto-disconnect
- `update_connect_button_appearance()` - Updates button text/tooltip with focus indicators
- Enhanced `_execute_macro_steps()` - Handles success actions, ignore, and dialog wait
- Enhanced `_wait_for_response()` - Added substring_match parameter for flexible matching
- Updated `_show_macro_dialog()` - Uses Continue/End Macro button labels

### Updated OutputBlock Features
- **Success action combo** - Dropdown with 6 action options
- **Fail action combo** - Updated with Ignore and Dialog and Wait options
- **Substring match checkbox** - Toggle between substring and full line matching
- **Custom command fields** - Separate inputs for success and fail commands
- **YAML serialization** - Actions and matching mode saved to macro files
- **Load compatibility** - Correctly restores actions when editing existing macros
- **Background styling** - Checkbox blends with block background color

## Upgrade Notes

- **No breaking changes** - All v2.3.0 settings and configurations fully compatible
- **Backward compatible macros** - Existing macros without success actions default to "Continue", substring_match defaults to True
- **Settings migration** - App version automatically tracked in settings.yaml
- **Seamless integration** - Theme dialog works with existing color customization
- **Automatic saves** - Theme selections, focus settings, and macro changes saved automatically
- **Color management** - Colors removed from Settings table, use Themes dialog or edit settings.yaml directly
- **Windows deployment** - Use build_windows.ps1 to create standalone .exe

## Known Issues

- None reported at this time

## Bug Fixes

This release includes important stability improvements:
- **Fixed filter_empty_lines bug** - Filter was being applied unconditionally regardless of setting state
- **Fixed empty sent line display** - Now respects filter_empty_lines setting when displaying sent commands
- **Fixed macro editor crashes** on some Windows systems when changing OutputBlock dropdown options
- **Resolved race conditions** in widget initialization that could cause crashes
- **Improved error recovery** - Application continues gracefully when encountering widget errors
- **Enhanced debugging** - Error messages now logged to console for troubleshooting

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

**Full Changelog:** [View on GitHub](https://github.com/DJA-prog/Serial-Gui/compare/v2.3.0...v2.4.0)
