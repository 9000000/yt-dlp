"""
Màn hình Tải Video Hàng Loạt & Danh Sách Phát (Batch & Playlist View).
Hỗ trợ tải nhiều link cùng lúc hoặc toàn bộ Playlist với các cột hiển thị Tiêu đề, Thời lượng, URL và Trạng thái riêng biệt 100% Tiếng Việt.
"""

import os
import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox
from pathlib import Path

from tool_gui.downloader import DownloadTask
from tool_gui.url_detector import URLDetector
from tool_gui.config import ConfigManager

class BatchView(ctk.CTkFrame):
    """Giao diện tải danh sách URL hoặc Playlist."""

    def __init__(self, master, config_manager: ConfigManager, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.log_callback = log_callback

        self.queue_items = []  # list of {url, title_lbl, duration_lbl, status_lbl, status}
        self.is_running = False
        self.current_index = 0

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # =========================================================================
        # 1. KHUNG NHẬP DANH SÁCH URL (BATCH INPUT CARD)
        # =========================================================================
        input_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        input_card.pack(fill="x", pady=(0, 15), padx=5)

        lbl_title = ctk.CTkLabel(input_card, text="📋 Nhập danh sách URL (mỗi dòng một link) hoặc Link Danh sách phát:", font=("Segoe UI", 13, "bold"))
        lbl_title.pack(anchor="w", padx=15, pady=(12, 6))

        self.text_urls = ctk.CTkTextbox(input_card, height=120, font=("Consolas", 12))
        self.text_urls.pack(fill="x", padx=15, pady=(0, 10))

        # Khung cài đặt nhanh
        opt_bar = ctk.CTkFrame(input_card, fg_color="transparent")
        opt_bar.pack(fill="x", padx=15, pady=(0, 12))
        opt_bar.grid_columnconfigure((0, 1, 2), weight=1)

        # Định dạng & Chất lượng
        self.fmt_combo = ctk.CTkComboBox(
            opt_bar,
            values=[
                "🌟 Video MP4 (Tốt nhất)",
                "🎬 Video Full HD 1080p",
                "📱 Video HD 720p",
                "🎵 Âm thanh MP3 (320kbps)",
                "🎵 Âm thanh M4A (Gốc)"
            ],
            height=34
        )
        self.fmt_combo.set("🌟 Video MP4 (Tốt nhất)")
        self.fmt_combo.grid(row=0, column=0, padx=5, sticky="ew")

        # Khoảng video playlist
        self.range_entry = ctk.CTkEntry(opt_bar, placeholder_text="Phạm vi playlist (VD: 1-10 hoặc để trống)", height=34)
        self.range_entry.grid(row=0, column=1, padx=5, sticky="ew")

        # Nút dán từ clipboard
        paste_btn = ctk.CTkButton(
            opt_bar,
            text="📋 Dán từ Clipboard",
            height=34,
            command=self.on_paste_all,
            fg_color="#64748B",
            hover_color="#475569"
        )
        paste_btn.grid(row=0, column=2, padx=5, sticky="ew")

        # =========================================================================
        # 2. KHUNG TIẾN TRÌNH & NÚT ĐIỀU KHIỂN
        # =========================================================================
        ctrl_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        ctrl_card.pack(fill="x", pady=(0, 15), padx=5)

        self.total_prog_lbl = ctk.CTkLabel(ctrl_card, text="Trạng thái: Chưa có tác vụ nào trong hàng đợi", font=("Segoe UI", 12, "bold"))
        self.total_prog_lbl.pack(anchor="w", padx=15, pady=(12, 4))

        self.total_bar = ctk.CTkProgressBar(ctrl_card, height=12, corner_radius=6)
        self.total_bar.set(0.0)
        self.total_bar.pack(fill="x", padx=15, pady=(0, 12))

        btn_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))

        self.start_btn = ctk.CTkButton(
            btn_row,
            text="▶️ BẮT ĐẦU TẢI DANH SÁCH",
            height=42,
            command=self.on_start_batch,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 13, "bold")
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            btn_row,
            text="🧹 Xóa danh sách",
            width=130,
            height=42,
            command=self.on_clear_batch,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Segoe UI", 12, "bold")
        )
        self.clear_btn.pack(side="right")

        # =========================================================================
        # 3. KHUNG BẢNG HÀNG ĐỢI VỚI CỘT HIỂN THỊ CHI TIẾT RIÊNG (QUEUE TABLE)
        # =========================================================================
        self.queue_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        self.queue_card.pack(fill="both", expand=True, pady=(0, 10), padx=5)

        q_title = ctk.CTkLabel(self.queue_card, text="📑 Danh sách video hàng đợi (kèm cột Tiêu đề & Thời lượng riêng):", font=("Segoe UI", 13, "bold"))
        q_title.pack(anchor="w", padx=15, pady=(12, 6))

        # Tiêu đề các cột trong bảng
        tbl_header = ctk.CTkFrame(self.queue_card, fg_color=("#CBD5E1", "#334155"), corner_radius=6, height=32)
        tbl_header.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkLabel(tbl_header, text="STT", width=45, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(tbl_header, text="🎬 Tiêu đề Video", anchor="w", width=260, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(tbl_header, text="⏱️ Thời lượng", width=90, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(tbl_header, text="🔗 Đường dẫn URL", anchor="w", font=("Segoe UI", 11, "bold")).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(tbl_header, text="Trạng thái", width=120, font=("Segoe UI", 11, "bold")).pack(side="right", padx=10)

        self.queue_frame = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        self.queue_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def on_paste_all(self):
        """Dán văn bản từ clipboard."""
        try:
            val = self.clipboard_get()
            if val:
                self.text_urls.insert("end", val + "\n")
        except Exception:
            pass

    def on_clear_batch(self):
        """Xóa toàn bộ hàng đợi."""
        if self.is_running:
            msgbox.showwarning("Cảnh báo", "Đang trong quá trình tải, không thể xóa danh sách!")
            return
        self.text_urls.delete("1.0", "end")
        for widget in self.queue_frame.winfo_children():
            widget.destroy()
        self.queue_items.clear()
        self.total_bar.set(0.0)
        self.total_prog_lbl.configure(text="Trạng thái: Đã dọn sạch danh sách")

    def on_start_batch(self):
        """Bắt đầu tải từng video trong danh sách."""
        if self.is_running:
            self.is_running = False
            self.start_btn.configure(text="▶️ BẮT ĐẦU TẢI DANH SÁCH", fg_color="#10B981", hover_color="#059669")
            self.total_prog_lbl.configure(text="⏹️ Đã dừng tiến trình tải hàng loạt.")
            return

        raw_text = self.text_urls.get("1.0", "end").strip()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip() and URLDetector.is_valid_url(line.strip())]

        if not lines:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một đường dẫn hợp lệ!")
            return

        for widget in self.queue_frame.winfo_children():
            widget.destroy()
        self.queue_items.clear()

        for idx, url in enumerate(lines):
            row_frame = ctk.CTkFrame(self.queue_frame, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
            row_frame.pack(fill="x", pady=3)

            idx_lbl = ctk.CTkLabel(row_frame, text=f"#{idx+1}", width=45, font=("Segoe UI", 11, "bold"))
            idx_lbl.pack(side="left", padx=5)

            title_lbl = ctk.CTkLabel(row_frame, text="Đang chờ phân tích...", width=260, anchor="w", font=("Segoe UI", 11, "bold"))
            title_lbl.pack(side="left", padx=5)

            dur_lbl = ctk.CTkLabel(row_frame, text="--:--", width=90, font=("Segoe UI", 11), text_color=("#64748B", "#94A3B8"))
            dur_lbl.pack(side="left", padx=5)

            url_lbl = ctk.CTkLabel(row_frame, text=url, anchor="w", font=("Segoe UI", 10), text_color=("#475569", "#94A3B8"))
            url_lbl.pack(side="left", fill="x", expand=True, padx=5)

            status_lbl = ctk.CTkLabel(row_frame, text="🕒 Chờ tải", width=120, font=("Segoe UI", 11, "bold"), text_color="#64748B")
            status_lbl.pack(side="right", padx=10)

            self.queue_items.append({
                "url": url,
                "title_lbl": title_lbl,
                "dur_lbl": dur_lbl,
                "status_lbl": status_lbl,
                "status": "pending"
            })

        self.is_running = True
        self.current_index = 0
        self.start_btn.configure(text="⏹️ DỪNG TIẾN TRÌNH", fg_color="#EF4444", hover_color="#DC2626")
        self.total_bar.set(0.0)
        self.log(f"[Tải hàng loạt] Bắt đầu tải {len(self.queue_items)} mục...")

        threading.Thread(target=self._process_batch, daemon=True).start()

    def _process_batch(self):
        """Xử lý tải tuần tự các mục trong hàng đợi."""
        total = len(self.queue_items)
        out_dir = self.config_manager.get("download_dir")
        fmt_choice = self.fmt_combo.get()
        audio_only = "Âm thanh" in fmt_choice
        playlist_range = self.range_entry.get().strip() or None

        quality = "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)"
        if "1080" in fmt_choice:
            quality = "Full HD (1080p)"
        elif "720" in fmt_choice:
            quality = "HD (720p)"

        out_fmt = "mp3" if "MP3" in fmt_choice else ("m4a" if "M4A" in fmt_choice else "mp4")
        cookie_browser = self.config_manager.get("browser_cookie", "none")
        cookie_file = self.config_manager.get("cookie_file_path", "")

        for idx, item in enumerate(self.queue_items):
            if not self.is_running:
                break

            self.current_index = idx
            url = item["url"]
            title_lbl = item["title_lbl"]
            dur_lbl = item["dur_lbl"]
            status_lbl = item["status_lbl"]

            # Phân tích nhanh metadata
            self.after(0, lambda sl=status_lbl, i=idx: (
                sl.configure(text="🔍 Đang lấy thông tin...", text_color="#3B82F6"),
                self.total_prog_lbl.configure(text=f"Đang xử lý mục {i+1}/{total}..."),
                self.total_bar.set(i / total)
            ))

            ok, meta, _ = URLDetector.fetch_metadata(url, cookie_browser=cookie_browser, cookie_file=cookie_file)
            if ok and meta:
                v_title = meta.get("title", url)
                v_dur = meta.get("duration_str", "--:--")
                self.after(0, lambda tl=title_lbl, dl=dur_lbl, t=v_title, d=v_dur: (
                    tl.configure(text=t[:35] + "..." if len(t) > 35 else t),
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
                playlist_items=playlist_range,
                on_finish=on_finish
            )
            task.start()
            finished_event.wait()

            if success_box[0]:
                self.after(0, lambda sl=status_lbl: sl.configure(text="✅ Hoàn tất", text_color="#10B981"))
            else:
                self.after(0, lambda sl=status_lbl: sl.configure(text="❌ Lỗi", text_color="#EF4444"))

        self.after(0, lambda: self._finish_batch(total))

    def _finish_batch(self, total: int):
        self.is_running = False
        self.start_btn.configure(text="▶️ BẮT ĐẦU TẢI DANH SÁCH", fg_color="#10B981", hover_color="#059669")
        self.total_bar.set(1.0)
        self.total_prog_lbl.configure(text=f"✅ Đã hoàn tất xử lý {total} mục trong hàng đợi!")
        self.log(f"[Tải hàng loạt] Hoàn tất {total} mục.")
        msgbox.showinfo("Hoàn tất", f"Đã hoàn thành quá trình tải hàng loạt ({total} mục)!")
