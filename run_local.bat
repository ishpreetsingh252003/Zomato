@echo off
echo Checking if Streamlit is installed...
cd /d "C:\Users\Dell\Cursor1"
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Streamlit not found. Installing requirements...
    pip install -r "Zomato\architecture\phase_7_deployment\requirements.txt"
) else (
    echo Streamlit is already installed.
)
echo.
echo Starting the app...
python -m streamlit run "Zomato\architecture\phase_7_deployment\app.py"
pause
