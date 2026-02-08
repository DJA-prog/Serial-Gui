# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.5.x   | :white_check_mark: |
| 2.4.x   | :white_check_mark: |
| 2.3.x   | :x:                |
| 2.2.x   | :x:                |
| < 2.2   | :x:                |

## Reporting a Vulnerability

We take the security of Serial Communication Monitor seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Preferred**: Open a security advisory on GitHub
   - Go to the [Security tab](https://github.com/DJA-prog/Serial-Gui/security)
   - Click "Report a vulnerability"
   - Fill out the form with details

### What to Include

Please include the following information in your report:

- **Type of vulnerability** (e.g., code injection, buffer overflow, privilege escalation)
- **Full paths** of source file(s) related to the vulnerability
- **Location** of the affected source code (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the vulnerability and potential attack scenarios
- **Any potential mitigations** you've identified


## Security Considerations

### Serial Communication

This application handles serial communication with hardware devices. Please be aware:

- **Device Access**: The application requires permission to access serial ports on your system
- **Data Transmission**: Commands sent through this application are transmitted directly to your hardware
- **No Encryption**: Serial communication is typically unencrypted
- **Physical Access**: Anyone with access to the serial port can intercept communications

### Configuration Files

- **Settings Storage**: Application settings are stored in user-specific directories
  - Windows: `%APPDATA%\SerialCommunicationMonitor\`
  - Linux: `~/.config/SerialCommunicationMonitor/`
  - macOS: `~/Library/Application Support/SerialCommunicationMonitor/`
- **File Permissions**: Ensure your configuration directory has appropriate permissions
- **Sensitive Data**: Do not store passwords or API keys in command sets or macros

### Debug Mode

- **Debug Builds**: Debug mode (version ending with 'd') logs detailed information
- **Crash Reports**: May contain system information, file paths, and environment variables
- **Sensitive Data**: Review crash reports before sharing to ensure no sensitive data is included
- **Log Files**: Debug logs are stored in the logs directory within the config directory

### Macro Execution

- **Automated Commands**: Macros can send automated command sequences to your devices
- **Review Before Running**: Always review macro contents before execution
- **Trusted Sources**: Only import macros from trusted sources
- **YAML Safety**: Macros are stored as YAML files; avoid loading untrusted YAML files

### Command Sets

- **Command Templates**: Command sets may contain templates with placeholders
- **Input Validation**: Always verify commands before sending to critical devices
- **Custom Commands**: Review custom command sets from third parties

## Best Practices

### For Users

1. **Keep Updated**: Always use the latest version with security patches
2. **Verify Downloads**: Only download releases from official GitHub releases page
3. **Check Checksums**: Verify file integrity using provided checksums (when available)
4. **Review Permissions**: Grant minimal necessary permissions to the application
5. **Secure Configuration**: Protect your configuration directory from unauthorized access
6. **Network Isolation**: Use on isolated networks when working with sensitive devices (note that this application has no reason to be connecting to the internet at all)

### For Developers

1. **Input Validation**: Always validate and sanitize user inputs
2. **Exception Handling**: Use try-catch blocks to prevent crashes from exposing sensitive data
3. **Dependency Updates**: Regularly update dependencies to patch known vulnerabilities
4. **Code Review**: Review all pull requests for potential security issues
5. **Type Safety**: Use Python type hints to catch potential type-related issues
6. **Thread Safety**: Ensure thread-safe operations, especially with serial I/O

## Known Security Considerations

### Current Implementation

1. **YAML Loading**: Uses `yaml.safe_load()` to prevent arbitrary code execution
2. **File Path Validation**: Uses OS-specific path resolution to prevent directory traversal
3. **Thread Safety**: Qt signals/slots ensure thread-safe cross-thread communication
4. **Memory Management**: Output buffer limited to prevent memory exhaustion

### Limitations

1. **No Authentication**: Application does not implement user authentication
2. **No Encryption**: Serial communication is transmitted in plaintext
3. **Local Storage**: Configuration files stored in plaintext
4. **No Audit Log**: Application does not maintain a security audit log

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 2.5.1)
- Announced in GitHub Security Advisories
- Documented in release notes
- Tagged with `security` label in releases

## Questions?

If you have questions about this security policy, please open a discussion on GitHub or contact the maintainers.

## Acknowledgments

We would like to thank all security researchers who have responsibly disclosed vulnerabilities to this project.

---

**Last Updated**: February 8, 2026  
**Policy Version**: 1.0
