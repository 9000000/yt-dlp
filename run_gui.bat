@echo off
chcp 65001 >nul
title ToolDL Pro - Trình Tải Video Đa Nền Tảng

echo ========================================================
echo   Dang khoi chay ToolDL Pro (GUI)...
echo ========================================================

python "%~dp0run_gui.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Loi] Co loi xay ra khi chay chuong trinh!
    pause
)
