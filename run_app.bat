@echo off
echo ============================================
echo   Football Match Visualizer
echo   Streamlit App Launcher
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if streamlit is installed
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Streamlit not installed!
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting Streamlit app...
echo App will open in your default browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

REM Run streamlit
streamlit run streamlit_app.py

pause
