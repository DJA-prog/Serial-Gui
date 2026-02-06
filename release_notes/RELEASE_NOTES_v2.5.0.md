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

### 🎨 Windows-Inspired Themes

#### Four New Theme Options
- **Windows XP** - Nostalgic Luna blue theme with iconic bright blue (#0063B1)
- **Windows 7** - Classic Aero-inspired glass-like aesthetics (#3E8EDE)  
- **Windows 10** - Modern flat design with Microsoft's signature blue (#0078D4)
- **Windows 11** - Refined modern design with soft rounded aesthetics (#0067C0)
- **Total themes available** - 11 pre-programmed themes to choose from
- **Easy access** - Available in Themes Dialog from About tab
- **Instant application** - Apply immediately with automatic settings save

#### Use Cases
- **Nostalgia** - Relive computing history with classic Windows themes
- **Consistency** - Match your operating system's look and feel
- **Variety** - More options for personal customization
- **Professional** - Windows-inspired themes offer familiar, professional appearance

### 📊 Serial Port Availability Detection

#### Smart Port Status Checking
- **Automatic detection** - Checks if serial ports are in use by other applications
- **Tooltip indicators** - Hover over ports to see availability status
  - "Available" - Port is free and ready to use
  - "Currently in use" - Port is occupied by another application
- **Real-time updates** - Status updates during periodic port refresh
- **Own port detection** - Your currently connected port shows as available
- **Non-intrusive** - Status available on-demand without visual clutter

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
- **App.py** - Added collapsible panel system, animation support, port availability checking, filter fixes, and version 2.5.0
- **MacroEditor.py** - Enhanced error handling for OutputBlock with signal blocking and RuntimeError protection
- **ThemesDialog.py** - Added four new Windows-inspired themes (XP, 7, 10, 11)
- **THEMES.md** - Documentation for all 11 themes including new Windows themes
- **StyleManager.py** - Removed color override from combo box dropdown to allow custom item styling

### New Imports in App.py
- **QPropertyAnimation** - Enables smooth width animations for panel toggle
- **QEasingCurve** - Provides animation easing for professional transitions
- **QStandardItemModel, QStandardItem** - For custom combo box item management

### New Methods in App.py
- `toggle_left_panel()` - Handles panel visibility toggle with animated transitions
- `is_port_in_use()` - Checks if a serial port is currently occupied
- `populate_port_combo()` - Populates combo box with port availability tooltips

### Enhanced Methods in App.py
- `create_left_panel()` - Updated to use container widget for animation support
- `handle_serial_data()` - Fixed filtering logic to preserve empty lines when appropriate
- `refresh_serial_ports()` - Now always repopulates combo box to update port availability

### Enhanced Methods in MacroEditor.py
- `OutputBlock.__init__()` - Added signal blocking and immediate visibility updates
- `OutputBlock.setup_block_content()` - Enhanced signal connection with RuntimeError protection
- `OutputBlock.on_success_action_changed()` - Added RuntimeError handling for widget access
- `OutputBlock.on_fail_action_changed()` - Added RuntimeError handling for widget access
- `OutputBlock.to_dict()` - Comprehensive RuntimeError protection for all widget access

### New Themes
- **Windows XP** - Luna blue (#0063B1, #3399FF, #E8F4FF, #001F3F)
- **Windows 7** - Aero glass (#3E8EDE, #6CB4EE, #F0F0F0, #1A2332)
- **Windows 10** - Flat modern (#0078D4, #40A0E0, #FFFFFF, #1E1E1E)
- **Windows 11** - Refined modern (#0067C0, #4DA3E0, #F5F5F5, #202020)

## Upgrade Notes

- **No breaking changes** - All v2.4.0 settings and configurations fully compatible
- **Seamless upgrade** - Panel visibility state not persisted, always starts visible
- **New themes** - Four additional Windows-themed color schemes now available
- **Backward compatible** - All existing features continue to work unchanged
- **Windows users** - Significant stability improvements for macro editor on Windows 11 and updated Windows 10 systems
- **Filter behavior** - Line filters now work correctly; may notice improved filtering behavior

## Known Issues

- None reported at this time

## Tested Platforms

- ✅ Debian 13
- ✅ Windows 10 (Version 22H2)
- 🔄 Should work on macOS and other Linux distributions

---

**Full Changelog:** [View on GitHub](https://github.com/DJA-prog/Serial-Gui/compare/v2.4.0...v2.5.0)
