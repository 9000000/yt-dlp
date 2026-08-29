"""
Màn hình Cài Đặt & Bản Quyền (Settings & License View).
Tùy chỉnh giao diện, thư mục, cookies trình duyệt và quản lý bản quyền 100% Tiếng Việt.
"""

import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from pathlib import Path

from tool_gui.config import ConfigManager
from tool_gui.license_manager import LicenseManager

class SettingsView(ctk.CTkFrame):
    """Giao diện cài đặt và bản quyền."""

    def __init__(self, master, config_manager: ConfigManager, license_manager: LicenseManager, on_reauth_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.license_manager = license_manager
        self.on_reauth_callback = on_reauth_callback

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. THẺ CÀI ĐẶT CHUNG
        gen_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        gen_card.pack(fill="x", pady=(0, 15), padx=5)

        lbl_gen = ctk.CTkLabel(gen_card, text="⚙️ CÀI ĐẶT ỨNG DỤNG", font=("Segoe UI", 14, "bold"))
        lbl_gen.pack(anchor="w", padx=15, pady=(15, 10))

        # Giao diện Theme
        theme_row = ctk.CTkFrame(gen_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(theme_row, text="Chế độ giao diện:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 15))
        self.theme_combo = ctk.CTkComboBox(
            theme_row,
            values=["Tối (Dark Mode)", "Sáng (Light Mode)", "Theo hệ thống (System)"],
            command=self.on_theme_changed,
            width=200
        )
        self.theme_combo.pack(side="left")

        # Thư mục lưu
        dir_box = ctk.CTkFrame(gen_card, fg_color="transparent")
        dir_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(dir_box, text="Thư mục tải xuống mặc định:", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 4))
        dir_inner = ctk.CTkFrame(dir_box, fg_color="transparent")
        dir_inner.pack(fill="x")

        self.dir_entry = ctk.CTkEntry(dir_inner, font=("Segoe UI", 11), height=34)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(dir_inner, text="📂 Duyệt...", width=100, height=34, command=self.on_browse, fg_color="#64748B", hover_color="#475569")
        browse_btn.pack(side="right")

        # Trình duyệt lấy Cookie
        cookie_box = ctk.CTkFrame(gen_card, fg_color="transparent")
        cookie_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(cookie_box, text="Trình duyệt trích xuất Cookie (dành cho video thành viên/hạn chế độ tuổi):", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 4))
        self.cookie_combo = ctk.CTkComboBox(
            cookie_box,
            values=["Không dùng Cookie", "Google Chrome", "Microsoft Edge", "Mozilla Firefox", "Brave Browser", "Opera", "Cốc Cốc / Chromium"],
            width=250
        )
        self.cookie_combo.pack(anchor="w")

        # Tùy chọn tự động bắt clipboard
        self.clip_cb = ctk.CTkCheckBox(gen_card, text="Tự động nhận diện đường dẫn khi sao chép (Clipboard Monitor)", font=("Segoe UI", 12))
        self.clip_cb.pack(anchor="w", padx=15, pady=(5, 15))

        # 2. THẺ THÔNG TIN BẢN QUYỀN
        lic_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        lic_card.pack(fill="x", pady=(0, 15), padx=5)

        lbl_lic = ctk.CTkLabel(lic_card, text="🔐 THÔNG TIN BẢN QUYỀN", font=("Segoe UI", 14, "bold"))
        lbl_lic.pack(anchor="w", padx=15, pady=(15, 10))

        lic_info_box = ctk.CTkFrame(lic_card, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
        lic_info_box.pack(fill="x", padx=15, pady=(0, 12))

        self.lic_status_lbl = ctk.CTkLabel(lic_info_box, text="Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", font=("Segoe UI", 12, "bold"), text_color="#10B981")
        self.lic_status_lbl.pack(anchor="w", padx=15, pady=(10, 4))

        self.lic_exp_lbl = ctk.CTkLabel(lic_info_box, text="Hạn sử dụng: Vĩnh viễn (Lifetime)", font=("Segoe UI", 11))
        self.lic_exp_lbl.pack(anchor="w", padx=15, pady=(0, 4))

        self.lic_m_lbl = ctk.CTkLabel(lic_info_box, text=f"Mã thiết bị: {self.license_manager.get_machine_id()}", font=("Consolas", 11), text_color=("#64748B", "#94A3B8"))
        self.lic_m_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Nút đổi key / hủy
        lic_btn_row = ctk.CTkFrame(lic_card, fg_color="transparent")
        lic_btn_row.pack(fill="x", padx=15, pady=(0, 15))

        change_key_btn = ctk.CTkButton(
            lic_btn_row,
            text="🔄 Đổi mã kích hoạt khác",
            command=self.on_change_key,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 12)
        )
        change_key_btn.pack(side="left", padx=(0, 10))

        deact_btn = ctk.CTkButton(
            lic_btn_row,
            text="❌ Hủy kích hoạt",
            command=self.on_deactivate,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Segoe UI", 12)
        )
        deact_btn.pack(side="left")

        # 3. NÚT LƯU CÀI ĐẶT
        save_btn = ctk.CTkButton(
            self.scroll,
            text="💾 LƯU THAY ĐỔI CÀI ĐẶT",
            height=42,
            command=self.save_settings,
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        save_btn.pack(fill="x", padx=5, pady=(0, 20))

    def load_settings(self):
        """Đọc cài đặt hiện tại đưa lên giao diện."""
        theme = self.config_manager.get("theme", "dark")
        theme_map = {"dark": "Tối (Dark Mode)", "light": "Sáng (Light Mode)", "system": "Theo hệ thống (System)"}
        self.theme_combo.set(theme_map.get(theme, "Tối (Dark Mode)"))

        self.dir_entry.delete(0, "end")
        self.dir_entry.insert(0, self.config_manager.get("download_dir"))

        if self.config_manager.get("auto_detect_clipboard", True):
            self.clip_cb.select()
        else:
            self.clip_cb.deselect()

        cookie_val = self.config_manager.get("browser_cookie", "none")
        cookie_map = {
            "none": "Không dùng Cookie",
            "chrome": "Google Chrome",
            "edge": "Microsoft Edge",
            "firefox": "Mozilla Firefox",
            "brave": "Brave Browser",
            "opera": "Opera",
            "chromium": "Cốc Cốc / Chromium"
        }
        self.cookie_combo.set(cookie_map.get(cookie_val, "Không dùng Cookie"))

        # Cập nhật thông tin bản quyền
        lic_info = self.license_manager.license_info
        if lic_info:
            exp_str = lic_info.get("expires_str", "Vĩnh viễn (Lifetime)")
            self.lic_status_lbl.configure(text="Trạng thái: 🟢 Đã kích hoạt bản quyền chính thức", text_color="#10B981")
            self.lic_exp_lbl.configure(text=f"Hạn sử dụng: {exp_str}")
        else:
            self.lic_status_lbl.configure(text="Trạng thái: ⚠️ Chưa kích hoạt", text_color="#EF4444")
            self.lic_exp_lbl.configure(text="Hạn sử dụng: Không có")

    def on_browse(self):
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)

    def on_theme_changed(self, choice):
        if "Tối" in choice:
            ctk.set_appearance_mode("dark")
        elif "Sáng" in choice:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("system")

    def save_settings(self):
        theme_str = "dark" if "Tối" in self.theme_combo.get() else ("light" if "Sáng" in self.theme_combo.get() else "system")
        dl_dir = self.dir_entry.get().strip()
        auto_clip = bool(self.clip_cb.get())
        
        cookie_text = self.cookie_combo.get()
        cookie_map_rev = {
            "Không dùng Cookie": "none",
            "Google Chrome": "chrome",
            "Microsoft Edge": "edge",
            "Mozilla Firefox": "firefox",
            "Brave Browser": "brave",
            "Opera": "opera",
            "Cốc Cốc / Chromium": "chromium"
        }
        cookie_val = cookie_map_rev.get(cookie_text, "none")

        self.config_manager.set("theme", theme_str)
        self.config_manager.set("download_dir", dl_dir)
        self.config_manager.set("auto_detect_clipboard", auto_clip)
        self.config_manager.set("browser_cookie", cookie_val)

        msgbox.showinfo("Thành công", "Đã lưu toàn bộ cài đặt thành công!")

    def on_change_key(self):
        if self.on_reauth_callback:
            self.on_reauth_callback()

    def on_deactivate(self):
        ans = msgbox.askyesno("Xác nhận", "Bạn có chắc chắn muốn hủy kích hoạt bản quyền trên máy này?")
        if ans:
            self.license_manager.deactivate()
            msgbox.showinfo("Thông báo", "Đã hủy kích hoạt bản quyền.")
            if self.on_reauth_callback:
                self.on_reauth_callback()
