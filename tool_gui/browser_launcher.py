"""
Module Khởi Chạy Trình Duyệt Web Độc Lập (Browser Launcher) Tích Hợp Thanh Công Cụ Quét Video Nổi.
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

# JavaScript & CSS tiêm thanh công cụ nổi đảm bảo hiển thị 100% trên mọi nền tảng
TOOLBAR_INJECTION_SCRIPT = r"""
(function() {
    try {
        if (document.getElementById('tooldl-floating-bar')) return;

        var target = document.body || document.documentElement;
        if (!target) return;

        var bar = document.createElement('div');
        bar.id = 'tooldl-floating-bar';
        bar.style.cssText = 'position:fixed !important; top:12px !important; left:50% !important; transform:translateX(-50%) !important; z-index:2147483647 !important; background:rgba(15, 23, 42, 0.95) !important; color:#FFFFFF !important; backdrop-filter:blur(16px) !important; padding:8px 18px !important; border-radius:35px !important; box-shadow:0 10px 35px rgba(0,0,0,0.8) !important; border:2px solid #38BDF8 !important; display:flex !important; align-items:center !important; gap:10px !important; font-family:"Segoe UI", Roboto, sans-serif !important; user-select:none !important;';

        bar.innerHTML = `
            <div style="display:flex; align-items:center; gap:6px; margin-right:4px;">
                <span style="font-size:16px;">🚀</span>
                <span style="color:#38BDF8; font-weight:800; font-size:13px; letter-spacing:0.5px;">ToolDL Pro</span>
            </div>
            <button id="tooldl-btn-scan" style="background:#10B981; color:white; border:none; padding:7px 15px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; display:flex; align-items:center; gap:4px; box-shadow:0 2px 8px rgba(0,0,0,0.3);">
                🔍 Quét Video Trang Này
            </button>
            <button id="tooldl-btn-dl" style="background:#3B82F6; color:white; border:none; padding:7px 15px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; display:flex; align-items:center; gap:4px; box-shadow:0 2px 8px rgba(0,0,0,0.3);">
                ⚡ Tải Video Đang Xem
            </button>
            <button id="tooldl-btn-copy" style="background:#334155; color:#F8FAFC; border:none; padding:7px 13px; border-radius:20px; font-size:12px; cursor:pointer;">
                📋 Copy Link
            </button>
            <button id="tooldl-btn-close" style="background:transparent; color:#94A3B8; border:none; padding:4px 6px; font-size:14px; cursor:pointer;" title="Ẩn thanh bar">
                ✖
            </button>
        `;

        target.appendChild(bar);

        // Sự kiện nút bấm
        var btnScan = document.getElementById('tooldl-btn-scan');
        if (btnScan) {
            btnScan.onclick = function() {
                var btn = this;
                btn.innerText = '⏳ Đang quét...';
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.scan_page(window.location.href).then(function() {
                        btn.innerText = '✅ Đã gửi sang Tool!';
                        setTimeout(function() { btn.innerText = '🔍 Quét Video Trang Này'; }, 2000);
                    });
                }
            };
        }

        var btnDl = document.getElementById('tooldl-btn-dl');
        if (btnDl) {
            btnDl.onclick = function() {
                var btn = this;
                btn.innerText = '⏳ Đang nạp...';
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.download_video(window.location.href).then(function() {
                        btn.innerText = '✅ Đã mở Tải Đơn!';
                        setTimeout(function() { btn.innerText = '⚡ Tải Video Đang Xem'; }, 2000);
                    });
                }
            };
        }

        var btnCopy = document.getElementById('tooldl-btn-copy');
        if (btnCopy) {
            btnCopy.onclick = function() {
                var btn = this;
                navigator.clipboard.writeText(window.location.href);
                btn.innerText = '✅ Đã chép!';
                setTimeout(function() { btn.innerText = '📋 Copy Link'; }, 1500);
            };
        }

        var btnClose = document.getElementById('tooldl-btn-close');
        if (btnClose) {
            btnClose.onclick = function() {
                bar.style.display = 'none';
            };
        }
    } catch(e) {
        console.error('ToolDL floating bar error:', e);
    }
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

        def _on_sync_loop():
            while True:
                time.sleep(1.0)
                try:
                    cur = window.get_current_url()
                    if cur:
                        with open(url_file, "w", encoding="utf-8") as f:
                            f.write(cur)
                    # Tiêm thanh công cụ nổi đảm bảo luôn hiển thị
                    window.evaluate_js(TOOLBAR_INJECTION_SCRIPT)
                except Exception:
                    break

        threading.Thread(target=_on_sync_loop, daemon=True).start()
        webview.start()

    except Exception as e:
        import webbrowser
        webbrowser.open(url)

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com"
    launch(target_url)
