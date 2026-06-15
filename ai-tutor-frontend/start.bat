@echo off
cd /d "%~dp0"
echo Installing dependencies...
call npm install
echo.
echo Starting AI Tutor Frontend...
start http://localhost:3000
npm run dev
pause
