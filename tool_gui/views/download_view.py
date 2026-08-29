"""
Màn hình Tải Video Đơn (Download View) - Bố Cục Tinh Gọn Xem Trọn Một Màn Hình.
Bố trí dạng lưới 2 cột: Xem trước Video bên trái, Tùy chọn chất lượng bên phải, Thanh tiến trình & nút tải ở dưới.
"""

import os
import sys
import threading
from pathlib import Path
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
from PIL import Image

from tool_gui.url_detector import URLDetector
from tool_gui.downloader import DownloadTask
from tool_gui.config import ConfigManager

class DownloadView(ctk.CTkFrame):
    """Giao diện tải video đơn tinh gọn."""

    def __init__(self, master, config_manager: ConfigManager, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.log_callback = log_callback

        self.current_meta = None
        self.current_task = None
        self.is_downloading = False
        self.last_analyzed_url = ""

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        # Không cần scrollable nếu toàn bộ nội dung đã vừa vặn màn hình
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # =========================================================================
        # 1. KHUNG NHẬP LIÊN KẾT TRÊN CÙNG (TOP URL BAR)
        # =========================================================================
        url_card = ctk.CTkFrame(main_container, corner_radius=10)
        url_card.pack(fill="x", pady=(0, 10))

        url_inner = ctk.CTkFrame(url_card, fg_color="transparent")
        url_inner.pack(fill="x", padx=12, pady=10)

        lbl_link = ctk.CTkLabel(url_inner, text="🔗 Liên kết:", font=("Segoe UI", 12, "bold"))
        lbl_link.pack(side="left", padx=(0, 8))

        self.url_entry = ctk.CTkEntry(
            url_inner,
            placeholder_text="Dán link YouTube, Facebook, TikTok, Instagram, Bilibili, Douyin...",
            font=("Segoe UI", 12),
            height=36
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self.on_analyze_clicked())

        paste_btn = ctk.CTkButton(
            url_inner,
            text="📋 Dán link",
            width=90,
            height=36,
            command=self.on_paste_clicked,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 11, "bold")
        )
        paste_btn.pack(side="left", padx=(0, 6))

        self.analyze_btn = ctk.CTkButton(
            url_inner,
            text="🔍 Phân tích",
            width=105,
            height=36,
            command=self.on_analyze_clicked,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 12, "bold")
        )
        self.analyze_btn.pack(side="left")

        # =========================================================================
        # 2. KHU VỰC THÂN CHÍNH: 2 CỘT (PREVIEW BÊN TRÁI + TÙY CHỌN BÊN PHẢI)
        # =========================================================================
        mid_grid = ctk.CTkFrame(main_container, fg_color="transparent")
        mid_grid.pack(fill="both", expand=True, pady=(0, 10))
        mid_grid.grid_columnconfigure(0, weight=4)  # Cột xem trước
        mid_grid.grid_columnconfigure(1, weight=5)  # Cột cài đặt chất lượng
        mid_grid.grid_rowconfigure(0, weight=1)

        # ---------------- CỘT TRÁI: Ô XEM TRƯỚC VIDEO ĐÃ PHÂN TÍCH ----------------
        self.preview_card = ctk.CTkFrame(mid_grid, corner_radius=10, fg_color=("#F8FAFC", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
        self.preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        pv_head = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        pv_head.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(pv_head, text="🎬 Thông tin Video", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            pv_head,
            text="Chờ URL...",
            font=("Segoe UI", 10, "bold"),
            fg_color=("#E2E8F0", "#334155"),
            corner_radius=6,
            height=20,
            padx=6
        )
        self.status_badge.pack(side="right")

        pv_content = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        pv_content.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.thumb_label = ctk.CTkLabel(
            pv_content,
            text="🖼️ Chưa có Video",
            width=220,
            height=124,
            corner_radius=8,
            fg_color=("#E2E8F0", "#0F172A"),
            font=("Segoe UI", 11)
        )
        self.thumb_label.pack(pady=(0, 6))

        badge_line = ctk.CTkFrame(pv_content, fg_color="transparent")
        badge_line.pack(fill="x", pady=(0, 4))

        self.platform_badge = ctk.CTkLabel(
            badge_line,
            text="Đa nền tảng",
            fg_color="#64748B",
            text_color="white",
            corner_radius=4,
            font=("Segoe UI", 9, "bold"),
            width=75,
            height=18
        )
        self.platform_badge.pack(side="left", padx=(0, 6))

        self.type_badge = ctk.CTkLabel(
            badge_line,
            text="Video Đơn",
            fg_color=("#E2E8F0", "#334155"),
            corner_radius=4,
            font=("Segoe UI", 9),
            height=18,
            padx=5
        )
        self.type_badge.pack(side="left")

        self.title_label = ctk.CTkLabel(
            pv_content,
            text="Vui lòng dán link và bấm Phân tích để xem thông tin video",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            justify="left",
            wraplength=340,
            text_color=("#1E293B", "#F8FAFC")
        )
        self.title_label.pack(anchor="w", fill="x", pady=(0, 2))

        self.author_label = ctk.CTkLabel(pv_content, text="👤 Tác giả/Kênh: --", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.author_label.pack(anchor="w", pady=(0, 1))

        self.duration_label = ctk.CTkLabel(pv_content, text="⏱️ Thời lượng: --", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.duration_label.pack(anchor="w")

        # ---------------- CỘT PHẢI: KHUNG TÙY CHỌN CHẤT LƯỢNG TINH GỌN ----------------
        opt_card = ctk.CTkFrame(mid_grid, corner_radius=10)
        opt_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="both", expand=True, padx=12, pady=8)

        ctk.CTkLabel(opt_inner, text="⚙️ Cài đặt tải & Định dạng xuất", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))

        # Chế độ tải (Video / Audio)
        self.mode_var = ctk.StringVar(value="video")
        self.mode_seg = ctk.CTkSegmentedButton(
            opt_inner,
            values=["🎬 Video + Tiếng", "🎵 Chỉ lấy Âm thanh"],
            command=self.on_mode_changed,
            height=28
        )
        self.mode_seg.set("🎬 Video + Tiếng")
        self.mode_seg.pack(fill="x", pady=(0, 6))

        # Lưới chọn chất lượng và container
        grid_controls = ctk.CTkFrame(opt_inner, fg_color="transparent")
        grid_controls.pack(fill="x", pady=(0, 6))
        grid_controls.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_controls, text="Độ phân giải:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", padx=(0, 4))
        ctk.CTkLabel(grid_controls, text="Định dạng Container:", font=("Segoe UI", 11)).grid(row=0, column=1, sticky="w", padx=(4, 0))

        self.quality_combo = ctk.CTkComboBox(
            grid_controls,
            values=[
                "🌟 Tốt nhất có thể (Gốc)",
                "🎬 8K Ultra HD (4320p)",
                "🎬 4K Ultra HD (2160p)",
                "📺 2K Quad HD (1440p)",
                "📺 Full HD 1080p (60fps)",
                "📺 Full HD 1080p",
                "📱 HD 720p (60fps)",
                "📱 HD 720p",
                "📱 SD 480p",
                "⚡ Thấp 360p",
                "⚡ Nhỏ nhất 240p/144p"
            ],
            height=30
        )
        self.quality_combo.set("🌟 Tốt nhất có thể (Gốc)")
        self.quality_combo.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(0, 4))

        self.fmt_combo = ctk.CTkComboBox(
            grid_controls,
            values=["MP4 (Khuyên dùng)", "MKV (Chất lượng gốc)", "WEBM (Web)", "MOV", "AVI"],
            height=30
        )
        self.fmt_combo.set("MP4 (Khuyên dùng)")
        self.fmt_combo.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(0, 4))

        # Dòng 2: Bitrate audio & Thư mục
        ctk.CTkLabel(grid_controls, text="Bitrate Âm thanh (Audio):", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w", padx=(0, 4))
        ctk.CTkLabel(grid_controls, text="Cookie xác thực:", font=("Segoe UI", 11)).grid(row=2, column=1, sticky="w", padx=(4, 0))

        self.audio_combo = ctk.CTkComboBox(
            grid_controls,
            values=[
                "MP3 - 320 kbps (Cực cao)",
                "MP3 - 256 kbps",
                "MP3 - 192 kbps",
                "MP3 - 128 kbps",
                "M4A / AAC (Gốc)",
                "FLAC (Lossless)",
                "WAV",
                "OPUS"
            ],
            height=30
        )
        self.audio_combo.set("MP3 - 320 kbps (Cực cao)")
        self.audio_combo.grid(row=3, column=0, sticky="ew", padx=(0, 4))
        self.audio_combo.configure(state="disabled")

        self.cookie_browser_combo = ctk.CTkComboBox(
            grid_controls,
            values=[
                "Không dùng Cookie",
                "Google Chrome",
                "Microsoft Edge",
                "Mozilla Firefox",
                "Brave Browser",
                "Opera",
                "Tệp Cookie (.txt)"
            ],
            height=30,
            command=self.on_cookie_changed
        )
        saved_b = self.config_manager.get("browser_cookie", "none")
        c_map = {"none": "Không dùng Cookie", "chrome": "Google Chrome", "edge": "Microsoft Edge", "firefox": "Mozilla Firefox", "brave": "Brave Browser", "opera": "Opera", "file": "Tệp Cookie (.txt)"}
        self.cookie_browser_combo.set(c_map.get(saved_b, "Không dùng Cookie"))
        self.cookie_browser_combo.grid(row=3, column=1, sticky="ew", padx=(4, 0))

        # Checkboxes tiện ích
        chk_line = ctk.CTkFrame(opt_inner, fg_color="transparent")
        chk_line.pack(fill="x", pady=(6, 4))

        self.thumb_check = ctk.CTkCheckBox(chk_line, text="Nhúng Ảnh bìa", font=("Segoe UI", 10))
        self.thumb_check.select()
        self.thumb_check.pack(side="left", padx=(0, 8))

        self.meta_check = ctk.CTkCheckBox(chk_line, text="Gắn Metadata", font=("Segoe UI", 10))
        self.meta_check.select()
        self.meta_check.pack(side="left", padx=(0, 8))

        self.sub_check = ctk.CTkCheckBox(chk_line, text="Nhúng Phụ đề", font=("Segoe UI", 10))
        self.sub_check.pack(side="left")

        # Thư mục lưu
        dir_line = ctk.CTkFrame(opt_inner, fg_color="transparent")
        dir_line.pack(fill="x", pady=(4, 0))

        lbl_d = ctk.CTkLabel(dir_line, text="📁 Lưu tại:", font=("Segoe UI", 10))
        lbl_d.pack(side="left", padx=(0, 6))

        self.dir_entry = ctk.CTkEntry(dir_line, font=("Segoe UI", 10), height=28)
        self.dir_entry.insert(0, self.config_manager.get("download_dir"))
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        browse_btn = ctk.CTkButton(
            dir_line,
            text="📂 Đổi",
            width=50,
            height=28,
            command=self.on_browse_dir,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10)
        )
        browse_btn.pack(side="right")

        # =========================================================================
        # 3. KHUNG TIẾN TRÌNH & NÚT BẮT ĐẦU TẢI (BOTTOM ACTION & PROGRESS)
        # =========================================================================
        action_card = ctk.CTkFrame(main_container, corner_radius=10)
        action_card.pack(fill="x")

        act_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        act_inner.pack(fill="x", padx=12, pady=10)

        prog_line = ctk.CTkFrame(act_inner, fg_color="transparent")
        prog_line.pack(fill="x", pady=(0, 4))

        self.prog_label = ctk.CTkLabel(prog_line, text="Sẵn sàng tải xuống", font=("Segoe UI", 11, "bold"))
        self.prog_label.pack(side="left")

        self.stats_label = ctk.CTkLabel(prog_line, text="", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"))
        self.stats_label.pack(side="right")

        self.prog_bar = ctk.CTkProgressBar(act_inner, height=10, corner_radius=5)
        self.prog_bar.set(0.0)
        self.prog_bar.pack(fill="x", pady=(0, 8))

        btn_row = ctk.CTkFrame(act_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        self.dl_btn = ctk.CTkButton(
            btn_row,
            text="⬇️ BẮT ĐẦU TẢI XUỐNG",
            height=38,
            command=self.on_download_toggle,
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=6
        )
        self.dl_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.open_folder_btn = ctk.CTkButton(
            btn_row,
            text="📂 Mở thư mục",
            width=120,
            height=38,
            command=self.on_open_folder,
            font=("Segoe UI", 11, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            corner_radius=6
        )
        self.open_folder_btn.pack(side="right")

    def on_cookie_changed(self, choice):
        c_map_rev = {"Không dùng Cookie": "none", "Google Chrome": "chrome", "Microsoft Edge": "edge", "Mozilla Firefox": "firefox", "Brave Browser": "brave", "Opera": "opera", "Tệp Cookie (.txt)": "file"}
        b_key = c_map_rev.get(choice, "none")
        self.config_manager.set("browser_cookie", b_key)
        if b_key == "file":
            fpath = filedialog.askopenfilename(title="Chọn tệp cookies.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if fpath:
                self.config_manager.set("cookie_file_path", fpath)
                self.log(f"[Cookie] Đã chọn file: {fpath}")

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

    def on_paste_clicked(self):
        try:
            val = self.clipboard_get().strip()
            if val:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, val)
                self.on_analyze_clicked()
        except Exception:
            pass

    def on_browse_dir(self):
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)
            self.config_manager.set("download_dir", folder)

    def on_analyze_clicked(self):
        url = self.url_entry.get().strip()
        if not url:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập hoặc dán đường dẫn URL!")
            return

        if not URLDetector.is_valid_url(url):
            msgbox.showwarning("Cảnh báo", "Đường dẫn không hợp lệ. Vui lòng kiểm tra lại URL.")
            return

        self.analyze_btn.configure(state="disabled", text="⏳ Đang...")
        self.status_badge.configure(text="⏳ Đang phân tích...", fg_color="#3B82F6", text_color="white")
        plat = URLDetector.detect_platform(url)
        self.prog_label.configure(text=f"Đang phân tích liên kết {plat}...")
        self.log(f"[Phân tích] Bắt đầu: {url}")

        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str):
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

            self.after(0, lambda: self._apply_metadata(meta, thumb_img))
        else:
            self.after(0, lambda: self._handle_analyze_error(msg))

    def _apply_metadata(self, meta: dict, thumb_img: Image.Image | None):
        self.current_meta = meta
        self.analyze_btn.configure(state="normal", text="🔍 Phân tích")
        self.status_badge.configure(text="✅ Sẵn sàng tải", fg_color="#10B981", text_color="white")

        self.title_label.configure(text=meta.get("title", ""))
        self.author_label.configure(text=f"👤 Kênh: {meta.get('uploader', 'Không rõ')}")
        self.duration_label.configure(text=f"⏱️ Thời lượng: {meta.get('duration_str', '--')}")
        
        plat = meta.get("platform", "Đa nền tảng")
        badge_colors = {"YouTube": "#EF4444", "TikTok": "#111827", "Facebook": "#2563EB", "Instagram": "#E11D48", "Bilibili": "#00A1D6", "Twitter / X": "#000000"}
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

    def _handle_analyze_error(self, err_msg: str):
        self.analyze_btn.configure(state="normal", text="🔍 Phân tích")
        self.status_badge.configure(text="❌ Thất bại", fg_color="#EF4444", text_color="white")
        self.prog_label.configure(text=f"❌ {err_msg}")
        self.log(f"[Phân tích] Thất bại: {err_msg}")
        msgbox.showerror("Thông báo", err_msg)

    def on_download_toggle(self):
        if self.is_downloading:
            if self.current_task:
                self.current_task.stop()
                self.prog_label.configure(text="⏹️ Đang dừng quá trình tải...")
                self.log("[Tải video] Đang hủy...")
            return

        url = self.url_entry.get().strip()
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
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clip_text)
            self.on_analyze_clicked()
