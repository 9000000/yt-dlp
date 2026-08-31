"""
Trình Duyệt Web Nhúng Trực Tiếp Trong Giao Diện GUI (Embedded WebView2 in Tkinter).
Tương thích ngược, chuyển tiếp sang module embedded_browser_manager.
"""

import sys
from tool_gui.embedded_browser_manager import run_embedded_browser

def run_embedded_webview(parent_hwnd: int, initial_url: str = "https://www.youtube.com", width: int = 800, height: int = 500, doh_url: str = "", app_dir: str = ""):
    run_embedded_browser(parent_hwnd, initial_url, width, height, doh_url, app_dir)

if __name__ == "__main__":
    p_hwnd = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    init_url = sys.argv[2] if len(sys.argv) > 2 else "https://www.youtube.com"
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 800
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 500
    run_embedded_webview(p_hwnd, init_url, w, h)

