@echo off
echo Changing to project folder...
cd /d "C:\Users\Dell\Cursor1"
echo.
echo Pulling latest changes from GitHub...
git pull origin master
echo.
echo Pushing local fix to GitHub...
git push origin master
echo.
echo Done! Press any key to close.
pause > nul
