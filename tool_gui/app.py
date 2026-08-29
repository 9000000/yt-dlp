"""
Cửa sổ Ứng dụng Chính (Main Application Window).
Không gian làm việc Hợp nhất Tất-Cả-Trong-Một: Tải Đơn, Tải Hàng Loạt, Quét Trang & Trình Duyệt Web 100% Tiếng Việt.
"""

import sys
import time
import threading
from pathlib import Path
import customtkinter as ctk

from tool_gui.config import ConfigManager
from tool_gui.license_manager import LicenseManager
from tool_gui.updater import UpdaterManager
from tool_gui.views.activation_view import ActivationView
from tool_gui.views.download_view import DownloadView
from tool_gui.views.tools_view import ToolsView
from tool_gui.views.settings_view import SettingsView
from tool_gui.views.log_view import LogView

class ToolDLApp(ctk.CTk):
    """Lớp cửa sổ chính của ToolDL."""

    def __init__(self, app_dir=None):
        super().__init__()

        # Khởi tạo quản lý
        self.config_manager = ConfigManager(app_dir)
        self.license_manager = LicenseManager(app_dir)
        self.updater_manager = UpdaterManager(app_dir)

        # Cấu hình Theme
        theme = self.config_manager.get("theme", "dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        # Cấu hình Cửa sổ
        self.title("ToolDL Pro - Trình Tải Video & Duyệt Web Hợp Nhất")
        self.geometry("1100x720")
        self.minsize(960, 620)

        # Trạng thái
        self.current_tab = None
        self.nav_buttons = {}
        self.last_clip_text = ""
        self._clip_thread_running = True

        # Giao diện chính
        self.setup_main_layout()

        # Kiểm tra bản quyền khi khởi động
        self.check_auth_and_render()

        # Bắt đầu luồng kiểm tra clipboard
        self.start_clipboard_monitor()

        # Kiểm tra phụ trợ khi khởi động
        self.check_startup_tools()

    def setup_main_layout(self):
        """Thiết lập khung sườn giao diện (Sidebar + Container)."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR ĐIỀU HƯỚNG BÊN TRÁI
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # Logo / Brand
        logo_lbl = ctk.CTkLabel(
            self.sidebar,
            text="🚀 ToolDL Pro",
            font=("Segoe UI", 20, "bold"),
            text_color=("#2563EB", "#38BDF8")
        )
        logo_lbl.grid(row=0, column=0, padx=20, pady=(20, 2), sticky="w")

        sub_logo = ctk.CTkLabel(
            self.sidebar,
            text="Tải Video & Trình Duyệt Web",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8")
        )
        sub_logo.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Các nút điều hướng tinh gọn (3 Mục Chính Hợp Nhất)
        nav_items = [
            ("download", "📥 Tải & Duyệt Video", self.show_download_view),
            ("settings", "⚙️ Cài Đặt & Phụ Trợ", self.show_settings_view),
            ("logs", "📜 Nhật Ký Hoạt Động", self.show_log_view),
        ]

        for i, (key, title, cmd) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=title,
                command=cmd,
                height=42,
                corner_radius=8,
                font=("Segoe UI", 13, "bold"),
                anchor="w",
                fg_color="transparent",
                text_color=("#334155", "#E2E8F0"),
                hover_color=("#E2E8F0", "#334155")
            )
            btn.grid(row=i + 2, column=0, padx=15, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Badge bản quyền ở chân sidebar
        self.lic_badge = ctk.CTkLabel(
            self.sidebar,
            text="🟢 Bản quyền: Đã kích hoạt",
            font=("Segoe UI", 11, "bold"),
            text_color="#10B981"
        )
        self.lic_badge.grid(row=7, column=0, padx=20, pady=(10, 15), sticky="w")

        # 2. KHUNG NỘI DUNG CHÍNH (CONTAINER BÊN PHẢI)
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Khởi tạo sẵn các Views
        self.log_view = LogView(self.container)
        self.download_view = DownloadView(self.container, self.config_manager, log_callback=self.log_view.append_log)
        self.settings_view = SettingsView(
            self.container,
            self.config_manager,
            self.license_manager,
            on_reauth_callback=self.show_activation_screen,
            log_callback=self.log_view.append_log
        )

        self.activation_view = ActivationView(
            self.container,
            self.license_manager,
            on_activated_callback=self.on_license_activated
        )

    def check_auth_and_render(self):
        """Kiểm tra bản quyền, nếu hợp lệ mở màn hình tải, nếu không mở màn hình kích hoạt."""
        is_valid, msg, details = self.license_manager.check_license()
        if is_valid and details:
            self.lic_badge.configure(text="🟢 Bản quyền: Đã kích hoạt", text_color="#10B981")
            self.show_download_view()
        else:
            self.show_activation_screen()

    def show_activation_screen(self):
        """Hiển thị màn hình kích hoạt bản quyền."""
        self.sidebar.grid_remove()
        self._hide_all_views()
        self.activation_view.grid(row=0, column=0, sticky="nsew")

    def on_license_activated(self):
        """Callback khi người dùng kích hoạt key thành công."""
        self.sidebar.grid()
        self.lic_badge.configure(text="🟢 Bản quyền: Đã kích hoạt", text_color="#10B981")
        self.settings_view.load_all_settings()
        self.show_download_view()

    def _hide_all_views(self):
        """Ẩn tất cả các view trong container."""
        for v in [
            self.activation_view,
            self.download_view,
            self.settings_view,
            self.log_view
        ]:
            v.grid_forget()

    def _set_active_nav(self, active_key: str):
        """Đổi màu nút đang active trên sidebar."""
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color="#3B82F6", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=("#334155", "#E2E8F0"))

    def show_download_view(self):
        self._hide_all_views()
        self._set_active_nav("download")
        self.download_view.grid(row=0, column=0, sticky="nsew")

    def show_tools_view(self):
        self.show_settings_view()
        self.settings_view.tabview.set("🛠️ Phụ Trợ & Cập Nhật")

    def show_settings_view(self):
        self._hide_all_views()
        self._set_active_nav("settings")
        self.settings_view.load_all_settings()
        self.settings_view.grid(row=0, column=0, sticky="nsew")

    def show_log_view(self):
        self._hide_all_views()
        self._set_active_nav("logs")
        self.log_view.grid(row=0, column=0, sticky="nsew")

    def start_clipboard_monitor(self):
        """Khởi động luồng theo dõi khay nhớ tạm (Clipboard)."""
        def _monitor():
            while self._clip_thread_running:
                try:
                    if self.config_manager.get("auto_detect_clipboard", True):
                        text = self.clipboard_get().strip()
                        if text and text != self.last_clip_text:
                            self.last_clip_text = text
                            self.after(0, lambda t=text: self.download_view.check_clipboard_url(t))
                except Exception:
                    pass
                time.sleep(1.0)

        threading.Thread(target=_monitor, daemon=True).start()

    def check_startup_tools(self):
        """Kiểm tra và ghi log trạng thái phụ trợ khi mở app."""
        if not self.updater_manager.is_ffmpeg_installed():
            self.log_view.append_log("[Cảnh báo] Chưa phát hiện FFmpeg trên máy. Vào tab 'Quản Lý Phụ Trợ' để cài đặt tự động.")
        else:
            ver = self.updater_manager.get_ffmpeg_version()
            self.log_view.append_log(f"[Hệ thống] FFmpeg đã sẵn sàng (Phiên bản: {ver}).")

    def destroy(self):
        self._clip_thread_running = False
        if hasattr(self, "download_view") and self.download_view and getattr(self.download_view, "browser_mgr", None):
            self.download_view.browser_mgr.stop()
        super().destroy()
