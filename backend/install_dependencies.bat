@echo off
echo ========================================
echo Installing Backend Dependencies
echo ========================================

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing/updating packages from requirements.txt...
pip install -r requirements.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run the backend with:
echo python main.py
echo.
pause
