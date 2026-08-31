"""
Điểm khởi chạy ứng dụng ToolDL (Main Entry Point).
Khởi động giao diện người dùng đồ họa (GUI) hoặc Trình duyệt Web nhúng/độc lập.
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

# Kiểm tra nếu chạy chế độ Trình duyệt nhúng trực tiếp vào HWND của GUI
if len(sys.argv) > 1 and sys.argv[1] == "--embedded-browser":
    from tool_gui.embedded_browser_manager import run_embedded_browser
    p_hwnd = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    init_url = sys.argv[3] if len(sys.argv) > 3 else "https://www.youtube.com"
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 1100
    h = int(sys.argv[5]) if len(sys.argv) > 5 else 650
    doh = sys.argv[6] if len(sys.argv) > 6 else ""
    a_dir = sys.argv[7] if len(sys.argv) > 7 else ""
    run_embedded_browser(p_hwnd, init_url, w, h, doh, a_dir)
    sys.exit(0)

# Kiểm tra nếu chạy chế độ Trình duyệt độc lập
if len(sys.argv) > 1 and sys.argv[1] == "--browser":
    from tool_gui.browser_launcher import launch
    target = sys.argv[2] if len(sys.argv) > 2 else "https://www.youtube.com"
    launch(target)
    sys.exit(0)

from tool_gui.app import ToolDLApp

def main():
    print("=" * 60)
    print("   🚀 Đang khởi động ToolDL Pro - Trình Tải Video Đa Nền Tảng")
    print("=" * 60)
    app = ToolDLApp(app_dir=CURRENT_DIR)
    app.mainloop()

if __name__ == "__main__":
    main()
