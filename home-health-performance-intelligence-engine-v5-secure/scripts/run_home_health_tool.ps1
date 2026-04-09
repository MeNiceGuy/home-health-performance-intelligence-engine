Write-Host "" 
Write-Host "=== Home Health Innovation Decision Engine Launcher ===" 
Write-Host "" 

if (-not $env:OPENAI_API_KEY) {
    Write-Host "OPENAI_API_KEY is not set for this session." -ForegroundColor Yellow
    Write-Host 'Set it with: $env:OPENAI_API_KEY=$env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"' -ForegroundColor Yellow
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Running Python engine..." -ForegroundColor Cyan
python .\home_health_decision_engine.py
