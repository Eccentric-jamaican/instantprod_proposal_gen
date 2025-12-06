# Quick activation script for the virtual environment
# Usage: .\activate.ps1

Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "Virtual environment activated!" -ForegroundColor Green
Write-Host ""
Write-Host "Quick commands:" -ForegroundColor Cyan
Write-Host "  python verify_setup.py          - Verify environment setup" -ForegroundColor Yellow
Write-Host "  python execution/example_script.py --help  - See example script usage" -ForegroundColor Yellow
Write-Host "  deactivate                      - Exit virtual environment" -ForegroundColor Yellow
Write-Host ""
