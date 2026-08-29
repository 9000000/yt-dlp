"""
Module Khởi Chạy Trình Duyệt Web Độc Lập (Browser Launcher) Tích Hợp Thanh Công Cụ Quét Video.
Chạy Edge WebView2 với thanh công cụ ToolDL Bar nổi trên đầu trang web:
- Nút 🔍 Quét Video Trang Này
- Nút ⚡ Tải Video Đang Xem
- Nút 📋 Copy Link
Tự động đồng bộ và kích hoạt tác vụ trên ToolDL Pro ngay lập tức.
"""

import sys
import os
import time
import json
import threading
from pathlib import Path

# JavaScript & CSS tiêm thanh công cụ nổi vào mọi trang web
TOOLBAR_INJECTION_SCRIPT = r"""
(function() {
    function injectToolbar() {
        if (document.getElementById('tooldl-floating-toolbar')) return;

        var bar = document.createElement('div');
        bar.id = 'tooldl-floating-toolbar';
        bar.style.cssText = 'position:fixed; top:12px; left:50%; transform:translateX(-50%); z-index:2147483647; background:rgba(15, 23, 42, 0.95); backdrop-filter:blur(16px); padding:8px 18px; border-radius:35px; box-shadow:0 10px 35px rgba(0,0,0,0.6); border:1.5px solid rgba(56, 189, 248, 0.35); display:flex; align-items:center; gap:10px; font-family:"Segoe UI", Tahoma, sans-serif; user-select:none; animation:tooldlFadeIn 0.3s ease-out;';

        var style = document.createElement('style');
        style.innerHTML = `
            @keyframes tooldlFadeIn { from { opacity: 0; transform: translate(-50%, -20px); } to { opacity: 1; transform: translate(-50%, 0); } }
            .tooldl-btn { border:none; padding:7px 15px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; display:flex; align-items:center; gap:5px; transition:all 0.2s ease; box-shadow:0 2px 8px rgba(0,0,0,0.3); }
            .tooldl-btn:hover { transform:translateY(-1px); filter:brightness(1.15); box-shadow:0 4px 12px rgba(0,0,0,0.4); }
            .tooldl-btn:active { transform:translateY(1px); }
        `;
        document.head.appendChild(style);

        bar.innerHTML = `
            <div style="display:flex; align-items:center; gap:6px; margin-right:4px;">
                <span style="font-size:15px;">🚀</span>
                <span style="color:#38BDF8; font-weight:800; font-size:13px; letter-spacing:0.5px;">ToolDL Pro</span>
            </div>
            <button id="tooldl-btn-scan" class="tooldl-btn" style="background:linear-gradient(135deg, #10B981, #059669); color:white;">
                🔍 Quét Video Trang Này
            </button>
            <button id="tooldl-btn-dl" class="tooldl-btn" style="background:linear-gradient(135deg, #3B82F6, #2563EB); color:white;">
                ⚡ Tải Video Đang Xem
            </button>
            <button id="tooldl-btn-copy" class="tooldl-btn" style="background:#334155; color:#F8FAFC;">
                📋 Copy Link
            </button>
            <button id="tooldl-btn-min" style="background:transparent; color:#94A3B8; border:none; padding:4px 6px; font-size:14px; cursor:pointer; border-radius:50%; transition:0.2s;" title="Ẩn/Hiện">
                ✖
            </button>
        `;

        document.body.appendChild(bar);

        // Xử lý sự kiện click
        document.getElementById('tooldl-btn-scan').onclick = function() {
            var btn = this;
            btn.innerHTML = '⏳ Đang quét...';
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.scan_page(window.location.href).then(function() {
                    btn.innerHTML = '✅ Đã gửi sang Tool!';
                    setTimeout(function() { btn.innerHTML = '🔍 Quét Video Trang Này'; }, 2000);
                });
            }
        };

        document.getElementById('tooldl-btn-dl').onclick = function() {
            var btn = this;
            btn.innerHTML = '⏳ Đang nạp...';
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.download_video(window.location.href).then(function() {
                    btn.innerHTML = '✅ Đã mở Tải Đơn!';
                    setTimeout(function() { btn.innerHTML = '⚡ Tải Video Đang Xem'; }, 2000);
                });
            }
        };

        document.getElementById('tooldl-btn-copy').onclick = function() {
            var btn = this;
            navigator.clipboard.writeText(window.location.href);
            btn.innerHTML = '✅ Đã chép!';
            setTimeout(function() { btn.innerHTML = '📋 Copy Link'; }, 1500);
        };

        document.getElementById('tooldl-btn-min').onclick = function() {
            bar.style.display = 'none';
        };
    }

    // Tiêm thanh công cụ
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        injectToolbar();
    } else {
        document.addEventListener('DOMContentLoaded', injectToolbar);
    }
    window.addEventListener('load', injectToolbar);
    // Theo dõi thay đổi DOM cho SPA (YouTube/TikTok navigation)
    setInterval(injectToolbar, 2000);
})();
"""

class BrowserAPI:
    """API giao tiếp hai chiều giữa WebView2 JavaScript và ToolDL Python GUI."""

    def __init__(self, action_file: Path, url_file: Path):
        self.action_file = action_file
        self.url_file = url_file

    def scan_page(self, current_url: str):
        """Kích hoạt quét toàn bộ video trên trang từ thanh bar trình duyệt."""
        try:
            with open(self.action_file, "w", encoding="utf-8") as f:
                json.dump({"action": "scan", "url": current_url, "time": time.time()}, f)
            with open(self.url_file, "w", encoding="utf-8") as f:
                f.write(current_url)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    def download_video(self, current_url: str):
        """Kích hoạt tải video đang xem từ thanh bar trình duyệt."""
        try:
            with open(self.action_file, "w", encoding="utf-8") as f:
                json.dump({"action": "download", "url": current_url, "time": time.time()}, f)
            with open(self.url_file, "w", encoding="utf-8") as f:
                f.write(current_url)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "msg": str(e)}

def launch(url: str = "https://www.youtube.com"):
    try:
        import webview
        app_dir = Path(__file__).resolve().parent.parent
        url_file = app_dir / ".current_browser_url.txt"
        action_file = app_dir / ".browser_action.json"

        # Ghi URL ban đầu
        try:
            with open(url_file, "w", encoding="utf-8") as f:
                f.write(url)
        except Exception:
            pass

        api = BrowserAPI(action_file, url_file)

        window = webview.create_window(
            title="ToolDL Pro - Trình Duyệt Web & Xem Video (Edge Chromium)",
            url=url,
            width=1180,
            height=780,
            js_api=api,
            resizable=True
        )

        def _on_loaded():
            while True:
                time.sleep(1.2)
                try:
                    cur = window.get_current_url()
                    if cur:
                        with open(url_file, "w", encoding="utf-8") as f:
                            f.write(cur)
                    # Tiêm thanh Toolbar vào trang
                    window.evaluate_js(TOOLBAR_INJECTION_SCRIPT)
                except Exception:
                    break

        threading.Thread(target=_on_loaded, daemon=True).start()
        webview.start()

    except Exception as e:
        import webbrowser
        webbrowser.open(url)

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com"
    launch(target_url)
