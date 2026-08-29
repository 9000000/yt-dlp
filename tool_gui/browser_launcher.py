"""
Module Khởi Chạy Trình Duyệt Web Độc Lập (Browser Launcher).
Chạy Edge WebView2 trong tiến trình riêng (Subprocess) với đầy đủ hỗ trợ JavaScript/4K/Audio/Cookie
và tự động đồng bộ URL đang duyệt về ToolDL Pro.
"""

import sys
import os
import time
import threading
from pathlib import Path

def launch(url: str = "https://www.youtube.com"):
    try:
        import webview
        app_dir = Path(__file__).resolve().parent.parent
        url_file = app_dir / ".current_browser_url.txt"

        # Ghi URL ban đầu
        try:
            with open(url_file, "w", encoding="utf-8") as f:
                f.write(url)
        except Exception:
            pass

        window = webview.create_window(
            title="ToolDL Pro - Trình Duyệt Web & Xem Video (Edge Chromium)",
            url=url,
            width=1160,
            height=760,
            resizable=True
        )

        def _sync_worker():
            while True:
                time.sleep(1.0)
                try:
                    cur = window.get_current_url()
                    if cur:
                        with open(url_file, "w", encoding="utf-8") as f:
                            f.write(cur)
                except Exception:
                    break

        threading.Thread(target=_sync_worker, daemon=True).start()
        webview.start()

    except Exception as e:
        import webbrowser
        webbrowser.open(url)

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com"
    launch(target_url)
