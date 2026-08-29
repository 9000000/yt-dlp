"""
Màn hình Cài Đặt & Bản Quyền (Settings & License View) - Bố Cục 2 Cột Tinh Gọn Xem Trọn Màn Hình.
"""

import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from pathlib import Path

from tool_gui.config import ConfigManager
from tool_gui.license_manager import LicenseManager

class SettingsView(ctk.CTkFrame):
    """Giao diện cài đặt và bản quyền tinh gọn."""

    def __init__(self, master, config_manager: ConfigManager, license_manager: LicenseManager, on_reauth_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.license_manager = license_manager
        self.on_reauth_callback = on_reauth_callback

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # Bố cục 2 Cột
        grid_cards = ctk.CTkFrame(main_container, fg_color="transparent")
        grid_cards.pack(fill="both", expand=True)
        grid_cards.grid_columnconfigure((0, 1), weight=1)
        grid_cards.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # 1. CỘT TRÁI: CÀI ĐẶT ỨNG DỤNG
        # =========================================================================
        left_card = ctk.CTkFrame(grid_cards, corner_radius=10)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        l_inner = ctk.CTkFrame(left_card, fg_color="transparent")
        l_inner.pack(fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(l_inner, text="⚙️ CÀI ĐẶT ỨNG DỤNG", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        # Giao diện Theme
        theme_row = ctk.CTkFrame(l_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(theme_row, text="Chế độ giao diện:", font=("Segoe UI", 11)).pack(side="left", padx=(0, 10))
        self.theme_combo = ctk.CTkComboBox(
            theme_row,
            values=["Tối (Dark Mode)", "Sáng (Light Mode)", "Theo hệ thống (System)"],
            command=self.on_theme_changed,
            height=28
        )
        self.theme_combo.pack(side="right", fill="x", expand=True)

        # Thư mục lưu
        ctk.CTkLabel(l_inner, text="Thư mục tải xuống mặc định:", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 2))
        dir_box = ctk.CTkFrame(l_inner, fg_color="transparent")
        dir_box.pack(fill="x", pady=(0, 8))

        self.dir_entry = ctk.CTkEntry(dir_box, font=("Segoe UI", 10), height=28)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        browse_btn = ctk.CTkButton(dir_box, text="📂 Duyệt", width=65, height=28, command=self.on_browse, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 10))
        browse_btn.pack(side="right")

        # Trình duyệt Cookie
        ctk.CTkLabel(l_inner, text="Nguồn Cookie xác thực:", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 2))
        self.cookie_combo = ctk.CTkComboBox(
            l_inner,
            values=["Không dùng Cookie", "Google Chrome", "Microsoft Edge", "Mozilla Firefox", "Brave Browser", "Opera", "Tệp Cookie (.txt)"],
            height=28
        )
        self.cookie_combo.pack(fill="x", pady=(0, 10))

        # Checkboxes
        self.pot_cb = ctk.CTkCheckBox(l_inner, text="🛡️ Chống chặn YouTube (PO Token Provider)", font=("Segoe UI", 11))
        self.pot_cb.select()
        self.pot_cb.pack(anchor="w", pady=(0, 6))

        self.clip_cb = ctk.CTkCheckBox(l_inner, text="Tự động bắt link Clipboard", font=("Segoe UI", 11))
        self.clip_cb.pack(anchor="w", pady=(0, 12))

        # Nút Lưu Cài Đặt
        save_btn = ctk.CTkButton(
            l_inner,
            text="💾 LƯU CÀI ĐẶT",
            height=36,
            command=self.save_settings,
            font=("Segoe UI", 12, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        save_btn.pack(fill="x")

        # =========================================================================
        # 2. CỘT PHẢI: THÔNG TIN BẢN QUYỀN & MÁY CHỦ
        # =========================================================================
        right_card = ctk.CTkFrame(grid_cards, corner_radius=10)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        r_inner = ctk.CTkFrame(right_card, fg_color="transparent")
        r_inner.pack(fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(r_inner, text="🔐 THÔNG TIN BẢN QUYỀN", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        lic_info_box = ctk.CTkFrame(r_inner, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
        lic_info_box.pack(fill="x", pady=(0, 12))

        lic_inner = ctk.CTkFrame(lic_info_box, fg_color="transparent")
        lic_inner.pack(fill="x", padx=12, pady=10)

        self.lic_status_lbl = ctk.CTkLabel(lic_inner, text="Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", font=("Segoe UI", 11, "bold"), text_color="#10B981")
        self.lic_status_lbl.pack(anchor="w", pady=(0, 4))

        self.lic_exp_lbl = ctk.CTkLabel(lic_inner, text="Hạn sử dụng: Vĩnh viễn (Lifetime)", font=("Segoe UI", 10))
        self.lic_exp_lbl.pack(anchor="w", pady=(0, 4))

        self.lic_m_lbl = ctk.CTkLabel(lic_inner, text=f"Mã thiết bị: {self.license_manager.get_machine_id()}", font=("Consolas", 10), text_color=("#64748B", "#94A3B8"))
        self.lic_m_lbl.pack(anchor="w")

        # Khung đổi key
        rekey_box = ctk.CTkFrame(r_inner, fg_color="transparent")
        rekey_box.pack(fill="x", pady=(0, 10))

        rekey_btn = ctk.CTkButton(
            rekey_box,
            text="🔑 Đổi License Key Mới",
            height=34,
            command=self.on_change_key,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 11, "bold")
        )
        rekey_btn.pack(fill="x")

        # Ghi chú hỗ trợ
        note_box = ctk.CTkFrame(r_inner, fg_color=("#F1F5F9", "#0F172A"), corner_radius=8)
        note_box.pack(fill="both", expand=True)

        note_inner = ctk.CTkFrame(note_box, fg_color="transparent")
        note_inner.pack(fill="both", expand=True, padx=10, pady=8)

        ctk.CTkLabel(note_inner, text="💡 Ghi chú hỗ trợ:", font=("Segoe UI", 10, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            note_inner,
            text="• Bản quyền gắn cố định theo Mã thiết bị phần cứng.\n• Đã nhúng sẵn FFmpeg mới nhất trong thư mục bin/.\n• Chế độ PO Token tự động giúp chống chặn YouTube.",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            text_color=("#64748B", "#94A3B8")
        ).pack(anchor="w")

    def load_settings(self):
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
        valid, msg, lic_data = self.license_manager.check_license()
        if valid and lic_data:
            exp_text = lic_data.get("expires_str", "Vĩnh viễn (Lifetime)")
            self.lic_status_lbl.configure(text=f"Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", text_color="#10B981")
            self.lic_exp_lbl.configure(text=f"Hạn sử dụng: {exp_text}")
        else:
            self.lic_status_lbl.configure(text="Trạng thái: 🔴 Chưa kích hoạt hoặc Key hết hạn", text_color="#EF4444")
            self.lic_exp_lbl.configure(text="Hạn sử dụng: --")

    def on_theme_changed(self, choice):
        theme_map_rev = {"Tối (Dark Mode)": "dark", "Sáng (Light Mode)": "light", "Theo hệ thống (System)": "system"}
        mode = theme_map_rev.get(choice, "dark")
        ctk.set_appearance_mode(mode)
        self.config_manager.set("theme", mode)

    def on_browse(self):
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)

    def save_settings(self):
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
        ans = msgbox.askyesno("Xác nhận", "Bạn có chắc chắn muốn gỡ License Key hiện tại để nhập Key mới?")
        if ans:
            self.license_manager.deactivate()
            if self.on_reauth_callback:
                self.on_reauth_callback()
