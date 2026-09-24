@echo off
title Auto Push to GitHub - Nayumi
cd /d "%~dp0"
echo ==============================================
echo   Pushing latest changes to GitHub...
echo ==============================================
git add .
git commit -m "Auto update: %date% %time%"
git push origin main
echo.
echo ==============================================
echo   Changes pushed successfully!
echo   Ab hosting panel pe jaake Restart dabao.
echo ==============================================
pause
