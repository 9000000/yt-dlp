"""
Màn hình Cài Đặt & Bản Quyền (Settings & License View).
Tùy chỉnh giao diện, thư mục, cookies trình duyệt, cơ chế chống chặn YouTube Botguard và quản lý bản quyền 100% Tiếng Việt.
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
            values=["Không dùng Cookie", "Google Chrome", "Microsoft Edge", "Mozilla Firefox", "Brave Browser", "Opera", "Tệp Cookie (.txt)"],
            width=250
        )
        self.cookie_combo.pack(anchor="w")

        # Tùy chọn chống chặn YouTube Botguard / PO Token
        self.pot_cb = ctk.CTkCheckBox(gen_card, text="🛡️ Bật chế độ Chống Chặn YouTube (Botguard / PO Token Provider)", font=("Segoe UI", 12))
        self.pot_cb.select()
        self.pot_cb.pack(anchor="w", padx=15, pady=(5, 5))

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

        rekey_btn = ctk.CTkButton(lic_btn_row, text="🔑 Đổi License Key Mới", height=36, command=self.on_change_key, fg_color="#3B82F6", hover_color="#2563EB")
        rekey_btn.pack(side="left", padx=(0, 10))

        # 3. NÚT LƯU CÀI ĐẶT
        save_btn = ctk.CTkButton(
            self.scroll,
            text="💾 LƯU CÀI ĐẶT",
            height=44,
            command=self.save_settings,
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        save_btn.pack(fill="x", pady=10, padx=5)

    def load_settings(self):
        """Tải các thiết lập từ config.json."""
        theme_map = {"dark": "Tối (Dark Mode)", "light": "Sáng (Light Mode)", "system": "Theo hệ thống (System)"}
        t = self.config_manager.get("theme", "dark")
        self.theme_combo.set(theme_map.get(t, "Tối (Dark Mode)"))

        self.dir_entry.delete(0, "end")
        self.dir_entry.insert(0, self.config_manager.get("download_dir", ""))

        cookie_map = {
            "none": "Không dùng Cookie",
            "chrome": "Google Chrome",
            "edge": "Microsoft Edge",
            "firefox": "Mozilla Firefox",
            "brave": "Brave Browser",
            "opera": "Opera",
            "file": "Tệp Cookie (.txt)"
        }
        b = self.config_manager.get("browser_cookie", "none")
        self.cookie_combo.set(cookie_map.get(b, "Không dùng Cookie"))

        if self.config_manager.get("youtube_pot_enabled", True):
            self.pot_cb.select()
        else:
            self.pot_cb.deselect()

        if self.config_manager.get("auto_detect_clipboard", True):
            self.clip_cb.select()
        else:
            self.clip_cb.deselect()

        self.refresh_license_display()

    def refresh_license_display(self):
        """Cập nhật thông tin bản quyền trên giao diện."""
        valid, msg, lic_data = self.license_manager.check_license()
        if valid and lic_data:
            exp_text = lic_data.get("expires_str", "Vĩnh viễn (Lifetime)")
            self.lic_status_lbl.configure(text=f"Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", text_color="#10B981")
            self.lic_exp_lbl.configure(text=f"Hạn sử dụng: {exp_text}")
        else:
            self.lic_status_lbl.configure(text="Trạng thái: 🔴 Chưa kích hoạt hoặc Key hết hạn", text_color="#EF4444")
            self.lic_exp_lbl.configure(text="Hạn sử dụng: --")

    def on_theme_changed(self, choice):
        """Thay đổi chế độ nền ngay lập tức."""
        theme_map_rev = {"Tối (Dark Mode)": "dark", "Sáng (Light Mode)": "light", "Theo hệ thống (System)": "system"}
        mode = theme_map_rev.get(choice, "dark")
        ctk.set_appearance_mode(mode)
        self.config_manager.set("theme", mode)

    def on_browse(self):
        """Chọn thư mục."""
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)

    def save_settings(self):
        """Lưu toàn bộ cài đặt."""
        cookie_map_rev = {
            "Không dùng Cookie": "none",
            "Google Chrome": "chrome",
            "Microsoft Edge": "edge",
            "Mozilla Firefox": "firefox",
            "Brave Browser": "brave",
            "Opera": "opera",
            "Tệp Cookie (.txt)": "file"
        }
        b_val = cookie_map_rev.get(self.cookie_combo.get(), "none")

        self.config_manager.set("download_dir", self.dir_entry.get().strip())
        self.config_manager.set("browser_cookie", b_val)
        self.config_manager.set("youtube_pot_enabled", bool(self.pot_cb.get()))
        self.config_manager.set("auto_detect_clipboard", bool(self.clip_cb.get()))

        msgbox.showinfo("Thông báo", "Đã lưu cài đặt thành công!")

    def on_change_key(self):
        """Hủy key cũ và chuyển về màn hình nhập key mới."""
        ans = msgbox.askyesno("Xác nhận", "Bạn có chắc chắn muốn gỡ License Key hiện tại để nhập Key mới?")
        if ans:
            self.license_manager.deactivate()
            if self.on_reauth_callback:
                self.on_reauth_callback()
