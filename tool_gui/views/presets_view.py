"""
Màn hình Quản Lý Cài Đặt Sẵn Chuyên Sâu (Presets Management View).
Cung cấp bộ công cụ cấu hình chuyên sâu và toàn diện: Định dạng, Chất lượng, Đa luồng, Phụ đề, Metadata, Chapters, Video Codec, FPS.
"""

import customtkinter as ctk
import tkinter.messagebox as msgbox
from tool_gui.config import ConfigManager, DEFAULT_DOWNLOAD_PRESETS

class PresetsView(ctk.CTkFrame):
    """Giao diện quản lý cấu hình mẫu tải sẵn (Presets) chuyên nghiệp."""

    def __init__(self, master, config_manager: ConfigManager, on_presets_updated=None, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.on_presets_updated = on_presets_updated
        self.log_callback = log_callback

        self.setup_ui()
        self.refresh_presets_list()

    def log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def setup_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=12)

        # 1. THANH TIÊU ĐỀ & CHỌN PRESET
        top_card = ctk.CTkFrame(main_container, corner_radius=10)
        top_card.pack(fill="x", pady=(0, 10))

        top_inner = ctk.CTkFrame(top_card, fg_color="transparent")
        top_inner.pack(fill="x", padx=15, pady=12)

        hdr_row = ctk.CTkFrame(top_inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            hdr_row,
            text="⚡ QUẢN LÝ CẤU HÌNH SẴN (DOWNLOAD PRESETS)",
            font=("Segoe UI", 15, "bold"),
            text_color=("#2563EB", "#38BDF8")
        ).pack(side="left")

        self.btn_reset_defaults = ctk.CTkButton(
            hdr_row,
            text="🔄 Khôi phục Mặc định",
            width=140,
            height=28,
            command=self.on_reset_defaults_clicked,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10)
        )
        self.btn_reset_defaults.pack(side="right")

        ctk.CTkLabel(
            top_inner,
            text="Tạo và tùy biến các cấu hình tải nhanh chuyên sâu (Định dạng, Độ phân giải, Đa luồng tải, Phụ đề, Metadata, Tách Chapter) để áp dụng 1-click khi tải đơn hoặc tải hàng loạt.",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
            wraplength=780,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # Thanh chọn Preset
        sel_row = ctk.CTkFrame(top_inner, fg_color="transparent")
        sel_row.pack(fill="x")

        ctk.CTkLabel(sel_row, text="Chọn Preset đang lưu:", font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 8))

        self.preset_select_combo = ctk.CTkComboBox(
            sel_row,
            values=[],
            command=self.on_preset_selected_in_combo,
            height=32,
            font=("Segoe UI", 11)
        )
        self.preset_select_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_new = ctk.CTkButton(
            sel_row,
            text="➕ Tạo Preset Mới",
            width=120,
            height=32,
            command=self.on_new_preset_clicked,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 11, "bold")
        )
        self.btn_new.pack(side="left", padx=(0, 6))

        self.btn_delete = ctk.CTkButton(
            sel_row,
            text="🗑️ Xóa",
            width=70,
            height=32,
            command=self.on_delete_preset_clicked,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Segoe UI", 11, "bold")
        )
        self.btn_delete.pack(side="left")

        # 2. KHUNG NỘI DUNG CHÍNH (2 CỘT: CƠ BẢN & NÂNG CAO CHUYÊN SÂU)
        content_scroll = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content_scroll.pack(fill="both", expand=True)

        grid_cols = ctk.CTkFrame(content_scroll, fg_color="transparent")
        grid_cols.pack(fill="both", expand=True)
        grid_cols.grid_columnconfigure((0, 1), weight=1)

        # =====================================================================
        # CỘT TRÁI: CÀI ĐẶT CƠ BẢN & ĐỊNH DẠNG
        # =====================================================================
        left_card = ctk.CTkFrame(grid_cols, corner_radius=10)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        l_in = ctk.CTkFrame(left_card, fg_color="transparent")
        l_in.pack(fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(l_in, text="⚙️ CÀI ĐẶT CƠ BẢN & ĐỊNH DẠNG", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(l_in, text="Tên cấu hình Preset:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(l_in, font=("Segoe UI", 11), height=30, placeholder_text="VD: 🎵 Nhạc MP3 320k Studio")
        self.name_entry.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(l_in, text="Mô tả / Ghi chú:", font=("Segoe UI", 10)).pack(anchor="w")
        self.desc_entry = ctk.CTkEntry(l_in, font=("Segoe UI", 10), height=28, placeholder_text="Mô tả ngắn về mục đích cấu hình này...")
        self.desc_entry.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(l_in, text="Loại nội dung tải:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.mode_seg = ctk.CTkSegmentedButton(l_in, values=["🎬 Video + Âm thanh", "🎵 Chỉ lấy Âm thanh"], command=self.on_mode_changed, height=28)
        self.mode_seg.set("🎬 Video + Âm thanh")
        self.mode_seg.pack(fill="x", pady=(2, 8))

        grid_l = ctk.CTkFrame(l_in, fg_color="transparent")
        grid_l.pack(fill="x", pady=(0, 6))
        grid_l.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_l, text="Độ phân giải tối đa:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(grid_l, text="Định dạng Video Container:", font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.quality_combo = ctk.CTkComboBox(grid_l, values=[
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
            "⚡ 240p",
            "⚡ 144p"
        ], height=28)
        self.quality_combo.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(0, 6))

        self.fmt_combo = ctk.CTkComboBox(grid_l, values=[
            "MP4 (Khuyên dùng - Chuẩn quốc tế)",
            "MKV (Matroska - Hỗ trợ đa luồng)",
            "WEBM (Google WebM)",
            "MOV (Apple QuickTime)",
            "AVI (Audio Video Interleave)",
            "TS (Transport Stream)",
            "FLV (Flash Video)",
            "3GP (Di động cổ điển)",
            "OGV (Ogg Video)",
            "WMV (Windows Media)"
        ], height=28)
        self.fmt_combo.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(0, 6))

        ctk.CTkLabel(grid_l, text="Bitrate Âm thanh (Audio Codec):", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        ctk.CTkLabel(grid_l, text="Định dạng Âm thanh (Audio Format):", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(6, 0))

        self.audio_combo = ctk.CTkComboBox(grid_l, values=[
            "MP3 - 320 kbps (Cực cao - Studio Master)",
            "MP3 - 256 kbps (Chất lượng rất cao)",
            "MP3 - 192 kbps (Tiêu chuẩn cao)",
            "MP3 - 128 kbps (Tiết kiệm dung lượng)",
            "MP3 - 96 kbps (Siêu nhẹ)",
            "M4A / AAC (Gốc - 256 kbps)",
            "FLAC (Lossless 24-bit)",
            "WAV (Studio PCM 1411 kbps)",
            "OPUS - 160 kbps (Siêu nét)",
            "OGG / Vorbis - 192 kbps",
            "ALAC (Apple Lossless)",
            "WMA (Windows Media)",
            "AIFF (Apple PCM)"
        ], height=28)
        self.audio_combo.grid(row=3, column=0, sticky="ew", padx=(0, 3))

        self.audio_fmt_combo = ctk.CTkComboBox(grid_l, values=[
            "MP3 (Phổ biến nhất)",
            "M4A / AAC (Apple/YouTube)",
            "FLAC (Lossless)",
            "WAV (Không nén PCM)",
            "OPUS (Hiện đại nhất)",
            "OGG / Vorbis",
            "ALAC (Apple Lossless)",
            "WMA",
            "AIFF"
        ], height=28)
        self.audio_fmt_combo.grid(row=3, column=1, sticky="ew", padx=(3, 0))

        # =====================================================================
        # CỘT PHẢI: CÀI ĐẶT NÂNG CAO & CHUYÊN SÂU
        # =====================================================================
        right_card = ctk.CTkFrame(grid_cols, corner_radius=10)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        r_in = ctk.CTkFrame(right_card, fg_color="transparent")
        r_in.pack(fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(r_in, text="🚀 CÀI ĐẶT NÂNG CAO & CHUYÊN SÂU", font=("Segoe UI", 12, "bold"), text_color=("#2563EB", "#60A5FA")).pack(anchor="w", pady=(0, 8))

        # Tốc độ & Luồng tải
        grid_r1 = ctk.CTkFrame(r_in, fg_color="transparent")
        grid_r1.pack(fill="x", pady=(0, 6))
        grid_r1.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_r1, text="Số luồng tải phân đoạn:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(grid_r1, text="Giới hạn tốc độ tải:", font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.threads_combo = ctk.CTkComboBox(grid_r1, values=["4 luồng (Chuẩn)", "8 luồng (Siêu tốc)", "16 luồng (Cực đại)", "2 luồng (Ổn định)", "1 luồng (Đơn)"], height=28)
        self.threads_combo.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(0, 6))

        self.ratelimit_combo = ctk.CTkComboBox(grid_r1, values=["Không giới hạn (Tối đa)", "50 MB/s", "20 MB/s", "10 MB/s", "5 MB/s", "2 MB/s"], height=28)
        self.ratelimit_combo.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(0, 6))

        # Video Codec & FPS
        grid_r2 = ctk.CTkFrame(r_in, fg_color="transparent")
        grid_r2.pack(fill="x", pady=(0, 8))
        grid_r2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_r2, text="Bộ mã hóa Video (Codec):", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(grid_r2, text="Tùy chọn Khung hình (FPS):", font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.codec_combo = ctk.CTkComboBox(grid_r2, values=[
            "Tự động (Tối ưu theo nguồn gốc)",
            "H.264 / AVC1 (Tương thích cao nhất)",
            "H.265 / HEVC (Siêu nén chất lượng cao)",
            "VP9 (Google 4K sắc nét)",
            "AV1 (Codec thế hệ mới)",
            "ProRes (Chất lượng dựng phim)",
            "MPEG-4 (Thiết bị đời cũ)"
        ], height=28)
        self.codec_combo.grid(row=1, column=0, sticky="ew", padx=(0, 3))

        self.fps_combo = ctk.CTkComboBox(grid_r2, values=["60fps (Mượt mà)", "30fps (Tiêu chuẩn)", "Mặc định (Theo video gốc)"], height=28)
        self.fps_combo.grid(row=1, column=1, sticky="ew", padx=(3, 0))

        # Phụ đề
        sub_box = ctk.CTkFrame(r_in, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6)
        sub_box.pack(fill="x", pady=(0, 8))
        sub_in = ctk.CTkFrame(sub_box, fg_color="transparent")
        sub_in.pack(fill="x", padx=10, pady=8)

        self.sub_cb = ctk.CTkCheckBox(sub_in, text="💬 Tải & Nhúng Phụ Đề vào Video", font=("Segoe UI", 10, "bold"))
        self.sub_cb.pack(anchor="w", pady=(0, 4))

        sub_sub_row = ctk.CTkFrame(sub_in, fg_color="transparent")
        sub_sub_row.pack(fill="x")

        self.auto_sub_cb = ctk.CTkCheckBox(sub_sub_row, text="Tự động lấy Phụ đề AI / Auto-sub", font=("Segoe UI", 9))
        self.auto_sub_cb.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(sub_sub_row, text="Mã ngôn ngữ:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.sub_lang_entry = ctk.CTkEntry(sub_sub_row, width=80, height=24, font=("Consolas", 9), placeholder_text="vi,en")
        self.sub_lang_entry.pack(side="left")

        # Metadata & Chapters
        meta_box = ctk.CTkFrame(r_in, fg_color=("#E2E8F0", "#1E293B"), corner_radius=6)
        meta_box.pack(fill="x", pady=(0, 8))
        meta_in = ctk.CTkFrame(meta_box, fg_color="transparent")
        meta_in.pack(fill="x", padx=10, pady=8)

        self.thumb_cb = ctk.CTkCheckBox(meta_in, text="🖼️ Nhúng Ảnh Bìa (Thumbnail) chất lượng cao", font=("Segoe UI", 10))
        self.thumb_cb.pack(anchor="w", pady=(0, 3))

        self.meta_cb = ctk.CTkCheckBox(meta_in, text="🏷️ Gắn Thẻ Metadata (Title, Artist, Album, Year, Description)", font=("Segoe UI", 10))
        self.meta_cb.pack(anchor="w", pady=(0, 3))

        self.split_chap_cb = ctk.CTkCheckBox(meta_in, text="✂️ Tự động chia nhỏ tệp theo từng Chapter / Chương mục", font=("Segoe UI", 10))
        self.split_chap_cb.pack(anchor="w")

        # NÚT LƯU PRESET TOÀN DIỆN
        self.btn_save = ctk.CTkButton(
            content_scroll,
            text="💾 LƯU CẤU HÌNH PRESET NÀY",
            height=40,
            command=lambda: self.on_save_preset_clicked(show_dialog=True),
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.btn_save.pack(fill="x", pady=(10, 15))

    # =========================================================================
    # XỬ LÝ SỰ KIỆN & DỮ LIỆU PRESET
    # =========================================================================
    def refresh_presets_list(self):
        presets = self.config_manager.get_presets()
        names = [p.get("name", "Preset") for p in presets]
        self.preset_select_combo.configure(values=names)
        if names:
            active = self.config_manager.get("active_preset", names[0])
            if active in names:
                self.preset_select_combo.set(active)
                self.load_preset_to_editor(active)
            else:
                self.preset_select_combo.set(names[0])
                self.load_preset_to_editor(names[0])

    def on_preset_selected_in_combo(self, choice):
        self.load_preset_to_editor(choice)
        self.config_manager.set("active_preset", choice)

    def load_preset_to_editor(self, name: str):
        p = self.config_manager.get_preset_by_name(name)
        if not p:
            return

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, p.get("name", ""))

        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, p.get("description", ""))

        mode = p.get("mode", "video")
        if mode == "audio":
            self.mode_seg.set("🎵 Chỉ lấy Âm thanh")
        else:
            self.mode_seg.set("🎬 Video + Âm thanh")
        self.on_mode_changed(self.mode_seg.get())

        if p.get("quality"):
            self.quality_combo.set(p["quality"])
        if p.get("format"):
            self.fmt_combo.set(p["format"])
        if p.get("audio_codec"):
            self.audio_combo.set(p["audio_codec"])

        # Luồng & Tốc độ
        frag = p.get("concurrent_fragments", 4)
        frag_map = {16: "16 luồng (Cực đại)", 8: "8 luồng (Siêu tốc)", 4: "4 luồng (Chuẩn)", 2: "2 luồng (Ổn định)", 1: "1 luồng (Đơn)"}
        self.threads_combo.set(frag_map.get(frag, "4 luồng (Chuẩn)"))

        self.ratelimit_combo.set(p.get("ratelimit", "Không giới hạn (Tối đa)"))
        self.codec_combo.set(p.get("video_codec", "Tự động (Tối ưu)"))
        self.fps_combo.set(p.get("fps_prefer", "60fps (Mượt mà)"))

        # Subtitles
        if p.get("embed_subtitles", True):
            self.sub_cb.select()
        else:
            self.sub_cb.deselect()

        if p.get("auto_subs", True):
            self.auto_sub_cb.select()
        else:
            self.auto_sub_cb.deselect()

        self.sub_lang_entry.delete(0, "end")
        self.sub_lang_entry.insert(0, p.get("sub_langs", "vi,en"))

        # Metadata
        if p.get("embed_thumbnail", True):
            self.thumb_cb.select()
        else:
            self.thumb_cb.deselect()

        if p.get("add_metadata", True):
            self.meta_cb.select()
        else:
            self.meta_cb.deselect()

        if p.get("split_chapters", False):
            self.split_chap_cb.select()
        else:
            self.split_chap_cb.deselect()

    def on_mode_changed(self, value):
        if "Chỉ lấy" in value or value == "audio":
            self.quality_combo.configure(state="disabled")
            self.fmt_combo.configure(state="disabled")
            self.codec_combo.configure(state="disabled")
            self.fps_combo.configure(state="disabled")
            self.sub_cb.configure(state="disabled")
            self.auto_sub_cb.configure(state="disabled")
            self.sub_lang_entry.configure(state="disabled")
            self.audio_combo.configure(state="normal")
            self.audio_fmt_combo.configure(state="normal")
        else:
            self.quality_combo.configure(state="normal")
            self.fmt_combo.configure(state="normal")
            self.codec_combo.configure(state="normal")
            self.fps_combo.configure(state="normal")
            self.sub_cb.configure(state="normal")
            self.auto_sub_cb.configure(state="normal")
            self.sub_lang_entry.configure(state="normal")
            self.audio_combo.configure(state="normal")
            self.audio_fmt_combo.configure(state="disabled")

    def on_new_preset_clicked(self):
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, "Mẫu Preset Mới")
        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, "Cấu hình tùy biến mới...")
        self.mode_seg.set("🎬 Video + Âm thanh")
        self.on_mode_changed("🎬 Video + Âm thanh")
        self.quality_combo.set("🌟 Tốt nhất có thể (Gốc)")
        self.fmt_combo.set("MP4 (Khuyên dùng)")
        self.audio_combo.set("MP3 - 320 kbps (Cực cao)")
        self.threads_combo.set("4 luồng (Chuẩn)")
        self.ratelimit_combo.set("Không giới hạn (Tối đa)")
        self.codec_combo.set("Tự động (Tối ưu)")
        self.fps_combo.set("60fps (Mượt mà)")
        self.sub_cb.select()
        self.auto_sub_cb.select()
        self.sub_lang_entry.delete(0, "end")
        self.sub_lang_entry.insert(0, "vi,en")
        self.thumb_cb.select()
        self.meta_cb.select()
        self.split_chap_cb.deselect()
        self.name_entry.focus()

    def on_save_preset_clicked(self, show_dialog: bool = True):
        name = self.name_entry.get().strip()
        if not name:
            if show_dialog:
                msgbox.showwarning("Cảnh báo", "Vui lòng nhập tên cho Preset!")
            return

        is_audio = ("Chỉ lấy" in self.mode_seg.get() or self.mode_seg.get() == "audio")
        threads_str = self.threads_combo.get()
        threads_val = 4
        if "16" in threads_str:
            threads_val = 16
        elif "8" in threads_str:
            threads_val = 8
        elif "2" in threads_str:
            threads_val = 2
        elif "1" in threads_str:
            threads_val = 1

        new_p = {
            "name": name,
            "description": self.desc_entry.get().strip(),
            "mode": "audio" if is_audio else "video",
            "quality": self.quality_combo.get(),
            "format": self.fmt_combo.get() if not is_audio else self.audio_fmt_combo.get(),
            "audio_codec": self.audio_combo.get(),
            "concurrent_fragments": threads_val,
            "ratelimit": self.ratelimit_combo.get(),
            "video_codec": self.codec_combo.get() if not is_audio else "Không áp dụng",
            "fps_prefer": self.fps_combo.get() if not is_audio else "Mặc định",
            "embed_subtitles": bool(self.sub_cb.get()) if not is_audio else False,
            "auto_subs": bool(self.auto_sub_cb.get()) if not is_audio else False,
            "sub_langs": self.sub_lang_entry.get().strip() if not is_audio else "",
            "embed_thumbnail": bool(self.thumb_cb.get()),
            "add_metadata": bool(self.meta_cb.get()),
            "split_chapters": bool(self.split_chap_cb.get())
        }

        self.config_manager.add_or_update_preset(new_p)
        self.config_manager.set("active_preset", name)
        self.refresh_presets_list()
        self.preset_select_combo.set(name)

        if self.on_presets_updated:
            self.on_presets_updated()

        if show_dialog:
            msgbox.showinfo("Thành công", f"Đã lưu Cấu Hình Sẵn: '{name}' thành công!")

    def on_delete_preset_clicked(self, confirm: bool = True):
        name = self.preset_select_combo.get()
        if not name:
            return
        ans = True
        if confirm:
            ans = msgbox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa Cấu Hình Sẵn '{name}' không?")
        if ans:
            self.config_manager.delete_preset(name)
            self.refresh_presets_list()
            if self.on_presets_updated:
                self.on_presets_updated()
            if confirm:
                msgbox.showinfo("Đã xóa", f"Đã xóa preset '{name}' thành công.")

    def on_reset_defaults_clicked(self):
        ans = msgbox.askyesno("Khôi phục mặc định", "Bạn có muốn đặt lại toàn bộ danh sách Preset về mặc định ban đầu không?")
        if ans:
            self.config_manager.set("download_presets", list(DEFAULT_DOWNLOAD_PRESETS))
            self.refresh_presets_list()
            if self.on_presets_updated:
                self.on_presets_updated()
            msgbox.showinfo("Hoàn tất", "Đã khôi phục danh sách Preset mặc định thành công!")
