# Macro System Documentation

## Overview
The macro system allows you to create automated sequences of serial commands with conditional logic, delays, and output validation.

## Features
- **Drag-and-Drop Editor**: Scratch-like interface for creating macros
- **Four Block Types**:
  - **Input Block** (Blue): Send commands to the serial port
  - **Delay Block** (Orange): Add delays between commands (in milliseconds)
  - **Dialog Wait Block** (Purple): Pause and show a dialog with Continue/End options
  - **Output Block** (Green): Wait for expected responses with timeout and fail handling

## Creating a Macro

1. Click the **Macros** tab in the left panel
2. Click **+ Create New Macro** button
3. In the editor:
   - Drag blocks from the left palette to the canvas on the right
   - Configure each block's parameters
   - Arrange blocks in the desired execution order
4. Enter a macro name at the top
5. Click **Save Macro**

## Block Types

### Input Block (Blue)
Sends a command to the serial port.
- **Command**: The text to send (e.g., "AT", "AT+CPIN?")

### Delay Block (Orange)
Pauses execution for a specified time.
- **Wait**: Time in milliseconds (0-60000 ms)

### Dialog Wait Block (Purple)
Pauses macro execution and displays a dialog with a custom message.
- **Message**: Custom text to display in the dialog
- **Options**: Continue (default) or End
- **Behavior**: 
  - **Continue**: Proceeds to the next step
  - **End**: Stops macro execution immediately

### Output Block (Green)
Waits for expected output from the serial port with timeout.
- **Expected**: The text to wait for (e.g., "OK", "READY")
  - Matching is done per line with leading/trailing spaces stripped
- **Timeout**: Maximum time to wait in milliseconds
- **On Fail**: Action to take if expected output is not received
  - **Continue**: Continue to next block
  - **Exit Macro**: Stop macro execution
  - **Custom Command**: Send a specific command (e.g., retry or recovery command)
  - **Dialog for Command**: Show dialog asking user to enter a recovery command

## YAML Format

Macros are saved as YAML files with the following structure:

```yaml
name: Macro Name
steps:
  - input: "AT"
  - delay: 1000
  - dialog_wait:
      message: "Check device status before continuing?"
  - output:
      expected: "OK"
      timeout: 1000
      fail: EXIT  # or fail: {input: "RETRY_COMMAND"}
  - input: "AT+CPIN?"
  - output:
      expected: "READY"
      fail:
        input: "AT+CPIN=1234"
```

## Example Macros

### Simple AT Test
```yaml
name: AT Test
steps:
  - input: "AT"
  - delay: 100
  - output:
      expected: "OK"
      timeout: 1000
      fail: EXIT
```

### SIM Check with PIN
```yaml
name: SIM Check
steps:
  - input: "AT+CPIN?"
  - output:
      expected: "READY"
      timeout: 2000
      fail:
        input: "AT+CPIN=1234"
  - delay: 1000
  - input: "AT+CSQ"
  - output:
   

### Interactive Configuration
```yaml
name: Interactive Setup
steps:
  - input: "AT"
  - output:
      expected: "OK"
      timeout: 1000
  - dialog_wait:
      message: "Device ready. Connect antenna now and click Continue."
  - input: "AT+CSQ"
  - output:
      expected: "+CSQ:"
      timeout: 2000
  - dialog_wait:
      message: "Signal check complete. Proceed with configuration?"
  - input: "AT+CREG?"
```

### Error Recovery with Dialog
```yaml
name: Flexible Error Recovery
steps:
  - input: "AT+CPIN?"
  - output:
      expected: "READY"
      timeout: 2000
      fail: DIALOG
  - input: "AT+CREG?"
  - output:
      expected: "+CREG: 0,1"
      timeout: 5000
      fail: DIALOG
```   expected: "+CSQ:"
      timeout: 1000
```

## Managing Macros

### Running a Macro
1. Connect to a serial port first
2. Click on any macro button in the Macros tab
3. Watch the output display for execution progress
Use "Dialog Wait" for user confirmation or manual intervention points
- Dialog Wait defaults to "Continue" button for quick execution flow
- 
### Editing a Macro
1. Right-click on a macro button
2. Select "Edit Macro"
3. Modify blocks in the editor
4. Save changes

### Deleting a Macro
1. Right-click on a macro button
2. Select "Delete Macro"
3. Confirm deletion

## Tips

- Test your serial commands individually before creating a macro
- Use appropriate timeouts based on your device's response time
- Add delays between commands if your device needs processing time
- Use the "Exit Macro" fail option for critical checks
- Use "Custom Command" for predefined error recovery scenarios
- Use "Dialog for Command" when you need flexible, user-defined recovery actions
- Use "Dialog Wait" for user confirmation or manual intervention points
- Dialog Wait defaults to "Continue" button for quick execution flow
- Output matching strips leading/trailing whitespace for more reliable matching
- Macro execution runs in a separate thread to keep the UI responsive

## Location

Macros are stored in:
- **Linux**: `~/.config/SerialCommunicationMonitor/macros/`
- **Windows**: `%APPDATA%/SerialCommunicationMonitor/macros/`
- **macOS**: `~/Library/Application Support/SerialCommunicationMonitor/macros/`
