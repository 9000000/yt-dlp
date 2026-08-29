"""
Hộp Thoại Xem & Chọn Luồng Chi Tiết (Custom Format / Stream Selector Dialog).
Tham khảo phong cách nâng cao của ytdlp-interface:
Bóc tách toàn bộ mảng dữ liệu `formats` từ yt-dlp, phân loại trực quan thành:
1. 🎥 Luồng Video riêng biệt (Độ phân giải, FPS, Codec H.264/VP9/AV1, Bitrate, Dung lượng MB).
2. 🎵 Luồng Âm thanh riêng biệt (Codec AAC/OPUS, Bitrate, Sample Rate, Ngôn ngữ thuyết minh).
3. 🎬 Luồng Kết hợp sẵn (Video + Audio).
Cho phép người dùng tích chọn chính xác ID luồng theo ý muốn (vd: 137+140).
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

        self.title("ToolDL Pro - Danh Sách Luồng Video & Âm Thanh Chi Tiết (Format Selector)")
        self.geometry("980x640")
        self.minsize(800, 500)
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
        
        # Tính ước lượng từ bitrate và thời lượng nếu có
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

            # Bỏ qua các ảnh Storyboard thumbnail của YouTube
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
            elif len(parts) == 1:
                self.selected_combined_id.set(parts[0])
        else:
            if self.video_streams:
                self.selected_video_id.set(self.video_streams[0]["id"])
            if self.audio_streams:
                self.selected_audio_id.set(self.audio_streams[0]["id"])

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=14, pady=12)

        # 1. Tiêu đề video header
        top_hdr = ctk.CTkFrame(container, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"))
        top_hdr.pack(fill="x", pady=(0, 8))

        th_inner = ctk.CTkFrame(top_hdr, fg_color="transparent")
        th_inner.pack(fill="x", padx=12, pady=10)

        title = self.meta.get("title", "Video không tiêu đề")
        uploader = self.meta.get("uploader", "--")
        dur = self.meta.get("duration_str", "--")

        ctk.CTkLabel(th_inner, text=f"🎬 {title}", font=("Segoe UI", 12, "bold"), anchor="w", justify="left").pack(anchor="w")
        ctk.CTkLabel(th_inner, text=f"👤 Kênh: {uploader}  |  ⏱️ Thời lượng: {dur}  |  📊 Tìm thấy: {len(self.video_streams)} luồng Video, {len(self.audio_streams)} luồng Audio", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8"), anchor="w").pack(anchor="w", pady=(2, 0))

        # 2. Tabview hiển thị 3 nhóm luồng
        self.tabview = ctk.CTkTabview(container, corner_radius=8)
        self.tabview.pack(fill="both", expand=True, pady=(0, 8))

        self.tab_video = self.tabview.add(f"🎥 Luồng Video Riêng ({len(self.video_streams)})")
        self.tab_audio = self.tabview.add(f"🎵 Luồng Âm Thanh Riêng ({len(self.audio_streams)})")
        self.tab_comb = self.tabview.add(f"🎬 Luồng Kết Hợp Sẵn ({len(self.combined_streams)})")

        self._build_video_tab()
        self._build_audio_tab()
        self._build_combined_tab()

        # 3. Thanh thông tin lựa chọn & Nút áp dụng
        bot_bar = ctk.CTkFrame(container, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"))
        bot_bar.pack(fill="x")

        bb_inner = ctk.CTkFrame(bot_bar, fg_color="transparent")
        bb_inner.pack(fill="x", padx=12, pady=10)

        self.selection_summary_lbl = ctk.CTkLabel(
            bb_inner,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color=("#2563EB", "#60A5FA"),
            anchor="w"
        )
        self.selection_summary_lbl.pack(side="left", fill="x", expand=True)

        btn_row = ctk.CTkFrame(bb_inner, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Đặt lại Chế độ Tự động",
            width=170,
            height=32,
            command=self.on_reset_auto,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="⚡ ÁP DỤNG & CHỌN LUỒNG NÀY",
            height=32,
            command=self.on_confirm_selection,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="Đóng",
            width=70,
            height=32,
            command=self.destroy,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=("#1E293B", "#F8FAFC"),
            font=("Segoe UI", 10)
        ).pack(side="left")

        self._update_summary_label()

    def _build_video_tab(self):
        # Header hàng
        hdr = ctk.CTkFrame(self.tab_video, height=26, fg_color=("#CBD5E1", "#334155"), corner_radius=4)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Chọn", width=50, font=("Segoe UI", 9, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="Format ID", width=70, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Độ phân giải", width=140, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bộ mã hóa (Codec)", width=130, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Định dạng", width=70, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bitrate", width=90, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Dung lượng", width=90, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Ghi chú", anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", fill="x", expand=True, padx=4)

        scroll = ctk.CTkScrollableFrame(self.tab_video, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.video_streams:
            ctk.CTkLabel(scroll, text="Không có luồng Video riêng lẻ nào.", font=("Segoe UI", 11)).pack(pady=20)
            return

        for s in self.video_streams:
            fid = s["id"]
            row = ctk.CTkFrame(scroll, corner_radius=4, fg_color=("#F8FAFC", "#1E293B"))
            row.pack(fill="x", pady=2)

            rb = ctk.CTkRadioButton(
                row,
                text="",
                value=fid,
                variable=self.selected_video_id,
                command=self._on_radio_changed,
                width=24
            )
            rb.pack(side="left", padx=(10, 16))

            ctk.CTkLabel(row, text=fid, width=70, font=("Consolas", 10, "bold"), text_color=("#2563EB", "#60A5FA")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["resolution"], width=140, anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["codec"], width=130, anchor="w", font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["ext"].upper(), width=70, font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["bitrate"], width=90, font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["size"], width=90, font=("Segoe UI", 10, "bold"), text_color=("#10B981", "#34D399")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["note"], anchor="w", font=("Segoe UI", 9), text_color=("#64748B", "#94A3B8")).pack(side="left", fill="x", expand=True, padx=4)

    def _build_audio_tab(self):
        hdr = ctk.CTkFrame(self.tab_audio, height=26, fg_color=("#CBD5E1", "#334155"), corner_radius=4)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Chọn", width=50, font=("Segoe UI", 9, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="Format ID", width=70, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Chất lượng Bitrate", width=130, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bộ mã hóa (Codec)", width=130, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Định dạng", width=70, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Sample Rate", width=90, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Ngôn ngữ", width=120, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Dung lượng", width=90, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(self.tab_audio, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.audio_streams:
            ctk.CTkLabel(scroll, text="Không có luồng Âm thanh riêng lẻ nào.", font=("Segoe UI", 11)).pack(pady=20)
            return

        for s in self.audio_streams:
            fid = s["id"]
            row = ctk.CTkFrame(scroll, corner_radius=4, fg_color=("#F8FAFC", "#1E293B"))
            row.pack(fill="x", pady=2)

            rb = ctk.CTkRadioButton(
                row,
                text="",
                value=fid,
                variable=self.selected_audio_id,
                command=self._on_radio_changed,
                width=24
            )
            rb.pack(side="left", padx=(10, 16))

            ctk.CTkLabel(row, text=fid, width=70, font=("Consolas", 10, "bold"), text_color=("#2563EB", "#60A5FA")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["bitrate"], width=130, anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["codec"], width=130, anchor="w", font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["ext"].upper(), width=70, font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["sample_rate"], width=90, font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["language"], width=120, anchor="w", font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["size"], width=90, font=("Segoe UI", 10, "bold"), text_color=("#10B981", "#34D399")).pack(side="left", padx=4)

    def _build_combined_tab(self):
        hdr = ctk.CTkFrame(self.tab_comb, height=26, fg_color=("#CBD5E1", "#334155"), corner_radius=4)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Chọn", width=50, font=("Segoe UI", 9, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="Format ID", width=70, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Độ phân giải", width=140, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Bộ mã hóa", width=180, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Định dạng", width=70, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Dung lượng", width=90, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(self.tab_comb, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.combined_streams:
            ctk.CTkLabel(scroll, text="Không có luồng Kết hợp sẵn nào (Video HD/4K đều được tách riêng luồng trên YouTube).", font=("Segoe UI", 11)).pack(pady=20)
            return

        for s in self.combined_streams:
            fid = s["id"]
            row = ctk.CTkFrame(scroll, corner_radius=4, fg_color=("#F8FAFC", "#1E293B"))
            row.pack(fill="x", pady=2)

            rb = ctk.CTkRadioButton(
                row,
                text="",
                value=fid,
                variable=self.selected_combined_id,
                command=self._on_combined_radio_changed,
                width=24
            )
            rb.pack(side="left", padx=(10, 16))

            ctk.CTkLabel(row, text=fid, width=70, font=("Consolas", 10, "bold"), text_color=("#2563EB", "#60A5FA")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["resolution"], width=140, anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["codec"], width=180, anchor="w", font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["ext"].upper(), width=70, font=("Segoe UI", 10)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["size"], width=90, font=("Segoe UI", 10, "bold"), text_color=("#10B981", "#34D399")).pack(side="left", padx=4)

    def _on_radio_changed(self):
        self.selected_combined_id.set("")
        self._update_summary_label()

    def _on_combined_radio_changed(self):
        self.selected_video_id.set("")
        self.selected_audio_id.set("")
        self._update_summary_label()

    def _update_summary_label(self):
        v_id = self.selected_video_id.get()
        a_id = self.selected_audio_id.get()
        c_id = self.selected_combined_id.get()

        if c_id:
            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn Luồng kết hợp: Format ID [{c_id}]"
            )
        elif v_id and a_id:
            # Tìm thông tin
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            v_desc = f"{v_info['resolution']} ({v_info['codec']})" if v_info else v_id
            a_desc = f"{a_info['bitrate']} ({a_info['codec']})" if a_info else a_id

            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn: Video [{v_id}: {v_desc}]  +  Audio [{a_id}: {a_desc}]  👉 Chuỗi lệnh: {v_id}+{a_id}"
            )
        elif v_id:
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            v_desc = f"{v_info['resolution']} ({v_info['codec']})" if v_info else v_id
            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn Chỉ Video: Format ID [{v_id}: {v_desc}]"
            )
        elif a_id:
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            a_desc = f"{a_info['bitrate']} ({a_info['codec']})" if a_info else a_id
            self.selection_summary_lbl.configure(
                text=f"🎯 Đang chọn Chỉ Audio: Format ID [{a_id}: {a_desc}]"
            )
        else:
            self.selection_summary_lbl.configure(
                text="⚠️ Chưa chọn luồng nào (Sử dụng chế độ Tự động)"
            )

    def on_confirm_selection(self):
        v_id = self.selected_video_id.get()
        a_id = self.selected_audio_id.get()
        c_id = self.selected_combined_id.get()

        if c_id:
            custom_id = c_id
            desc = f"Luồng kết hợp [{c_id}]"
        elif v_id and a_id:
            custom_id = f"{v_id}+{a_id}"
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            v_desc = v_info['resolution'] if v_info else v_id
            a_desc = a_info['bitrate'] if a_info else a_id
            desc = f"{v_desc} + {a_desc} ({custom_id})"
        elif v_id:
            custom_id = v_id
            v_info = next((s for s in self.video_streams if s["id"] == v_id), None)
            desc = f"Chỉ Video {v_info['resolution']} ({custom_id})" if v_info else custom_id
        elif a_id:
            custom_id = a_id
            a_info = next((s for s in self.audio_streams if s["id"] == a_id), None)
            desc = f"Chỉ Audio {a_info['bitrate']} ({custom_id})" if a_info else custom_id
        else:
            msgbox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một luồng Video hoặc Audio!")
            return

        if self.on_apply:
            self.on_apply(custom_id, desc)

        self.destroy()

    def on_reset_auto(self):
        if self.on_apply:
            self.on_apply("", "")
        self.destroy()
