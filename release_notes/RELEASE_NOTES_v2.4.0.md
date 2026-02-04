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

### 🔧 User Interface Refinements
- **Consistent styling** - Themes dialog inherits application styling
- **Improved button sizing** - Buttons use default heights for consistency
- **Clean list displays** - Removed alternating row colors for better theme compatibility

### 📚 Enhanced Documentation
- **THEMES.md reference** - Complete guide to available themes and customization
- **Color specifications** - Hex codes and usage guidelines for all themes
- **Theme descriptions** - Detailed explanations of each theme's purpose and best use cases

## Technical Details

### New Files
- **ThemesDialog.py** - Theme selection dialog implementation

### Modified Files
- **App.py** - Added theme dialog integration, callback methods, and enhanced macro execution logic
- **MacroEditor.py** - Expanded OutputBlock with success/fail actions and serialization

### New Methods in App.py
- `open_themes_dialog()` - Opens the theme selection dialog
- `apply_theme_settings()` - Applies selected theme colors and updates UI
- Enhanced `_execute_macro_steps()` - Handles success actions, ignore, and dialog wait
- Updated `_show_macro_dialog()` - Uses Continue/End Macro button labels

### Updated OutputBlock Features
- **Success action combo** - Dropdown with 6 action options
- **Fail action combo** - Updated with Ignore and Dialog and Wait options
- **Custom command fields** - Separate inputs for success and fail commands
- **YAML serialization** - Both success and fail actions saved to macro files
- **Load compatibility** - Correctly restores actions when editing existing macros

## Upgrade Notes

- **No breaking changes** - All v2.3.0 settings and configurations fully compatible
- **Backward compatible macros** - Existing macros without success actions default to "Continue"
- **Seamless integration** - Theme dialog works with existing color customization
- **Automatic saves** - Theme selections and macro changes saved automatically
- **Manual customization preserved** - Can still manually adjust colors in Settings tab

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

**Full Changelog:** [View on GitHub](https://github.com/DJA-prog/Serial-Gui/compare/v2.3.0...v2.4.0)
