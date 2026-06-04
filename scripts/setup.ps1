# SysAdmin AI Setup Script for Windows
# Run from project root: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

Write-Host "Setting up SysAdmin AI..." -ForegroundColor Cyan

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
} else {
    Write-Host "No requirements.txt found. Installing core packages..." -ForegroundColor Yellow
    pip install langchain langchain-community chromadb sentence-transformers
    pip install fastapi uvicorn pydantic python-dotenv psutil
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run the agent with: .\scripts\run.bat"
