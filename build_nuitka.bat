@echo off
chcp 65001 >nul 2>&1
title ToolDL - Nuitka Non-Intrusive Builder
cls

python build_nuitka.py

pause
