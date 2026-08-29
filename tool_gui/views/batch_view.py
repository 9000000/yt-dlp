"""
Màn hình Tải Video Hàng Loạt & Danh Sách Phát (Batch & Playlist View).
Hỗ trợ tải nhiều link cùng lúc hoặc toàn bộ Playlist với giao diện 100% Tiếng Việt.
"""

import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog
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

        self.queue_items = []  # list of {url, status, task}
        self.is_running = False
        self.current_index = 0

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. KHUNG NHẬP DANH SÁCH URL
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

        # Định dạng
        self.fmt_combo = ctk.CTkComboBox(opt_bar, values=["Video MP4 (Tốt nhất)", "Video Full HD 1080p", "Video 720p", "Âm thanh MP3 320k", "Âm thanh M4A"])
        self.fmt_combo.set("Video MP4 (Tốt nhất)")
        self.fmt_combo.grid(row=0, column=0, padx=5, sticky="ew")

        # Khoảng video playlist
        self.range_entry = ctk.CTkEntry(opt_bar, placeholder_text="Phạm vi playlist (VD: 1-10 hoặc để trống)")
        self.range_entry.grid(row=0, column=1, padx=5, sticky="ew")

        # Nút dán từ clipboard
        paste_btn = ctk.CTkButton(opt_bar, text="📥 Dán từ Clipboard", command=self.on_paste_all, fg_color="#64748B", hover_color="#475569")
        paste_btn.grid(row=0, column=2, padx=5, sticky="ew")

        # 2. KHUNG TIẾN TRÌNH & NÚT ĐIỀU KHIỂN
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
            height=40,
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
            height=40,
            command=self.on_clear_batch,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Segoe UI", 12, "bold")
        )
        self.clear_btn.pack(side="right")

        # 3. KHUNG HÀNG ĐỢI (QUEUE LIST)
        self.queue_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        self.queue_card.pack(fill="both", expand=True, pady=(0, 10), padx=5)

        q_title = ctk.CTkLabel(self.queue_card, text="📑 Danh sách video đang chờ tải:", font=("Segoe UI", 13, "bold"))
        q_title.pack(anchor="w", padx=15, pady=(12, 8))

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
            # Dừng
            self.is_running = False
            self.start_btn.configure(text="▶️ BẮT ĐẦU TẢI DANH SÁCH", fg_color="#10B981", hover_color="#059669")
            self.total_prog_lbl.configure(text="⏹️ Đã dừng tiến trình tải hàng loạt.")
            return

        raw_text = self.text_urls.get("1.0", "end").strip()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip() and URLDetector.is_valid_url(line.strip())]

        if not lines:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một đường dẫn hợp lệ!")
            return

        # Dọn dẹp giao diện hàng đợi
        for widget in self.queue_frame.winfo_children():
            widget.destroy()
        self.queue_items.clear()

        for idx, url in enumerate(lines):
            row_frame = ctk.CTkFrame(self.queue_frame, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
            row_frame.pack(fill="x", pady=3)

            idx_lbl = ctk.CTkLabel(row_frame, text=f"#{idx+1}", width=40, font=("Segoe UI", 11, "bold"))
            idx_lbl.pack(side="left", padx=5)

            url_lbl = ctk.CTkLabel(row_frame, text=url, anchor="w", font=("Segoe UI", 11))
            url_lbl.pack(side="left", fill="x", expand=True, padx=5)

            status_lbl = ctk.CTkLabel(row_frame, text="🕒 Chờ tải", width=120, font=("Segoe UI", 11, "bold"), text_color="#64748B")
            status_lbl.pack(side="right", padx=10)

            self.queue_items.append({
                "url": url,
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

        quality = "Tốt nhất (Mặc định)"
        if "1080" in fmt_choice:
            quality = "Full HD (1080p)"
        elif "720" in fmt_choice:
            quality = "HD (720p)"

        out_fmt = "mp3" if "MP3" in fmt_choice else ("m4a" if "M4A" in fmt_choice else "mp4")

        for idx, item in enumerate(self.queue_items):
            if not self.is_running:
                break

            self.current_index = idx
            url = item["url"]
            status_lbl = item["status_lbl"]

            # Cập nhật UI
            self.after(0, lambda sl=status_lbl, i=idx: (
                sl.configure(text="⏳ Đang tải...", text_color="#3B82F6"),
                self.total_prog_lbl.configure(text=f"Đang tải mục {i+1}/{total}..."),
                self.total_bar.set(i / total)
            ))

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
                playlist_items=playlist_range,
                on_finish=on_finish
            )
            task.start()
            finished_event.wait()

            if success_box[0]:
                self.after(0, lambda sl=status_lbl: sl.configure(text="✅ Hoàn tất", text_color="#10B981"))
            else:
                self.after(0, lambda sl=status_lbl: sl.configure(text="❌ Lỗi", text_color="#EF4444"))

        # Kết thúc toàn bộ
        self.after(0, lambda: self._finish_batch(total))

    def _finish_batch(self, total: int):
        self.is_running = False
        self.start_btn.configure(text="▶️ BẮT ĐẦU TẢI DANH SÁCH", fg_color="#10B981", hover_color="#059669")
        self.total_bar.set(1.0)
        self.total_prog_lbl.configure(text=f"✅ Đã hoàn tất xử lý {total} mục trong hàng đợi!")
        self.log(f"[Tải hàng loạt] Hoàn tất {total} mục.")
        msgbox.showinfo("Hoàn tất", f"Đã hoàn thành quá trình tải hàng loạt ({total} mục)!")
