"""
Màn hình Cài Đặt Toàn Diện (Settings & Tools View).
Tích hợp:
1. ⚙️ Cài Đặt Chung & DNS Vượt Chặn Web
2. 🎛️ Quản Lý Cài Đặt Sẵn (Download Presets - Tạo mới / Sửa / Xóa)
3. 🛠️ Quản Lý Phụ Trợ & Cập Nhật (FFmpeg & yt-dlp Engine)
4. 🔐 Bản Quyền & Thiết Bị (License PRO)
"""

import time
import socket
import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from pathlib import Path

from tool_gui.config import ConfigManager, DNS_PRESETS, DEFAULT_DOWNLOAD_PRESETS
from tool_gui.license_manager import LicenseManager
from tool_gui.updater import UpdaterManager

class SettingsView(ctk.CTkFrame):
    """Giao diện Cài đặt toàn diện tích hợp Quản lý Phụ trợ và Quản lý Presets."""

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

        # Tabview Chính
        self.tabview = ctk.CTkTabview(main_container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True)

        self.tab_general = self.tabview.add("⚙️ Cài Đặt Chung & DNS")
        self.tab_presets = self.tabview.add("🎛️ Quản Lý Cài Đặt Sẵn (Presets)")
        self.tab_tools = self.tabview.add("🛠️ Phụ Trợ & Cập Nhật")
        self.tab_license = self.tabview.add("🔐 Bản Quyền PRO")

        # Thiết lập nội dung từng tab
        self._setup_tab_general()
        self._setup_tab_presets()
        self._setup_tab_tools()
        self._setup_tab_license()

    # =========================================================================
    # TAB 1: CÀI ĐẶT CHUNG & DNS VƯỢT CHẶN
    # =========================================================================
    def _setup_tab_general(self):
        scroll = ctk.CTkScrollableFrame(self.tab_general, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=8)

        # 1. Khung Giao Diện & Thư Mục
        g_card = ctk.CTkFrame(scroll, corner_radius=8)
        g_card.pack(fill="x", pady=(0, 10))

        g_inner = ctk.CTkFrame(g_card, fg_color="transparent")
        g_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(g_inner, text="🖥️ GIAO DIỆN & LƯU TRỮ", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 8))

        theme_row = ctk.CTkFrame(g_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(theme_row, text="Chế độ giao diện:", font=("Segoe UI", 11)).pack(side="left", padx=(0, 10))
        self.theme_combo = ctk.CTkComboBox(
            theme_row,
            values=["Tối (Dark Mode)", "Sáng (Light Mode)", "Theo hệ thống (System)"],
            command=self.on_theme_changed,
            height=28
        )
        self.theme_combo.pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(g_inner, text="Thư mục tải xuống mặc định:", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 2))
        dir_box = ctk.CTkFrame(g_inner, fg_color="transparent")
        dir_box.pack(fill="x", pady=(0, 6))
        self.dir_entry = ctk.CTkEntry(dir_box, font=("Segoe UI", 10), height=28)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(dir_box, text="📂 Duyệt", width=65, height=28, command=self.on_browse, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 10)).pack(side="right")

        ctk.CTkLabel(g_inner, text="Nguồn Cookie xác thực:", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 2))
        self.cookie_combo = ctk.CTkComboBox(
            g_inner,
            values=["Không dùng Cookie", "Google Chrome", "Microsoft Edge", "Mozilla Firefox", "Brave Browser", "Opera", "Tệp Cookie (.txt)"],
            height=28
        )
        self.cookie_combo.pack(fill="x", pady=(0, 4))

        # 2. Khung Cấu hình DNS & Vượt chặn
        dns_card = ctk.CTkFrame(scroll, corner_radius=8, fg_color=("#E2E8F0", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        dns_card.pack(fill="x", pady=(0, 10))

        dns_inner = ctk.CTkFrame(dns_card, fg_color="transparent")
        dns_inner.pack(fill="x", padx=15, pady=12)

        dns_hdr = ctk.CTkFrame(dns_inner, fg_color="transparent")
        dns_hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(dns_hdr, text="🌐 Cấu hình DNS & Vượt chặn Web (DoH):", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(side="left")
        self.btn_test_dns = ctk.CTkButton(dns_hdr, text="⚡ Test DNS", width=75, height=24, command=self.on_test_dns, font=("Segoe UI", 9, "bold"), fg_color="#3B82F6", hover_color="#2563EB")
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
            height=28
        )
        self.dns_combo.pack(fill="x", pady=(0, 6))

        self.custom_dns_frame = ctk.CTkFrame(dns_inner, fg_color="transparent")
        ctk.CTkLabel(self.custom_dns_frame, text="DNS Servers (cách nhau dấu phẩy):", font=("Segoe UI", 9)).pack(anchor="w")
        self.custom_dns_entry = ctk.CTkEntry(self.custom_dns_frame, placeholder_text="VD: 1.1.1.1, 1.0.0.1", height=26, font=("Consolas", 9))
        self.custom_dns_entry.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(self.custom_dns_frame, text="DoH URL (DNS over HTTPS):", font=("Segoe UI", 9)).pack(anchor="w")
        self.custom_doh_entry = ctk.CTkEntry(self.custom_dns_frame, placeholder_text="VD: https://cloudflare-dns.com/dns-query", height=26, font=("Consolas", 9))
        self.custom_doh_entry.pack(fill="x")

        self.dns_test_lbl = ctk.CTkLabel(dns_inner, text="💡 DNS giúp truy cập các trang web/video bị nhà mạng ISP chặn.", font=("Segoe UI", 9), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.dns_test_lbl.pack(anchor="w", pady=(4, 0))

        # Checkboxes
        chk_card = ctk.CTkFrame(scroll, corner_radius=8)
        chk_card.pack(fill="x", pady=(0, 10))
        chk_in = ctk.CTkFrame(chk_card, fg_color="transparent")
        chk_in.pack(fill="x", padx=15, pady=10)

        self.pot_cb = ctk.CTkCheckBox(chk_in, text="🛡️ Chống chặn YouTube (PO Token Provider)", font=("Segoe UI", 11))
        self.pot_cb.select()
        self.pot_cb.pack(anchor="w", pady=(0, 6))

        self.clip_cb = ctk.CTkCheckBox(chk_in, text="📋 Tự động bắt liên kết từ Clipboard", font=("Segoe UI", 11))
        self.clip_cb.pack(anchor="w")

        # Nút Lưu Cài Đặt Chung
        save_btn = ctk.CTkButton(
            scroll,
            text="💾 LƯU CÀI ĐẶT CHUNG",
            height=38,
            command=lambda: self.save_general_settings(show_dialog=True),
            font=("Segoe UI", 12, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        save_btn.pack(fill="x", pady=(5, 10))

    # =========================================================================
    # TAB 2: QUẢN LÝ CÀI ĐẶT SẴN (PRESETS)
    # =========================================================================
    def _setup_tab_presets(self):
        scroll = ctk.CTkScrollableFrame(self.tab_presets, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=8)

        # Header và chọn Preset
        top_box = ctk.CTkFrame(scroll, corner_radius=8)
        top_box.pack(fill="x", pady=(0, 10))

        t_in = ctk.CTkFrame(top_box, fg_color="transparent")
        t_in.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(t_in, text="🎛️ DANH SÁCH CẤU HÌNH SẴN (PRESETS)", font=("Segoe UI", 13, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(t_in, text="Tạo và quản lý các mẫu tải nhanh (định dạng, chất lượng, phụ đề, âm thanh) để áp dụng chỉ với 1 click khi tải video.", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), wraplength=620, justify="left").pack(anchor="w", pady=(0, 10))

        sel_row = ctk.CTkFrame(t_in, fg_color="transparent")
        sel_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(sel_row, text="Chọn Preset:", font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 10))

        self.preset_select_combo = ctk.CTkComboBox(sel_row, values=[], command=self.on_preset_picked_in_editor, height=30)
        self.preset_select_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_new_preset = ctk.CTkButton(sel_row, text="➕ Tạo Mới", width=85, height=30, command=self.on_new_preset_clicked, fg_color="#3B82F6", hover_color="#2563EB", font=("Segoe UI", 11, "bold"))
        self.btn_new_preset.pack(side="right")

        # Form chỉnh sửa Preset
        edit_box = ctk.CTkFrame(scroll, corner_radius=8, fg_color=("#F8FAFC", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
        edit_box.pack(fill="x", pady=(0, 10))

        e_in = ctk.CTkFrame(edit_box, fg_color="transparent")
        e_in.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(e_in, text="📝 THÔNG TIN CẤU HÌNH PRESET", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(e_in, text="Tên cấu hình mẫu:", font=("Segoe UI", 11)).pack(anchor="w")
        self.preset_name_entry = ctk.CTkEntry(e_in, font=("Segoe UI", 11), height=30, placeholder_text="VD: 🎵 Nhạc MP3 320k Studio")
        self.preset_name_entry.pack(fill="x", pady=(2, 8))

        mode_row = ctk.CTkFrame(e_in, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(mode_row, text="Loại tải:", font=("Segoe UI", 11)).pack(side="left", padx=(0, 10))
        self.preset_mode_seg = ctk.CTkSegmentedButton(mode_row, values=["🎬 Video + Âm thanh", "🎵 Chỉ lấy Âm thanh"], command=self.on_preset_mode_changed, height=28)
        self.preset_mode_seg.set("🎬 Video + Âm thanh")
        self.preset_mode_seg.pack(side="right", fill="x", expand=True)

        grid_p = ctk.CTkFrame(e_in, fg_color="transparent")
        grid_p.pack(fill="x", pady=(0, 8))
        grid_p.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_p, text="Chất lượng Video:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(grid_p, text="Định dạng Video:", font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.preset_quality_combo = ctk.CTkComboBox(grid_p, values=["🌟 Tốt nhất có thể (Gốc)", "🎬 8K Ultra HD (4320p)", "🎬 4K Ultra HD (2160p)", "📺 2K Quad HD (1440p)", "📺 Full HD 1080p (60fps)", "📺 Full HD 1080p", "📱 HD 720p (60fps)", "📱 HD 720p", "📱 SD 480p", "⚡ Thấp 360p"], height=28)
        self.preset_quality_combo.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(0, 6))

        self.preset_fmt_combo = ctk.CTkComboBox(grid_p, values=["MP4 (Khuyên dùng)", "MKV (Chất lượng gốc)", "WEBM", "MOV", "AVI"], height=28)
        self.preset_fmt_combo.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(0, 6))

        ctk.CTkLabel(grid_p, text="Bitrate Âm thanh (Audio Codec):", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        ctk.CTkLabel(grid_p, text="Định dạng Âm thanh:", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(6, 0))

        self.preset_audio_combo = ctk.CTkComboBox(grid_p, values=["MP3 - 320 kbps (Cực cao)", "MP3 - 256 kbps", "MP3 - 192 kbps", "MP3 - 128 kbps", "M4A / AAC (Gốc)", "FLAC (Lossless)", "WAV", "OPUS"], height=28)
        self.preset_audio_combo.grid(row=3, column=0, sticky="ew", padx=(0, 3))

        self.preset_audio_fmt_combo = ctk.CTkComboBox(grid_p, values=["MP3", "M4A", "FLAC", "WAV", "OPUS"], height=28)
        self.preset_audio_fmt_combo.grid(row=3, column=1, sticky="ew", padx=(3, 0))

        # Checkboxes Preset
        chk_p = ctk.CTkFrame(e_in, fg_color="transparent")
        chk_p.pack(fill="x", pady=(8, 8))

        self.p_thumb_cb = ctk.CTkCheckBox(chk_p, text="🖼️ Nhúng Ảnh Bìa (Thumbnail)", font=("Segoe UI", 10))
        self.p_thumb_cb.select()
        self.p_thumb_cb.pack(side="left", padx=(0, 10))

        self.p_meta_cb = ctk.CTkCheckBox(chk_p, text="🏷️ Gắn Thẻ Metadata", font=("Segoe UI", 10))
        self.p_meta_cb.select()
        self.p_meta_cb.pack(side="left", padx=(0, 10))

        self.p_sub_cb = ctk.CTkCheckBox(chk_p, text="💬 Tải & Nhúng Phụ Đề", font=("Segoe UI", 10))
        self.p_sub_cb.pack(side="left")

        # Nút Hành động cho Preset
        btn_act_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_act_row.pack(fill="x", pady=(0, 10))

        self.btn_save_preset = ctk.CTkButton(
            btn_act_row,
            text="💾 LƯU / CẬP NHẬT PRESET NÀY",
            height=36,
            command=self.on_save_preset_clicked,
            font=("Segoe UI", 11, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.btn_save_preset.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_del_preset = ctk.CTkButton(
            btn_act_row,
            text="🗑️ Xóa Preset",
            width=100,
            height=36,
            command=self.on_delete_preset_clicked,
            font=("Segoe UI", 11, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626"
        )
        self.btn_del_preset.pack(side="right")

    # =========================================================================
    # TAB 3: PHỤ TRỢ & CẬP NHẬT (FFMPEG & YT-DLP CORE)
    # =========================================================================
    def _setup_tab_tools(self):
        scroll = ctk.CTkScrollableFrame(self.tab_tools, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=8)

        # 1. THẺ FFMPEG
        ffmpeg_card = ctk.CTkFrame(scroll, corner_radius=8)
        ffmpeg_card.pack(fill="x", pady=(0, 10))

        ff_inner = ctk.CTkFrame(ffmpeg_card, fg_color="transparent")
        ff_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(ff_inner, text="🎬 TRÌNH XỬ LÝ VIDEO & ÂM THANH (FFMPEG)", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(ff_inner, text="FFmpeg là phụ trợ bắt buộc để ghép luồng Video 1080p/2K/4K với Audio chất lượng cao, trích xuất nhạc MP3/M4A và nhúng phụ đề.", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), wraplength=620, justify="left").pack(anchor="w", pady=(0, 8))

        ff_info_box = ctk.CTkFrame(ff_inner, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6)
        ff_info_box.pack(fill="x", pady=(0, 8))

        ff_info_in = ctk.CTkFrame(ff_info_box, fg_color="transparent")
        ff_info_in.pack(fill="x", padx=10, pady=8)

        self.ff_status_lbl = ctk.CTkLabel(ff_info_in, text="Trạng thái: Đang kiểm tra...", font=("Segoe UI", 11, "bold"))
        self.ff_status_lbl.pack(anchor="w", pady=(0, 2))
        self.ff_path_lbl = ctk.CTkLabel(ff_info_in, text="Đường dẫn: --", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"))
        self.ff_path_lbl.pack(anchor="w")

        self.ff_prog_lbl = ctk.CTkLabel(ff_inner, text="", font=("Segoe UI", 10))
        self.ff_prog_lbl.pack(anchor="w", pady=(0, 2))

        self.ff_prog_bar = ctk.CTkProgressBar(ff_inner, height=8, corner_radius=4)
        self.ff_prog_bar.set(0.0)
        self.ff_prog_bar.pack(fill="x", pady=(0, 8))
        self.ff_prog_bar.pack_forget()

        ff_btn_row = ctk.CTkFrame(ff_inner, fg_color="transparent")
        ff_btn_row.pack(fill="x")

        self.ff_install_btn = ctk.CTkButton(
            ff_btn_row,
            text="⬇️ TỰ ĐỘNG TẢI & CÀI ĐẶT FFMPEG",
            command=self.on_download_ffmpeg,
            height=34,
            font=("Segoe UI", 11, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.ff_install_btn.pack(side="left", padx=(0, 8))

        self.ff_refresh_btn = ctk.CTkButton(
            ff_btn_row,
            text="🔄 Kiểm tra lại",
            command=self.refresh_tools_status,
            width=110,
            height=34,
            font=("Segoe UI", 11),
            fg_color="#64748B",
            hover_color="#475569"
        )
        self.ff_refresh_btn.pack(side="left")

        # 2. THẺ YT-DLP CORE
        ytdlp_card = ctk.CTkFrame(scroll, corner_radius=8)
        ytdlp_card.pack(fill="x", pady=(0, 10))

        yt_inner = ctk.CTkFrame(ytdlp_card, fg_color="transparent")
        yt_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(yt_inner, text="🚀 LÕI TẢI VIDEO ĐA NỀN TẢNG (YT-DLP CORE)", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(yt_inner, text="Cập nhật yt-dlp thường xuyên giúp khắc phục các lỗi thay đổi API từ YouTube, TikTok, Facebook, Instagram.", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), wraplength=620, justify="left").pack(anchor="w", pady=(0, 8))

        yt_info_box = ctk.CTkFrame(yt_inner, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6)
        yt_info_box.pack(fill="x", pady=(0, 8))

        yt_info_in = ctk.CTkFrame(yt_info_box, fg_color="transparent")
        yt_info_in.pack(fill="x", padx=10, pady=8)

        self.yt_ver_lbl = ctk.CTkLabel(yt_info_in, text=f"Phiên bản yt-dlp hiện tại: {self.updater.get_ytdlp_version()}", font=("Segoe UI", 11, "bold"))
        self.yt_ver_lbl.pack(anchor="w", pady=(0, 2))
        self.yt_status_lbl = ctk.CTkLabel(yt_info_in, text="Trạng thái: Đang hoạt động bình thường", font=("Segoe UI", 10), text_color="#10B981")
        self.yt_status_lbl.pack(anchor="w")

        self.yt_update_btn = ctk.CTkButton(
            yt_inner,
            text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP",
            command=self.on_update_ytdlp,
            height=34,
            font=("Segoe UI", 11, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.yt_update_btn.pack(anchor="w")

        # 3. Tự động kiểm tra
        auto_card = ctk.CTkFrame(scroll, corner_radius=8)
        auto_card.pack(fill="x", pady=(0, 10))
        auto_in = ctk.CTkFrame(auto_card, fg_color="transparent")
        auto_in.pack(fill="x", padx=15, pady=10)

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
    # TAB 4: BẢN QUYỀN PRO
    # =========================================================================
    def _setup_tab_license(self):
        scroll = ctk.CTkScrollableFrame(self.tab_license, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=8)

        lic_card = ctk.CTkFrame(scroll, corner_radius=8)
        lic_card.pack(fill="x", pady=(0, 10))

        l_in = ctk.CTkFrame(lic_card, fg_color="transparent")
        l_in.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(l_in, text="🔐 THÔNG TIN BẢN QUYỀN PRO", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 8))

        lic_box = ctk.CTkFrame(l_in, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6)
        lic_box.pack(fill="x", pady=(0, 10))

        lb_in = ctk.CTkFrame(lic_box, fg_color="transparent")
        lb_in.pack(fill="x", padx=12, pady=10)

        self.lic_status_lbl = ctk.CTkLabel(lb_in, text="Trạng thái: 🟢 Đã kích hoạt bản quyền PRO", font=("Segoe UI", 11, "bold"), text_color="#10B981")
        self.lic_status_lbl.pack(anchor="w", pady=(0, 4))

        self.lic_exp_lbl = ctk.CTkLabel(lb_in, text="Hạn sử dụng: Vĩnh viễn (Lifetime)", font=("Segoe UI", 10))
        self.lic_exp_lbl.pack(anchor="w", pady=(0, 4))

        self.lic_m_lbl = ctk.CTkLabel(lb_in, text=f"Mã thiết bị: {self.license_manager.get_machine_id()}", font=("Consolas", 10), text_color=("#64748B", "#94A3B8"))
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

        # 2. Tab Presets
        self.refresh_presets_dropdown()

        # 3. Tab Tools
        self.refresh_tools_status()

        # 4. Tab License
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

    # --- Handlers Tab Presets ---
    def refresh_presets_dropdown(self):
        presets = self.config_manager.get_presets()
        names = [p.get("name", "Preset") for p in presets]
        self.preset_select_combo.configure(values=names)
        if names:
            self.preset_select_combo.set(names[0])
            self.on_preset_picked_in_editor(names[0])

    def on_preset_picked_in_editor(self, choice):
        p = self.config_manager.get_preset_by_name(choice)
        if not p:
            return

        self.preset_name_entry.delete(0, "end")
        self.preset_name_entry.insert(0, p.get("name", ""))

        mode = p.get("mode", "video")
        if mode == "audio":
            self.preset_mode_seg.set("🎵 Chỉ lấy Âm thanh")
        else:
            self.preset_mode_seg.set("🎬 Video + Âm thanh")
        self.on_preset_mode_changed(self.preset_mode_seg.get())

        if p.get("quality"):
            self.preset_quality_combo.set(p["quality"])
        if p.get("format"):
            self.preset_fmt_combo.set(p["format"])
        if p.get("audio_codec"):
            self.preset_audio_combo.set(p["audio_codec"])

        if p.get("embed_thumbnail", True):
            self.p_thumb_cb.select()
        else:
            self.p_thumb_cb.deselect()

        if p.get("add_metadata", True):
            self.p_meta_cb.select()
        else:
            self.p_meta_cb.deselect()

        if p.get("embed_subtitles", True):
            self.p_sub_cb.select()
        else:
            self.p_sub_cb.deselect()

    def on_preset_mode_changed(self, value):
        if "Âm thanh" in value:
            self.preset_quality_combo.configure(state="disabled")
            self.preset_fmt_combo.configure(state="disabled")
            self.preset_audio_combo.configure(state="normal")
            self.preset_audio_fmt_combo.configure(state="normal")
            self.p_sub_cb.configure(state="disabled")
        else:
            self.preset_quality_combo.configure(state="normal")
            self.preset_fmt_combo.configure(state="normal")
            self.preset_audio_combo.configure(state="normal")
            self.preset_audio_fmt_combo.configure(state="disabled")
            self.p_sub_cb.configure(state="normal")

    def on_new_preset_clicked(self):
        self.preset_name_entry.delete(0, "end")
        self.preset_name_entry.insert(0, "Mẫu Preset Mới")
        self.preset_mode_seg.set("🎬 Video + Âm thanh")
        self.on_preset_mode_changed("🎬 Video + Âm thanh")
        self.preset_quality_combo.set("🌟 Tốt nhất có thể (Gốc)")
        self.preset_fmt_combo.set("MP4 (Khuyên dùng)")
        self.preset_audio_combo.set("MP3 - 320 kbps (Cực cao)")
        self.p_thumb_cb.select()
        self.p_meta_cb.select()
        self.p_sub_cb.select()
        self.preset_name_entry.focus()

    def on_save_preset_clicked(self, show_dialog: bool = True):
        name = self.preset_name_entry.get().strip()
        if not name:
            if show_dialog:
                msgbox.showwarning("Cảnh báo", "Vui lòng nhập tên cho Cài Đặt Sẵn (Preset)!")
            return

        is_audio = ("Âm thanh" in self.preset_mode_seg.get())
        new_p = {
            "name": name,
            "mode": "audio" if is_audio else "video",
            "quality": self.preset_quality_combo.get(),
            "format": self.preset_fmt_combo.get() if not is_audio else self.preset_audio_fmt_combo.get(),
            "audio_codec": self.preset_audio_combo.get(),
            "embed_thumbnail": bool(self.p_thumb_cb.get()),
            "add_metadata": bool(self.p_meta_cb.get()),
            "embed_subtitles": bool(self.p_sub_cb.get()) if not is_audio else False
        }

        self.config_manager.add_or_update_preset(new_p)
        self.refresh_presets_dropdown()
        self.preset_select_combo.set(name)
        if show_dialog:
            msgbox.showinfo("Thành công", f"Đã lưu Cài Đặt Sẵn: '{name}' thành công!")

    def on_delete_preset_clicked(self, confirm: bool = True):
        name = self.preset_select_combo.get()
        if not name:
            return
        ans = True
        if confirm:
            ans = msgbox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa Cài Đặt Sẵn '{name}' không?")
        if ans:
            self.config_manager.delete_preset(name)
            self.refresh_presets_dropdown()
            if confirm:
                msgbox.showinfo("Đã xóa", f"Đã xóa preset '{name}' thành công.")

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
