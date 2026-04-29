@echo off
echo Adding richer sample data...
cd /d "C:\Users\Dell\Cursor1"
git add -A
git commit -m "Add 30 sample restaurants across Bangalore neighborhoods for Streamlit Cloud"
echo.
echo Pushing to GitHub...
git push origin master
echo.
echo Done! Press any key to close.
pause > nul
