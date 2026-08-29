"""
Module Quản Lý Trình Duyệt Chromium (Edge WebView2) Nhúng Trực Tiếp Vào GUI.
- Nhúng cửa sổ Chromium Native vào trong khung Tkinter (WS_CHILD).
- Tự động co giãn 100% mượt mà khi phóng to toàn màn hình (Fullscreen/Maximize) hoặc thay đổi kích thước.
- Đồng bộ URL hai chiều và điều khiển chuyển trang.
"""

import os
import sys
import time
import json
import ctypes
import ctypes.wintypes
from pathlib import Path
import subprocess
import threading

class EmbeddedBrowserManager:
    """Quản lý tiến trình Chromium nhúng vào HWND cha của Tkinter Frame."""

    def __init__(self, parent_hwnd: int, initial_url: str = "https://www.youtube.com", app_dir: Path = None, doh_url: str = ""):
        self.parent_hwnd = parent_hwnd
        self.initial_url = initial_url
        self.app_dir = app_dir or Path(__file__).resolve().parent.parent
        self.doh_url = doh_url
        self.sync_url_file = self.app_dir / ".current_browser_url.txt"
        self.action_file = self.app_dir / ".browser_action.json"
        self.cmd_file = self.app_dir / ".browser_cmd.json"
        self.proc = None
        self._enum_cb = None

    def start(self, width: int = 1100, height: int = 650):
        # Thiết lập style WS_CLIPCHILDREN cho cửa sổ cha
        GWL_STYLE = -16
        WS_CLIPCHILDREN = 0x02000000
        cur_style = ctypes.windll.user32.GetWindowLongW(self.parent_hwnd, GWL_STYLE)
        ctypes.windll.user32.SetWindowLongW(self.parent_hwnd, GWL_STYLE, cur_style | WS_CLIPCHILDREN)

        # Khởi chạy tiến trình con chạy pywebview nhúng
        sub_code = f"""
import os
import webview
import time
import threading
import ctypes
import json
from pathlib import Path

p_hwnd = {self.parent_hwnd}
app_dir = Path(r'{self.app_dir}')
sync_file = app_dir / '.current_browser_url.txt'
cmd_file = app_dir / '.browser_cmd.json'
initial_url = r'{self.initial_url}'
doh_url = r'{self.doh_url}'

if doh_url:
    os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = f'--enable-features=DnsOverHttps --force-doh-template={{doh_url}}'

window = None
target_hwnd = None

def attach_and_sync():
    global window, target_hwnd
    # Đợi cửa sổ tạo xong
    for _ in range(20):
        time.sleep(0.15)
        target_title = 'ToolDL_Embedded_Chromium_Surface'
        hwnd = ctypes.windll.user32.FindWindowW(None, target_title)
        if hwnd:
            target_hwnd = hwnd
            break
    
    if target_hwnd and p_hwnd:
        GWL_STYLE = -16
        WS_CHILD = 0x40000000
        WS_VISIBLE = 0x10000000
        WS_POPUP = 0x80000000
        
        old_style = ctypes.windll.user32.GetWindowLongW(target_hwnd, GWL_STYLE)
        new_style = (old_style & ~WS_POPUP) | WS_CHILD | WS_VISIBLE
        ctypes.windll.user32.SetWindowLongW(target_hwnd, GWL_STYLE, new_style)
        ctypes.windll.user32.SetParent(target_hwnd, p_hwnd)
        ctypes.windll.user32.SetWindowPos(target_hwnd, 0, 0, 0, {width}, {height}, 0x0040 | 0x0020)

    last_cmd_time = 0
    while True:
        time.sleep(0.5)
        try:
            if window:
                cur = window.get_current_url()
                if cur:
                    with open(sync_file, 'w', encoding='utf-8') as f:
                        f.write(cur)
        except Exception:
            pass

        # Lắng nghe lệnh từ GUI (Navigate, Back, Forward, Reload, Resize)
        try:
            if cmd_file.exists():
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    cdata = json.load(f)
                ctime = cdata.get('time', 0)
                if ctime > last_cmd_time:
                    last_cmd_time = ctime
                    cmd = cdata.get('cmd')
                    arg = cdata.get('arg')
                    if cmd == 'navigate' and arg and window:
                        window.load_url(arg)
                    elif cmd == 'reload' and window:
                        window.evaluate_js('window.location.reload();')
                    elif cmd == 'back' and window:
                        window.evaluate_js('window.history.back();')
                    elif cmd == 'forward' and window:
                        window.evaluate_js('window.history.forward();')
                    elif cmd == 'resize' and window and isinstance(arg, dict):
                        w_val = arg.get('w', {width})
                        h_val = arg.get('h', {height})
                        window.resize(w_val, h_val)
                        if target_hwnd:
                            ctypes.windll.user32.SetWindowPos(target_hwnd, 0, 0, 0, w_val, h_val, 0x0004 | 0x0010 | 0x0040)
        except Exception:
            pass

threading.Thread(target=attach_and_sync, daemon=True).start()

window = webview.create_window(
    'ToolDL_Embedded_Chromium_Surface',
    url=initial_url,
    width={width},
    height={height},
    frameless=True
)
webview.start()
"""
        self.proc = subprocess.Popen([sys.executable, "-c", sub_code])

    def resize(self, width: int, height: int):
        """Thay đổi kích thước cửa sổ nhúng khi người dùng co giãn hoặc phóng to full màn hình."""
        if width <= 0 or height <= 0:
            return

        # 1. Gửi lệnh resize tới pywebview
        self.send_cmd("resize", {"w": width, "h": height})

        # 2. Resize trực tiếp tất cả HWND con bên trong parent_hwnd
        try:
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            def _enum_proc(hwnd, lparam):
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, width, height,
                    0x0004 | 0x0010 | 0x0040 # SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
                return True

            self._enum_cb = WNDENUMPROC(_enum_proc)
            ctypes.windll.user32.EnumChildWindows(self.parent_hwnd, self._enum_cb, 0)
        except Exception:
            pass

    def send_cmd(self, cmd: str, arg: any = ""):
        """Gửi lệnh điều khiển trình duyệt (navigate, reload, back, forward, resize)."""
        try:
            with open(self.cmd_file, "w", encoding="utf-8") as f:
                json.dump({"cmd": cmd, "arg": arg, "time": time.time()}, f)
        except Exception:
            pass

    def stop(self):
        """Dừng tiến trình Chromium nhúng."""
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None
