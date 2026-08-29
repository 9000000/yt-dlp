"""
Module Khởi Chạy Trình Duyệt Web Độc Lập (Browser Launcher).
Chạy WebView2 trong tiến trình riêng (Subprocess) để tránh xung đột Main Thread với Tkinter GUI.
"""

import sys
import os

def launch(url: str = "https://www.youtube.com"):
    try:
        import webview
        window = webview.create_window(
            title="ToolDL Pro - Trình Duyệt Web & Xem Video (Edge Chromium)",
            url=url,
            width=1120,
            height=740,
            resizable=True
        )
        webview.start()
    except Exception as e:
        import webbrowser
        webbrowser.open(url)

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com"
    launch(target_url)
