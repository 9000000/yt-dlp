"""
Màn hình Tải Video Hàng Loạt (Batch & Playlist View) - Bố Cục Tinh Gọn Xem Trọn Một Màn Hình.
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

        self.queue_items = []
        self.is_running = False
        self.current_index = 0

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # =========================================================================
        # 1. KHU VỰC NHẬP DANH SÁCH & CÀI ĐẶT NHANH (TOP SECTION - 2 CỘT)
        # =========================================================================
        top_grid = ctk.CTkFrame(main_container, corner_radius=10)
        top_grid.pack(fill="x", pady=(0, 10))

        top_inner = ctk.CTkFrame(top_grid, fg_color="transparent")
        top_inner.pack(fill="x", padx=12, pady=10)
        top_inner.grid_columnconfigure(0, weight=6)
        top_inner.grid_columnconfigure(1, weight=4)

        # Cột trái: Ô nhập danh sách link
        left_input = ctk.CTkFrame(top_inner, fg_color="transparent")
        left_input.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(left_input, text="📋 Danh sách liên kết (mỗi dòng 1 link hoặc link Playlist):", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))
        self.text_urls = ctk.CTkTextbox(left_input, height=90, font=("Consolas", 11))
        self.text_urls.pack(fill="both", expand=True)

        # Cột phải: Tùy chọn định dạng & Điều khiển
        right_ctrl = ctk.CTkFrame(top_inner, fg_color="transparent")
        right_ctrl.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(right_ctrl, text="⚙️ Cài đặt nhanh:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        row_opt = ctk.CTkFrame(right_ctrl, fg_color="transparent")
        row_opt.pack(fill="x", pady=(0, 4))

        self.fmt_combo = ctk.CTkComboBox(
            row_opt,
            values=["🌟 Video MP4 (Gốc)", "🎬 Video 1080p", "📱 Video 720p", "🎵 Âm thanh MP3 320k", "🎵 Âm thanh M4A"],
            height=28
        )
        self.fmt_combo.set("🌟 Video MP4 (Gốc)")
        self.fmt_combo.pack(side="left", fill="x", expand=True, padx=(0, 4))

        paste_btn = ctk.CTkButton(row_opt, text="📋 Dán", width=55, height=28, command=self.on_paste_all, fg_color="#64748B", hover_color="#475569")
        paste_btn.pack(side="right")

        self.range_entry = ctk.CTkEntry(right_ctrl, placeholder_text="Phạm vi playlist (VD: 1-10 hoặc để trống)", height=28, font=("Segoe UI", 10))
        self.range_entry.pack(fill="x", pady=(0, 6))

        btn_bar = ctk.CTkFrame(right_ctrl, fg_color="transparent")
        btn_bar.pack(fill="x")

        self.start_btn = ctk.CTkButton(
            btn_bar,
            text="▶️ BẮT ĐẦU TẢI",
            height=32,
            command=self.on_start_batch,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 12, "bold")
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.clear_btn = ctk.CTkButton(
            btn_bar,
            text="🧹 Xóa",
            width=70,
            height=32,
            command=self.on_clear_batch,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Segoe UI", 11, "bold")
        )
        self.clear_btn.pack(side="right")

        # =========================================================================
        # 2. KHUNG TIẾN TRÌNH & BẢNG DANH SÁCH HÀNG ĐỢI (BOTTOM SECTION)
        # =========================================================================
        queue_card = ctk.CTkFrame(main_container, corner_radius=10)
        queue_card.pack(fill="both", expand=True)

        q_inner = ctk.CTkFrame(queue_card, fg_color="transparent")
        q_inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Thanh tiến trình tổng thể
        prog_row = ctk.CTkFrame(q_inner, fg_color="transparent")
        prog_row.pack(fill="x", pady=(0, 4))

        self.total_prog_lbl = ctk.CTkLabel(prog_row, text="Trạng thái: Chưa có tác vụ nào", font=("Segoe UI", 11, "bold"))
        self.total_prog_lbl.pack(side="left")

        self.total_bar = ctk.CTkProgressBar(q_inner, height=8, corner_radius=4)
        self.total_bar.set(0.0)
        self.total_bar.pack(fill="x", pady=(0, 8))

        # Tiêu đề bảng hàng đợi
        tbl_header = ctk.CTkFrame(q_inner, fg_color=("#CBD5E1", "#334155"), corner_radius=6, height=26)
        tbl_header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(tbl_header, text="STT", width=40, font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(tbl_header, text="🎬 Tiêu đề Video", anchor="w", width=280, font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(tbl_header, text="⏱️ Thời lượng", width=80, font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(tbl_header, text="🔗 Đường dẫn URL", anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(tbl_header, text="Trạng thái", width=110, font=("Segoe UI", 10, "bold")).pack(side="right", padx=8)

        # Khung chứa các dòng danh sách
        self.queue_scroll = ctk.CTkScrollableFrame(q_inner, fg_color="transparent")
        self.queue_scroll.pack(fill="both", expand=True)

    def on_paste_all(self):
        try:
            val = self.clipboard_get()
            if val:
                self.text_urls.insert("end", val + "\n")
        except Exception:
            pass

    def on_clear_batch(self):
        if self.is_running:
            msgbox.showwarning("Cảnh báo", "Đang trong quá trình tải, không thể xóa danh sách!")
            return
        self.text_urls.delete("1.0", "end")
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()
        self.queue_items.clear()
        self.total_bar.set(0.0)
        self.total_prog_lbl.configure(text="Trạng thái: Đã dọn sạch danh sách")

    def on_start_batch(self):
        if self.is_running:
            self.is_running = False
            self.start_btn.configure(text="▶️ BẮT ĐẦU TẢI", fg_color="#10B981", hover_color="#059669")
            self.total_prog_lbl.configure(text="⏹️ Đã dừng tiến trình tải.")
            return

        raw_text = self.text_urls.get("1.0", "end").strip()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip() and URLDetector.is_valid_url(line.strip())]

        if not lines:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một đường dẫn hợp lệ!")
            return

        for widget in self.queue_scroll.winfo_children():
            widget.destroy()
        self.queue_items.clear()

        for idx, url in enumerate(lines):
            row_frame = ctk.CTkFrame(self.queue_scroll, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6, height=30)
            row_frame.pack(fill="x", pady=2)

            idx_lbl = ctk.CTkLabel(row_frame, text=f"#{idx+1}", width=40, font=("Segoe UI", 10, "bold"))
            idx_lbl.pack(side="left", padx=4)

            title_lbl = ctk.CTkLabel(row_frame, text="Đang chờ phân tích...", width=280, anchor="w", font=("Segoe UI", 10, "bold"))
            title_lbl.pack(side="left", padx=4)

            dur_lbl = ctk.CTkLabel(row_frame, text="--:--", width=80, font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"))
            dur_lbl.pack(side="left", padx=4)

            url_lbl = ctk.CTkLabel(row_frame, text=url, anchor="w", font=("Segoe UI", 9), text_color=("#475569", "#94A3B8"))
            url_lbl.pack(side="left", fill="x", expand=True, padx=4)

            status_lbl = ctk.CTkLabel(row_frame, text="🕒 Chờ", width=110, font=("Segoe UI", 10, "bold"), text_color="#64748B")
            status_lbl.pack(side="right", padx=8)

            self.queue_items.append({
                "url": url,
                "title_lbl": title_lbl,
                "dur_lbl": dur_lbl,
                "status_lbl": status_lbl,
                "status": "pending"
            })

        self.is_running = True
        self.current_index = 0
        self.start_btn.configure(text="⏹️ DỪNG LẠI", fg_color="#EF4444", hover_color="#DC2626")
        self.total_bar.set(0.0)
        self.log(f"[Tải hàng loạt] Bắt đầu tải {len(self.queue_items)} mục...")

        threading.Thread(target=self._process_batch, daemon=True).start()

    def _process_batch(self):
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
        pot_enabled = self.config_manager.get("youtube_pot_enabled", True)
        pot_url = self.config_manager.get("youtube_pot_provider_url", "")

        for idx, item in enumerate(self.queue_items):
            if not self.is_running:
                break

            self.current_index = idx
            url = item["url"]
            title_lbl = item["title_lbl"]
            dur_lbl = item["dur_lbl"]
            status_lbl = item["status_lbl"]

            self.after(0, lambda sl=status_lbl, i=idx: (
                sl.configure(text="🔍 Đang đọc...", text_color="#3B82F6"),
                self.total_prog_lbl.configure(text=f"Đang xử lý mục {i+1}/{total}..."),
                self.total_bar.set(i / total)
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
        self.is_running = False
        self.start_btn.configure(text="▶️ BẮT ĐẦU TẢI", fg_color="#10B981", hover_color="#059669")
        self.total_bar.set(1.0)
        self.total_prog_lbl.configure(text=f"✅ Đã hoàn tất {total} mục!")
        self.log(f"[Tải hàng loạt] Hoàn tất {total} mục.")
        msgbox.showinfo("Hoàn tất", f"Đã hoàn thành quá trình tải hàng loạt ({total} mục)!")
