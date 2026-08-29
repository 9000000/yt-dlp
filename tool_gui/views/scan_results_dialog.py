"""
Hộp Thoại Danh Sách Video Quét Được (Scan Results Dialog).
Hiển thị danh sách toàn bộ video bóc tách được từ trang web kèm Ảnh Thumbnail 16:9, Tiêu đề, Thời lượng
cho phép người dùng kiểm tra, chọn/bỏ chọn trước khi quyết định Tải Hàng Loạt hoặc Tải Đơn lẻ.
"""

import threading
import tkinter as tk
import customtkinter as ctk
import tkinter.messagebox as msgbox
from PIL import Image
from tool_gui.url_detector import URLDetector

class ScanResultsDialog(ctk.CTkToplevel):
    """Cửa sổ hiển thị danh sách video quét được trước khi tải."""

    def __init__(self, master, url: str, results: list, on_export_batch=None, on_download_single=None):
        super().__init__(master)
        self.target_url = url
        self.raw_results = results or []
        self.on_export_batch = on_export_batch
        self.on_download_single = on_download_single
        self.item_entries = []

        self.title("ToolDL Pro - Danh Sách Video Quét Được")
        self.geometry("980x620")
        self.minsize(750, 480)
        self.transient(master)
        self.after(50, self.lift)

        self.setup_ui()

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=14, pady=12)

        # 1. Thanh tiêu đề & Thông tin quét
        top_bar = ctk.CTkFrame(container, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"))
        top_bar.pack(fill="x", pady=(0, 8))

        tb_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        tb_inner.pack(fill="x", padx=12, pady=10)

        left_info = ctk.CTkFrame(tb_inner, fg_color="transparent")
        left_info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left_info,
            text=f"🔍 Tìm thấy {len(self.raw_results)} video từ trang web:",
            font=("Segoe UI", 12, "bold"),
            text_color=("#2563EB", "#60A5FA")
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_info,
            text=self.target_url,
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
            anchor="w"
        ).pack(anchor="w")

        # Nút Chọn tất cả / Bỏ chọn
        sel_row = ctk.CTkFrame(tb_inner, fg_color="transparent")
        sel_row.pack(side="right")

        ctk.CTkButton(
            sel_row,
            text="[✓] Chọn tất cả",
            width=95,
            height=30,
            command=self.select_all,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            sel_row,
            text="[ ] Bỏ chọn",
            width=80,
            height=30,
            command=self.deselect_all,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10)
        ).pack(side="left")

        # 2. Bảng cuộn danh sách video dạng thẻ (Card List with 16:9 Thumbnail)
        self.scroll_frame = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

        if not self.raw_results:
            ctk.CTkLabel(
                self.scroll_frame,
                text="❌ Không tìm thấy video nào trên trang web này.",
                font=("Segoe UI", 12),
                text_color="#EF4444"
            ).pack(pady=40)
        else:
            for item in self.raw_results:
                card = ctk.CTkFrame(self.scroll_frame, corner_radius=8, fg_color=("#F8FAFC", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
                card.pack(fill="x", pady=4, padx=2)

                c_box = ctk.CTkFrame(card, fg_color="transparent")
                c_box.pack(fill="x", padx=10, pady=8)

                chk_var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(c_box, text="", variable=chk_var, width=22)
                chk.pack(side="left", padx=(0, 10))

                # Ảnh Thumbnail 16:9 sắc nét (110x62 px)
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

                t_row = ctk.CTkFrame(info_col, fg_color="transparent")
                t_row.pack(fill="x", pady=(0, 2))

                plat = item.get("platform", "Đa nền tảng")
                badge_colors = {"YouTube": "#EF4444", "TikTok": "#111827", "Facebook": "#2563EB", "Instagram": "#E11D48", "Bilibili": "#00A1D6"}
                plat_badge = ctk.CTkLabel(t_row, text=plat, fg_color=badge_colors.get(plat, "#64748B"), text_color="white", corner_radius=4, font=("Segoe UI", 9, "bold"), width=65, height=18)
                plat_badge.pack(side="left", padx=(0, 6))

                t_text = item.get("title", item.get("url"))
                lbl_t = ctk.CTkLabel(t_row, text=t_text[:85] + "..." if len(t_text) > 85 else t_text, font=("Segoe UI", 11, "bold"), anchor="w")
                lbl_t.pack(side="left", fill="x", expand=True)

                sub_r = ctk.CTkFrame(info_col, fg_color="transparent")
                sub_r.pack(fill="x", pady=(0, 2))

                u_info = f"👤 {item.get('uploader')}" if item.get('uploader') and item.get('uploader') != '--' else ""
                if u_info:
                    ctk.CTkLabel(sub_r, text=u_info[:35], font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), anchor="w").pack(side="left", padx=(0, 10))

                ctk.CTkLabel(sub_r, text=f"⏱️ {item.get('duration_str', '--:--')}", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8")).pack(side="left")

                url_row = ctk.CTkFrame(info_col, fg_color="transparent")
                url_row.pack(fill="x")
                ctk.CTkLabel(url_row, text=f"🔗 {item.get('url')}", font=("Segoe UI", 9), text_color=("#475569", "#94A3B8"), anchor="w").pack(side="left", fill="x", expand=True)

                # Nút tải đơn lẻ video này
                dl_single_btn = ctk.CTkButton(
                    c_box,
                    text="📥 Tải Video Này",
                    width=105,
                    height=32,
                    command=lambda u=item["url"]: self._click_single_download(u),
                    fg_color="#3B82F6",
                    hover_color="#2563EB",
                    font=("Segoe UI", 10, "bold")
                )
                dl_single_btn.pack(side="right", padx=(8, 0))

                self.item_entries.append({
                    "data": item,
                    "chk_var": chk_var
                })

        # 3. Thanh tác vụ dưới cùng (Bottom Actions)
        bottom_bar = ctk.CTkFrame(container, fg_color="transparent")
        bottom_bar.pack(fill="x")

        self.selected_count_lbl = ctk.CTkLabel(bottom_bar, text=f"Đã chọn: {len(self.raw_results)}/{len(self.raw_results)} video", font=("Segoe UI", 11, "bold"))
        self.selected_count_lbl.pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="✖ Đóng",
            width=80,
            height=36,
            command=self.destroy,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 11)
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            bottom_bar,
            text="🚀 GỬI CÁC VIDEO ĐÃ CHỌN SANG TẢI HÀNG LOẠT",
            height=36,
            command=self._click_export_batch,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 11, "bold")
        ).pack(side="right")

    def _async_load_thumb(self, url: str, target_lbl: ctk.CTkLabel):
        try:
            img = URLDetector.load_thumbnail_image(url, size=(110, 62))
            if img:
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(110, 62))
                self.after(0, lambda: target_lbl.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def select_all(self):
        for entry in self.item_entries:
            entry["chk_var"].set(True)
        self.update_count()

    def deselect_all(self):
        for entry in self.item_entries:
            entry["chk_var"].set(False)
        self.update_count()

    def update_count(self):
        sel = sum(1 for e in self.item_entries if e["chk_var"].get())
        self.selected_count_lbl.configure(text=f"Đã chọn: {sel}/{len(self.item_entries)} video")

    def _click_single_download(self, url: str):
        if self.on_download_single:
            self.on_download_single(url)
        self.destroy()

    def _click_export_batch(self):
        selected_urls = [e["data"]["url"] for e in self.item_entries if e["chk_var"].get()]
        if not selected_urls:
            msgbox.showwarning("Cảnh báo", "Vui lòng tích chọn ít nhất một video để tải!")
            return

        if self.on_export_batch:
            self.on_export_batch(selected_urls)
        self.destroy()
