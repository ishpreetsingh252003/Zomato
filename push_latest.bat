@echo off
echo Adding changes...
cd /d "C:\Users\Dell\Cursor1"
git add -A
git commit -m "Add Streamlit Secrets support for GROQ_API_KEY on cloud deployment"
echo.
echo Pushing to GitHub...
git push origin master
echo.
echo Done! Press any key to close.
pause > nul
