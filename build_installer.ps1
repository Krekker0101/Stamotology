# Build Script for Laboratory Management System Installer
# This script helps build the installer using PyInstaller

Write-Host "=== Laboratory Management System Installer Build ===" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Build the main application first so the installer packages the latest exe.
Write-Host "Building main application with PyInstaller..." -ForegroundColor Yellow
pyinstaller laboratory.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Main application build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Build the installer using PyInstaller
Write-Host ""
Write-Host "Building installer with PyInstaller..." -ForegroundColor Yellow
pyinstaller installer.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Installer built successfully!" -ForegroundColor Green
    Write-Host "Location: $(Join-Path $PSScriptRoot 'dist\LaboratoryManagementSetup.exe')" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Installer build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
