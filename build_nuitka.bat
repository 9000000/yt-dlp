@echo off
chcp 65001 > nul
title ToolDL - Nuitka Obfuscator & Builder
cls

echo ================================================================
echo    🛡️  TRÌNH MÃ HÓA & ĐÓNG GÓI BẢO VỆ MÃ NGUỒN (NUITKA C++)
echo ================================================================
echo.

python build_nuitka.py

pause
