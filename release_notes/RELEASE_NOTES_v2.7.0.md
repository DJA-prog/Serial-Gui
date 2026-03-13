# Serial Communication Monitor v2.7.0 Release Notes

**Release Date:** March 13, 2026

## What's New in v2.7.0

### Serial Port Update Control

#### New Auto Serial Update Setting
- Added a new **Auto Serial Update** setting in the Settings tab.
- Default value is **True** to preserve current behavior for existing users.
- When enabled, the app continues refreshing serial ports automatically every second.

#### New Manual Update Workflow
- Added a new **Update Serial** button in the top ribbon.
- The button is automatically shown when **Auto Serial Update** is disabled.
- Clicking **Update Serial** refreshes the port list on demand.
- A status message is printed to the output area after manual refresh.

#### Smart UI Behavior
- The refresh timer now starts only when auto update is enabled.
- Switching the setting immediately applies behavior without restarting the app.
- The app now toggles between automatic refresh and manual refresh mode dynamically.

## Technical Details

### Updated Defaults
- `settings['general']['auto_serial_update']` added with default value `True`.

### MainWindow Changes
- Added `self.update_serial_button` in the top ribbon.
- Added `manual_update_serial_ports()` for manual list refresh.
- Added `toggle_auto_serial_update(enabled: bool)` to switch refresh mode.
- Updated timer startup logic to respect `auto_serial_update` on launch.

### Settings Table Updates
- Increased settings table row count from `18` to `19`.
- Added new row: **Auto Serial Update**.
- Added handling for boolean edit/validation and immediate apply behavior.

### Version Update
- Application version updated from `2.6.0` to `2.7.0` in `App.py`.

## Upgrade Notes
- No breaking changes.
- Existing users retain automatic serial refresh by default.
- Users who prefer full manual control can disable auto update and use the new button.

## Known Issues
- Automatic serial port scanning may interrupt some serial devices and processes.
