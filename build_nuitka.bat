@echo off
chcp 65001 > nul
title ToolDL - Nuitka Non-Intrusive Builder
cls

echo ================================================================
echo    🛡️  TRÌNH ĐÓNG GÓI & MÃ HÓA NUITKA (CÁCH LY ĐỘC LẬP)
echo    💡 100%% Không làm thay đổi bất kỳ file nào trong dự án gốc
echo ================================================================
echo.

python build_nuitka.py

pause
