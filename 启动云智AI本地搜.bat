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

if exist "云智AI本地搜.exe" (
    echo 启动桌面应用...
    start "" "云智AI本地搜.exe"
) else (
    echo 未找到 exe，使用源码启动...
    start "" "python\python.exe" "app\main.py"
)
