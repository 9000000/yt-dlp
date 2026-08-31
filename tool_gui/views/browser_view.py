"""
Màn hình Trình Duyệt Web & Bộ Quét Video Trên Trang (Browser & Web Scanner View).
Tích hợp duyệt web qua Edge WebView2, quét trích xuất toàn bộ video/reels/shorts trên bất kỳ trang web nào
kèm Thumbnail sắc nét và chọn lọc để tải hàng loạt 100% Tiếng Việt.
"""

import os
import sys
import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox

from tool_gui.page_scanner import PageVideoScanner
from tool_gui.url_detector import URLDetector

try:
    import webview
except ImportError:
    webview = None

class BrowserView(ctk.CTkFrame):
    """Giao diện trình duyệt web và quét video trên trang."""

    def __init__(self, master, on_download_single=None, on_download_batch=None, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_download_single = on_download_single
        self.on_download_batch = on_download_batch
        self.log_callback = log_callback

        self.scanned_items = []
        self.is_scanning = False

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # =========================================================================
        # 1. THANH ĐỊA CHỈ & NÚT ĐIỀU HƯỚNG TRÌNH DUYỆT
        # =========================================================================
        nav_card = ctk.CTkFrame(main_container, corner_radius=10)
        nav_card.pack(fill="x", pady=(0, 10))

        nav_inner = ctk.CTkFrame(nav_card, fg_color="transparent")
        nav_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkButton(nav_inner, text="🏠", width=34, height=34, command=lambda: self.navigate_to("https://www.youtube.com"), font=("Segoe UI", 12)).pack(side="left", padx=(0, 6))

        self.url_entry = ctk.CTkEntry(
            nav_inner,
            placeholder_text="Nhập địa chỉ trang web hoặc kênh cần quét (VD: https://www.youtube.com, tiktok.com, facebook.com...)",
            font=("Segoe UI", 11),
            height=34
        )
        self.url_entry.insert(0, "https://www.youtube.com")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.url_entry.bind("<Return>", lambda e: self.on_scan_clicked())

        self.scan_btn = ctk.CTkButton(
            nav_inner,
            text="🔍 Quét Video Trang",
            width=135,
            height=34,
            command=self.on_scan_clicked,
            font=("Segoe UI", 11, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.scan_btn.pack(side="left", padx=(0, 6))

        self.open_browser_btn = ctk.CTkButton(
            nav_inner,
            text="🌐 Mở Trình Duyệt Web",
            width=150,
            height=34,
            command=self.on_open_embedded_browser,
            font=("Segoe UI", 11, "bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED"
        )
        self.open_browser_btn.pack(side="right")

        # =========================================================================
        # 2. THANH DẤU TRANG TRUY CẬP NHANH
        # =========================================================================
        bm_bar = ctk.CTkFrame(main_container, fg_color="transparent")
        bm_bar.pack(fill="x", pady=(0, 10))

        bookmarks = [
            ("🔴 YouTube", "https://www.youtube.com"),
            ("🎵 TikTok", "https://www.tiktok.com"),
            ("🔵 Facebook", "https://www.facebook.com"),
            ("📸 Instagram", "https://www.instagram.com"),
            ("📺 Bilibili", "https://www.bilibili.com"),
            ("🔎 Google", "https://www.google.com")
        ]

        for title, url in bookmarks:
            btn = ctk.CTkButton(
                bm_bar,
                text=title,
                height=26,
                command=lambda u=url: self.navigate_to(u),
                fg_color=("#E2E8F0", "#334155"),
                text_color=("#1E293B", "#F8FAFC"),
                hover_color=("#CBD5E1", "#475569"),
                font=("Segoe UI", 10)
            )
            btn.pack(side="left", padx=(0, 6))

        # =========================================================================
        # 3. KHUNG ĐIỀU KHIỂN CHỌN TẢI HÀNG LOẠT
        # =========================================================================
        ctrl_card = ctk.CTkFrame(main_container, corner_radius=8, fg_color=("#E2E8F0", "#1E293B"), height=36)
        ctrl_card.pack(fill="x", pady=(0, 10))

        c_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        c_inner.pack(fill="x", padx=10, pady=4)

        self.scan_count_lbl = ctk.CTkLabel(c_inner, text="Danh sách: Chưa quét", font=("Segoe UI", 11, "bold"), text_color=("#2563EB", "#60A5FA"))
        self.scan_count_lbl.pack(side="left", padx=(0, 12))

        btn_all = ctk.CTkButton(c_inner, text="[✓] Chọn tất cả", width=85, height=26, command=self.select_all, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 10, "bold"))
        btn_all.pack(side="left", padx=(0, 6))

        btn_none = ctk.CTkButton(c_inner, text="[ ] Bỏ chọn", width=75, height=26, command=self.deselect_all, fg_color="#64748B", hover_color="#475569", font=("Segoe UI", 10))
        btn_none.pack(side="left", padx=(0, 12))

        self.batch_btn = ctk.CTkButton(
            c_inner,
            text="🚀 GỬI CÁC VIDEO ĐÃ CHỌN SANG TẢI HÀNG LOẠT",
            height=28,
            command=self.on_export_to_batch,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 11, "bold")
        )
        self.batch_btn.pack(side="right")

        # =========================================================================
        # 4. DANH SÁCH CÁC VIDEO QUÉT ĐƯỢC TRÊN TRANG (SCANNED VIDEO LIST)
        # =========================================================================
        self.list_scroll = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True)

        self.empty_lbl = ctk.CTkLabel(
            self.list_scroll,
            text="💡 Nhập URL trang web hoặc kênh rồi bấm 'Quét Video Trang' để lấy danh sách toàn bộ video có trên trang",
            font=("Segoe UI", 12),
            text_color=("#64748B", "#94A3B8")
        )
        self.empty_lbl.pack(pady=40)

    def navigate_to(self, url: str):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self.on_scan_clicked()

    def on_scan_clicked(self):
        url = self.url_entry.get().strip()
        if not url:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập đường dẫn trang web cần quét!")
            return

        if not URLDetector.is_valid_url(url):
            msgbox.showwarning("Cảnh báo", "Đường dẫn không hợp lệ. Vui lòng nhập đúng định dạng https://...")
            return

        self.scan_btn.configure(state="disabled", text="⏳ Đang quét...")
        self.scan_count_lbl.configure(text="Đang quét video trên trang...")
        self.log(f"[Quét trang] Bắt đầu quét: {url}")

        for widget in self.list_scroll.winfo_children():
            widget.destroy()
        self.scanned_items.clear()

        threading.Thread(target=self._scan_worker, args=(url,), daemon=True).start()

    def _scan_worker(self, url: str):
        ok, items, msg = PageVideoScanner.scan_webpage_for_videos(url)
        self.after(0, lambda: self._apply_scanned_items(ok, items, msg))

    def _apply_scanned_items(self, ok: bool, items: list, msg: str):
        self.scan_btn.configure(state="normal", text="🔍 Quét Video Trang")
        self.log(f"[Quét trang] {msg}")

        if not ok or not items:
            self.scan_count_lbl.configure(text="Tìm thấy: 0 video")
            lbl = ctk.CTkLabel(self.list_scroll, text=f"❌ {msg}", font=("Segoe UI", 12), text_color="#EF4444")
            lbl.pack(pady=30)
            return

        self.scan_count_lbl.configure(text=f"Tìm thấy: {len(items)} video trên trang")

        for item in items:
            card = ctk.CTkFrame(self.list_scroll, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
            card.pack(fill="x", pady=4, padx=2)

            c_box = ctk.CTkFrame(card, fg_color="transparent")
            c_box.pack(fill="x", padx=10, pady=8)

            chk_var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(c_box, text="", variable=chk_var, width=22)
            chk.pack(side="left", padx=(0, 10))

            # Khung Ảnh Thumbnail Video (110x62)
            thumb_lbl = ctk.CTkLabel(
                c_box,
                text="🖼️",
                width=110,
                height=62,
                corner_radius=6,
                fg_color=("#E2E8F0", "#0F172A"),
                font=("Segoe UI", 10)
            )
            thumb_lbl.pack(side="left", padx=(0, 12))

            thumb_url = item.get("thumbnail_url")
            if thumb_url:
                threading.Thread(target=self._async_load_thumb, args=(thumb_url, thumb_lbl), daemon=True).start()

            info_col = ctk.CTkFrame(c_box, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True)

            title_row = ctk.CTkFrame(info_col, fg_color="transparent")
            title_row.pack(fill="x", pady=(0, 2))

            plat = item.get("platform", "Đa nền tảng")
            badge_colors = {"YouTube": "#EF4444", "TikTok": "#111827", "Facebook": "#2563EB", "Instagram": "#E11D48", "Bilibili": "#00A1D6"}
            plat_badge = ctk.CTkLabel(
                title_row,
                text=plat,
                fg_color=badge_colors.get(plat, "#64748B"),
                text_color="white",
                corner_radius=4,
                font=("Segoe UI", 9, "bold"),
                width=65,
                height=18
            )
            plat_badge.pack(side="left", padx=(0, 6))

            t_text = item.get("title", item.get("url"))
            lbl_title = ctk.CTkLabel(
                title_row,
                text=t_text[:85] + "..." if len(t_text) > 85 else t_text,
                font=("Segoe UI", 11, "bold"),
                anchor="w"
            )
            lbl_title.pack(side="left", fill="x", expand=True)

            sub_row = ctk.CTkFrame(info_col, fg_color="transparent")
            sub_row.pack(fill="x", pady=(0, 2))

            u_info = f"👤 {item.get('uploader')}" if item.get('uploader') and item.get('uploader') != '--' else ""
            if u_info:
                u_lbl = ctk.CTkLabel(sub_row, text=u_info[:40], font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), anchor="w")
                u_lbl.pack(side="left", padx=(0, 10))

            dur_lbl = ctk.CTkLabel(sub_row, text=f"⏱️ {item.get('duration_str', '--:--')}", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"))
            dur_lbl.pack(side="left")

            url_row = ctk.CTkFrame(info_col, fg_color="transparent")
            url_row.pack(fill="x")
            url_lbl = ctk.CTkLabel(url_row, text=f"🔗 {item.get('url')}", font=("Segoe UI", 9), text_color=("#475569", "#94A3B8"), anchor="w")
            url_lbl.pack(side="left", fill="x", expand=True)

            dl_btn = ctk.CTkButton(
                c_box,
                text="📥 Tải Ngay",
                width=80,
                height=32,
                command=lambda u=item["url"]: self.on_single_download_clicked(u),
                fg_color="#3B82F6",
                hover_color="#2563EB",
                font=("Segoe UI", 10, "bold")
            )
            dl_btn.pack(side="right", padx=(8, 0))

            self.scanned_items.append({
                "data": item,
                "chk_var": chk_var,
                "frame": card
            })

    def _async_load_thumb(self, url: str, target_lbl: ctk.CTkLabel):
        try:
            img = URLDetector.load_thumbnail_image(url, size=(110, 62))
            if img:
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(110, 62))
                self.after(0, lambda: target_lbl.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def select_all(self):
        for item in self.scanned_items:
            item["chk_var"].set(True)

    def deselect_all(self):
        for item in self.scanned_items:
            item["chk_var"].set(False)

    def on_single_download_clicked(self, url: str):
        if self.on_download_single:
            self.on_download_single(url)

    def on_export_to_batch(self):
        selected_urls = [item["data"]["url"] for item in self.scanned_items if item["chk_var"].get()]
        if not selected_urls:
            msgbox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một video để gửi sang Tải Hàng Loạt!")
            return

        if self.on_download_batch:
            self.on_download_batch(selected_urls)
            self.log(f"[Quét trang] Đã gửi {len(selected_urls)} video sang Tải Hàng Loạt.")
            msgbox.showinfo("Thành công", f"Đã chuyển {len(selected_urls)} video sang danh sách Tải Hàng Loạt!")

    def on_open_embedded_browser(self):
        """Mở cửa sổ trình duyệt Edge WebView2 nhúng trong tiến trình riêng."""
        import subprocess
        from pathlib import Path
        target_url = self.url_entry.get().strip() or "https://www.youtube.com"
        self.log(f"[Trình duyệt] Đang khởi chạy Trình duyệt Web (Edge WebView2): {target_url}")

        try:
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable, "--browser", target_url])
            else:
                run_gui_py = Path(__file__).resolve().parent.parent.parent / "run_gui.py"
                subprocess.Popen([sys.executable, str(run_gui_py), "--browser", target_url])
        except Exception as e:
            self.log(f"[Trình duyệt] Mở qua trình duyệt hệ thống: {e}")
            import webbrowser
            webbrowser.open(target_url)
