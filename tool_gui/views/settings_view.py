"""
Màn hình Cài Đặt Chung & Quản Lý Phụ Trợ (Settings View).
Bao gồm:
1. ⚙️ Cài Đặt Chung & DNS Vượt Chặn Web
2. 🛠️ Quản Lý Phụ Trợ & Cập Nhật (FFmpeg & yt-dlp Core)
3. 🔐 Bản Quyền PRO & Máy Chủ
"""

import time
import socket
import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from pathlib import Path

from tool_gui.config import ConfigManager, DNS_PRESETS
from tool_gui.license_manager import LicenseManager
from tool_gui.updater import UpdaterManager

class SettingsView(ctk.CTkFrame):
    """Giao diện Cài đặt toàn diện tích hợp Quản lý Phụ trợ và Cấu hình DNS."""

    def __init__(self, master, config_manager: ConfigManager, license_manager: LicenseManager, on_reauth_callback=None, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.license_manager = license_manager
        self.on_reauth_callback = on_reauth_callback
        self.log_callback = log_callback
        self.updater = UpdaterManager()

        self.setup_ui()
        self.load_all_settings()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=12, pady=10)

        # Tabview Chính (3 Tab)
        self.tabview = ctk.CTkTabview(main_container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True)

        self.tab_general = self.tabview.add("⚙️ Cài Đặt Chung & DNS")
        self.tab_tools = self.tabview.add("🛠️ Phụ Trợ & Cập Nhật")
        self.tab_license = self.tabview.add("🔐 Bản Quyền PRO")

        # Thiết lập nội dung từng tab
        self._setup_tab_general()
        self._setup_tab_tools()
        self._setup_tab_license()

    # =========================================================================
    # TAB 1: CÀI ĐẶT CHUNG & DNS VƯỢT CHẶN
    # =========================================================================
    def _setup_tab_general(self):
        scroll = ctk.CTkScrollableFrame(self.tab_general, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=10)

        # 1. Khung Giao Diện & Thư Mục
        g_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        g_card.pack(fill="x", pady=(0, 10))

        g_inner = ctk.CTkFrame(g_card, fg_color="transparent")
        g_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(g_inner, text="🖥️ GIAO DIỆN & LƯU TRỮ", font=("Segoe UI", 13, "bold"), text_color=("#1D4ED8", "#60A5FA")).pack(anchor="w", pady=(0, 10))

        theme_row = ctk.CTkFrame(g_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(theme_row, text="Chế độ giao diện:", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=(0, 10))
        self.theme_combo = ctk.CTkComboBox(
            theme_row,
            values=["Tối (Dark Mode)", "Sáng (Light Mode)", "Theo hệ thống (System)"],
            command=self.on_theme_changed,
            height=32,
            font=("Segoe UI", 11)
        )
        self.theme_combo.pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(g_inner, text="Thư mục tải xuống mặc định:", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", pady=(4, 2))
        dir_box = ctk.CTkFrame(g_inner, fg_color="transparent")
        dir_box.pack(fill="x", pady=(0, 8))
        self.dir_entry = ctk.CTkEntry(dir_box, font=("Segoe UI", 11), height=32)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(dir_box, text="📂 Duyệt", width=75, height=32, command=self.on_browse, fg_color="#475569", hover_color="#334155", font=("Segoe UI", 11, "bold")).pack(side="right")

        ctk.CTkLabel(g_inner, text="Nguồn Cookie xác thực:", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", pady=(4, 2))
        self.cookie_combo = ctk.CTkComboBox(
            g_inner,
            values=["Không dùng Cookie", "Google Chrome", "Microsoft Edge", "Mozilla Firefox", "Brave Browser", "Opera", "Tệp Cookie (.txt)"],
            height=32,
            font=("Segoe UI", 11)
        )
        self.cookie_combo.pack(fill="x", pady=(0, 4))

        # 2. Khung Cấu hình DNS & Vượt chặn
        dns_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        dns_card.pack(fill="x", pady=(0, 10))

        dns_inner = ctk.CTkFrame(dns_card, fg_color="transparent")
        dns_inner.pack(fill="x", padx=16, pady=14)

        dns_hdr = ctk.CTkFrame(dns_inner, fg_color="transparent")
        dns_hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(dns_hdr, text="🌐 Cấu hình DNS & Vượt chặn Web (DoH):", font=("Segoe UI", 13, "bold"), text_color=("#1D4ED8", "#60A5FA")).pack(side="left")
        self.btn_test_dns = ctk.CTkButton(dns_hdr, text="⚡ Test DNS", width=90, height=28, command=self.on_test_dns, font=("Segoe UI", 10, "bold"), fg_color="#2563EB", hover_color="#1D4ED8")
        self.btn_test_dns.pack(side="right")

        self.dns_combo = ctk.CTkComboBox(
            dns_inner,
            values=[
                "🛡️ Cloudflare DNS (1.1.1.1 - Khuyên dùng vượt chặn)",
                "🚀 Google Public DNS (8.8.8.8, 8.8.4.4)",
                "🔒 Quad9 DNS (9.9.9.9 - Bảo mật cao)",
                "🛡️ AdGuard DNS (Chặn quảng cáo & Vượt chặn)",
                "✏️ Tùy chỉnh DNS (Custom IP / DoH)",
                "🌟 Mặc định hệ thống (ISP)"
            ],
            command=self.on_dns_choice_changed,
            height=32,
            font=("Segoe UI", 11)
        )
        self.dns_combo.pack(fill="x", pady=(0, 8))

        self.custom_dns_frame = ctk.CTkFrame(dns_inner, fg_color="transparent")
        ctk.CTkLabel(self.custom_dns_frame, text="DNS Servers (cách nhau dấu phẩy):", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.custom_dns_entry = ctk.CTkEntry(self.custom_dns_frame, placeholder_text="VD: 1.1.1.1, 1.0.0.1", height=30, font=("Consolas", 11))
        self.custom_dns_entry.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(self.custom_dns_frame, text="DoH URL (DNS over HTTPS):", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.custom_doh_entry = ctk.CTkEntry(self.custom_dns_frame, placeholder_text="VD: https://cloudflare-dns.com/dns-query", height=30, font=("Consolas", 11))
        self.custom_doh_entry.pack(fill="x")

        self.dns_test_lbl = ctk.CTkLabel(dns_inner, text="💡 DNS giúp truy cập các trang web/video bị nhà mạng ISP chặn.", font=("Segoe UI", 11), text_color=("#475569", "#94A3B8"), anchor="w")
        self.dns_test_lbl.pack(anchor="w", pady=(6, 0))

        # Checkboxes
        chk_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        chk_card.pack(fill="x", pady=(0, 10))
        chk_in = ctk.CTkFrame(chk_card, fg_color="transparent")
        chk_in.pack(fill="x", padx=16, pady=12)

        self.pot_cb = ctk.CTkCheckBox(chk_in, text="🛡️ Chống chặn YouTube (PO Token Provider)", font=("Segoe UI", 11, "bold"))
        self.pot_cb.select()
        self.pot_cb.pack(anchor="w", pady=(0, 8))

        self.clip_cb = ctk.CTkCheckBox(chk_in, text="📋 Tự động bắt liên kết từ Clipboard", font=("Segoe UI", 11, "bold"))
        self.clip_cb.pack(anchor="w")

        # Nút Lưu Cài Đặt Chung
        save_btn = ctk.CTkButton(
            scroll,
            text="💾 LƯU CÀI ĐẶT CHUNG",
            height=42,
            command=lambda: self.save_general_settings(show_dialog=True),
            font=("Segoe UI", 13, "bold"),
            fg_color="#059669",
            hover_color="#047857"
        )
        save_btn.pack(fill="x", pady=(6, 12))

    # =========================================================================
    # TAB 2: PHỤ TRỢ & CẬP NHẬT (FFMPEG & YT-DLP CORE)
    # =========================================================================
    def _setup_tab_tools(self):
        scroll = ctk.CTkScrollableFrame(self.tab_tools, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=10)

        # 1. THẺ FFMPEG
        ffmpeg_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        ffmpeg_card.pack(fill="x", pady=(0, 10))

        ff_inner = ctk.CTkFrame(ffmpeg_card, fg_color="transparent")
        ff_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(ff_inner, text="🎬 TRÌNH XỬ LÝ VIDEO & ÂM THANH (FFMPEG)", font=("Segoe UI", 13, "bold"), text_color=("#1D4ED8", "#60A5FA")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(ff_inner, text="FFmpeg là phụ trợ bắt buộc để ghép luồng Video 1080p/2K/4K với Audio chất lượng cao, trích xuất nhạc MP3/M4A và nhúng phụ đề.", font=("Segoe UI", 11), text_color=("#475569", "#94A3B8"), wraplength=640, justify="left").pack(anchor="w", pady=(0, 8))

        ff_info_box = ctk.CTkFrame(ff_inner, fg_color=("#EFF6FF", "#0F172A"), corner_radius=8, border_width=1, border_color=("#3B82F6", "#1D4ED8"))
        ff_info_box.pack(fill="x", pady=(0, 8))

        ff_info_in = ctk.CTkFrame(ff_info_box, fg_color="transparent")
        ff_info_in.pack(fill="x", padx=12, pady=10)

        self.ff_status_lbl = ctk.CTkLabel(ff_info_in, text="Trạng thái: Đang kiểm tra...", font=("Segoe UI", 12, "bold"))
        self.ff_status_lbl.pack(anchor="w", pady=(0, 2))
        self.ff_path_lbl = ctk.CTkLabel(ff_info_in, text="Đường dẫn: --", font=("Segoe UI", 11), text_color=("#475569", "#94A3B8"))
        self.ff_path_lbl.pack(anchor="w")

        self.ff_prog_lbl = ctk.CTkLabel(ff_inner, text="", font=("Segoe UI", 11))
        self.ff_prog_lbl.pack(anchor="w", pady=(0, 2))

        self.ff_prog_bar = ctk.CTkProgressBar(ff_inner, height=9, corner_radius=4)
        self.ff_prog_bar.set(0.0)
        self.ff_prog_bar.pack(fill="x", pady=(0, 8))
        self.ff_prog_bar.pack_forget()

        ff_btn_row = ctk.CTkFrame(ff_inner, fg_color="transparent")
        ff_btn_row.pack(fill="x")

        self.ff_install_btn = ctk.CTkButton(
            ff_btn_row,
            text="⬇️ TỰ ĐỘNG TẢI & CÀI ĐẶT FFMPEG",
            command=self.on_download_ffmpeg,
            height=36,
            font=("Segoe UI", 12, "bold"),
            fg_color="#059669",
            hover_color="#047857"
        )
        self.ff_install_btn.pack(side="left", padx=(0, 8))

        self.ff_refresh_btn = ctk.CTkButton(
            ff_btn_row,
            text="🔄 Kiểm tra lại",
            command=self.refresh_tools_status,
            width=120,
            height=36,
            font=("Segoe UI", 11, "bold"),
            fg_color="#475569",
            hover_color="#334155"
        )
        self.ff_refresh_btn.pack(side="left")

        # 2. THẺ YT-DLP CORE
        ytdlp_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        ytdlp_card.pack(fill="x", pady=(0, 10))

        yt_inner = ctk.CTkFrame(ytdlp_card, fg_color="transparent")
        yt_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(yt_inner, text="🚀 LÕI TẢI VIDEO ĐA NỀN TẢNG (YT-DLP CORE)", font=("Segoe UI", 13, "bold"), text_color=("#1D4ED8", "#60A5FA")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(yt_inner, text="Cập nhật yt-dlp thường xuyên giúp khắc phục các lỗi thay đổi API từ YouTube, TikTok, Facebook, Instagram.", font=("Segoe UI", 11), text_color=("#475569", "#94A3B8"), wraplength=640, justify="left").pack(anchor="w", pady=(0, 8))

        yt_info_box = ctk.CTkFrame(yt_inner, fg_color=("#EFF6FF", "#0F172A"), corner_radius=8, border_width=1, border_color=("#3B82F6", "#1D4ED8"))
        yt_info_box.pack(fill="x", pady=(0, 8))

        yt_info_in = ctk.CTkFrame(yt_info_box, fg_color="transparent")
        yt_info_in.pack(fill="x", padx=12, pady=10)

        self.yt_ver_lbl = ctk.CTkLabel(yt_info_in, text=f"Phiên bản yt-dlp hiện tại: {self.updater.get_ytdlp_version()}", font=("Segoe UI", 12, "bold"))
        self.yt_ver_lbl.pack(anchor="w", pady=(0, 2))
        self.yt_status_lbl = ctk.CTkLabel(yt_info_in, text="Trạng thái: Đang hoạt động bình thường", font=("Segoe UI", 11, "bold"), text_color="#10B981")
        self.yt_status_lbl.pack(anchor="w")

        self.yt_update_btn = ctk.CTkButton(
            yt_inner,
            text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP",
            command=self.on_update_ytdlp,
            height=36,
            font=("Segoe UI", 12, "bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8"
        )
        self.yt_update_btn.pack(anchor="w")

        # 3. Tự động kiểm tra
        auto_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        auto_card.pack(fill="x", pady=(0, 10))
        auto_in = ctk.CTkFrame(auto_card, fg_color="transparent")
        auto_in.pack(fill="x", padx=16, pady=12)

        self.auto_check_cb = ctk.CTkCheckBox(
            auto_in,
            text="Tự động kiểm tra và cập nhật phụ trợ khi khởi động phần mềm",
            font=("Segoe UI", 11, "bold"),
            command=self.on_toggle_auto_check
        )
        if self.config_manager.get("auto_check_updates", True):
            self.auto_check_cb.select()
        self.auto_check_cb.pack(anchor="w")

    # =========================================================================
    # TAB 3: BẢN QUYỀN PRO
    # =========================================================================
    def _setup_tab_license(self):
        scroll = ctk.CTkScrollableFrame(self.tab_license, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=10)

        lic_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        lic_card.pack(fill="x", pady=(0, 10))

        l_in = ctk.CTkFrame(lic_card, fg_color="transparent")
        l_in.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(l_in, text="🔐 THÔNG TIN BẢN QUYỀN PRO", font=("Segoe UI", 13, "bold"), text_color=("#1D4ED8", "#60A5FA")).pack(anchor="w", pady=(0, 8))

        lic_box = ctk.CTkFrame(l_in, fg_color=("#EFF6FF", "#0F172A"), corner_radius=8, border_width=1, border_color=("#3B82F6", "#1D4ED8"))
        lic_box.pack(fill="x", pady=(0, 10))

        lb_in = ctk.CTkFrame(lic_box, fg_color="transparent")
        lb_in.pack(fill="x", padx=14, pady=12)

        self.lic_status_lbl = ctk.CTkLabel(lb_in, text="Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", font=("Segoe UI", 12, "bold"), text_color="#10B981")
        self.lic_status_lbl.pack(anchor="w", pady=(0, 4))

        self.lic_exp_lbl = ctk.CTkLabel(lb_in, text="Hạn sử dụng: Vĩnh viễn (Lifetime)", font=("Segoe UI", 11, "bold"))
        self.lic_exp_lbl.pack(anchor="w", pady=(0, 4))

        self.lic_m_lbl = ctk.CTkLabel(lb_in, text=f"Mã thiết bị: {self.license_manager.get_machine_id()}", font=("Consolas", 11, "bold"), text_color=("#1D4ED8", "#60A5FA"))
        self.lic_m_lbl.pack(anchor="w")

        rekey_btn = ctk.CTkButton(
            l_in,
            text="🔑 Đổi License Key Mới",
            height=34,
            command=self.on_change_key,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 11, "bold")
        )
        rekey_btn.pack(fill="x", pady=(0, 8))

        note_box = ctk.CTkFrame(l_in, fg_color=("#F1F5F9", "#0F172A"), corner_radius=6)
        note_box.pack(fill="x")
        nb_in = ctk.CTkFrame(note_box, fg_color="transparent")
        nb_in.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(nb_in, text="💡 Ghi chú hỗ trợ:", font=("Segoe UI", 10, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            nb_in,
            text="• Bản quyền gắn cố định theo Mã thiết bị phần cứng.\n• Đã nhúng sẵn FFmpeg mới nhất trong thư mục bin/.\n• Tự động vượt chặn ISP qua Cloudflare DoH.",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            text_color=("#64748B", "#94A3B8")
        ).pack(anchor="w")

    # =========================================================================
    # CÁC HÀM XỬ LÝ DỮ LIỆU & SỰ KIỆN
    # =========================================================================
    def load_all_settings(self):
        # 1. Tab General
        theme_map = {"dark": "Tối (Dark Mode)", "light": "Sáng (Light Mode)", "system": "Theo hệ thống (System)"}
        t = self.config_manager.get("theme", "dark")
        self.theme_combo.set(theme_map.get(t, "Tối (Dark Mode)"))

        self.dir_entry.delete(0, "end")
        self.dir_entry.insert(0, self.config_manager.get("download_dir", ""))

        cookie_map = {
            "none": "Không dùng Cookie", "chrome": "Google Chrome", "edge": "Microsoft Edge",
            "firefox": "Mozilla Firefox", "brave": "Brave Browser", "opera": "Opera", "file": "Tệp Cookie (.txt)"
        }
        b = self.config_manager.get("browser_cookie", "none")
        self.cookie_combo.set(cookie_map.get(b, "Không dùng Cookie"))

        dns_prov = self.config_manager.get("dns_provider", "cloudflare")
        dns_map = {
            "cloudflare": "🛡️ Cloudflare DNS (1.1.1.1 - Khuyên dùng vượt chặn)",
            "google": "🚀 Google Public DNS (8.8.8.8, 8.8.4.4)",
            "quad9": "🔒 Quad9 DNS (9.9.9.9 - Bảo mật cao)",
            "adguard": "🛡️ AdGuard DNS (Chặn quảng cáo & Vượt chặn)",
            "custom": "✏️ Tùy chỉnh DNS (Custom IP / DoH)",
            "default": "🌟 Mặc định hệ thống (ISP)"
        }
        self.dns_combo.set(dns_map.get(dns_prov, "🛡️ Cloudflare DNS (1.1.1.1 - Khuyên dùng vượt chặn)"))
        self.custom_dns_entry.delete(0, "end")
        self.custom_dns_entry.insert(0, self.config_manager.get("custom_dns_servers", "1.1.1.1,1.0.0.1"))
        self.custom_doh_entry.delete(0, "end")
        self.custom_doh_entry.insert(0, self.config_manager.get("custom_doh_url", "https://cloudflare-dns.com/dns-query"))
        self.on_dns_choice_changed(self.dns_combo.get())

        if self.config_manager.get("youtube_pot_enabled", True):
            self.pot_cb.select()
        else:
            self.pot_cb.deselect()

        if self.config_manager.get("auto_detect_clipboard", True):
            self.clip_cb.select()
        else:
            self.clip_cb.deselect()

        # 2. Tab Tools
        self.refresh_tools_status()

        # 3. Tab License
        self.refresh_license_display()

    # --- Handlers Tab General ---
    def on_dns_choice_changed(self, choice):
        if "Tùy chỉnh" in choice:
            self.custom_dns_frame.pack(fill="x", pady=(2, 0))
        else:
            self.custom_dns_frame.pack_forget()

    def on_test_dns(self):
        self.btn_test_dns.configure(state="disabled", text="⏳ Test...")
        self.dns_test_lbl.configure(text="⏳ Đang kiểm tra phân giải tên miền...")

        def _test_worker():
            t0 = time.time()
            ok = False
            msg = ""
            try:
                ip = socket.gethostbyname("www.youtube.com")
                lat = int((time.time() - t0) * 1000)
                ok = True
                msg = f"✅ DNS hoạt động tốt! Độ trễ: {lat}ms (IP: {ip})"
            except Exception as e:
                msg = f"❌ Lỗi DNS: {e}"

            self.after(0, lambda: self._apply_dns_test_result(ok, msg))

        threading.Thread(target=_test_worker, daemon=True).start()

    def _apply_dns_test_result(self, ok: bool, msg: str):
        self.btn_test_dns.configure(state="normal", text="⚡ Test DNS")
        self.dns_test_lbl.configure(text=msg, text_color="#10B981" if ok else "#EF4444")

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

    def save_general_settings(self, show_dialog: bool = True):
        cookie_map_rev = {
            "Không dùng Cookie": "none", "Google Chrome": "chrome", "Microsoft Edge": "edge",
            "Mozilla Firefox": "firefox", "Brave Browser": "brave", "Opera": "opera", "Tệp Cookie (.txt)": "file"
        }
        b_val = cookie_map_rev.get(self.cookie_combo.get(), "none")

        dns_map_rev = {
            "🛡️ Cloudflare DNS (1.1.1.1 - Khuyên dùng vượt chặn)": "cloudflare",
            "🚀 Google Public DNS (8.8.8.8, 8.8.4.4)": "google",
            "🔒 Quad9 DNS (9.9.9.9 - Bảo mật cao)": "quad9",
            "🛡️ AdGuard DNS (Chặn quảng cáo & Vượt chặn)": "adguard",
            "✏️ Tùy chỉnh DNS (Custom IP / DoH)": "custom",
            "🌟 Mặc định hệ thống (ISP)": "default"
        }
        dns_val = dns_map_rev.get(self.dns_combo.get(), "cloudflare")

        self.config_manager.set("download_dir", self.dir_entry.get().strip())
        self.config_manager.set("browser_cookie", b_val)
        self.config_manager.set("dns_provider", dns_val)
        self.config_manager.set("custom_dns_servers", self.custom_dns_entry.get().strip())
        self.config_manager.set("custom_doh_url", self.custom_doh_entry.get().strip())
        self.config_manager.set("youtube_pot_enabled", bool(self.pot_cb.get()))
        self.config_manager.set("auto_detect_clipboard", bool(self.clip_cb.get()))

        if show_dialog:
            msgbox.showinfo("Thông báo", "Đã lưu cài đặt chung và DNS vượt chặn thành công!")

    # --- Handlers Tab Tools ---
    def refresh_tools_status(self):
        is_ff_ok = self.updater.is_ffmpeg_installed()
        ff_ver = self.updater.get_ffmpeg_version()
        ff_path = self.updater.get_ffmpeg_path()

        if is_ff_ok:
            self.ff_status_lbl.configure(text=f"Trạng thái: 🟢 Đã cài đặt (Phiên bản: {ff_ver})", text_color="#10B981")
            self.ff_path_lbl.configure(text=f"Đường dẫn: {ff_path}")
            self.ff_install_btn.configure(text="🔄 CẬP NHẬT LẠI FFMPEG", fg_color="#3B82F6", hover_color="#2563EB")
        else:
            self.ff_status_lbl.configure(text="Trạng thái: ⚠️ Chưa phát hiện FFmpeg", text_color="#EF4444")
            self.ff_path_lbl.configure(text="Đường dẫn: Chưa có trong bin/ hoặc PATH")
            self.ff_install_btn.configure(text="⬇️ TỰ ĐỘNG TẢI & CÀI ĐẶT FFMPEG", fg_color="#10B981", hover_color="#059669")

        self.yt_ver_lbl.configure(text=f"Phiên bản yt-dlp hiện tại: {self.updater.get_ytdlp_version()}")

    def on_download_ffmpeg(self):
        self.ff_install_btn.configure(state="disabled")
        self.ff_prog_bar.pack(fill="x", pady=(0, 8))
        self.ff_prog_bar.set(0.0)
        self.ff_prog_lbl.configure(text="Đang kết nối tới máy chủ tải...")
        self.log("[Phụ trợ] Bắt đầu tải FFmpeg...")

        def _worker():
            def on_prog(frac):
                self.after(0, lambda: self.ff_prog_bar.set(frac))

            def on_stat(msg):
                self.after(0, lambda: self.ff_prog_lbl.configure(text=msg))
                self.log(f"[FFmpeg] {msg}")

            success, msg = self.updater.download_and_install_ffmpeg(progress_callback=on_prog, status_callback=on_stat)
            self.after(0, lambda: self._finish_ffmpeg_install(success, msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _finish_ffmpeg_install(self, success: bool, msg: str):
        self.ff_install_btn.configure(state="normal")
        self.refresh_tools_status()
        if success:
            msgbox.showinfo("Thành công", "Đã cài đặt FFmpeg thành công và sẵn sàng hoạt động!")
        else:
            msgbox.showerror("Lỗi", msg)

    def on_update_ytdlp(self):
        self.yt_update_btn.configure(state="disabled", text="⏳ Đang kiểm tra...")
        self.log("[yt-dlp] Bắt đầu kiểm tra phiên bản mới...")

        def _worker():
            has_up, latest_ver = self.updater.check_ytdlp_latest_version()
            if has_up:
                self.after(0, lambda: self._prompt_ytdlp_update(latest_ver))
            else:
                self.after(0, lambda: self._finish_ytdlp_check(latest_ver))

        threading.Thread(target=_worker, daemon=True).start()

    def _prompt_ytdlp_update(self, latest_ver: str):
        self.yt_update_btn.configure(state="normal", text="🔄 CẬP NHẬT YT-DLP")
        self.yt_status_lbl.configure(text=f"Có phiên bản mới: {latest_ver}!", text_color="#3B82F6")
        ans = msgbox.askyesno("Cập nhật yt-dlp", f"Phát hiện phiên bản mới: {latest_ver}\nBạn có muốn nâng cấp ngay không?")
        if ans:
            self.yt_update_btn.configure(state="disabled", text="⏳ Đang cập nhật...")
            def _run():
                success, msg = self.updater.update_ytdlp(status_callback=lambda m: self.log(f"[yt-dlp] {m}"))
                self.after(0, lambda: self._finish_ytdlp_upgrade(success, msg))
            threading.Thread(target=_run, daemon=True).start()

    def _finish_ytdlp_upgrade(self, success: bool, msg: str):
        self.yt_update_btn.configure(state="normal", text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP")
        self.refresh_tools_status()
        if success:
            msgbox.showinfo("Thành công", "Đã cập nhật yt-dlp thành công!")
        else:
            msgbox.showerror("Lỗi cập nhật", msg)

    def _finish_ytdlp_check(self, ver_info: str):
        self.yt_update_btn.configure(state="normal", text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP")
        cur_ver = self.updater.get_ytdlp_version()
        self.yt_status_lbl.configure(text=f"🟢 Bạn đang sử dụng phiên bản mới nhất ({cur_ver}).", text_color="#10B981")
        msgbox.showinfo("Thông báo", f"Lõi yt-dlp đã ở phiên bản mới nhất ({cur_ver})!")

    def on_toggle_auto_check(self):
        val = bool(self.auto_check_cb.get())
        self.config_manager.set("auto_check_updates", val)

    # --- Handlers Tab License ---
    def refresh_license_display(self):
        valid, msg, lic_data = self.license_manager.check_license()
        if valid and lic_data:
            exp_text = lic_data.get("expires_str", "Vĩnh viễn (Lifetime)")
            self.lic_status_lbl.configure(text="Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", text_color="#10B981")
            self.lic_exp_lbl.configure(text=f"Hạn sử dụng: {exp_text}")
        else:
            self.lic_status_lbl.configure(text="Trạng thái: 🔴 Chưa kích hoạt hoặc Key hết hạn", text_color="#EF4444")
            self.lic_exp_lbl.configure(text="Hạn sử dụng: --")

    def on_change_key(self):
        ans = msgbox.askyesno("Xác nhận", "Bạn có chắc chắn muốn gỡ License Key hiện tại để nhập Key mới?")
        if ans:
            self.license_manager.deactivate()
            if self.on_reauth_callback:
                self.on_reauth_callback()
