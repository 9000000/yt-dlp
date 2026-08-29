"""
Hộp Thoại Xem & Chọn Luồng Chi Tiết (Custom Format / Stream Selector Dialog).
Tham khảo phong cách nâng cao của ytdlp-interface:
Bóc tách toàn bộ mảng dữ liệu `formats` từ yt-dlp, phân loại trực quan thành:
1. 🎥 Luồng Video riêng biệt (Độ phân giải, FPS, Codec H.264/VP9/AV1, Bitrate, Dung lượng MB).
2. 🎵 Luồng Âm thanh riêng biệt (Codec AAC/OPUS, Bitrate, Sample Rate, Ngôn ngữ thuyết minh).
3. 🎬 Luồng Kết hợp sẵn (Video + Audio).
Hỗ trợ:
- Tích chọn / Bỏ chọn linh hoạt (Toggle on/off khi click lại)
- Màu sắc tương phản cao, làm nổi bật rõ ràng dòng đang được chọn (Selected Row Highlight)
- Tải chỉ Video (không tiếng), chỉ Âm thanh (không hình), hoặc ghép 2 luồng.
"""

import tkinter as tk
import customtkinter as ctk
import tkinter.messagebox as msgbox

class FormatPickerDialog(ctk.CTkToplevel):
    """Cửa sổ chọn chi tiết luồng Video và Audio theo format_id."""

    def __init__(self, master, meta: dict, current_custom_id: str = "", on_apply=None):
        super().__init__(master)
        self.meta = meta or {}
        self.raw_formats = self.meta.get("formats", [])
        self.current_custom_id = current_custom_id
        self.on_apply = on_apply

        self.selected_video_id = tk.StringVar(value="")
        self.selected_audio_id = tk.StringVar(value="")
        self.selected_combined_id = tk.StringVar(value="")

        self.enable_video_var = tk.BooleanVar(value=True)
        self.enable_audio_var = tk.BooleanVar(value=True)

        self.video_row_widgets = {}
        self.audio_row_widgets = {}
        self.combined_row_widgets = {}

        self.title("ToolDL Pro - Danh Sách Luồng Video & Âm Thanh Chi Tiết (Format Selector)")
        self.geometry("1060x700")
        self.minsize(860, 560)
        self.transient(master)
        self.after(50, self.lift)

        self._parse_streams()
        self.setup_ui()

    def _format_size(self, size_bytes: int | float | None, approx_kbps: int | float | None = None) -> str:
        """Định dạng dung lượng tệp sang MB / GB dễ đọc."""
        if size_bytes and size_bytes > 0:
            if size_bytes >= 1024 * 1024 * 1024:
                return f"{size_bytes / (1024*1024*1024):.2f} GB"
            return f"{size_bytes / (1024*1024):.1f} MB"
        
        dur = self.meta.get("duration_sec") or 0
        if approx_kbps and approx_kbps > 0 and dur > 0:
            est_bytes = (approx_kbps * 1000 / 8) * dur
            if est_bytes >= 1024 * 1024 * 1024:
                return f"~{est_bytes / (1024*1024*1024):.2f} GB"
            return f"~{est_bytes / (1024*1024):.1f} MB"

        return "--"

    def _clean_codec_name(self, codec: str | None) -> str:
        if not codec or codec == "none":
            return "Không có"
        c = codec.lower()
        if "avc1" in c or "h264" in c:
            return "H.264 / AVC"
        if "hev1" in c or "h265" in c or "hevc" in c:
            return "H.265 / HEVC"
        if "vp9" in c or "vp09" in c:
            return "VP9"
        if "av01" in c or "av1" in c:
            return "AV1"
        if "mp4a" in c or "aac" in c:
            return "AAC / M4A"
        if "opus" in c:
            return "OPUS"
        if "vorbis" in c:
            return "Vorbis"
        return codec.split(".")[0]

    def _parse_streams(self):
        """Phân loại danh sách formats thành Video-only, Audio-only và Combined."""
        self.video_streams = []
        self.audio_streams = []
        self.combined_streams = []

        for f in self.raw_formats:
            fid = str(f.get("format_id", ""))
            if not fid:
                continue

            proto = str(f.get("protocol", "")).lower()
            ext = str(f.get("ext", "")).lower()
            note = str(f.get("format_note", "") or "")
            if proto == "mhtml" or ext == "mhtml" or "storyboard" in note.lower() or fid.startswith("sb"):
                continue

            vcodec = str(f.get("vcodec") or "none")
            acodec = str(f.get("acodec") or "none")
            height = f.get("height") or 0
            width = f.get("width") or 0
            fps = f.get("fps") or 0
            tbr = f.get("tbr") or 0
            vbr = f.get("vbr") or 0
            abr = f.get("abr") or 0
            filesize = f.get("filesize") or f.get("filesize_approx")
            lang = f.get("language") or ""
            asr = f.get("asr") or 0

            has_v = (vcodec != "none" and bool(vcodec)) or (height and height > 0) or (f.get("video_ext") and f.get("video_ext") != "none")
            has_a = (acodec != "none" and bool(acodec)) or (abr and abr > 0) or (asr and asr > 0) or (f.get("audio_ext") and f.get("audio_ext") != "none") or ("audio" in note.lower())

            # 1. Luồng Video riêng (Video-only)
            if has_v and not has_a:
                res_str = f"{height}p" if height else (f"{width}x{height}" if width else "Video")
                if fps and fps > 30:
                    res_str += f" ({fps}fps)"
                
                size_str = self._format_size(filesize, vbr or tbr)
                codec_clean = self._clean_codec_name(vcodec if vcodec != "none" else (f.get("video_ext") or "Video"))
                bitrate_str = f"{int(vbr or tbr)} kbps" if (vbr or tbr) else "--"

                self.video_streams.append({
                    "id": fid,
                    "ext": ext,
                    "resolution": res_str,
                    "height": height or 0,
                    "fps": fps or 0,
                    "codec": codec_clean,
                    "codec_raw": vcodec,
                    "bitrate": bitrate_str,
                    "size": size_str,
                    "note": note,
                    "raw": f
                })

            # 2. Luồng Audio riêng (Audio-only)
            elif has_a and not has_v:
                codec_clean = self._clean_codec_name(acodec if acodec != "none" else (f.get("audio_ext") or "Audio"))
                bitrate_str = f"{int(abr or tbr)} kbps" if (abr or tbr) else "--"
                size_str = self._format_size(filesize, abr or tbr)
                asr_str = f"{asr//1000} kHz" if asr else "--"
                lang_str = lang.upper() if lang else "Gốc / Mặc định"

                self.audio_streams.append({
                    "id": fid,
                    "ext": ext,
                    "codec": codec_clean,
                    "bitrate": bitrate_str,
                    "abr_num": abr or tbr or 0,
                    "sample_rate": asr_str,
                    "language": lang_str,
                    "size": size_str,
                    "note": note,
                    "raw": f
                })

            # 3. Luồng Kết hợp sẵn (Video + Audio)
            elif has_v and has_a:
                res_str = f"{height}p" if height else "Video"
                size_str = self._format_size(filesize, tbr)
                codec_clean = f"{self._clean_codec_name(vcodec)} + {self._clean_codec_name(acodec)}"

                self.combined_streams.append({
                    "id": fid,
                    "ext": ext,
                    "resolution": res_str,
                    "height": height or 0,
                    "codec": codec_clean,
                    "size": size_str,
                    "note": note,
                    "raw": f
                })

        # Sắp xếp Video từ độ phân giải cao nhất xuống thấp nhất
        self.video_streams.sort(key=lambda x: (x["height"], x["fps"]), reverse=True)
        # Sắp xếp Audio từ bitrate cao nhất xuống thấp nhất
        self.audio_streams.sort(key=lambda x: x["abr_num"], reverse=True)
        # Sắp xếp Combined từ cao xuống thấp
        self.combined_streams.sort(key=lambda x: x["height"], reverse=True)

        # Khởi tạo mặc định nếu có current_custom_id
        if self.current_custom_id:
            parts = self.current_custom_id.split("+")
            if len(parts) == 2:
                self.selected_video_id.set(parts[0])
                self.selected_audio_id.set(parts[1])
                self.enable_video_var.set(True)
                self.enable_audio_var.set(True)
            elif len(parts) == 1:
                cid = parts[0]
                is_a = any(s["id"] == cid for s in self.audio_streams)
                is_v = any(s["id"] == cid for s in self.video_streams)
                is_c = any(s["id"] == cid for s in self.combined_streams)
                if is_a:
                    self.selected_audio_id.set(cid)
                    self.enable_audio_var.set(True)
                    self.enable_video_var.set(False)
                elif is_v:
                    self.selected_video_id.set(cid)
                    self.enable_video_var.set(True)
                    self.enable_audio_var.set(False)
                elif is_c:
                    self.selected_combined_id.set(cid)
                    self.enable_video_var.set(False)
                    self.enable_audio_var.set(False)
        else:
            if self.video_streams:
                self.selected_video_id.set(self.video_streams[0]["id"])
            if self.audio_streams:
                self.selected_audio_id.set(self.audio_streams[0]["id"])
            self.enable_video_var.set(True)
            self.enable_audio_var.set(True)

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # 1. Tiêu đề video header
        top_hdr = ctk.CTkFrame(container, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        top_hdr.pack(fill="x", pady=(0, 10))

        th_inner = ctk.CTkFrame(top_hdr, fg_color="transparent")
        th_inner.pack(fill="x", padx=14, pady=12)

        title = self.meta.get("title", "Video không tiêu đề")
        uploader = self.meta.get("uploader", "--")
        dur = self.meta.get("duration_str", "--")

        ctk.CTkLabel(th_inner, text=f"🎬 {title}", font=("Segoe UI", 13, "bold"), text_color=("#0F172A", "#F8FAFC"), anchor="w", justify="left").pack(anchor="w")
        ctk.CTkLabel(th_inner, text=f"👤 Kênh: {uploader}   |   ⏱️ Thời lượng: {dur}   |   📊 Tìm thấy: {len(self.video_streams)} luồng Video, {len(self.audio_streams)} luồng Audio", font=("Segoe UI", 11), text_color=("#475569", "#94A3B8"), anchor="w").pack(anchor="w", pady=(3, 0))

        # 2. Tabview hiển thị 3 nhóm luồng
        self.tabview = ctk.CTkTabview(container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, pady=(0, 10))

        self.tab_video = self.tabview.add(f"🎥 Luồng Video Riêng ({len(self.video_streams)})")
        self.tab_audio = self.tabview.add(f"🎵 Luồng Âm Thanh Riêng ({len(self.audio_streams)})")
        self.tab_comb = self.tabview.add(f"🎬 Luồng Kết Hợp Sẵn ({len(self.combined_streams)})")

        self._build_video_tab()
        self._build_audio_tab()
        self._build_combined_tab()

        # 3. Thanh thông tin lựa chọn & Nút áp dụng
        bot_bar = ctk.CTkFrame(container, corner_radius=10, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        bot_bar.pack(fill="x")

        bb_inner = ctk.CTkFrame(bot_bar, fg_color="transparent")
        bb_inner.pack(fill="x", padx=14, pady=12)

        self.selection_summary_lbl = ctk.CTkLabel(
            bb_inner,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color=("#1D4ED8", "#60A5FA"),
            anchor="w",
            wraplength=540,
            justify="left"
        )
        self.selection_summary_lbl.pack(side="left", fill="x", expand=True)

        btn_row = ctk.CTkFrame(bb_inner, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Tải Tự Động (Preset)",
            width=180,
            height=38,
            command=self.on_reset_auto,
            fg_color="#475569",
            hover_color="#334155",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="⚡ ÁP DỤNG LỰA CHỌN NÀY",
            height=38,
            command=self.on_confirm_selection,
            fg_color="#059669",
            hover_color="#047857",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Đóng",
            width=80,
            height=38,
            command=self.destroy,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        self._update_summary_label()
        self._refresh_row_highlights()

    def _build_video_tab(self):
        # Thanh công cụ trên đầu Tab Video
        top_ctrl = ctk.CTkFrame(self.tab_video, fg_color=("#EFF6FF", "#0F172A"), corner_radius=8, border_width=1, border_color=("#3B82F6", "#1D4ED8"))
        top_ctrl.pack(fill="x", pady=(0, 8), padx=2)

        tc_inner = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        tc_inner.pack(fill="x", padx=10, pady=6)

        self.chk_video = ctk.CTkCheckBox(
            tc_inner,
            text="☑️ TẢI LUỒNG VIDEO NÀY (Bỏ tích nếu bạn chỉ muốn tải riêng file Âm thanh)",
            variable=self.enable_video_var,
            command=self._on_enable_video_toggled,
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.chk_video.pack(side="left")

        ctk.CTkButton(
            tc_inner,
            text="✕ Bỏ chọn Video",
            width=120,
            height=28,
            command=self.deselect_video,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            font=("Segoe UI", 10, "bold")
        ).pack(side="right")

        # Header bảng
        hdr = ctk.CTkFrame(self.tab_video, height=30, fg_color=("#CBD5E1", "#334155"), corner_radius=6)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Chọn", width=55, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="Format ID", width=80, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Độ phân giải", width=150, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bộ mã hóa (Codec)", width=140, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Định dạng", width=75, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bitrate", width=95, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Dung lượng", width=95, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Ghi chú", anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", fill="x", expand=True, padx=4)

        scroll = ctk.CTkScrollableFrame(self.tab_video, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.video_streams:
            ctk.CTkLabel(scroll, text="Không có luồng Video riêng lẻ nào.", font=("Segoe UI", 12)).pack(pady=20)
            return

        for s in self.video_streams:
            fid = s["id"]
            row = ctk.CTkFrame(scroll, corner_radius=6, fg_color=("#F8FAFC", "#1E293B"), height=34)
            row.pack(fill="x", pady=2)
            self.video_row_widgets[fid] = row

            rb = ctk.CTkRadioButton(
                row,
                text="",
                value=fid,
                variable=self.selected_video_id,
                command=lambda f=fid: self._on_video_row_clicked(f),
                width=24
            )
            rb.pack(side="left", padx=(10, 16))

            l1 = ctk.CTkLabel(row, text=fid, width=80, font=("Consolas", 11, "bold"), text_color=("#1D4ED8", "#60A5FA"))
            l1.pack(side="left", padx=4)
            l2 = ctk.CTkLabel(row, text=s["resolution"], width=150, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC"))
            l2.pack(side="left", padx=4)
            l3 = ctk.CTkLabel(row, text=s["codec"], width=140, anchor="w", font=("Segoe UI", 11), text_color=("#334155", "#E2E8F0"))
            l3.pack(side="left", padx=4)
            l4 = ctk.CTkLabel(row, text=s["ext"].upper(), width=75, font=("Segoe UI", 11, "bold"), text_color=("#475569", "#94A3B8"))
            l4.pack(side="left", padx=4)
            l5 = ctk.CTkLabel(row, text=s["bitrate"], width=95, font=("Segoe UI", 11), text_color=("#334155", "#E2E8F0"))
            l5.pack(side="left", padx=4)
            l6 = ctk.CTkLabel(row, text=s["size"], width=95, font=("Segoe UI", 11, "bold"), text_color=("#059669", "#34D399"))
            l6.pack(side="left", padx=4)
            l7 = ctk.CTkLabel(row, text=s["note"], anchor="w", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"))
            l7.pack(side="left", fill="x", expand=True, padx=4)

            for w in (row, l1, l2, l3, l4, l5, l6, l7):
                w.bind("<Button-1>", lambda e, f=fid: self._on_video_row_clicked(f))

    def _build_audio_tab(self):
        # Thanh công cụ trên đầu Tab Audio
        top_ctrl = ctk.CTkFrame(self.tab_audio, fg_color=("#EFF6FF", "#0F172A"), corner_radius=8, border_width=1, border_color=("#3B82F6", "#1D4ED8"))
        top_ctrl.pack(fill="x", pady=(0, 8), padx=2)

        tc_inner = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        tc_inner.pack(fill="x", padx=10, pady=6)

        self.chk_audio = ctk.CTkCheckBox(
            tc_inner,
            text="☑️ TẢI LUỒNG ÂM THANH NÀY (Bỏ tích nếu bạn chỉ muốn tải Video không tiếng)",
            variable=self.enable_audio_var,
            command=self._on_enable_audio_toggled,
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.chk_audio.pack(side="left")

        ctk.CTkButton(
            tc_inner,
            text="✕ Bỏ chọn Audio",
            width=120,
            height=28,
            command=self.deselect_audio,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            font=("Segoe UI", 10, "bold")
        ).pack(side="right")

        # Header bảng
        hdr = ctk.CTkFrame(self.tab_audio, height=30, fg_color=("#CBD5E1", "#334155"), corner_radius=6)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Chọn", width=55, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="Format ID", width=80, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Chất lượng Bitrate", width=140, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bộ mã hóa (Codec)", width=140, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Định dạng", width=75, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Sample Rate", width=95, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Ngôn ngữ", width=130, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Dung lượng", width=95, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(self.tab_audio, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.audio_streams:
            ctk.CTkLabel(scroll, text="Không có luồng Âm thanh riêng lẻ nào.", font=("Segoe UI", 12)).pack(pady=20)
            return

        for s in self.audio_streams:
            fid = s["id"]
            row = ctk.CTkFrame(scroll, corner_radius=6, fg_color=("#F8FAFC", "#1E293B"), height=34)
            row.pack(fill="x", pady=2)
            self.audio_row_widgets[fid] = row

            rb = ctk.CTkRadioButton(
                row,
                text="",
                value=fid,
                variable=self.selected_audio_id,
                command=lambda f=fid: self._on_audio_row_clicked(f),
                width=24
            )
            rb.pack(side="left", padx=(10, 16))

            l1 = ctk.CTkLabel(row, text=fid, width=80, font=("Consolas", 11, "bold"), text_color=("#1D4ED8", "#60A5FA"))
            l1.pack(side="left", padx=4)
            l2 = ctk.CTkLabel(row, text=s["bitrate"], width=140, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC"))
            l2.pack(side="left", padx=4)
            l3 = ctk.CTkLabel(row, text=s["codec"], width=140, anchor="w", font=("Segoe UI", 11), text_color=("#334155", "#E2E8F0"))
            l3.pack(side="left", padx=4)
            l4 = ctk.CTkLabel(row, text=s["ext"].upper(), width=75, font=("Segoe UI", 11, "bold"), text_color=("#475569", "#94A3B8"))
            l4.pack(side="left", padx=4)
            l5 = ctk.CTkLabel(row, text=s["sample_rate"], width=95, font=("Segoe UI", 11), text_color=("#334155", "#E2E8F0"))
            l5.pack(side="left", padx=4)
            l6 = ctk.CTkLabel(row, text=s["language"], width=130, anchor="w", font=("Segoe UI", 11), text_color=("#334155", "#E2E8F0"))
            l6.pack(side="left", padx=4)
            l7 = ctk.CTkLabel(row, text=s["size"], width=95, font=("Segoe UI", 11, "bold"), text_color=("#059669", "#34D399"))
            l7.pack(side="left", padx=4)

            for w in (row, l1, l2, l3, l4, l5, l6, l7):
                w.bind("<Button-1>", lambda e, f=fid: self._on_audio_row_clicked(f))

    def _build_combined_tab(self):
        # Thanh công cụ trên đầu Tab Combined
        top_ctrl = ctk.CTkFrame(self.tab_comb, fg_color=("#EFF6FF", "#0F172A"), corner_radius=8, border_width=1, border_color=("#3B82F6", "#1D4ED8"))
        top_ctrl.pack(fill="x", pady=(0, 8), padx=2)

        tc_inner = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        tc_inner.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(tc_inner, text="🎬 Các luồng chứa sẵn cả Video + Âm thanh gốc", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        ctk.CTkButton(
            tc_inner,
            text="✕ Bỏ chọn Luồng kết hợp",
            width=175,
            height=28,
            command=self.deselect_combined,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            font=("Segoe UI", 10, "bold")
        ).pack(side="right")

        hdr = ctk.CTkFrame(self.tab_comb, height=30, fg_color=("#CBD5E1", "#334155"), corner_radius=6)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Chọn", width=55, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="Format ID", width=80, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Độ phân giải", width=150, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bộ mã hóa", width=200, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Định dạng", width=75, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Dung lượng", width=95, font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC")).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(self.tab_comb, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.combined_streams:
            ctk.CTkLabel(scroll, text="Không có luồng Kết hợp sẵn nào (Video HD/4K đều được tách riêng luồng trên YouTube).", font=("Segoe UI", 12)).pack(pady=20)
            return

        for s in self.combined_streams:
            fid = s["id"]
            row = ctk.CTkFrame(scroll, corner_radius=6, fg_color=("#F8FAFC", "#1E293B"), height=34)
            row.pack(fill="x", pady=2)
            self.combined_row_widgets[fid] = row

            rb = ctk.CTkRadioButton(
                row,
                text="",
                value=fid,
                variable=self.selected_combined_id,
                command=lambda f=fid: self._on_combined_row_clicked(f),
                width=24
            )
            rb.pack(side="left", padx=(10, 16))

            l1 = ctk.CTkLabel(row, text=fid, width=80, font=("Consolas", 11, "bold"), text_color=("#1D4ED8", "#60A5FA"))
            l1.pack(side="left", padx=4)
            l2 = ctk.CTkLabel(row, text=s["resolution"], width=150, anchor="w", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#F8FAFC"))
            l2.pack(side="left", padx=4)
            l3 = ctk.CTkLabel(row, text=s["codec"], width=200, anchor="w", font=("Segoe UI", 11), text_color=("#334155", "#E2E8F0"))
            l3.pack(side="left", padx=4)
            l4 = ctk.CTkLabel(row, text=s["ext"].upper(), width=75, font=("Segoe UI", 11, "bold"), text_color=("#475569", "#94A3B8"))
            l4.pack(side="left", padx=4)
            l5 = ctk.CTkLabel(row, text=s["size"], width=95, font=("Segoe UI", 11, "bold"), text_color=("#059669", "#34D399"))
            l5.pack(side="left", padx=4)

            for w in (row, l1, l2, l3, l4, l5):
                w.bind("<Button-1>", lambda e, f=fid: self._on_combined_row_clicked(f))

    # =========================================================================
    # CÁC HÀM XỬ LÝ SỰ KIỆN TƯƠNG TÁC (TOGGLE / CLICK / CHECKBOX)
    # =========================================================================
    def _refresh_row_highlights(self):
        """Cập nhật viền và màu nền tương phản cao cho các dòng đang được chọn."""
        sel_v = self.selected_video_id.get() if self.enable_video_var.get() else ""
        sel_a = self.selected_audio_id.get() if self.enable_audio_var.get() else ""
        sel_c = self.selected_combined_id.get()

        for fid, row in self.video_row_widgets.items():
            if fid == sel_v:
                row.configure(fg_color=("#DBEAFE", "#1E3A8A"), border_width=1.5, border_color="#3B82F6")
            else:
                row.configure(fg_color=("#F8FAFC", "#1E293B"), border_width=0)

        for fid, row in self.audio_row_widgets.items():
            if fid == sel_a:
                row.configure(fg_color=("#EDE9FE", "#4C1D95"), border_width=1.5, border_color="#8B5CF6")
            else:
                row.configure(fg_color=("#F8FAFC", "#1E293B"), border_width=0)

        for fid, row in self.combined_row_widgets.items():
            if fid == sel_c:
                row.configure(fg_color=("#DCFCE7", "#064E3B"), border_width=1.5, border_color="#10B981")
            else:
                row.configure(fg_color=("#F8FAFC", "#1E293B"), border_width=0)

    def _on_enable_video_toggled(self):
        if self.enable_video_var.get():
            if not self.selected_video_id.get() and self.video_streams:
                self.selected_video_id.set(self.video_streams[0]["id"])
            self.selected_combined_id.set("")
        else:
            self.selected_video_id.set("")
        self._update_summary_label()
        self._refresh_row_highlights()

    def _on_enable_audio_toggled(self):
        if self.enable_audio_var.get():
            if not self.selected_audio_id.get() and self.audio_streams:
                self.selected_audio_id.set(self.audio_streams[0]["id"])
            self.selected_combined_id.set("")
        else:
            self.selected_audio_id.set("")
        self._update_summary_label()
        self._refresh_row_highlights()

    def _on_video_row_clicked(self, fid: str):
        self.selected_combined_id.set("")
        if self.selected_video_id.get() == fid and not self.enable_video_var.get():
            self.enable_video_var.set(True)
        elif self.selected_video_id.get() == fid and self.enable_video_var.get():
            self.deselect_video()
            return
        else:
            self.selected_video_id.set(fid)
            self.enable_video_var.set(True)
        self._update_summary_label()
        self._refresh_row_highlights()

    def _on_audio_row_clicked(self, fid: str):
        self.selected_combined_id.set("")
        if self.selected_audio_id.get() == fid and not self.enable_audio_var.get():
            self.enable_audio_var.set(True)
        elif self.selected_audio_id.get() == fid and self.enable_audio_var.get():
            self.deselect_audio()
            return
        else:
            self.selected_audio_id.set(fid)
            self.enable_audio_var.set(True)
        self._update_summary_label()
        self._refresh_row_highlights()

    def _on_combined_row_clicked(self, fid: str):
        if self.selected_combined_id.get() == fid:
            self.deselect_combined()
            return
        self.selected_combined_id.set(fid)
        self.enable_video_var.set(False)
        self.enable_audio_var.set(False)
        self.selected_video_id.set("")
        self.selected_audio_id.set("")
        self._update_summary_label()
        self._refresh_row_highlights()

    def deselect_video(self):
        self.selected_video_id.set("")
        self.enable_video_var.set(False)
        self._update_summary_label()
        self._refresh_row_highlights()

    def deselect_audio(self):
        self.selected_audio_id.set("")
        self.enable_audio_var.set(False)
        self._update_summary_label()
        self._refresh_row_highlights()

    def deselect_combined(self):
        self.selected_combined_id.set("")
        self._update_summary_label()
        self._refresh_row_highlights()

    def _update_summary_label(self):
        v_active = self.enable_video_var.get() and bool(self.selected_video_id.get())
        a_active = self.enable_audio_var.get() and bool(self.selected_audio_id.get())
        c_active = bool(self.selected_combined_id.get())

        v_id = self.selected_video_id.get()
        a_id = self.selected_audio_id.get()
        c_id = self.selected_combined_id.get()

        if c_active:
            c_info = next((s for s in self.combined_streams if s["id"] == c_id), None)
            c_desc = f"{c_info['resolution']} ({c_info['codec']})" if c_info else c_id
            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn: Luồng kết hợp sẵn [{c_id}: {c_desc}]",
                text_color=("#059669", "#34D399")
            )
        elif v_active and a_active:
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            v_desc = f"{v_info['resolution']} ({v_info['codec']})" if v_info else v_id
            a_desc = f"{a_info['bitrate']} ({a_info['codec']})" if a_info else a_id

            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn: Video [{v_id}: {v_desc}]  +  Audio [{a_id}: {a_desc}]  👉 Ghép: {v_id}+{a_id}",
                text_color=("#1D4ED8", "#60A5FA")
            )
        elif v_active and not a_active:
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            v_desc = f"{v_info['resolution']} ({v_info['codec']})" if v_info else v_id
            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn: CHỈ TẢI VIDEO [{v_id}: {v_desc}] (Không có tiếng)",
                text_color=("#D97706", "#FBBF24")
            )
        elif a_active and not v_active:
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            a_desc = f"{a_info['bitrate']} ({a_info['codec']})" if a_info else a_id
            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn: CHỈ TẢI ÂM THANH [{a_id}: {a_desc}] (Không có video)",
                text_color=("#7C3AED", "#A78BFA")
            )
        else:
            self.selection_summary_lbl.configure(
                text="🌟 Chưa chọn luồng cụ thể 👉 Tự động tải chất lượng cao nhất theo Preset",
                text_color=("#64748B", "#94A3B8")
            )

    def on_confirm_selection(self):
        v_active = self.enable_video_var.get() and bool(self.selected_video_id.get())
        a_active = self.enable_audio_var.get() and bool(self.selected_audio_id.get())
        c_active = bool(self.selected_combined_id.get())

        v_id = self.selected_video_id.get()
        a_id = self.selected_audio_id.get()
        c_id = self.selected_combined_id.get()

        if c_active:
            custom_id = c_id
            c_info = next((s for s in self.combined_streams if s["id"] == c_id), None)
            desc = f"Luồng kết hợp [{c_id}]" if not c_info else f"Luồng kết hợp {c_info['resolution']} ({c_id})"
        elif v_active and a_active:
            custom_id = f"{v_id}+{a_id}"
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            v_desc = v_info['resolution'] if v_info else v_id
            a_desc = a_info['bitrate'] if a_info else a_id
            desc = f"{v_desc} + {a_desc} ({custom_id})"
        elif v_active and not a_active:
            custom_id = v_id
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            v_desc = v_info['resolution'] if v_info else v_id
            desc = f"Chỉ Video {v_desc} ({custom_id})"
        elif a_active and not v_active:
            custom_id = a_id
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            a_desc = a_info['bitrate'] if a_info else a_id
            desc = f"Chỉ Audio {a_desc} ({custom_id})"
        else:
            custom_id = ""
            desc = ""

        if self.on_apply:
            self.on_apply(custom_id, desc)

        self.destroy()

    def on_reset_auto(self):
        if self.on_apply:
            self.on_apply("", "")
        self.destroy()
