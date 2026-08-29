"""
Màn hình Quản lý & Cập nhật Phụ trợ (Tools & Updater View).
Quản lý trạng thái, tự động tải và cập nhật FFmpeg & yt-dlp 100% Tiếng Việt.
"""

import threading
import customtkinter as ctk
import tkinter.messagebox as msgbox

from tool_gui.updater import UpdaterManager
from tool_gui.config import ConfigManager

class ToolsView(ctk.CTkFrame):
    """Giao diện quản lý phụ trợ và cập nhật."""

    def __init__(self, master, config_manager: ConfigManager, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.log_callback = log_callback
        self.updater = UpdaterManager()

        self.setup_ui()
        self.refresh_status()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Tiêu đề chung
        header = ctk.CTkLabel(
            self.scroll,
            text="🛠️ QUẢN LÝ PHỤ TRỢ & CẬP NHẬT HỆ THỐNG",
            font=("Segoe UI", 16, "bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=5, pady=(0, 15))

        # 1. THẺ FFMPEG
        ffmpeg_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        ffmpeg_card.pack(fill="x", pady=(0, 15), padx=5)

        ff_title = ctk.CTkLabel(ffmpeg_card, text="🎬 Trình Xử Lý Video & Âm Thanh (FFmpeg)", font=("Segoe UI", 14, "bold"))
        ff_title.pack(anchor="w", padx=15, pady=(15, 6))

        ff_desc = ctk.CTkLabel(
            ffmpeg_card,
            text="FFmpeg là phụ trợ bắt buộc để ghép luồng Video 1080p/2K/4K với Audio chất lượng cao, trích xuất nhạc MP3/M4A và nhúng phụ đề.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
            wraplength=600,
            justify="left"
        )
        ff_desc.pack(anchor="w", padx=15, pady=(0, 10))

        # Khung trạng thái FFmpeg
        ff_info_box = ctk.CTkFrame(ffmpeg_card, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
        ff_info_box.pack(fill="x", padx=15, pady=(0, 12))

        self.ff_status_lbl = ctk.CTkLabel(ff_info_box, text="Trạng thái: Đang kiểm tra...", font=("Segoe UI", 12, "bold"))
        self.ff_status_lbl.pack(anchor="w", padx=15, pady=(10, 4))

        self.ff_path_lbl = ctk.CTkLabel(ff_info_box, text="Đường dẫn: --", font=("Segoe UI", 11), text_color=("#64748B", "#94A3B8"))
        self.ff_path_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Tiến trình tải FFmpeg
        self.ff_prog_lbl = ctk.CTkLabel(ffmpeg_card, text="", font=("Segoe UI", 11))
        self.ff_prog_lbl.pack(anchor="w", padx=15, pady=(0, 4))

        self.ff_prog_bar = ctk.CTkProgressBar(ffmpeg_card, height=10, corner_radius=5)
        self.ff_prog_bar.set(0.0)
        self.ff_prog_bar.pack(fill="x", padx=15, pady=(0, 12))
        self.ff_prog_bar.pack_forget()

        # Nút thao tác FFmpeg
        ff_btn_row = ctk.CTkFrame(ffmpeg_card, fg_color="transparent")
        ff_btn_row.pack(fill="x", padx=15, pady=(0, 15))

        self.ff_install_btn = ctk.CTkButton(
            ff_btn_row,
            text="⬇️ TỰ ĐỘNG TẢI & CÀI ĐẶT FFMPEG",
            command=self.on_download_ffmpeg,
            height=38,
            font=("Segoe UI", 12, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.ff_install_btn.pack(side="left", padx=(0, 10))

        self.ff_refresh_btn = ctk.CTkButton(
            ff_btn_row,
            text="🔄 Kiểm tra lại",
            command=self.refresh_status,
            width=120,
            height=38,
            font=("Segoe UI", 12),
            fg_color="#64748B",
            hover_color="#475569"
        )
        self.ff_refresh_btn.pack(side="left")

        # 2. THẺ YT-DLP CORE
        ytdlp_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        ytdlp_card.pack(fill="x", pady=(0, 15), padx=5)

        yt_title = ctk.CTkLabel(ytdlp_card, text="🚀 Lõi Tải Video Đa Nền Tảng (yt-dlp Engine)", font=("Segoe UI", 14, "bold"))
        yt_title.pack(anchor="w", padx=15, pady=(15, 6))

        yt_desc = ctk.CTkLabel(
            ytdlp_card,
            text="Cập nhật yt-dlp thường xuyên giúp khắc phục các lỗi thay đổi API từ YouTube, TikTok, Facebook, Instagram.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
            wraplength=600,
            justify="left"
        )
        yt_desc.pack(anchor="w", padx=15, pady=(0, 10))

        # Khung thông tin yt-dlp
        yt_info_box = ctk.CTkFrame(ytdlp_card, fg_color=("#E2E8F0", "#1E293B"), corner_radius=8)
        yt_info_box.pack(fill="x", padx=15, pady=(0, 12))

        self.yt_ver_lbl = ctk.CTkLabel(yt_info_box, text=f"Phiên bản hiện tại: {self.updater.get_ytdlp_version()}", font=("Segoe UI", 12, "bold"))
        self.yt_ver_lbl.pack(anchor="w", padx=15, pady=(10, 4))

        self.yt_status_lbl = ctk.CTkLabel(yt_info_box, text="Trạng thái: Đang hoạt động bình thường", font=("Segoe UI", 11), text_color="#10B981")
        self.yt_status_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Nút thao tác yt-dlp
        yt_btn_row = ctk.CTkFrame(ytdlp_card, fg_color="transparent")
        yt_btn_row.pack(fill="x", padx=15, pady=(0, 15))

        self.yt_update_btn = ctk.CTkButton(
            yt_btn_row,
            text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP",
            command=self.on_update_ytdlp,
            height=38,
            font=("Segoe UI", 12, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.yt_update_btn.pack(side="left", padx=(0, 10))

        # 3. TÙY CHỌN TỰ ĐỘNG CẬP NHẬT
        auto_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        auto_card.pack(fill="x", pady=(0, 15), padx=5)

        self.auto_check_cb = ctk.CTkCheckBox(
            auto_card,
            text="Tự động kiểm tra và cập nhật phụ trợ khi khởi động phần mềm",
            font=("Segoe UI", 12, "bold"),
            command=self.on_toggle_auto_check
        )
        if self.config_manager.get("auto_check_updates", True):
            self.auto_check_cb.select()
        self.auto_check_cb.pack(anchor="w", padx=15, pady=15)

    def on_toggle_auto_check(self):
        val = bool(self.auto_check_cb.get())
        self.config_manager.set("auto_check_updates", val)

    def refresh_status(self):
        """Làm mới thông tin hiển thị FFmpeg và yt-dlp."""
        is_ff_ok = self.updater.is_ffmpeg_installed()
        ff_ver = self.updater.get_ffmpeg_version()
        ff_path = self.updater.get_ffmpeg_path()

        if is_ff_ok:
            self.ff_status_lbl.configure(text=f"Trạng thái: 🟢 Đã cài đặt (Phiên bản: {ff_ver})", text_color="#10B981")
            self.ff_path_lbl.configure(text=f"Đường dẫn: {ff_path}")
            self.ff_install_btn.configure(text="🔄 CẬP NHẬT LẠI FFMPEG", fg_color="#3B82F6", hover_color="#2563EB")
        else:
            self.ff_status_lbl.configure(text="Trạng thái: ⚠️ Chưa phát hiện FFmpeg", text_color="#EF4444")
            self.ff_path_lbl.configure(text="Đường dẫn: Chưa có trong bin/ hoặc PATH")
            self.ff_install_btn.configure(text="⬇️ TỰ ĐỘNG TẢI & CÀI ĐẶT FFMPEG", fg_color="#10B981", hover_color="#059669")

        self.yt_ver_lbl.configure(text=f"Phiên bản yt-dlp hiện tại: {self.updater.get_ytdlp_version()}")

    def on_download_ffmpeg(self):
        """Khởi chạy tải và cài đặt FFmpeg tự động."""
        self.ff_install_btn.configure(state="disabled")
        self.ff_prog_bar.pack(fill="x", padx=15, pady=(0, 12))
        self.ff_prog_bar.set(0.0)
        self.ff_prog_lbl.configure(text="Đang kết nối tới máy chủ...")
        self.log("[Phụ trợ] Bắt đầu tải và cấu hình FFmpeg...")

        threading.Thread(target=self._download_ffmpeg_worker, daemon=True).start()

    def _download_ffmpeg_worker(self):
        def on_prog(frac):
            self.after(0, lambda: self.ff_prog_bar.set(frac))

        def on_stat(msg):
            self.after(0, lambda: self.ff_prog_lbl.configure(text=msg))
            self.log(f"[FFmpeg] {msg}")

        success, msg = self.updater.download_and_install_ffmpeg(progress_callback=on_prog, status_callback=on_stat)
        self.after(0, lambda: self._finish_ffmpeg_install(success, msg))

    def _finish_ffmpeg_install(self, success: bool, msg: str):
        self.ff_install_btn.configure(state="normal")
        self.refresh_status()
        if success:
            msgbox.showinfo("Thành công", "Đã cài đặt FFmpeg thành công và sẵn sàng hoạt động!")
        else:
            msgbox.showerror("Lỗi", msg)

    def on_update_ytdlp(self):
        """Kiểm tra và cập nhật yt-dlp."""
        self.yt_update_btn.configure(state="disabled", text="⏳ Đang kiểm tra...")
        self.log("[yt-dlp] Bắt đầu kiểm tra phiên bản mới...")

        threading.Thread(target=self._update_ytdlp_worker, daemon=True).start()

    def _update_ytdlp_worker(self):
        has_up, latest_ver = self.updater.check_ytdlp_latest_version()
        if has_up:
            self.after(0, lambda: self._prompt_ytdlp_update(latest_ver))
        else:
            self.after(0, lambda: self._finish_ytdlp_check(latest_ver))

    def _prompt_ytdlp_update(self, latest_ver: str):
        self.yt_update_btn.configure(state="normal", text="🔄 CẬP NHẬT YT-DLP")
        self.yt_status_lbl.configure(text=f"Có phiên bản mới: {latest_ver}!", text_color="#3B82F6")
        
        ans = msgbox.askyesno("Cập nhật yt-dlp", f"Phát hiện phiên bản mới: {latest_ver}\nBạn có muốn nâng cấp ngay không?")
        if ans:
            self.yt_update_btn.configure(state="disabled", text="⏳ Đang cập nhật...")
            threading.Thread(target=self._run_ytdlp_upgrade, daemon=True).start()

    def _run_ytdlp_upgrade(self):
        def on_stat(msg):
            self.log(f"[yt-dlp] {msg}")

        success, msg = self.updater.update_ytdlp(status_callback=on_stat)
        self.after(0, lambda: self._finish_ytdlp_upgrade(success, msg))

    def _finish_ytdlp_upgrade(self, success: bool, msg: str):
        self.yt_update_btn.configure(state="normal", text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP")
        self.refresh_status()
        if success:
            msgbox.showinfo("Thành công", "Đã cập nhật yt-dlp thành công!")
        else:
            msgbox.showerror("Lỗi cập nhật", msg)

    def _finish_ytdlp_check(self, ver_info: str):
        self.yt_update_btn.configure(state="normal", text="🔄 KIỂM TRA & CẬP NHẬT YT-DLP")
        self.yt_status_lbl.configure(text="Bạn đang sử dụng phiên bản mới nhất.", text_color="#10B981")
        msgbox.showinfo("Thông báo", f"Lõi yt-dlp đã ở phiên bản mới nhất ({ver_info})!")
