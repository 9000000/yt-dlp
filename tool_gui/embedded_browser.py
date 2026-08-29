"""
Trình Duyệt Web Nhúng Trực Tiếp Trong Giao Diện GUI (Embedded WebView2 in Tkinter).
Sử dụng Win32 SetParent để nhúng cửa sổ Edge WebView2 trực tiếp vào khung Frame của CustomTkinter.
Tự động đồng bộ URL đang duyệt về tiến trình chính để phục vụ quét video tức thì.
"""

import sys
import os
import time
import ctypes
import json
from pathlib import Path

def run_embedded_webview(parent_hwnd: int, initial_url: str = "https://www.youtube.com", width: int = 800, height: int = 500):
    try:
        import webview

        # File lưu vết URL đang duyệt
        app_dir = Path(__file__).resolve().parent.parent
        url_sync_file = app_dir / ".current_browser_url.txt"

        def on_url_changed(new_url):
            try:
                with open(url_sync_file, "w", encoding="utf-8") as f:
                    f.write(new_url)
            except Exception:
                pass

        # Tạo cửa sổ webview với tiêu đề định danh
        unique_title = f"ToolDLEmbeddedBrowser_{os.getpid()}"
        window = webview.create_window(
            title=unique_title,
            url=initial_url,
            width=width,
            height=height,
            resizable=True
        )

        def on_embed_worker():
            time.sleep(0.3)
            # Tìm handle HWND của cửa sổ webview vừa tạo
            hwnd = ctypes.windll.user32.FindWindowW(None, unique_title)
            if hwnd and parent_hwnd:
                # Thiết lập thuộc tính WS_CHILD và gán cha là khung Tkinter
                GWL_STYLE = -16
                WS_CHILD = 0x40000000
                WS_VISIBLE = 0x10000000
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, WS_CHILD | WS_VISIBLE)
                ctypes.windll.user32.SetParent(hwnd, parent_hwnd)
                ctypes.windll.user32.MoveWindow(hwnd, 0, 0, width, height, True)

            # Lặp theo dõi URL hiện tại
            while True:
                time.sleep(1.0)
                try:
                    cur_url = window.get_current_url()
                    if cur_url:
                        on_url_changed(cur_url)
                except Exception:
                    break

        import threading
        threading.Thread(target=on_embed_worker, daemon=True).start()
        
        on_url_changed(initial_url)
        webview.start()

    except Exception as e:
        print(f"Lỗi khởi chạy Embedded WebView: {e}")

if __name__ == "__main__":
    p_hwnd = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    init_url = sys.argv[2] if len(sys.argv) > 2 else "https://www.youtube.com"
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 800
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 500
    run_embedded_webview(p_hwnd, init_url, w, h)
