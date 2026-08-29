@echo off
chcp 65001 >nul
title Đóng gói ToolDL Pro Portable ZIP

echo ========================================================
echo   Đang chuẩn bị đóng gói ToolDL Pro thành bản Portable ZIP...
echo ========================================================

python "%~dp0build_portable.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Lỗi] Quá trình đóng gói gặp lỗi!
) else (
    echo.
    echo [Thành công] Đã tạo file ToolDL_Portable.zip trong thư mục dist/
)

pause
