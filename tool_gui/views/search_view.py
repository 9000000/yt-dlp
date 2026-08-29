"""
Màn hình Tìm Kiếm Video Trực Tiếp (Search View).
Tìm kiếm video theo từ khóa trên YouTube và đa nền tảng, hiển thị danh sách trực quan kèm Thumbnail,
hỗ trợ tải ngay từng video hoặc chọn nhiều video để tải hàng loạt 100% Tiếng Việt.
"""

import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox
from PIL import Image

from tool_gui.page_scanner import PageVideoScanner
from tool_gui.url_detector import URLDetector

class SearchView(ctk.CTkFrame):
    """Giao diện tìm kiếm video trực tiếp."""

    def __init__(self, master, on_download_single=None, on_download_batch=None, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_download_single = on_download_single
        self.on_download_batch = on_download_batch
        self.log_callback = log_callback

        self.search_results = []
        self.is_searching = False

        self.setup_ui()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # =========================================================================
        # 1. KHUNG TÌM KIẾM TRÊN CÙNG
        # =========================================================================
        search_card = ctk.CTkFrame(main_container, corner_radius=10)
        search_card.pack(fill="x", pady=(0, 10))

        s_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        s_inner.pack(fill="x", padx=12, pady=10)

        lbl_s = ctk.CTkLabel(s_inner, text="🔍 Từ khóa:", font=("Segoe UI", 12, "bold"))
        lbl_s.pack(side="left", padx=(0, 8))

        self.search_entry = ctk.CTkEntry(
            s_inner,
            placeholder_text="Nhập tên bài hát, video, chủ đề cần tìm (VD: nhạc lofi chill, hài hước 2026...)",
            font=("Segoe UI", 12),
            height=36
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.on_search_clicked())

        self.platform_combo = ctk.CTkComboBox(
            s_inner,
            values=["🔴 YouTube", "🎵 Đa nền tảng"],
            width=130,
            height=36
        )
        self.platform_combo.set("🔴 YouTube")
        self.platform_combo.pack(side="left", padx=(0, 8))

        self.search_btn = ctk.CTkButton(
            s_inner,
            text="🔍 Tìm Kiếm",
            width=110,
            height=36,
            command=self.on_search_clicked,
            font=("Segoe UI", 12, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.search_btn.pack(side="left")

        # =========================================================================
        # 2. KHUNG ĐIỀU KHIỂN & CHỌN TẢI HÀNG LOẠT
        # =========================================================================
        ctrl_card = ctk.CTkFrame(main_container, corner_radius=8, fg_color=("#E2E8F0", "#1E293B"), height=38)
        ctrl_card.pack(fill="x", pady=(0, 10))

        c_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        c_inner.pack(fill="x", padx=10, pady=4)

        self.result_count_lbl = ctk.CTkLabel(c_inner, text="Kết quả: Chưa có tìm kiếm", font=("Segoe UI", 11, "bold"), text_color=("#2563EB", "#60A5FA"))
        self.result_count_lbl.pack(side="left", padx=(0, 15))

        btn_select_all = ctk.CTkButton(
            c_inner,
            text="[✓] Chọn tất cả",
            width=90,
            height=28,
            command=self.select_all,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10, "bold")
        )
        btn_select_all.pack(side="left", padx=(0, 6))

        btn_deselect = ctk.CTkButton(
            c_inner,
            text="[ ] Bỏ chọn",
            width=80,
            height=28,
            command=self.deselect_all,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10)
        )
        btn_deselect.pack(side="left", padx=(0, 15))

        self.batch_export_btn = ctk.CTkButton(
            c_inner,
            text="🚀 GỬI CÁC VIDEO ĐÃ CHỌN SANG TẢI HÀNG LOẠT",
            height=30,
            command=self.on_export_to_batch,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 11, "bold")
        )
        self.batch_export_btn.pack(side="right")

        # =========================================================================
        # 3. DANH SÁCH KẾT QUẢ TÌM KIẾM
        # =========================================================================
        self.result_scroll = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        self.result_scroll.pack(fill="both", expand=True)

        self.empty_lbl = ctk.CTkLabel(
            self.result_scroll,
            text="💡 Nhập từ khóa vào ô trên và bấm 'Tìm Kiếm' để khám phá video",
            font=("Segoe UI", 12),
            text_color=("#64748B", "#94A3B8")
        )
        self.empty_lbl.pack(pady=40)

    def on_search_clicked(self):
        kw = self.search_entry.get().strip()
        if not kw:
            msgbox.showwarning("Cảnh báo", "Vui lòng nhập từ khóa tìm kiếm!")
            return

        self.search_btn.configure(state="disabled", text="⏳ Đang tìm...")
        self.result_count_lbl.configure(text=f"Đang tìm kiếm '{kw}'...")
        self.log(f"[Tìm kiếm] Bắt đầu tìm: '{kw}'")

        for widget in self.result_scroll.winfo_children():
            widget.destroy()
        self.search_results.clear()

        threading.Thread(target=self._search_worker, args=(kw,), daemon=True).start()

    def _search_worker(self, keyword: str):
        plat = self.platform_combo.get()
        ok, results, msg = PageVideoScanner.search_videos_by_keyword(keyword, max_results=20, platform=plat)
        self.after(0, lambda: self._apply_search_results(ok, results, msg))

    def _apply_search_results(self, ok: bool, results: list, msg: str):
        self.search_btn.configure(state="normal", text="🔍 Tìm Kiếm")
        self.log(f"[Tìm kiếm] {msg}")

        if not ok or not results:
            self.result_count_lbl.configure(text="Kết quả: 0 video")
            lbl = ctk.CTkLabel(self.result_scroll, text=f"❌ {msg}", font=("Segoe UI", 12), text_color="#EF4444")
            lbl.pack(pady=30)
            return

        self.result_count_lbl.configure(text=f"Kết quả: Tìm thấy {len(results)} video")

        for item in results:
            card = ctk.CTkFrame(self.result_scroll, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
            card.pack(fill="x", pady=4, padx=2)

            c_box = ctk.CTkFrame(card, fg_color="transparent")
            c_box.pack(fill="x", padx=10, pady=8)

            # Checkbox chọn tải
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

            # Thông tin video
            info_col = ctk.CTkFrame(c_box, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True)

            title_row = ctk.CTkFrame(info_col, fg_color="transparent")
            title_row.pack(fill="x", pady=(0, 2))

            plat = item.get("platform", "YouTube")
            plat_badge = ctk.CTkLabel(
                title_row,
                text=plat,
                fg_color="#EF4444",
                text_color="white",
                corner_radius=4,
                font=("Segoe UI", 9, "bold"),
                width=65,
                height=18
            )
            plat_badge.pack(side="left", padx=(0, 6))

            t_text = item.get("title", "Video")
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

            self.search_results.append({
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
        for item in self.search_results:
            item["chk_var"].set(True)

    def deselect_all(self):
        for item in self.search_results:
            item["chk_var"].set(False)

    def on_single_download_clicked(self, url: str):
        if self.on_download_single:
            self.on_download_single(url)

    def on_export_to_batch(self):
        selected_urls = [item["data"]["url"] for item in self.search_results if item["chk_var"].get()]
        if not selected_urls:
            msgbox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một video để chuyển sang Tải Hàng Loạt!")
            return

        if self.on_download_batch:
            self.on_download_batch(selected_urls)
            self.log(f"[Tìm kiếm] Đã chuyển {len(selected_urls)} video sang Tải Hàng Loạt.")
            msgbox.showinfo("Thành công", f"Đã chuyển {len(selected_urls)} video sang danh sách Tải Hàng Loạt!")
