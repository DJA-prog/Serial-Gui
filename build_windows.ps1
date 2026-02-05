# PowerShell script to build Serial Communication Monitor .exe using PyInstaller
# Run this script from the project root directory

Write-Host "Serial Communication Monitor - Windows Build Script" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python and add it to your PATH" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: No virtual environment found at venv\" -ForegroundColor Yellow
    Write-Host "Proceeding with system Python..." -ForegroundColor Yellow
}

# Install PyInstaller if not present
Write-Host ""
Write-Host "Checking for PyInstaller..." -ForegroundColor Yellow
try {
    $pyinstallerVersion = pyinstaller --version 2>&1
    Write-Host "Found PyInstaller: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "PyInstaller not found, installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "  Removed build directory" -ForegroundColor Gray
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "  Removed dist directory" -ForegroundColor Gray
}
if (Test-Path "*.spec") {
    Remove-Item -Force "*.spec"
    Write-Host "  Removed old spec files" -ForegroundColor Gray
}

# Verify icon exists
if (-not (Test-Path "images\icon.png")) {
    Write-Host "Error: Icon file not found at images\icon.png" -ForegroundColor Red
    exit 1
}

# Build the executable
Write-Host ""
Write-Host "Building executable with PyInstaller..." -ForegroundColor Cyan
Write-Host ""

$buildCommand = @(
    "pyinstaller",
    "--onefile",                              # Single executable file
    "--windowed",                             # No console window (GUI app)
    "--name=Serial_monitor_v2.4.0_x86-64",                   # Output executable name
    "--icon=images\icon.png",                 # Application icon
    "--add-data=images\icon.png;images",      # Include icon for runtime use
    "--add-data=commands;commands",           # Include command YAML files
    "--clean",                                # Clean PyInstaller cache
    "--noconfirm",                            # Overwrite without confirmation
    "App.py"                                  # Main entry point
)

Write-Host "Command: $($buildCommand -join ' ')" -ForegroundColor Gray
Write-Host ""

& $buildCommand[0] $buildCommand[1..($buildCommand.Length-1)]

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location: dist\Serial_monitor_v2.4.0_x86-64.exe" -ForegroundColor Cyan
    Write-Host ""
    
    # Display file size
    if (Test-Path "dist\Serial_monitor_v2.4.0_x86-64.exe") {
        $fileSize = (Get-Item "dist\Serial_monitor_v2.4.0_x86-64.exe").Length / 1MB
        Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "You can now distribute the .exe file independently." -ForegroundColor White
        Write-Host "Note: First run may create config directory in %APPDATA%\SerialCommunicationMonitor" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Red
    Write-Host "Build failed! Check the error messages above." -ForegroundColor Red
    Write-Host "=====================================================" -ForegroundColor Red
    exit 1
}
