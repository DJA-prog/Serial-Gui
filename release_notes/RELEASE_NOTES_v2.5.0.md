# Serial Communication Monitor v2.5.0 Release Notes

**Release Date:** February 6, 2026

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

### 🐛 Bug Fixes and Stability Improvements

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

### Modified Files
- **App.py** - Added collapsible panel system, animation support, filter fixes, and version bump to 2.5.0
- **MacroEditor.py** - Enhanced error handling for OutputBlock with signal blocking and RuntimeError protection

### New Imports in App.py
- **QPropertyAnimation** - Enables smooth width animations for panel toggle
- **QEasingCurve** - Provides animation easing for professional transitions

### New Methods in App.py
- `toggle_left_panel()` - Handles panel visibility toggle with animated transitions

### Enhanced Methods in App.py
- `create_left_panel()` - Updated to use container widget for animation support
- `handle_serial_data()` - Fixed filtering logic to preserve empty lines when appropriate

### Enhanced Methods in MacroEditor.py
- `OutputBlock.__init__()` - Added signal blocking and immediate visibility updates
- `OutputBlock.setup_block_content()` - Enhanced signal connection with RuntimeError protection
- `OutputBlock.on_success_action_changed()` - Added RuntimeError handling for widget access
- `OutputBlock.on_fail_action_changed()` - Added RuntimeError handling for widget access
- `OutputBlock.to_dict()` - Comprehensive RuntimeError protection for all widget access

## Upgrade Notes

- **No breaking changes** - All v2.4.0 settings and configurations fully compatible
- **Seamless upgrade** - Panel visibility state not persisted, always starts visible
- **Backward compatible** - All existing features continue to work unchanged
- **Windows users** - Significant stability improvements for macro editor on Windows 11 and updated Windows 10 systems
- **Filter behavior** - Line filters now work correctly; may notice improved filtering behavior

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
