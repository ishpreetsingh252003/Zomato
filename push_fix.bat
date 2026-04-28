@echo off
echo Adding fix...
cd /d "C:\Users\Dell\Cursor1"
git add -A
git commit -m "Fix: use sample restaurants when full dataset is missing on Streamlit Cloud"
echo.
echo Pushing to GitHub...
git push origin master
echo.
echo Done! Press any key to close.
pause > nul
