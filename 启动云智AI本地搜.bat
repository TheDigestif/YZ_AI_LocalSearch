@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ====================================
echo   云智AI本地搜 v3.3 开源版
echo   Powered by 云感数字科技
echo   https://www.yungantech.com
echo ====================================
echo.
start "" "%~dp0python\python.exe" "%~dp0app\main.py"
