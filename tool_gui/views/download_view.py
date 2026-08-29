"""
Màn hình Tải Video Đơn (Download View).
Tự động nhận diện URL, hiển thị thông tin metadata, thumbnail và bộ chọn chất lượng đa dạng 100% Tiếng Việt.
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
    """Giao diện tải video chính."""

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
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. KHUNG NHẬP LIÊN KẾT (URL INPUT CARD)
        input_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        input_card.pack(fill="x", pady=(0, 15), padx=5)

        lbl_input = ctk.CTkLabel(input_card, text="🔗 Nhập hoặc Dán đường dẫn Video / Danh sách phát:", font=("Segoe UI", 13, "bold"))
        lbl_input.pack(anchor="w", padx=15, pady=(12, 6))

        url_bar = ctk.CTkFrame(input_card, fg_color="transparent")
        url_bar.pack(fill="x", padx=15, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            url_bar,
            placeholder_text="Dán link YouTube, TikTok, Facebook, Instagram, Bilibili...",
            font=("Segoe UI", 12),
            height=38
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self.on_analyze_clicked())

        paste_btn = ctk.CTkButton(
            url_bar,
            text="📋 Dán link",
            width=100,
            height=38,
            command=self.on_paste_clicked,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 12)
        )
        paste_btn.pack(side="left", padx=(0, 8))

        self.analyze_btn = ctk.CTkButton(
            url_bar,
            text="🔍 Phân tích",
            width=110,
            height=38,
            command=self.on_analyze_clicked,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 12, "bold")
        )
        self.analyze_btn.pack(side="left")

        # 2. KHUNG THÔNG TIN PREVIEW VIDEO (METADATA CARD)
        self.meta_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        self.meta_card.pack(fill="x", pady=(0, 15), padx=5)
        self.meta_card.pack_forget()

        meta_inner = ctk.CTkFrame(self.meta_card, fg_color="transparent")
        meta_inner.pack(fill="x", padx=15, pady=15)

        # Cột trái: Thumbnail
        self.thumb_label = ctk.CTkLabel(meta_inner, text="", width=180, height=101, corner_radius=8, fg_color=("#E2E8F0", "#1E293B"))
        self.thumb_label.pack(side="left", padx=(0, 15))

        # Cột phải: Thông tin chi tiết
        info_col = ctk.CTkFrame(meta_inner, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        self.platform_badge = ctk.CTkLabel(
            info_col,
            text="YouTube",
            fg_color="#EF4444",
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            width=80,
            height=20
        )
        self.platform_badge.pack(anchor="w", pady=(0, 4))

        self.title_label = ctk.CTkLabel(
            info_col,
            text="Tiêu đề video",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            justify="left",
            wraplength=480
        )
        self.title_label.pack(anchor="w", fill="x", pady=(0, 4))

        self.author_label = ctk.CTkLabel(info_col, text="Kênh: --", font=("Segoe UI", 11), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.author_label.pack(anchor="w", pady=(0, 2))

        self.duration_label = ctk.CTkLabel(info_col, text="Thời lượng: --", font=("Segoe UI", 11), text_color=("#64748B", "#94A3B8"), anchor="w")
        self.duration_label.pack(anchor="w")

        # 3. KHUNG TÙY CHỌN CHẤT LƯỢNG & ĐỊNH DẠNG (EXPANDED OPTIONS CARD)
        opt_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        opt_card.pack(fill="x", pady=(0, 15), padx=5)

        lbl_opt = ctk.CTkLabel(opt_card, text="⚙️ Cài đặt định dạng & chất lượng chi tiết:", font=("Segoe UI", 13, "bold"))
        lbl_opt.pack(anchor="w", padx=15, pady=(12, 8))

        opt_grid = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_grid.pack(fill="x", padx=15, pady=(0, 12))
        opt_grid.grid_columnconfigure((0, 1), weight=1)

        # Chế độ tải (Video / Audio)
        lbl_mode = ctk.CTkLabel(opt_grid, text="Kiểu tải xuống:", font=("Segoe UI", 12))
        lbl_mode.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        self.mode_var = ctk.StringVar(value="video")
        self.mode_seg = ctk.CTkSegmentedButton(
            opt_grid,
            values=["🎬 Video + Âm thanh", "🎵 Chỉ lấy Âm thanh (Audio)"],
            command=self.on_mode_changed
        )
        self.mode_seg.set("🎬 Video + Âm thanh")
        self.mode_seg.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        # Độ phân giải / Chất lượng
        self.lbl_quality = ctk.CTkLabel(opt_grid, text="Độ phân giải Video:", font=("Segoe UI", 12))
        self.lbl_quality.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        self.quality_combo = ctk.CTkComboBox(
            opt_grid,
            values=[
                "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)",
                "🎬 8K Ultra HD (4320p)",
                "🎬 4K Ultra HD (2160p)",
                "📺 2K Quad HD (1440p)",
                "📺 Full HD 1080p (60fps)",
                "📺 Full HD 1080p",
                "📱 HD 720p (60fps)",
                "📱 HD 720p",
                "📱 SD 480p",
                "⚡ Thấp 360p (Tiết kiệm dung lượng)",
                "⚡ Nhỏ nhất 240p / 144p"
            ],
            height=34
        )
        self.quality_combo.set("🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)")
        self.quality_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))

        # Định dạng xuất
        self.lbl_fmt = ctk.CTkLabel(opt_grid, text="Định dạng xuất (Container):", font=("Segoe UI", 12))
        self.lbl_fmt.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)

        self.fmt_combo = ctk.CTkComboBox(
            opt_grid,
            values=["MP4 (Tương thích cao nhất)", "MKV (Chất lượng gốc & đa track)", "WEBM (Chuẩn Web)", "MOV (Apple QuickTime)", "AVI"],
            height=34
        )
        self.fmt_combo.set("MP4 (Tương thích cao nhất)")
        self.fmt_combo.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        # Định dạng Audio / Bitrate
        self.lbl_audio_fmt = ctk.CTkLabel(opt_grid, text="Bitrate / Định dạng Âm thanh:", font=("Segoe UI", 12))
        self.lbl_audio_fmt.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)

        self.audio_combo = ctk.CTkComboBox(
            opt_grid,
            values=[
                "MP3 - 320 kbps (Cực cao - Studio Master)",
                "MP3 - 256 kbps (Chất lượng rất cao)",
                "MP3 - 192 kbps (Chuẩn CD Audio)",
                "MP3 - 128 kbps (Tiết kiệm dung lượng)",
                "M4A / AAC (Chất lượng gốc)",
                "FLAC (Lossless không nén)",
                "WAV (Lossless Studio)",
                "OPUS (Siêu nhẹ)"
            ],
            height=34
        )
        self.audio_combo.set("MP3 - 320 kbps (Cực cao - Studio Master)")
        self.audio_combo.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))
        self.audio_combo.configure(state="disabled")

        # CÁC CHECKBOX TIỆN ÍCH MỞ RỘNG
        chk_box = ctk.CTkFrame(opt_card, fg_color="transparent")
        chk_box.pack(fill="x", padx=15, pady=(0, 10))
        chk_box.grid_columnconfigure((0, 1), weight=1)

        self.sub_check = ctk.CTkCheckBox(chk_box, text="Tải & Nhúng Phụ đề Tiếng Việt / Đa ngữ", font=("Segoe UI", 11))
        self.sub_check.grid(row=0, column=0, sticky="w", pady=3)

        self.thumb_check = ctk.CTkCheckBox(chk_box, text="Tự động nhúng Ảnh bìa (Thumbnail) vào file", font=("Segoe UI", 11))
        self.thumb_check.select()
        self.thumb_check.grid(row=0, column=1, sticky="w", pady=3)

        self.meta_check = ctk.CTkCheckBox(chk_box, text="Tự động gắn thẻ Metadata (Tên bài, tác giả)", font=("Segoe UI", 11))
        self.meta_check.select()
        self.meta_check.grid(row=1, column=0, sticky="w", pady=3)

        # Thư mục lưu
        dir_frame = ctk.CTkFrame(opt_card, fg_color="transparent")
        dir_frame.pack(fill="x", padx=15, pady=(5, 15))

        lbl_dir = ctk.CTkLabel(dir_frame, text="📁 Thư mục lưu tệp:", font=("Segoe UI", 12))
        lbl_dir.pack(anchor="w", pady=(0, 4))

        dir_inner = ctk.CTkFrame(dir_frame, fg_color="transparent")
        dir_inner.pack(fill="x")

        self.dir_entry = ctk.CTkEntry(dir_inner, font=("Segoe UI", 11), height=34)
        self.dir_entry.insert(0, self.config_manager.get("download_dir"))
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            dir_inner,
            text="📂 Chọn thư mục",
            width=120,
            height=34,
            command=self.on_browse_dir,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 11)
        )
        browse_btn.pack(side="right")

        # 4. KHUNG TIẾN TRÌNH & NÚT BẮT ĐẦU TẢI (ACTION & PROGRESS CARD)
        action_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        action_card.pack(fill="x", pady=(0, 15), padx=5)

        self.prog_label = ctk.CTkLabel(action_card, text="Sẵn sàng tải xuống", font=("Segoe UI", 12, "bold"))
        self.prog_label.pack(anchor="w", padx=15, pady=(12, 4))

        self.prog_bar = ctk.CTkProgressBar(action_card, height=12, corner_radius=6)
        self.prog_bar.set(0.0)
        self.prog_bar.pack(fill="x", padx=15, pady=(0, 8))

        self.stats_label = ctk.CTkLabel(action_card, text="", font=("Segoe UI", 11), text_color=("#64748B", "#94A3B8"))
        self.stats_label.pack(anchor="w", padx=15, pady=(0, 12))

        btn_row = ctk.CTkFrame(action_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))

        self.dl_btn = ctk.CTkButton(
            btn_row,
            text="⬇️ BẮT ĐẦU TẢI XUỐNG",
            height=44,
            command=self.on_download_toggle,
            font=("Segoe UI", 14, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=8
        )
        self.dl_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.open_folder_btn = ctk.CTkButton(
            btn_row,
            text="📂 Mở thư mục",
            width=130,
            height=44,
            command=self.on_open_folder,
            font=("Segoe UI", 12, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            corner_radius=8
        )
        self.open_folder_btn.pack(side="right")

    def on_mode_changed(self, value):
        """Chuyển đổi giữa chế độ Video và Audio."""
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
        """Dán link từ clipboard và kích hoạt phân tích tự động."""
        try:
            val = self.clipboard_get().strip()
            if val:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, val)
                self.on_analyze_clicked()
        except Exception:
            pass

    def on_browse_dir(self):
        """Chọn thư mục lưu tệp."""
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)
            self.config_manager.set("download_dir", folder)

    def on_analyze_clicked(self):
        """Phân tích metadata của URL trong luồng phụ."""
        url = self.url_entry.get().strip()
        if not url:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập hoặc dán đường dẫn URL!")
            return

        if not URLDetector.is_valid_url(url):
            msgbox.showwarning("Cảnh báo", "Đường dẫn không hợp lệ. Vui lòng kiểm tra lại URL.")
            return

        self.analyze_btn.configure(state="disabled", text="⏳ Đang phân tích...")
        plat = URLDetector.detect_platform(url)
        self.prog_label.configure(text=f"Đang phân tích liên kết {plat}...")
        self.log(f"[Phân tích] Bắt đầu phân tích URL: {url}")

        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str):
        """Thực thi phân tích metadata trong background."""
        browser_cookie = self.config_manager.get("browser_cookie", "none")
        success, meta, msg = URLDetector.fetch_metadata(url, cookie_browser=browser_cookie)

        if success and meta:
            thumb_img = None
            if meta.get("thumbnail_url"):
                thumb_img = URLDetector.load_thumbnail_image(meta["thumbnail_url"])

            self.after(0, lambda: self._apply_metadata(meta, thumb_img))
        else:
            self.after(0, lambda: self._handle_analyze_error(msg))

    def _apply_metadata(self, meta: dict, thumb_img: Image.Image | None):
        """Cập nhật giao diện sau khi phân tích thành công."""
        self.current_meta = meta
        self.analyze_btn.configure(state="normal", text="🔍 Phân tích")
        self.meta_card.pack(fill="x", pady=(0, 15), padx=5)

        self.title_label.configure(text=meta.get("title", ""))
        self.author_label.configure(text=f"👤 Tác giả/Kênh: {meta.get('uploader', 'Không rõ')}")
        self.duration_label.configure(text=f"⏱️ Thời lượng: {meta.get('duration_str', '--')}")
        
        plat = meta.get("platform", "Đa nền tảng")
        badge_colors = {
            "YouTube": "#EF4444",
            "TikTok": "#111827",
            "Facebook": "#2563EB",
            "Instagram": "#E11D48",
            "Bilibili": "#00A1D6",
            "Twitter / X": "#000000"
        }
        self.platform_badge.configure(text=plat, fg_color=badge_colors.get(plat, "#64748B"))

        if thumb_img:
            ctk_img = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(180, 101))
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
        """Xử lý khi phân tích gặp lỗi."""
        self.analyze_btn.configure(state="normal", text="🔍 Phân tích")
        self.prog_label.configure(text=f"❌ {err_msg}")
        self.log(f"[Phân tích] Thất bại: {err_msg}")
        msgbox.showerror("Thông báo", err_msg)

    def on_download_toggle(self):
        """Bắt đầu hoặc hủy quá trình tải."""
        if self.is_downloading:
            if self.current_task:
                self.current_task.stop()
                self.prog_label.configure(text="⏹️ Đang dừng quá trình tải...")
                self.log("[Tải video] Đang hủy tác vụ...")
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
        self.log(f"[Tải video] Bắt đầu tải: {url} | Định dạng: {fmt} | Chất lượng: {quality}")

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
