Write-Host "========================================" -ForegroundColor Cyan
Write-Host " PDF RAG Chat - Backend Setup & Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & venv\Scripts\Activate.ps1
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & venv\Scripts\Activate.ps1
}

Write-Host ""
Write-Host "Step 2: Fixing NumPy version..." -ForegroundColor Yellow
pip uninstall numpy -y
pip install "numpy<2.0"

Write-Host ""
Write-Host "Step 3: Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Step 4: Starting backend server..." -ForegroundColor Green
Write-Host "Backend will run on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
uvicorn main:app --reload
