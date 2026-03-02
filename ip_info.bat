@echo off
chcp 65001 >nul
title IP Info
:again
cls
echo.
echo  ==========================================
echo   IP / Hostname Lookup
echo  ==========================================
echo.
set /p TARGET= Enter IP or hostname (or q to exit):
if /i "%TARGET%"=="q" exit /b
if "%TARGET%"=="" goto again
echo.
python "%~dp0ip_info.py" "%TARGET%"
echo.
pause
goto again
