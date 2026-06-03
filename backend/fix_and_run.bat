@echo off
echo ========================================
echo  PDF RAG Chat - Backend Setup & Run
echo ========================================
echo.

echo Step 1: Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo.
echo Step 2: Fixing NumPy version...
pip uninstall numpy -y
pip install "numpy<2.0"

echo.
echo Step 3: Installing dependencies...
pip install -r requirements.txt

echo.
echo Step 4: Starting backend server...
echo Backend will run on http://localhost:8000
echo Press Ctrl+C to stop
echo.
uvicorn main:app --reload
