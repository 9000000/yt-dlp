"""
Điểm khởi chạy ứng dụng ToolDL (Main Entry Point).
Khởi động giao diện người dùng đồ họa (GUI).
"""

import sys
import os
from pathlib import Path

# Thêm thư mục hiện tại vào sys.path để nhận diện package yt_dlp và tool_gui
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Đảm bảo UTF-8 output trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tool_gui.app import ToolDLApp

def main():
    print("=" * 60)
    print("   🚀 Đang khởi động ToolDL Pro - Trình Tải Video Đa Nền Tảng")
    print("=" * 60)
    app = ToolDLApp(app_dir=CURRENT_DIR)
    app.mainloop()

if __name__ == "__main__":
    main()
