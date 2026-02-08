# PowerShell script to build Serial Communication Monitor .exe using PyInstaller
# Run this script from the project root directory
# Usage: .\build_windows.ps1 [release|debug]
#        Default is 'release' if no parameter provided

param(
    [Parameter(Position=0)]
    [ValidateSet('release', 'debug')]
    [string]$BuildMode = 'release'
)

$version = "2.5.0"

# Add 'd' suffix for debug builds
if ($BuildMode -eq 'debug') {
    $versionSuffix = $version + "d"
    $buildType = "DEBUG"
} else {
    $versionSuffix = $version
    $buildType = "RELEASE"
}

Write-Host "Serial Communication Monitor - Windows Build Script" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Build Mode: $buildType" -ForegroundColor $(if ($BuildMode -eq 'debug') {'Yellow'} else {'Green'})
Write-Host "Version: $versionSuffix" -ForegroundColor Cyan
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

# Base build command
$buildCommand = @(
    "pyinstaller",
    "--onefile",                                               # Single executable file
    "--name=Serial_monitor_v" + $versionSuffix + "_x86-64",    # Output executable name with version suffix
    "--icon=images\icon.png",                                  # Application icon
    "'"--add-data=images\icon.png;images"'",                       # Include icon for runtime use
    "'"--add-data=commands;commands"'",                            # Include command YAML files
    "--clean",                                                 # Clean PyInstaller cache
    "--noconfirm"                                              # Overwrite without confirmation
)

# Add mode-specific flags
if ($BuildMode -eq 'debug') {
    # Debug mode: Show console window for debugging output
    $buildCommand += "--console"
    $buildCommand += "--debug=all"                             # Enable PyInstaller debug output
    Write-Host "Debug mode enabled: Console window will be visible" -ForegroundColor Yellow
} else {
    # Release mode: No console window (GUI only)
    $buildCommand += "--windowed"
    Write-Host "Release mode: GUI-only executable" -ForegroundColor Green
}

# Add the main Python file
$buildCommand += "App.py"

# Execute the build command
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
$commandString = $buildCommand -join " "
Invoke-Expression $commandString

# Check if build succeeded
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host "Build completed successfully! ($buildType)" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location: dist\Serial_monitor_" + $versionSuffix + "_x86-64.exe" -ForegroundColor Cyan
    Write-Host ""
    
    # Display file size
    if (Test-Path "dist\Serial_monitor_$versionSuffix_x86-64.exe") {
        $fileSize = (Get-Item "dist\Serial_monitor_$versionSuffix_x86-64.exe").Length / 1MB
        Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow
        Write-Host ""
        
        if ($BuildMode -eq 'debug') {
            Write-Host "Debug build notes:" -ForegroundColor Yellow
            Write-Host "  - Console window will be visible for debugging" -ForegroundColor Gray
            Write-Host "  - Version suffix includes 'd' ($versionSuffix)" -ForegroundColor Gray
            Write-Host "  - Debug logging enabled in application" -ForegroundColor Gray
        } else {
            Write-Host "You can now distribute the .exe file independently." -ForegroundColor White
            Write-Host "Note: First run may create config directory in %APPDATA%\SerialCommunicationMonitor" -ForegroundColor Gray
        }
    }
} else {
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Red
    Write-Host "Build failed! Check the error messages above." -ForegroundColor Red
    Write-Host "=====================================================" -ForegroundColor Red
    exit 1
}
