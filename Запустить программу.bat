@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m cycle_project web
) else (
  python -m cycle_project web
)
if errorlevel 1 echo Установите Python 3.10 или новее. При установке включите Add Python to PATH.
pause
