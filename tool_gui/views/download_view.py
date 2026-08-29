"""
Màn hình Tải & Duyệt Video Hợp Nhất (Unified Downloader & In-App Browser Workspace).
- Tự động nhận diện loại liên kết (Link đơn, Playlist/Kênh/Trang web, Từ khóa tìm kiếm).
- Tích hợp Trình duyệt Web Edge WebView2 nhúng trực tiếp ngay trong GUI (không mở cửa sổ ngoài).
- Nút Quét trang tự động lấy URL đang duyệt trong trình duyệt nhúng để trích xuất video tức thì kèm Thumbnail.
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from PIL import Image

from tool_gui.url_detector import URLDetector
from tool_gui.downloader import DownloadTask
from tool_gui.page_scanner import PageVideoScanner
from tool_gui.config import ConfigManager

class DownloadView(ctk.CTkFrame):
    """Màn hình Tải & Duyệt Video hợp nhất thông minh."""

    def __init__(self, master, config_manager: ConfigManager, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.log_callback = log_callback

        # Trạng thái tải đơn
        self.current_meta = None
        self.current_task = None
        self.is_downloading = False
        self.last_analyzed_url = ""

        # Trạng thái tải hàng loạt
        self.queue_items = []
        self.is_batch_running = False
        self.batch_current_idx = 0

        # Trạng thái tìm kiếm & quét trang
        self.search_results = []
        self.embedded_browser_proc = None

        # File lưu URL đang duyệt
        self.app_dir = Path(__file__).resolve().parent.parent
        self.url_sync_file = self.app_dir / ".current_browser_url.txt"

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # =========================================================================
        # 1. THANH NHẬP LIỆU & TỰ ĐỘNG NHẬN DIỆN THÔNG MINH (UNIVERSAL TOP BAR)
        # =========================================================================
        top_card = ctk.CTkFrame(main_container, corner_radius=10)
        top_card.pack(fill="x", pady=(0, 10))

        top_inner = ctk.CTkFrame(top_card, fg_color="transparent")
        top_inner.pack(fill="x", padx=12, pady=10)

        lbl_input = ctk.CTkLabel(top_inner, text="🔗 Nhập liên kết / Từ khóa:", font=("Segoe UI", 12, "bold"))
        lbl_input.pack(side="left", padx=(0, 8))

        self.universal_entry = ctk.CTkEntry(
            top_inner,
            placeholder_text="Dán link Video đơn, Playlist, Kênh, Trang web bất kỳ HOẶC nhập từ khóa tìm kiếm...",
            font=("Segoe UI", 11),
            height=36
        )
        self.universal_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.universal_entry.bind("<Return>", lambda e: self.on_auto_detect_action())

        paste_btn = ctk.CTkButton(
            top_inner,
            text="📋 Dán link",
            width=85,
            height=36,
            command=self.on_paste_universal,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 11)
        )
        paste_btn.pack(side="left", padx=(0, 6))

        self.detect_btn = ctk.CTkButton(
            top_inner,
            text="⚡ Phân Tích Tự Động",
            width=145,
            height=36,
            command=self.on_auto_detect_action,
            font=("Segoe UI", 11, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.detect_btn.pack(side="left")

        # =========================================================================
        # 2. BỘ CHUYỂN CHẾ ĐỘ XEM (MODE SWITCHER)
        # =========================================================================
        switcher_card = ctk.CTkFrame(main_container, fg_color="transparent")
        switcher_card.pack(fill="x", pady=(0, 8))

        self.mode_switcher = ctk.CTkSegmentedButton(
            switcher_card,
            values=["🎬 Tải Video Đơn", "📑 Tải Hàng Loạt & Danh Sách", "🌐 Trình Duyệt Web Nhúng"],
            command=self.on_mode_switched,
            height=32,
            font=("Segoe UI", 11, "bold")
        )
        self.mode_switcher.set("🎬 Tải Video Đơn")
        self.mode_switcher.pack(fill="x")

        # =========================================================================
        # 3. KHU VỰC NỘI DUNG CHÍNH (CONTAINER 3 CHẾ ĐỘ)
        # =========================================================================
        self.content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True)

        self.frame_single = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frame_batch = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frame_browser = ctk.CTkFrame(self.content_area, fg_color="transparent")

        self.setup_single_mode_ui()
        self.setup_batch_mode_ui()
        self.setup_browser_mode_ui()

        # Mặc định hiện chế độ Tải Đơn
        self.show_single_mode()

    def on_mode_switched(self, choice):
        if "Đơn" in choice:
            self.show_single_mode()
        elif "Hàng Loạt" in choice:
            self.show_batch_mode()
        elif "Trình Duyệt" in choice:
            self.show_browser_mode()

    def show_single_mode(self):
        self.frame_batch.pack_forget()
        self.frame_browser.pack_forget()
        self.frame_single.pack(fill="both", expand=True)
        self.mode_switcher.set("🎬 Tải Video Đơn")

    def show_batch_mode(self):
        self.frame_single.pack_forget()
        self.frame_browser.pack_forget()
        self.frame_batch.pack(fill="both", expand=True)
        self.mode_switcher.set("📑 Tải Hàng Loạt & Danh Sách")

    def show_browser_mode(self):
        self.frame_single.pack_forget()
        self.frame_batch.pack_forget()
        self.frame_browser.pack(fill="both", expand=True)
        self.mode_switcher.set("🌐 Trình Duyệt Web Nhúng")

    # =========================================================================
    # TỰ ĐỘNG NHẬN DIỆN LIÊN KẾT THÔNG MINH
    # =========================================================================
    def on_paste_universal(self):
        try:
            val = self.clipboard_get().strip()
            if val:
                self.universal_entry.delete(0, "end")
                self.universal_entry.insert(0, val)
                self.on_auto_detect_action()
        except Exception:
            pass

    def on_auto_detect_action(self):
        raw = self.universal_entry.get().strip()
        if not raw:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập hoặc dán liên kết/từ khóa!")
            return

        lines = [line.strip() for line in raw.splitlines() if line.strip()]

        # 1. Nếu dán nhiều dòng link -> Chuyển ngay sang Tải Hàng Loạt
        if len(lines) > 1:
            self.show_batch_mode()
            self.text_urls.delete("1.0", "end")
            self.text_urls.insert("end", "\n".join(lines) + "\n")
            self.log(f"[Tự động nhận diện] Đã nhận diện danh sách {len(lines)} liên kết hàng loạt.")
            return

        target = lines[0]

        # 2. Nếu là từ khóa tìm kiếm (không phải URL) -> Chuyển sang Tìm kiếm & quét
        if not URLDetector.is_valid_url(target):
            self.show_browser_mode()
            self.browser_search_worker(target, is_keyword=True)
            return

        # 3. Nếu là Playlist / Kênh / Trang web -> Quét toàn bộ video trên trang
        t_low = target.lower()
        if "playlist?list=" in t_low or "/channel/" in t_low or "/user/" in t_low or "/c/" in t_low or "/@" in t_low and "/video/" not in t_low:
            self.show_browser_mode()
            self.browser_search_worker(target, is_keyword=False)
            return

        # 4. Mặc định là Video Đơn -> Phân tích tải đơn
        self.show_single_mode()
        self.start_analyze_single_url(target)

    # =========================================================================
    # CHẾ ĐỘ 1: TẢI VIDEO ĐƠN (SINGLE DOWNLOAD)
    # =========================================================================
    def setup_single_mode_ui(self):
        mid_grid = ctk.CTkFrame(self.frame_single, fg_color="transparent")
        mid_grid.pack(fill="both", expand=True, pady=(0, 8))
        mid_grid.grid_columnconfigure(0, weight=4)
        mid_grid.grid_columnconfigure(1, weight=5)
        mid_grid.grid_rowconfigure(0, weight=1)

        # Cột Trái: Thông tin video đã phân tích
        self.preview_card = ctk.CTkFrame(mid_grid, corner_radius=10, fg_color=("#F8FAFC", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
        self.preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        pv_head = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        pv_head.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(pv_head, text="🎬 Thông tin Video", font=("Segoe UI", 11, "bold"), text_color=("#2563EB", "#60A5FA")).pack(side="left")
        self.status_badge = ctk.CTkLabel(pv_head, text="Chờ URL...", font=("Segoe UI", 9, "bold"), fg_color=("#E2E8F0", "#334155"), corner_radius=4, height=18, padx=5)
        self.status_badge.pack(side="right")

        pv_body = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        pv_body.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.thumb_label = ctk.CTkLabel(pv_body, text="🖼️ Chưa có Video", width=220, height=124, corner_radius=6, fg_color=("#E2E8F0", "#0F172A"), font=("Segoe UI", 10))
        self.thumb_label.pack(pady=(0, 4))

        badge_line = ctk.CTkFrame(pv_body, fg_color="transparent")
        badge_line.pack(fill="x", pady=(0, 2))
        self.platform_badge = ctk.CTkLabel(badge_line, text="Đa nền tảng", fg_color="#64748B", text_color="white", corner_radius=4, font=("Segoe UI", 9, "bold"), width=70, height=16)
        self.platform_badge.pack(side="left", padx=(0, 4))
        self.type_badge = ctk.CTkLabel(badge_line, text="Video Đơn", fg_color=("#E2E8F0", "#334155"), corner_radius=4, font=("Segoe UI", 9), height=16, padx=4)
        self.type_badge.pack(side="left")

        self.title_label = ctk.CTkLabel(pv_body, text="Dán link vào ô trên và bấm Phân tích để xem thông tin", font=("Segoe UI", 11, "bold"), anchor="w", justify="left", wraplength=320, text_color=("#1E293B", "#F8FAFC"))
        self.title_label.pack(anchor="w", fill="x", pady=(0, 1))

        self.author_label = ctk.CTkLabel(pv_body, text="👤 Kênh: --", font=("Segoe UI", 9), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.author_label.pack(anchor="w")

        self.duration_label = ctk.CTkLabel(pv_body, text="⏱️ Thời lượng: --", font=("Segoe UI", 9), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.duration_label.pack(anchor="w")

        # Cột Phải: Cài đặt chất lượng
        opt_card = ctk.CTkFrame(mid_grid, corner_radius=10)
        opt_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="both", expand=True, padx=10, pady=6)

        ctk.CTkLabel(opt_inner, text="⚙️ Cài đặt định dạng & chất lượng", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        self.mode_var = ctk.StringVar(value="video")
        self.mode_seg = ctk.CTkSegmentedButton(opt_inner, values=["🎬 Video + Tiếng", "🎵 Chỉ lấy Âm thanh"], command=self.on_mode_changed, height=26)
        self.mode_seg.set("🎬 Video + Tiếng")
        self.mode_seg.pack(fill="x", pady=(0, 4))

        grid_c = ctk.CTkFrame(opt_inner, fg_color="transparent")
        grid_c.pack(fill="x", pady=(0, 4))
        grid_c.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_c, text="Độ phân giải:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(grid_c, text="Định dạng xuất:", font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(4, 0))

        self.quality_combo = ctk.CTkComboBox(grid_c, values=["🌟 Tốt nhất có thể (Gốc)", "🎬 8K Ultra HD (4320p)", "🎬 4K Ultra HD (2160p)", "📺 2K Quad HD (1440p)", "📺 Full HD 1080p (60fps)", "📺 Full HD 1080p", "📱 HD 720p (60fps)", "📱 HD 720p", "📱 SD 480p", "⚡ Thấp 360p", "⚡ 240p/144p"], height=28)
        self.quality_combo.set("🌟 Tốt nhất có thể (Gốc)")
        self.quality_combo.grid(row=1, column=0, sticky="ew", padx=(0, 2), pady=(0, 4))

        self.fmt_combo = ctk.CTkComboBox(grid_c, values=["MP4 (Khuyên dùng)", "MKV (Chất lượng gốc)", "WEBM", "MOV", "AVI"], height=28)
        self.fmt_combo.set("MP4 (Khuyên dùng)")
        self.fmt_combo.grid(row=1, column=1, sticky="ew", padx=(2, 0), pady=(0, 4))

        ctk.CTkLabel(grid_c, text="Bitrate Âm thanh:", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        ctk.CTkLabel(grid_c, text="Cookie xác thực:", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(4, 0))

        self.audio_combo = ctk.CTkComboBox(grid_c, values=["MP3 - 320 kbps (Cực cao)", "MP3 - 256 kbps", "MP3 - 192 kbps", "MP3 - 128 kbps", "M4A / AAC (Gốc)", "FLAC", "WAV", "OPUS"], height=28)
        self.audio_combo.set("MP3 - 320 kbps (Cực cao)")
        self.audio_combo.grid(row=3, column=0, sticky="ew", padx=(0, 2))
        self.audio_combo.configure(state="disabled")

        self.cookie_browser_combo = ctk.CTkComboBox(grid_c, values=["Không dùng Cookie", "Google Chrome", "Microsoft Edge", "Mozilla Firefox", "Brave Browser", "Opera", "Tệp Cookie (.txt)"], height=28, command=self.on_cookie_changed)
        saved_b = self.config_manager.get("browser_cookie", "none")
        c_map = {"none": "Không dùng Cookie", "chrome": "Google Chrome", "edge": "Microsoft Edge", "firefox": "Mozilla Firefox", "brave": "Brave Browser", "opera": "Opera", "file": "Tệp Cookie (.txt)"}
        self.cookie_browser_combo.set(c_map.get(saved_b, "Không dùng Cookie"))
        self.cookie_browser_combo.grid(row=3, column=1, sticky="ew", padx=(2, 0))

        chk_line = ctk.CTkFrame(opt_inner, fg_color="transparent")
        chk_line.pack(fill="x", pady=(4, 2))
        self.thumb_check = ctk.CTkCheckBox(chk_line, text="Nhúng Thumbnail", font=("Segoe UI", 9))
        self.thumb_check.select()
        self.thumb_check.pack(side="left", padx=(0, 6))

        self.meta_check = ctk.CTkCheckBox(chk_line, text="Gắn Metadata", font=("Segoe UI", 9))
        self.meta_check.select()
        self.meta_check.pack(side="left", padx=(0, 6))

        self.sub_check = ctk.CTkCheckBox(chk_line, text="Nhúng Phụ đề", font=("Segoe UI", 9))
        self.sub_check.pack(side="left")

        dir_line = ctk.CTkFrame(opt_inner, fg_color="transparent")
        dir_line.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(dir_line, text="📁 Lưu tại:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.dir_entry = ctk.CTkEntry(dir_line, font=("Segoe UI", 9), height=26)
        self.dir_entry.insert(0, self.config_manager.get("download_dir"))
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(dir_line, text="📂 Đổi", width=45, height=26, command=self.on_browse_dir, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 9)).pack(side="right")

        # Khung Tiến Trình & Nút Tải
        act_card = ctk.CTkFrame(self.frame_single, corner_radius=10)
        act_card.pack(fill="x")

        act_inner = ctk.CTkFrame(act_card, fg_color="transparent")
        act_inner.pack(fill="x", padx=12, pady=8)

        prog_line = ctk.CTkFrame(act_inner, fg_color="transparent")
        prog_line.pack(fill="x", pady=(0, 2))
        self.prog_label = ctk.CTkLabel(prog_line, text="Sẵn sàng tải xuống", font=("Segoe UI", 11, "bold"))
        self.prog_label.pack(side="left")
        self.stats_label = ctk.CTkLabel(prog_line, text="", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"))
        self.stats_label.pack(side="right")

        self.prog_bar = ctk.CTkProgressBar(act_inner, height=9, corner_radius=4)
        self.prog_bar.set(0.0)
        self.prog_bar.pack(fill="x", pady=(0, 6))

        btn_row = ctk.CTkFrame(act_inner, fg_color="transparent")
        btn_row.pack(fill="x")
        self.dl_btn = ctk.CTkButton(btn_row, text="⬇️ BẮT ĐẦU TẢI XUỐNG", height=36, command=self.on_download_toggle, font=("Segoe UI", 12, "bold"), fg_color="#10B981", hover_color="#059669", corner_radius=6)
        self.dl_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.open_folder_btn = ctk.CTkButton(btn_row, text="📂 Mở thư mục", width=110, height=36, command=self.on_open_folder, font=("Segoe UI", 11, "bold"), fg_color="#3B82F6", hover_color="#2563EB", corner_radius=6)
        self.open_folder_btn.pack(side="right")

    def start_analyze_single_url(self, url: str):
        self.status_badge.configure(text="⏳ Đang phân tích...", fg_color="#3B82F6", text_color="white")
        plat = URLDetector.detect_platform(url)
        self.prog_label.configure(text=f"Đang phân tích liên kết {plat}...")
        self.log(f"[Phân tích] Bắt đầu: {url}")

        def _worker():
            browser_cookie = self.config_manager.get("browser_cookie", "none")
            cookie_file = self.config_manager.get("cookie_file_path", "")
            pot_enabled = self.config_manager.get("youtube_pot_enabled", True)
            pot_url = self.config_manager.get("youtube_pot_provider_url", "")

            success, meta, msg = URLDetector.fetch_metadata(
                url,
                cookie_browser=browser_cookie,
                cookie_file=cookie_file,
                pot_enabled=pot_enabled,
                pot_provider_url=pot_url
            )

            if success and meta:
                thumb_img = None
                if meta.get("thumbnail_url"):
                    thumb_img = URLDetector.load_thumbnail_image(meta["thumbnail_url"], size=(220, 124))
                self.after(0, lambda: self._apply_single_metadata(meta, thumb_img))
            else:
                self.after(0, lambda: self._handle_single_error(msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_single_metadata(self, meta: dict, thumb_img: Image.Image | None):
        self.current_meta = meta
        self.status_badge.configure(text="✅ Sẵn sàng tải", fg_color="#10B981", text_color="white")
        self.title_label.configure(text=meta.get("title", ""))
        self.author_label.configure(text=f"👤 Kênh: {meta.get('uploader', 'Không rõ')}")
        self.duration_label.configure(text=f"⏱️ Thời lượng: {meta.get('duration_str', '--')}")
        
        plat = meta.get("platform", "Đa nền tảng")
        badge_colors = {"YouTube": "#EF4444", "TikTok": "#111827", "Facebook": "#2563EB", "Instagram": "#E11D48", "Bilibili": "#00A1D6"}
        self.platform_badge.configure(text=plat, fg_color=badge_colors.get(plat, "#64748B"))

        is_pl = meta.get("is_playlist", False)
        pl_cnt = meta.get("playlist_count", 1)
        self.type_badge.configure(text=f"Playlist ({pl_cnt} video)" if is_pl else "Video Đơn")

        if thumb_img:
            ctk_img = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(220, 124))
            self.thumb_label.configure(image=ctk_img, text="")
        else:
            self.thumb_label.configure(image=None, text="🖼️ Không có ảnh")

        qualities = meta.get("qualities", [])
        if qualities:
            self.quality_combo.configure(values=qualities)
            self.quality_combo.set(qualities[0])

        self.prog_label.configure(text="✅ Phân tích thành công! Sẵn sàng tải xuống.")
        self.log(f"[Phân tích] Thành công: {meta.get('title')}")

    def _handle_single_error(self, err_msg: str):
        self.status_badge.configure(text="❌ Thất bại", fg_color="#EF4444", text_color="white")
        self.prog_label.configure(text=f"❌ {err_msg}")
        self.log(f"[Phân tích] Thất bại: {err_msg}")
        msgbox.showerror("Thông báo", err_msg)

    # =========================================================================
    # CHẾ ĐỘ 2: TẢI HÀNG LOẠT & QUÉT TRANG (BATCH MODE)
    # =========================================================================
    def setup_batch_mode_ui(self):
        top_grid = ctk.CTkFrame(self.frame_batch, corner_radius=10)
        top_grid.pack(fill="x", pady=(0, 8))

        top_inner = ctk.CTkFrame(top_grid, fg_color="transparent")
        top_inner.pack(fill="x", padx=10, pady=8)
        top_inner.grid_columnconfigure(0, weight=6)
        top_inner.grid_columnconfigure(1, weight=4)

        left_in = ctk.CTkFrame(top_inner, fg_color="transparent")
        left_in.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(left_in, text="📋 Danh sách liên kết hàng loạt (mỗi dòng 1 link):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        self.text_urls = ctk.CTkTextbox(left_in, height=80, font=("Consolas", 10))
        self.text_urls.pack(fill="both", expand=True)

        right_ctrl = ctk.CTkFrame(top_inner, fg_color="transparent")
        right_ctrl.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(right_ctrl, text="⚙️ Cài đặt hàng loạt:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))

        row_b_opt = ctk.CTkFrame(right_ctrl, fg_color="transparent")
        row_b_opt.pack(fill="x", pady=(0, 4))
        self.batch_fmt_combo = ctk.CTkComboBox(row_b_opt, values=["🌟 Video MP4 (Gốc)", "🎬 Video 1080p", "📱 Video 720p", "🎵 Âm thanh MP3 320k", "🎵 Âm thanh M4A"], height=26, font=("Segoe UI", 10))
        self.batch_fmt_combo.set("🌟 Video MP4 (Gốc)")
        self.batch_fmt_combo.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.batch_range_entry = ctk.CTkEntry(right_ctrl, placeholder_text="Phạm vi playlist (VD: 1-10 hoặc để trống)", height=26, font=("Segoe UI", 9))
        self.batch_range_entry.pack(fill="x", pady=(0, 4))

        b_btn_row = ctk.CTkFrame(right_ctrl, fg_color="transparent")
        b_btn_row.pack(fill="x")
        self.batch_start_btn = ctk.CTkButton(b_btn_row, text="▶️ BẮT ĐẦU TẢI DANH SÁCH", height=28, command=self.on_start_batch, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 11, "bold"))
        self.batch_start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(b_btn_row, text="🧹 Xóa", width=60, height=28, command=self.on_clear_batch, fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 10, "bold")).pack(side="right")

        # Bảng hàng đợi
        queue_card = ctk.CTkFrame(self.frame_batch, corner_radius=10)
        queue_card.pack(fill="both", expand=True)

        q_inner = ctk.CTkFrame(queue_card, fg_color="transparent")
        q_inner.pack(fill="both", expand=True, padx=10, pady=8)

        prog_r = ctk.CTkFrame(q_inner, fg_color="transparent")
        prog_r.pack(fill="x", pady=(0, 2))
        self.batch_total_lbl = ctk.CTkLabel(prog_r, text="Trạng thái: Chưa có tác vụ nào", font=("Segoe UI", 10, "bold"))
        self.batch_total_lbl.pack(side="left")

        self.batch_total_bar = ctk.CTkProgressBar(q_inner, height=7, corner_radius=3)
        self.batch_total_bar.set(0.0)
        self.batch_total_bar.pack(fill="x", pady=(0, 6))

        tbl_hdr = ctk.CTkFrame(q_inner, fg_color=("#CBD5E1", "#334155"), corner_radius=4, height=24)
        tbl_hdr.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(tbl_hdr, text="STT", width=35, font=("Segoe UI", 9, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(tbl_hdr, text="🎬 Tiêu đề Video", anchor="w", width=280, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(tbl_hdr, text="⏱️ Thời lượng", width=75, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(tbl_hdr, text="🔗 Đường dẫn URL", anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(tbl_hdr, text="Trạng thái", width=100, font=("Segoe UI", 9, "bold")).pack(side="right", padx=6)

        self.batch_scroll = ctk.CTkScrollableFrame(q_inner, fg_color="transparent")
        self.batch_scroll.pack(fill="both", expand=True)

    # =========================================================================
    # CHẾ ĐỘ 3: TRÌNH DUYỆT WEB NHÚNG & QUÉT TRANG TỨC THÌ (IN-APP BROWSER)
    # =========================================================================
    def setup_browser_mode_ui(self):
        # 1. Thanh điều khiển trình duyệt nhúng & quét tức thì
        br_ctrl = ctk.CTkFrame(self.frame_browser, corner_radius=10)
        br_ctrl.pack(fill="x", pady=(0, 8))

        bc_inner = ctk.CTkFrame(br_ctrl, fg_color="transparent")
        bc_inner.pack(fill="x", padx=10, pady=8)

        # Nút Quét Link Đang Mở trong Trình duyệt nhúng
        self.btn_scan_current_live = ctk.CTkButton(
            bc_inner,
            text="🔍 QUÉT VIDEO TRÊN TRANG ĐANG XEM NÀY",
            height=34,
            command=self.on_scan_current_browser_url,
            font=("Segoe UI", 11, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.btn_scan_current_live.pack(side="left", padx=(0, 8))

        self.btn_download_current_live = ctk.CTkButton(
            bc_inner,
            text="⚡ TẢI VIDEO ĐANG XEM NÀY",
            height=34,
            command=self.on_download_current_browser_video,
            font=("Segoe UI", 11, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.btn_download_current_live.pack(side="left", padx=(0, 8))

        self.btn_launch_embedded = ctk.CTkButton(
            bc_inner,
            text="🌐 MỞ / TẢI LẠI TRÌNH DUYỆT TRONG APP",
            height=34,
            command=self.on_launch_embedded_browser_frame,
            font=("Segoe UI", 11, "bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED"
        )
        self.btn_launch_embedded.pack(side="right")

        # 2. Không gian nhúng Trình Duyệt Web & Danh Sách Quét (2 Nửa Màn Hình)
        br_body = ctk.CTkFrame(self.frame_browser, fg_color="transparent")
        br_body.pack(fill="both", expand=True)
        br_body.grid_columnconfigure(0, weight=5)  # Khung trình duyệt nhúng
        br_body.grid_columnconfigure(1, weight=5)  # Khung danh sách quét được
        br_body.grid_rowconfigure(0, weight=1)

        # Nửa Trái: Khung Trình Duyệt Web Nhúng (Edge WebView2 Frame)
        self.browser_host_card = ctk.CTkFrame(br_body, corner_radius=10, fg_color=("#0F172A", "#0F172A"))
        self.browser_host_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Tkinter native frame để nhúng HWND
        self.tk_browser_frame = tk.Frame(self.browser_host_card, bg="#0F172A")
        self.tk_browser_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Nửa Phải: Danh sách video quét được kèm Thumbnail đầy đủ
        res_card = ctk.CTkFrame(br_body, corner_radius=10)
        res_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        rc_head = ctk.CTkFrame(res_card, fg_color="transparent")
        rc_head.pack(fill="x", padx=10, pady=(8, 4))

        self.browser_res_count_lbl = ctk.CTkLabel(rc_head, text="Kết quả: Chưa quét", font=("Segoe UI", 10, "bold"), text_color=("#2563EB", "#60A5FA"))
        self.browser_res_count_lbl.pack(side="left")

        ctk.CTkButton(rc_head, text="[✓] Chọn hết", width=65, height=24, command=self.search_select_all, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 2))
        ctk.CTkButton(rc_head, text="[ ] Bỏ chọn", width=60, height=24, command=self.search_deselect_all, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 9)).pack(side="left", padx=2)

        self.btn_export_batch_from_scan = ctk.CTkButton(rc_head, text="🚀 GỬI TẢI HÀNG LOẠT", height=24, command=self.export_search_to_batch, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 9, "bold"))
        self.btn_export_batch_from_scan.pack(side="right")

        self.browser_res_scroll = ctk.CTkScrollableFrame(res_card, fg_color="transparent")
        self.browser_res_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.browser_empty_lbl = ctk.CTkLabel(self.browser_res_scroll, text="💡 Duyệt web bên trái hoặc bấm 'QUÉT VIDEO TRÊN TRANG' để lấy danh sách đầy đủ video kèm Thumbnail", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), wraplength=280)
        self.browser_empty_lbl.pack(pady=40)

    def on_launch_embedded_browser_frame(self):
        """Khởi chạy trình duyệt Edge WebView2 nhúng trực tiếp vào khung Frame."""
        self.update_idletasks()
        hwnd = self.tk_browser_frame.winfo_id()
        w = max(400, self.tk_browser_frame.winfo_width())
        h = max(350, self.tk_browser_frame.winfo_height())

        raw_url = self.universal_entry.get().strip()
        target_url = raw_url if URLDetector.is_valid_url(raw_url) else "https://www.youtube.com"

        if self.embedded_browser_proc:
            try:
                self.embedded_browser_proc.terminate()
            except Exception:
                pass

        self.log(f"[Trình duyệt nhúng] Đang gắn WebView2 vào GUI: {target_url}")
        
        try:
            if getattr(sys, 'frozen', False):
                self.embedded_browser_proc = subprocess.Popen([sys.executable, "--embedded-browser", str(hwnd), target_url, str(w), str(h)])
            else:
                script_path = str(self.app_dir / "tool_gui" / "embedded_browser.py")
                self.embedded_browser_proc = subprocess.Popen([sys.executable, script_path, str(hwnd), target_url, str(w), str(h)])
        except Exception as e:
            self.log(f"[Trình duyệt nhúng] Lỗi: {e}")

    def get_current_active_url(self) -> str:
        """Lấy URL đang mở hiện tại trong trình duyệt nhúng hoặc ô nhập liệu."""
        if self.url_sync_file.exists():
            try:
                with open(self.url_sync_file, "r", encoding="utf-8") as f:
                    u = f.read().strip()
                    if u and URLDetector.is_valid_url(u):
                        return u
            except Exception:
                pass

        u_entry = self.universal_entry.get().strip()
        if URLDetector.is_valid_url(u_entry):
            return u_entry
        return "https://www.youtube.com"

    def on_scan_current_browser_url(self):
        """Quét toàn bộ video có trên trang web đang duyệt."""
        current_url = self.get_current_active_url()
        self.log(f"[Quét trang hiện tại] Bắt đầu quét URL: {current_url}")
        self.browser_search_worker(current_url, is_keyword=False)

    def on_download_current_browser_video(self):
        """Tải video đang xem hiện tại trong trình duyệt."""
        current_url = self.get_current_active_url()
        self.show_single_mode()
        self.universal_entry.delete(0, "end")
        self.universal_entry.insert(0, current_url)
        self.start_analyze_single_url(current_url)

    def browser_search_worker(self, query: str, is_keyword: bool = False):
        self.browser_res_count_lbl.configure(text="Đang phân tích...")
        for widget in self.browser_res_scroll.winfo_children():
            widget.destroy()
        self.search_results.clear()

        def _worker():
            if is_keyword:
                ok, results, msg = PageVideoScanner.search_videos_by_keyword(query, max_results=20)
                m_name = "Tìm kiếm"
            else:
                ok, results, msg = PageVideoScanner.scan_webpage_for_videos(query)
                m_name = "Quét trang"

            self.after(0, lambda: self._apply_browser_results(ok, results, msg, m_name))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_browser_results(self, ok: bool, results: list, msg: str, mode_name: str):
        self.log(f"[{mode_name}] {msg}")

        if not ok or not results:
            self.browser_res_count_lbl.configure(text="Kết quả: 0 video")
            ctk.CTkLabel(self.browser_res_scroll, text=f"❌ {msg}", font=("Segoe UI", 10), text_color="#EF4444").pack(pady=30)
            return

        self.browser_res_count_lbl.configure(text=f"Tìm thấy: {len(results)} video")

        for item in results:
            card = ctk.CTkFrame(self.browser_res_scroll, corner_radius=6, fg_color=("#F1F5F9", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
            card.pack(fill="x", pady=3, padx=2)

            c_box = ctk.CTkFrame(card, fg_color="transparent")
            c_box.pack(fill="x", padx=6, pady=4)

            chk_var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(c_box, text="", variable=chk_var, width=20)
            chk.pack(side="left", padx=(0, 6))

            # Thumbnail hiển thị cho từng video
            thumb_lbl = ctk.CTkLabel(
                c_box,
                text="🖼️",
                width=90,
                height=52,
                corner_radius=4,
                fg_color=("#E2E8F0", "#0F172A"),
                font=("Segoe UI", 9)
            )
            thumb_lbl.pack(side="left", padx=(0, 8))

            thumb_url = item.get("thumbnail_url")
            if thumb_url:
                threading.Thread(target=self._async_load_thumb_card, args=(thumb_url, thumb_lbl), daemon=True).start()

            # Thông tin video
            info_col = ctk.CTkFrame(c_box, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True)

            t_row = ctk.CTkFrame(info_col, fg_color="transparent")
            t_row.pack(fill="x")

            plat = item.get("platform", "Đa nền tảng")
            badge_colors = {"YouTube": "#EF4444", "TikTok": "#111827", "Facebook": "#2563EB", "Instagram": "#E11D48", "Bilibili": "#00A1D6"}
            plat_badge = ctk.CTkLabel(t_row, text=plat, fg_color=badge_colors.get(plat, "#64748B"), text_color="white", corner_radius=3, font=("Segoe UI", 8, "bold"), width=55, height=16)
            plat_badge.pack(side="left", padx=(0, 4))

            t_text = item.get("title", item.get("url"))
            lbl_t = ctk.CTkLabel(t_row, text=t_text[:50] + "..." if len(t_text) > 50 else t_text, font=("Segoe UI", 10, "bold"), anchor="w")
            lbl_t.pack(side="left", fill="x", expand=True)

            sub_r = ctk.CTkFrame(info_col, fg_color="transparent")
            sub_r.pack(fill="x")

            u_info = f"👤 {item.get('uploader')}" if item.get('uploader') and item.get('uploader') != '--' else ""
            if u_info:
                ctk.CTkLabel(sub_r, text=u_info[:25], font=("Segoe UI", 8), text_color=("#64748B", "#94A3B8"), anchor="w").pack(side="left", padx=(0, 6))

            ctk.CTkLabel(sub_r, text=f"⏱️ {item.get('duration_str', '--:--')}", font=("Segoe UI", 8), text_color=("#64748B", "#94A3B8")).pack(side="left")

            dl_btn = ctk.CTkButton(c_box, text="📥 Tải", width=55, height=24, command=lambda u=item["url"]: self.load_single_and_download(u), fg_color="#3B82F6", hover_color="#2563EB", font=("Segoe UI", 9, "bold"))
            dl_btn.pack(side="right", padx=(4, 0))

            self.search_results.append({
                "data": item,
                "chk_var": chk_var,
                "frame": card
            })

    def _async_load_thumb_card(self, url: str, target_lbl: ctk.CTkLabel):
        try:
            img = URLDetector.load_thumbnail_image(url, size=(90, 52))
            if img:
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(90, 52))
                self.after(0, lambda: target_lbl.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def search_select_all(self):
        for item in self.search_results:
            item["chk_var"].set(True)

    def search_deselect_all(self):
        for item in self.search_results:
            item["chk_var"].set(False)

    def export_search_to_batch(self):
        selected = [item["data"]["url"] for item in self.search_results if item["chk_var"].get()]
        if not selected:
            msgbox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một video để chuyển sang Tải Hàng Loạt!")
            return

        self.show_batch_mode()
        self.text_urls.delete("1.0", "end")
        self.text_urls.insert("end", "\n".join(selected) + "\n")
        self.log(f"[Chuyển đổi] Đã chuyển {len(selected)} video sang Tải Hàng Loạt.")
        msgbox.showinfo("Thành công", f"Đã nạp {len(selected)} video vào danh sách Tải Hàng Loạt!")

    def load_single_and_download(self, url: str):
        self.show_single_mode()
        self.universal_entry.delete(0, "end")
        self.universal_entry.insert(0, url)
        self.start_analyze_single_url(url)

    # =========================================================================
    # CÁC HÀM XỬ LÝ TẢI ĐƠN & TẢI HÀNG LOẠT
    # =========================================================================
    def on_cookie_changed(self, choice):
        c_map_rev = {"Không dùng Cookie": "none", "Google Chrome": "chrome", "Microsoft Edge": "edge", "Mozilla Firefox": "firefox", "Brave Browser": "brave", "Opera": "opera", "Tệp Cookie (.txt)": "file"}
        b_key = c_map_rev.get(choice, "none")
        self.config_manager.set("browser_cookie", b_key)
        if b_key == "file":
            fpath = filedialog.askopenfilename(title="Chọn tệp cookies.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if fpath:
                self.config_manager.set("cookie_file_path", fpath)

    def on_mode_changed(self, value):
        if "Âm thanh" in value:
            self.mode_var.set("audio")
            self.quality_combo.configure(state="disabled")
            self.fmt_combo.configure(state="disabled")
            self.audio_combo.configure(state="normal")
            self.sub_check.configure(state="disabled")
        else:
            self.mode_var.set("video")
            self.quality_combo.configure(state="normal")
            self.fmt_combo.configure(state="normal")
            self.audio_combo.configure(state="disabled")
            self.sub_check.configure(state="normal")

    def on_browse_dir(self):
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)
            self.config_manager.set("download_dir", folder)

    def on_download_toggle(self):
        if self.is_downloading:
            if self.current_task:
                self.current_task.stop()
                self.prog_label.configure(text="⏹️ Đang dừng quá trình tải...")
                self.log("[Tải video] Đang hủy...")
            return

        url = self.universal_entry.get().strip()
        if not url:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập hoặc dán đường dẫn URL!")
            return

        out_dir = self.dir_entry.get().strip()
        if not out_dir:
            msgbox.showwarning("Cảnh báo", "Vui lòng chọn thư mục lưu tệp!")
            return

        audio_only = (self.mode_var.get() == "audio")
        quality = self.quality_combo.get()
        fmt = self.fmt_combo.get()
        audio_codec = self.audio_combo.get()
        embed_subs = bool(self.sub_check.get())
        embed_thumb = bool(self.thumb_check.get())
        add_meta = bool(self.meta_check.get())
        cookie_browser = self.config_manager.get("browser_cookie", "none")
        cookie_file = self.config_manager.get("cookie_file_path", "")
        pot_enabled = self.config_manager.get("youtube_pot_enabled", True)
        pot_url = self.config_manager.get("youtube_pot_provider_url", "")

        direct_url = None
        if self.current_meta:
            if audio_only and self.current_meta.get("direct_audio_url"):
                direct_url = self.current_meta["direct_audio_url"]
            elif not audio_only and self.current_meta.get("direct_video_url"):
                direct_url = self.current_meta["direct_video_url"]

        self.is_downloading = True
        self.dl_btn.configure(text="⏹️ HỦY TẢI XUỐNG", fg_color="#EF4444", hover_color="#DC2626")
        self.prog_bar.set(0.0)
        self.prog_label.configure(text="Đang bắt đầu tải...")
        self.stats_label.configure(text="")
        self.log(f"[Tải video] Bắt đầu: {url}")

        self.current_task = DownloadTask(
            url=url,
            output_dir=out_dir,
            quality=quality,
            output_format=fmt,
            audio_only=audio_only,
            audio_codec=audio_codec,
            embed_subs=embed_subs,
            embed_thumbnail=embed_thumb,
            add_metadata=add_meta,
            cookie_browser=cookie_browser,
            cookie_file=cookie_file,
            pot_enabled=pot_enabled,
            pot_provider_url=pot_url,
            direct_url=direct_url,
            on_progress=self._on_download_progress,
            on_status=self._on_download_status,
            on_finish=self._on_download_finished
        )
        self.current_task.start()

    def _on_download_progress(self, data: dict):
        pct_float = data.get("percent_float", 0.0)
        status_text = data.get("status_text", "")
        stats_text = f"Tốc độ: {data.get('speed', '--')} | Đã tải: {data.get('size_info', '--')} | Còn lại: {data.get('eta', '--')}"
        self.after(0, lambda: self._update_ui_progress(pct_float, status_text, stats_text))

    def _update_ui_progress(self, pct_float: float, status_text: str, stats_text: str):
        self.prog_bar.set(pct_float)
        self.prog_label.configure(text=status_text)
        self.stats_label.configure(text=stats_text)

    def _on_download_status(self, msg: str):
        self.after(0, lambda: self.prog_label.configure(text=msg))
        self.log(f"[Tải video] {msg}")

    def _on_download_finished(self, success: bool, msg: str, saved_dir: str):
        self.after(0, lambda: self._finish_ui(success, msg, saved_dir))

    def _finish_ui(self, success: bool, msg: str, saved_dir: str):
        self.is_downloading = False
        self.dl_btn.configure(text="⬇️ BẮT ĐẦU TẢI XUỐNG", fg_color="#10B981", hover_color="#059669")
        self.prog_label.configure(text=msg)
        self.log(f"[Tải video] Kết thúc: {msg}")

        if success:
            self.prog_bar.set(1.0)
            msgbox.showinfo("Thành công", f"{msg}\nTệp đã được lưu vào thư mục:\n{saved_dir}")
        else:
            if "hủy" not in msg.lower() and "dừng" not in msg.lower():
                msgbox.showerror("Lỗi tải", msg)

    def on_open_folder(self):
        folder = self.dir_entry.get().strip()
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            msgbox.showwarning("Cảnh báo", "Thư mục chưa tồn tại!")

    def check_clipboard_url(self, clip_text: str):
        if URLDetector.is_valid_url(clip_text) and clip_text != self.last_analyzed_url and not self.is_downloading:
            self.last_analyzed_url = clip_text
            self.universal_entry.delete(0, "end")
            self.universal_entry.insert(0, clip_text)
            self.on_auto_detect_action()

    # Tải hàng loạt
    def on_clear_batch(self):
        if self.is_batch_running:
            msgbox.showwarning("Cảnh báo", "Đang trong quá trình tải, không thể xóa danh sách!")
            return
        self.text_urls.delete("1.0", "end")
        for widget in self.batch_scroll.winfo_children():
            widget.destroy()
        self.queue_items.clear()
        self.batch_total_bar.set(0.0)
        self.batch_total_lbl.configure(text="Trạng thái: Đã dọn sạch danh sách")

    def on_start_batch(self):
        if self.is_batch_running:
            self.is_batch_running = False
            self.batch_start_btn.configure(text="▶️ BẮT ĐẦU TẢI DANH SÁCH", fg_color="#10B981", hover_color="#059669")
            self.batch_total_lbl.configure(text="⏹️ Đã dừng tiến trình tải.")
            return

        raw_text = self.text_urls.get("1.0", "end").strip()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip() and URLDetector.is_valid_url(line.strip())]

        if not lines:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một đường dẫn hợp lệ!")
            return

        for widget in self.batch_scroll.winfo_children():
            widget.destroy()
        self.queue_items.clear()

        for idx, url in enumerate(lines):
            row_frame = ctk.CTkFrame(self.batch_scroll, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6, height=28)
            row_frame.pack(fill="x", pady=2)

            idx_lbl = ctk.CTkLabel(row_frame, text=f"#{idx+1}", width=35, font=("Segoe UI", 9, "bold"))
            idx_lbl.pack(side="left", padx=2)

            title_lbl = ctk.CTkLabel(row_frame, text="Đang chờ phân tích...", width=280, anchor="w", font=("Segoe UI", 9, "bold"))
            title_lbl.pack(side="left", padx=4)

            dur_lbl = ctk.CTkLabel(row_frame, text="--:--", width=75, font=("Segoe UI", 9), text_color=("#64748B", "#94A3B8"))
            dur_lbl.pack(side="left", padx=4)

            url_lbl = ctk.CTkLabel(row_frame, text=url, anchor="w", font=("Segoe UI", 8), text_color=("#475569", "#94A3B8"))
            url_lbl.pack(side="left", fill="x", expand=True, padx=4)

            status_lbl = ctk.CTkLabel(row_frame, text="🕒 Chờ", width=100, font=("Segoe UI", 9, "bold"), text_color="#64748B")
            status_lbl.pack(side="right", padx=6)

            self.queue_items.append({
                "url": url,
                "title_lbl": title_lbl,
                "dur_lbl": dur_lbl,
                "status_lbl": status_lbl,
                "status": "pending"
            })

        self.is_batch_running = True
        self.batch_current_idx = 0
        self.batch_start_btn.configure(text="⏹️ DỪNG LẠI", fg_color="#EF4444", hover_color="#DC2626")
        self.batch_total_bar.set(0.0)
        self.log(f"[Tải hàng loạt] Bắt đầu tải {len(self.queue_items)} mục...")

        threading.Thread(target=self._process_batch, daemon=True).start()

    def _process_batch(self):
        total = len(self.queue_items)
        out_dir = self.config_manager.get("download_dir")
        fmt_choice = self.batch_fmt_combo.get()
        audio_only = "Âm thanh" in fmt_choice
        playlist_range = self.batch_range_entry.get().strip() or None

        quality = "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)"
        if "1080" in fmt_choice:
            quality = "Full HD (1080p)"
        elif "720" in fmt_choice:
            quality = "HD (720p)"

        out_fmt = "mp3" if "MP3" in fmt_choice else ("m4a" if "M4A" in fmt_choice else "mp4")
        cookie_browser = self.config_manager.get("browser_cookie", "none")
        cookie_file = self.config_manager.get("cookie_file_path", "")
        pot_enabled = self.config_manager.get("youtube_pot_enabled", True)
        pot_url = self.config_manager.get("youtube_pot_provider_url", "")

        for idx, item in enumerate(self.queue_items):
            if not self.is_batch_running:
                break

            self.batch_current_idx = idx
            url = item["url"]
            title_lbl = item["title_lbl"]
            dur_lbl = item["dur_lbl"]
            status_lbl = item["status_lbl"]

            self.after(0, lambda sl=status_lbl, i=idx: (
                sl.configure(text="🔍 Đang đọc...", text_color="#3B82F6"),
                self.batch_total_lbl.configure(text=f"Đang xử lý mục {i+1}/{total}..."),
                self.batch_total_bar.set(i / total)
            ))

            ok, meta, _ = URLDetector.fetch_metadata(url, cookie_browser=cookie_browser, cookie_file=cookie_file, pot_enabled=pot_enabled, pot_provider_url=pot_url)
            if ok and meta:
                v_title = meta.get("title", url)
                v_dur = meta.get("duration_str", "--:--")
                self.after(0, lambda tl=title_lbl, dl=dur_lbl, t=v_title, d=v_dur: (
                    tl.configure(text=t[:38] + "..." if len(t) > 38 else t),
                    dl.configure(text=d)
                ))

            self.after(0, lambda sl=status_lbl: sl.configure(text="⏳ Đang tải...", text_color="#3B82F6"))

            finished_event = threading.Event()
            success_box = [False]

            def on_finish(success, msg, saved_dir):
                success_box[0] = success
                finished_event.set()

            task = DownloadTask(
                url=url,
                output_dir=out_dir,
                quality=quality,
                output_format=out_fmt,
                audio_only=audio_only,
                audio_codec=out_fmt,
                cookie_browser=cookie_browser,
                cookie_file=cookie_file,
                pot_enabled=pot_enabled,
                pot_provider_url=pot_url,
                playlist_items=playlist_range,
                on_finish=on_finish
            )
            task.start()
            finished_event.wait()

            if success_box[0]:
                self.after(0, lambda sl=status_lbl: sl.configure(text="✅ Xong", text_color="#10B981"))
            else:
                self.after(0, lambda sl=status_lbl: sl.configure(text="❌ Lỗi", text_color="#EF4444"))

        self.after(0, lambda: self._finish_batch(total))

    def _finish_batch(self, total: int):
        self.is_batch_running = False
        self.batch_start_btn.configure(text="▶️ BẮT ĐẦU TẢI DANH SÁCH", fg_color="#10B981", hover_color="#059669")
        self.batch_total_bar.set(1.0)
        self.batch_total_lbl.configure(text=f"✅ Đã hoàn tất {total} mục!")
        self.log(f"[Tải hàng loạt] Hoàn tất {total} mục.")
        msgbox.showinfo("Hoàn tất", f"Đã hoàn thành quá trình tải hàng loạt ({total} mục)!")
