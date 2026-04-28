@echo off
echo Finishing the unfinished merge...
cd /d "C:\Users\Dell\Cursor1"
git commit -m "Merge remote changes"
echo.
echo Pushing to GitHub...
git push origin master
echo.
echo Done! Press any key to close.
pause > nul
