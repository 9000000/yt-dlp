"""
Lõi Xử lý & Tải Video Đa luồng Bất đồng bộ (Downloader Engine).
Hỗ trợ đầy đủ các mức chất lượng (8K/4K/2K/1080p60/720p), bitrate âm thanh,
gắn thẻ metadata, nhúng thumbnail, phụ đề, tăng tốc đa luồng và tích hợp PO Token Botguard bypass.
"""

import os
import sys
import time
import threading
import requests
from pathlib import Path
from typing import Callable

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from tool_gui.updater import UpdaterManager

class QuietYTDLPLogger:
    """Bộ ghi log yên lặng ngăn yt-dlp in lỗi khóa cookie ra màn hình."""
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class DownloadTask:
    """Tác vụ tải video / âm thanh."""

    def __init__(
        self,
        url: str,
        output_dir: str,
        title: str = "",
        quality: str = "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)",
        output_format: str = "MP4",
        audio_only: bool = False,
        audio_codec: str = "MP3 - 320 kbps (Cực cao)",
        embed_subs: bool = False,
        sub_langs: str = "vi,en",
        embed_thumbnail: bool = True,
        add_metadata: bool = True,
        cookie_browser: str = "none",
        cookie_file: str = "",
        pot_enabled: bool = True,
        pot_provider_url: str = "",
        playlist_items: str = None,
        direct_url: str = None,
        dns_servers: list = None,
        concurrent_fragments: int = 4,
        ratelimit: str = "",
        auto_subs: bool = True,
        split_chapters: bool = False,
        video_codec: str = "",
        fps_prefer: str = "",
        custom_format_id: str = "",
        on_progress: Callable[[dict], None] = None,
        on_status: Callable[[str], None] = None,
        on_finish: Callable[[bool, str, str], None] = None
    ):
        self.url = url
        self.output_dir = output_dir
        self.title = title
        self.quality = quality
        self.output_format = output_format.lower()
        self.audio_only = audio_only
        self.audio_codec = audio_codec
        self.embed_subs = embed_subs
        self.sub_langs = sub_langs
        self.embed_thumbnail = embed_thumbnail
        self.add_metadata = add_metadata
        self.cookie_browser = cookie_browser
        self.cookie_file = cookie_file
        self.pot_enabled = pot_enabled
        self.pot_provider_url = pot_provider_url
        self.playlist_items = playlist_items
        self.direct_url = direct_url
        self.dns_servers = dns_servers or []
        self.concurrent_fragments = concurrent_fragments or 4
        self.ratelimit = ratelimit
        self.auto_subs = auto_subs
        self.split_chapters = split_chapters
        self.video_codec = video_codec
        self.fps_prefer = fps_prefer
        self.custom_format_id = custom_format_id

        self.on_progress = on_progress
        self.on_status = on_status
        self.on_finish = on_finish

        self._stop_requested = False
        self._thread = None
        self._updater = UpdaterManager()

    def stop(self):
        """Yêu cầu dừng tiến trình tải."""
        self._stop_requested = True

    def start(self):
        """Bắt đầu tải trong luồng nền (Background Thread)."""
        self._stop_requested = False
        self._thread = threading.Thread(target=self._run_download, daemon=True)
        self._thread.start()

    def _build_format_spec(self) -> str:
        """Xây dựng chuỗi định dạng chọn chất lượng video và codec cho yt-dlp."""
        if self.custom_format_id:
            return self.custom_format_id

        if self.audio_only:
            return "bestaudio/best"

        q = self.quality
        height = None
        if "4320" in q or "8K" in q:
            height = 4320
        elif "2160" in q or "4K" in q:
            height = 2160
        elif "1440" in q or "2K" in q:
            height = 1440
        elif "1080" in q or "Full HD" in q:
            height = 1080
        elif "720" in q or "HD" in q:
            height = 720
        elif "480" in q or "SD" in q:
            height = 480
        elif "360" in q:
            height = 360
        elif "240" in q or "144" in q:
            height = 240

        v_filter = f"[height<={height}]" if height else ""
        if "60fps" in q or (self.fps_prefer and "60fps" in self.fps_prefer):
            v_filter += "[fps>=50]"

        codec_tag = ""
        c = (self.video_codec or "").lower()
        if "h.264" in c or "avc" in c:
            codec_tag = "[vcodec^=avc1]"
        elif "h.265" in c or "hevc" in c:
            codec_tag = "[vcodec^=hev1]"
        elif "vp9" in c:
            codec_tag = "[vcodec^=vp9]"
        elif "av1" in c:
            codec_tag = "[vcodec^=av01]"

        if codec_tag:
            return f"bestvideo{v_filter}{codec_tag}+bestaudio/bestvideo{v_filter}+bestaudio/best{v_filter}/best"
        elif v_filter:
            return f"bestvideo{v_filter}+bestaudio/best{v_filter}/best"
        else:
            return "bestvideo+bestaudio/best"

    def _format_size(self, bytes_val: int | float | None) -> str:
        """Định dạng byte thành MB, GB dễ nhìn."""
        if not bytes_val or bytes_val <= 0:
            return "0 MB"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"

    def _format_speed(self, speed_bytes: int | float | None) -> str:
        """Định dạng tốc độ tải."""
        if not speed_bytes or speed_bytes <= 0:
            return "0 KB/s"
        if speed_bytes >= 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024):.2f} MB/s"
        return f"{speed_bytes / 1024:.1f} KB/s"

    def _progress_hook(self, d: dict):
        """Bắt thông tin tiến trình từ yt-dlp."""
        if self._stop_requested:
            raise Exception("Người dùng đã hủy quá trình tải.")

        status = d.get('status')
        if status == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded_bytes = d.get('downloaded_bytes', 0)
            speed = d.get('speed') or 0
            eta = d.get('eta')

            pct = 0.0
            if total_bytes > 0:
                pct = (downloaded_bytes / total_bytes) * 100.0

            eta_str = f"{eta}s" if eta is not None else "--"
            speed_str = self._format_speed(speed)
            size_str = f"{self._format_size(downloaded_bytes)} / {self._format_size(total_bytes)}"

            progress_data = {
                "percent": pct,
                "percent_float": pct / 100.0,
                "speed": speed_str,
                "eta": eta_str,
                "size_info": size_str,
                "status_text": f"Đang tải: {pct:.1f}% ({speed_str}) - Còn: {eta_str}"
            }

            if self.on_progress:
                self.on_progress(progress_data)

        elif status == 'finished':
            if self.on_status:
                self.on_status("Đang hoàn thiện, nhúng metadata & gộp file qua FFmpeg...")

    def _download_direct_stream(self, out_path: Path):
        """Tải trực tiếp nếu có direct URL từ fallback (ví dụ TikTok TikWM)."""
        target_url = self.direct_url
        if not target_url:
            return False

        if self.on_status:
            self.on_status("Đang tải trực tiếp video chất lượng cao...")

        resp = requests.get(target_url, stream=True, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return False

        total_len = int(resp.headers.get('content-length', 0))
        downloaded = 0
        file_ext = "mp3" if self.audio_only else "mp4"

        # Đặt tên file theo tiêu đề video nếu có
        import re
        clean_title = re.sub(r'[\\/*?:"<>|]', "", self.title).strip() if self.title else ""
        if not clean_title:
            clean_title = f"video_{int(time.time())}"
        if len(clean_title) > 100:
            clean_title = clean_title[:100].strip()

        file_name = f"{clean_title}.{file_ext}"
        target_file = out_path / file_name

        start_time = time.time()
        with open(target_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 64):
                if self._stop_requested:
                    raise Exception("Người dùng đã dừng tải.")
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    elapsed = time.time() - start_time
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    eta = int((total_len - downloaded) / speed) if speed > 0 and total_len > downloaded else None
                    if total_len > 0 and self.on_progress:
                        pct = (downloaded / total_len) * 100.0
                        self.on_progress({
                            "percent": pct,
                            "percent_float": pct / 100.0,
                            "speed": self._format_speed(speed),
                            "eta": f"{eta}s" if eta is not None else "--",
                            "size_info": f"{self._format_size(downloaded)} / {self._format_size(total_len)}",
                            "status_text": f"Đang tải: {pct:.1f}% ({self._format_speed(speed)})"
                        })

        if self.on_finish:
            self.on_finish(True, "✅ Tải hoàn tất thành công!", str(target_file))
        return True

    def _run_download(self):
        """Hàm thực thi tải trong background thread."""
        out_path = Path(self.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        if self.direct_url:
            try:
                if self._download_direct_stream(out_path):
                    return
            except Exception:
                pass

        if not yt_dlp:
            if self.on_finish:
                self.on_finish(False, "Thư viện yt-dlp chưa được cài đặt.", "")
            return

        out_template = str(out_path / "%(title)s [%(id)s].%(ext)s")
        ffmpeg_path = self._updater.get_ffmpeg_path()

        base_opts = {
            'outtmpl': out_template,
            'format': self._build_format_spec(),
            'progress_hooks': [self._progress_hook],
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'quiet': True,
            'no_warnings': True,
            'logger': QuietYTDLPLogger(),
            'concurrent_fragment_downloads': self.concurrent_fragments,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept-Language': 'vi,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate'
            }
        }

        if self.ratelimit and "MB/s" in self.ratelimit:
            try:
                mb = float(self.ratelimit.replace("MB/s", "").strip())
                base_opts['ratelimit'] = int(mb * 1024 * 1024)
            except Exception:
                pass

        # Tích hợp YouTube Botguard / PO Token Provider
        if ("youtube.com" in self.url.lower() or "youtu.be" in self.url.lower()) and self.pot_enabled and self.pot_provider_url and self.pot_provider_url.startswith("http"):
            base_opts['extractor_args'] = {
                'youtubepot-bgutil': {
                    'provider_url': [self.pot_provider_url]
                }
            }

        if ffmpeg_path:
            base_opts['ffmpeg_location'] = ffmpeg_path

        if self.dns_servers:
            base_opts['dns_servers'] = self.dns_servers

        postprocessors = []

        if self.split_chapters:
            postprocessors.append({'key': 'FFmpegSplitChapters'})

        if self.audio_only:
            audio_text = self.audio_codec.lower()
            codec = 'mp3'
            bitrate = '320'
            if '256' in audio_text:
                bitrate = '256'
            elif '192' in audio_text:
                bitrate = '192'
            elif '128' in audio_text:
                bitrate = '128'
            elif '96' in audio_text:
                bitrate = '96'

            if 'm4a' in audio_text or 'aac' in audio_text:
                codec = 'm4a'
            elif 'flac' in audio_text:
                codec = 'flac'
            elif 'wav' in audio_text:
                codec = 'wav'
            elif 'opus' in audio_text:
                codec = 'opus'
            elif 'vorbis' in audio_text or 'ogg' in audio_text:
                codec = 'vorbis'
            elif 'alac' in audio_text:
                codec = 'alac'
            elif 'wma' in audio_text:
                codec = 'wma'
            elif 'aiff' in audio_text:
                codec = 'aiff'

            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': bitrate,
            })
        else:
            fmt_lower = self.output_format.lower()
            target_ext = 'mp4'
            for ext in ['mp4', 'mkv', 'webm', 'mov', 'avi', 'ts', 'flv', '3gp', 'ogv', 'wmv']:
                if ext in fmt_lower:
                    target_ext = ext
                    break
            base_opts['merge_output_format'] = target_ext

        if self.add_metadata:
            postprocessors.append({'key': 'FFmpegMetadata'})

        if self.embed_thumbnail:
            base_opts['writethumbnail'] = True
            postprocessors.append({'key': 'EmbedThumbnail'})

        if postprocessors:
            base_opts['postprocessors'] = postprocessors

        if self.embed_subs and not self.audio_only:
            langs = [l.strip() for l in self.sub_langs.split(',') if l.strip()]
            base_opts['writesubtitles'] = True
            if self.auto_subs:
                base_opts['writeautomaticsub'] = True
            base_opts['subtitleslangs'] = langs
            base_opts['embedsubtitles'] = True

        if self.playlist_items:
            base_opts['playlist_items'] = self.playlist_items

        ydl_opts = dict(base_opts)

        if self.cookie_file and os.path.exists(self.cookie_file):
            ydl_opts['cookiefile'] = self.cookie_file
        elif self.cookie_browser and self.cookie_browser not in ["none", "file", ""]:
            ydl_opts['cookiesfrombrowser'] = (self.cookie_browser,)

        try:
            if self.on_status:
                self.on_status("Đang kết nối máy chủ video...")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url, download=True)
            except Exception as e:
                err_text = str(e).lower()
                if "cookie" in err_text and ("copy" in err_text or "lock" in err_text or "find" in err_text) and 'cookiesfrombrowser' in ydl_opts:
                    if self.on_status:
                        self.on_status("Cookie trình duyệt bị khóa, tự động chuyển sang chế độ chuẩn...")
                    with yt_dlp.YoutubeDL(base_opts) as ydl:
                        info = ydl.extract_info(self.url, download=True)
                else:
                    raise

            if self.on_finish:
                self.on_finish(True, "✅ Tải hoàn tất thành công!", str(out_path))

        except Exception as e:
            err_msg = str(e)
            if self._stop_requested or "hủy" in err_msg.lower() or "dừng" in err_msg.lower():
                if self.on_finish:
                    self.on_finish(False, "⏹️ Đã dừng quá trình tải.", "")
            else:
                if "cannot parse data" in err_msg.lower() or "login" in err_msg.lower():
                    err_msg = "Video Facebook này yêu cầu phiên đăng nhập (Cookie).\n👉 Hãy chọn 'Tệp Cookie (.txt)' hoặc đóng trình duyệt Chrome/Edge rồi chọn lại để xác thực."

                if self.on_finish:
                    self.on_finish(False, f"❌ {err_msg}", "")
