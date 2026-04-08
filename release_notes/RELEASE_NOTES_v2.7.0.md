# Serial Communication Monitor v2.7.0 Release Notes

**Release Date:** March 13, 2026

## What's New in v2.7.0

### Macro and Command File Version Compatibility

#### Version Metadata in Saved Files
- Macro files now save the app version in `app_version`.
- Command list files now save the app version in `app_version`.

#### Compatibility Rules
- Files with no `app_version` are always allowed.
- Files with version less than or equal to the running app version are allowed.
- Files with newer version are ignored by default.

#### New Compatibility Setting
- Added **Allow Newer File Versions** in Settings.
- Default value is **False** for safer compatibility behavior.
- When enabled, newer-version macro and command files are shown and can be used.

### Serial Port Update Control

#### New Auto Serial Update Setting
- Added a new **Auto Serial Update** setting in the Settings tab.
- Default value is **False** so auto scanning is opt-in.
- When enabled, the app continues refreshing serial ports automatically every second.

#### New Manual Update Workflow
- Added a new **Update Serial** button in the top ribbon.
- The button is automatically shown when **Auto Serial Update** is disabled.
- Clicking **Update Serial** refreshes the port list on demand.
- A status message is printed to the output area after manual refresh.
- Fixed manual refresh to perform a fresh port scan before repopulating the combo box.

### Output Display Options in Settings

#### Settings Relocation
- Moved **Display Format** (text/hex) control from output context menu to Settings.
- Moved **Show Timestamps** toggle from output context menu to Settings.
- Output context menu now keeps text actions only (Copy / Select All).

#### Stability Fix
- Fixed a crash when clicking Send caused by Qt passing a boolean signal argument into `send_command()`.

#### Smart UI Behavior
- The refresh timer now starts only when auto update is enabled.
- Switching the setting immediately applies behavior without restarting the app.
- The app now toggles between automatic refresh and manual refresh mode dynamically.
- Fixed a bug where scanning could restart after disconnect even when disabled.

## Technical Details

### Updated Defaults
- `settings['general']['auto_serial_update']` added with default value `False`.
- `settings['general']['allow_newer_file_versions']` added with default value `False`.

### Version Gating Logic
- Added app/file version comparison for macro and command files.
- Added compatibility checks while listing, opening, and executing files.
- Added parser support for debug-style versions such as `2.7.0d`.

### MainWindow Changes
- Added `self.update_serial_button` in the top ribbon.
- Added `manual_update_serial_ports()` for manual list refresh.
- Added `toggle_auto_serial_update(enabled: bool)` to switch refresh mode.
- Updated timer startup logic to respect `auto_serial_update` on launch.
- Updated disconnect logic so scan timer resumes only when auto update is enabled.
- Added `parse_version_tuple()` and `is_file_version_compatible()`.
- Added command/macro filtering based on compatibility setting.

### Settings Table Updates
- Increased settings table row count from `19` to `22`.
- Added new row: **Allow Newer File Versions**.
- Added new row: **Display Format**.
- Added new row: **Show Timestamps**.
- Added handling for boolean edit/validation and immediate apply behavior.

### Version Update
- Application version updated from `2.6.0` to `2.7.0` in `App.py`.

## Upgrade Notes
- No breaking changes.
- Auto serial refresh is disabled by default and can be enabled manually in Settings.
- Users have full manual control via the **Update Serial** button.
- Existing macro/command files without version metadata continue to work normally.

## Known Issues
- Automatic serial port scanning may interrupt some serial devices and processes.
