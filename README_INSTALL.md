# Laboratory Management System - Installation Guide

## Current Status

✅ **Application EXE built successfully**
- Location: `dist\LaboratoryManagement.exe`
- Includes all dependencies and logo icon
- Ready to run on Windows systems

⚠️ **Installer requires Inno Setup**
- Inno Setup is not currently installed on this system
- To build the professional installer, install Inno Setup first

## Options for Distribution

### Option 1: Use the Pre-built EXE (Recommended for now)

The application EXE is ready to use:

1. Navigate to the `dist` folder
2. Copy `LaboratoryManagement.exe` to any location
3. Run the application directly

**For users:**
- Simply copy the `dist` folder to the target computer
- Run `LaboratoryManagement.exe`
- No installation required (portable application)

### Option 2: Build Professional Installer

To create a professional Windows installer with desktop shortcuts:

1. **Download and Install Inno Setup:**
   - Visit: https://jrsoftware.org/isdl.php
   - Download "Inno Setup 6" (recommended)
   - Run the installer with default settings

2. **Build the Installer:**
   - Run: `build_installer.ps1`
   - Or manually: `iscc installer_script.iss`
   - The installer will be created in the `Output` folder

3. **Installer Features:**
   - Installs to Program Files
   - Creates desktop shortcut
   - Creates Start Menu entry
   - Includes uninstaller
   - Uses logo as installer icon
   - Russian and English language support

### Option 3: Manual Installation Script

For users without admin rights or for portable deployment:

```batch
@echo off
REM Manual Installation Script
echo Installing Laboratory Management System...
mkdir "%USERPROFILE%\LaboratoryManagement" 2>nul
copy "LaboratoryManagement.exe" "%USERPROFILE%\LaboratoryManagement\"
echo Installation complete!
echo Application location: %USERPROFILE%\LaboratoryManagement
pause
```

## File Structure

```
dist/
└── LaboratoryManagement.exe    # Main application (ready to use)

img/
├── logo.png                     # Original logo
└── logo.ico                     # Icon for Windows

installer_script.iss             # Inno Setup script (requires Inno Setup)
build_installer.ps1              # PowerShell build script
```

## Application Features

- ✅ Patient management
- ✅ Treatment tracking
- ✅ Statistics and reports
- ✅ Export to Excel and PDF
- ✅ Import from Excel and CSV
- ✅ Backup functionality
- ✅ Multi-language support (Russian/Tajik)
- ✅ Modern UI with dark/light themes

## System Requirements

- Windows 7 or later
- 2GB RAM minimum
- 100MB free disk space
- No additional dependencies required

## Support

For issues or questions, contact the development team.
