"""
Màn hình Tải Video Hàng Loạt & Danh Sách Phát (Batch & Playlist View).
Hỗ trợ tải nhiều link cùng lúc hoặc toàn bộ Playlist với cột hiển thị Cookie riêng biệt 100% Tiếng Việt.
"""

import os
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

        self.queue_items = []  # list of {url, status, cookie_src, status_lbl}
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
        # 1. KHUNG CHỌN COOKIE TRÊN CÙNG (TOP COOKIE BAR)
        # =========================================================================
        cookie_card = ctk.CTkFrame(self.scroll, corner_radius=12, fg_color=("#F1F5F9", "#1E293B"))
        cookie_card.pack(fill="x", pady=(0, 12), padx=5)

        cookie_inner = ctk.CTkFrame(cookie_card, fg_color="transparent")
        cookie_inner.pack(fill="x", padx=15, pady=10)

        lbl_cookie = ctk.CTkLabel(
            cookie_inner,
            text="🍪 Nguồn Cookie xác thực (Áp dụng cho tải hàng loạt):",
            font=("Segoe UI", 12, "bold"),
            text_color=("#2563EB", "#60A5FA")
        )
        lbl_cookie.pack(side="left", padx=(0, 10))

        self.cookie_browser_combo = ctk.CTkComboBox(
            cookie_inner,
            values=[
                "🌐 Không dùng Cookie (Mặc định)",
                "🌐 Google Chrome",
                "🌐 Microsoft Edge",
                "🌐 Mozilla Firefox",
                "🌐 Brave Browser",
                "🌐 Opera",
                "📁 Tệp Cookie riêng (.txt)"
            ],
            width=220,
            height=32,
            command=self.on_cookie_browser_changed
        )
        self.cookie_browser_combo.pack(side="left", padx=(0, 10))

        saved_cookie = self.config_manager.get("browser_cookie", "none")
        cookie_map_rev = {
            "none": "🌐 Không dùng Cookie (Mặc định)",
            "chrome": "🌐 Google Chrome",
            "edge": "🌐 Microsoft Edge",
            "firefox": "🌐 Mozilla Firefox",
            "brave": "🌐 Brave Browser",
            "opera": "🌐 Opera",
            "file": "📁 Tệp Cookie riêng (.txt)"
        }
        self.cookie_browser_combo.set(cookie_map_rev.get(saved_cookie, "🌐 Không dùng Cookie (Mặc định)"))

        self.cookie_file_btn = ctk.CTkButton(
            cookie_inner,
            text="📂 Chọn file cookies.txt",
            width=150,
            height=32,
            command=self.on_browse_cookie_file,
            fg_color="#475569",
            hover_color="#334155",
            font=("Segoe UI", 11)
        )
        self.cookie_file_btn.pack(side="left")
        if saved_cookie != "file":
            self.cookie_file_btn.pack_forget()

        # =========================================================================
        # 2. KHUNG NHẬP DANH SÁCH URL (BATCH INPUT CARD)
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
        # 3. KHUNG TIẾN TRÌNH & NÚT ĐIỀU KHIỂN
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
        # 4. KHUNG BẢNG HÀNG ĐỢI VỚI CỘT COOKIE RIÊNG (QUEUE TABLE)
        # =========================================================================
        self.queue_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        self.queue_card.pack(fill="both", expand=True, pady=(0, 10), padx=5)

        q_title = ctk.CTkLabel(self.queue_card, text="📑 Danh sách video hàng đợi (kèm thông tin Cookie xác thực):", font=("Segoe UI", 13, "bold"))
        q_title.pack(anchor="w", padx=15, pady=(12, 6))

        # Tiêu đề các cột
        tbl_header = ctk.CTkFrame(self.queue_card, fg_color=("#CBD5E1", "#334155"), corner_radius=6, height=30)
        tbl_header.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkLabel(tbl_header, text="STT", width=45, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(tbl_header, text="Đường dẫn URL", anchor="w", font=("Segoe UI", 11, "bold")).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(tbl_header, text="🍪 Nguồn Cookie", width=140, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(tbl_header, text="Trạng thái", width=120, font=("Segoe UI", 11, "bold")).pack(side="right", padx=10)

        self.queue_frame = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        self.queue_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def on_cookie_browser_changed(self, value):
        """Xử lý thay đổi nguồn Cookie."""
        val_map = {
            "🌐 Không dùng Cookie (Mặc định)": "none",
            "🌐 Google Chrome": "chrome",
            "🌐 Microsoft Edge": "edge",
            "🌐 Mozilla Firefox": "firefox",
            "🌐 Brave Browser": "brave",
            "🌐 Opera": "opera",
            "📁 Tệp Cookie riêng (.txt)": "file"
        }
        key = val_map.get(value, "none")
        self.config_manager.set("browser_cookie", key)

        if key == "file":
            self.cookie_file_btn.pack(side="left")
            if not self.config_manager.get("cookie_file_path"):
                self.on_browse_cookie_file()
        else:
            self.cookie_file_btn.pack_forget()

        self.log(f"[Tải hàng loạt] Đã chuyển nguồn Cookie sang: {value}")

    def on_browse_cookie_file(self):
        """Mở hộp thoại chọn tệp cookie .txt."""
        fpath = filedialog.askopenfilename(
            title="Chọn tệp cookies.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if fpath:
            self.config_manager.set("cookie_file_path", fpath)
            self.config_manager.set("browser_cookie", "file")
            fname = Path(fpath).name
            self.cookie_file_btn.configure(text=f"📄 {fname}")
            self.log(f"[Cookie] Đã nạp tệp Cookie: {fpath}")

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

        # Dọn dẹp giao diện hàng đợi
        for widget in self.queue_frame.winfo_children():
            widget.destroy()
        self.queue_items.clear()

        # Lấy nhãn nguồn cookie hiện tại
        active_cookie_label = self.cookie_browser_combo.get()
        if "Chrome" in active_cookie_label:
            cookie_badge_txt = "Chrome"
        elif "Edge" in active_cookie_label:
            cookie_badge_txt = "Edge"
        elif "Firefox" in active_cookie_label:
            cookie_badge_txt = "Firefox"
        elif "Brave" in active_cookie_label:
            cookie_badge_txt = "Brave"
        elif "Opera" in active_cookie_label:
            cookie_badge_txt = "Opera"
        elif "Tệp" in active_cookie_label:
            cookie_badge_txt = "Tệp .txt"
        else:
            cookie_badge_txt = "Chuẩn (Không)"

        for idx, url in enumerate(lines):
            row_frame = ctk.CTkFrame(self.queue_frame, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
            row_frame.pack(fill="x", pady=3)

            idx_lbl = ctk.CTkLabel(row_frame, text=f"#{idx+1}", width=45, font=("Segoe UI", 11, "bold"))
            idx_lbl.pack(side="left", padx=5)

            url_lbl = ctk.CTkLabel(row_frame, text=url, anchor="w", font=("Segoe UI", 11))
            url_lbl.pack(side="left", fill="x", expand=True, padx=5)

            cookie_lbl = ctk.CTkLabel(
                row_frame,
                text=cookie_badge_txt,
                width=140,
                font=("Segoe UI", 10, "bold"),
                fg_color=("#CBD5E1", "#334155"),
                corner_radius=6,
                height=22
            )
            cookie_lbl.pack(side="left", padx=5)

            status_lbl = ctk.CTkLabel(row_frame, text="🕒 Chờ tải", width=120, font=("Segoe UI", 11, "bold"), text_color="#64748B")
            status_lbl.pack(side="right", padx=10)

            self.queue_items.append({
                "url": url,
                "status_lbl": status_lbl,
                "cookie_lbl": cookie_lbl,
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
            status_lbl = item["status_lbl"]

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
