"""
Module Tự động Nhận diện & Trích xuất Metadata Liên kết (URL Detector & Extractor).
Hỗ trợ TikTok (kèm fallback TikWM), Facebook, YouTube, Bilibili, Instagram, và hơn 1000 nền tảng.
Tự động hỗ trợ Cookie trình duyệt và Tệp cookies.txt trực tiếp.
"""

import os
import re
import io
import time
import urllib.parse
from pathlib import Path
from PIL import Image
import requests

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

class URLDetector:
    """Xử lý nhận diện và trích xuất thông tin URL."""

    @staticmethod
    def is_valid_url(text: str) -> bool:
        """Kiểm tra xem chuỗi có phải là đường dẫn URL hợp lệ không."""
        if not text or not isinstance(text, str):
            return False
        text = text.strip()
        if not (text.startswith("http://") or text.startswith("https://")):
            return False
        try:
            parsed = urllib.parse.urlparse(text)
            return bool(parsed.netloc) and len(parsed.netloc.split('.')) >= 2
        except Exception:
            return False

    @classmethod
    def detect_platform(cls, url: str) -> str:
        """Nhận diện nền tảng từ URL."""
        if not url:
            return "Khác"
        u = url.lower()
        if "youtube.com" in u or "youtu.be" in u:
            return "YouTube"
        elif "tiktok.com" in u or "douyin.com" in u:
            return "TikTok"
        elif "facebook.com" in u or "fb.watch" in u or "fb.com" in u:
            return "Facebook"
        elif "instagram.com" in u:
            return "Instagram"
        elif "bilibili.com" in u:
            return "Bilibili"
        elif "twitter.com" in u or "x.com" in u:
            return "Twitter / X"
        elif "threads.net" in u:
            return "Threads"
        elif "soundcloud.com" in u:
            return "SoundCloud"
        elif "twitch.tv" in u:
            return "Twitch"
        elif "vimeo.com" in u:
            return "Vimeo"
        elif "reddit.com" in u:
            return "Reddit"
        elif "kuaishou.com" in u:
            return "Kuaishou"
        return "Đa nền tảng"

    @staticmethod
    def format_duration(seconds: int | float | None) -> str:
        """Định dạng số giây thành chuỗi thời lượng (hh:mm:ss hoặc mm:ss)."""
        if not seconds or seconds < 0:
            return "Không xác định"
        seconds = int(seconds)
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    @classmethod
    def _extract_tiktok_fallback(cls, url: str) -> tuple[bool, dict | None, str]:
        """Trích xuất nhanh video TikTok qua TikWM API nếu yt-dlp gặp lỗi."""
        try:
            resp = requests.post('https://www.tikwm.com/api/', data={'url': url, 'count': 12, 'cursor': 0, 'web': 1, 'hd': 1}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 0:
                    d = data.get('data', {})
                    title = d.get('title') or 'TikTok Video'
                    author = d.get('author', {}).get('nickname') or d.get('author', {}).get('unique_id') or 'TikTok Creator'
                    duration = d.get('duration', 0)
                    cover = d.get('cover', '')
                    if cover and not cover.startswith('http'):
                        cover = 'https://www.tikwm.com' + cover

                    play_url = d.get('hdplay') or d.get('play')
                    if play_url and not play_url.startswith('http'):
                        play_url = 'https://www.tikwm.com' + play_url

                    music_url = d.get('music')
                    if music_url and not music_url.startswith('http'):
                        music_url = 'https://www.tikwm.com' + music_url

                    result = {
                        "url": url,
                        "title": title,
                        "uploader": author,
                        "duration_sec": duration,
                        "duration_str": cls.format_duration(duration),
                        "thumbnail_url": cover,
                        "platform": "TikTok",
                        "is_playlist": False,
                        "playlist_count": 1,
                        "direct_video_url": play_url,
                        "direct_audio_url": music_url,
                        "qualities": [
                            "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)",
                            "📱 Full HD (1080p)",
                            "📱 HD (720p)",
                            "⚡ SD (480p)",
                            "🎵 Chỉ tải Âm thanh (Audio MP3/M4A)"
                        ]
                    }
                    return True, result, "Lấy thông tin TikTok thành công!"
        except Exception:
            pass
        return False, None, "Không thể lấy dữ liệu TikTok."

    @classmethod
    def fetch_metadata(cls, url: str, cookie_browser: str = "none", cookie_file: str = "") -> tuple[bool, dict | None, str]:
        """
        Trích xuất thông tin chi tiết video/playlist từ URL bằng yt-dlp và bộ giải mã phụ trợ.
        Tự động hỗ trợ cookie file (.txt) hoặc cookie trình duyệt với cơ chế an toàn.
        """
        plat = cls.detect_platform(url)

        if yt_dlp:
            base_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'skip_download': True,
                'ignoreerrors': False,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept-Language': 'vi,en;q=0.9',
                    'Sec-Fetch-Mode': 'navigate'
                }
            }

            info = None
            last_err = ""

            # 1. Thử với tệp Cookie (.txt) nếu có
            if cookie_file and os.path.exists(cookie_file):
                ydl_opts_file = dict(base_opts)
                ydl_opts_file['cookiefile'] = cookie_file
                try:
                    with yt_dlp.YoutubeDL(ydl_opts_file) as ydl:
                        info = ydl.extract_info(url, download=False)
                except Exception as e:
                    last_err = str(e)

            # 2. Thử với Cookie trình duyệt nếu được chọn
            if not info and cookie_browser and cookie_browser not in ["none", "file", ""]:
                ydl_opts_cookie = dict(base_opts)
                ydl_opts_cookie['cookiesfrombrowser'] = (cookie_browser,)
                try:
                    with yt_dlp.YoutubeDL(ydl_opts_cookie) as ydl:
                        info = ydl.extract_info(url, download=False)
                except Exception as e:
                    last_err = str(e)

            # 3. Thử chế độ chuẩn không cookie
            if not info:
                try:
                    with yt_dlp.YoutubeDL(base_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                except Exception as e:
                    last_err = str(e)

            if info:
                is_playlist = info.get('_type') == 'playlist' or 'entries' in info
                title = info.get('title', 'Không có tiêu đề')
                uploader = info.get('uploader') or info.get('channel') or info.get('uploader_id') or 'Không rõ người đăng'
                duration_sec = info.get('duration')
                thumbnail_url = info.get('thumbnail')

                qualities_list = [
                    "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)",
                    "🎬 8K Ultra HD (4320p)",
                    "🎬 4K Ultra HD (2160p)",
                    "📺 2K Quad HD (1440p)",
                    "📺 Full HD 1080p (60fps)",
                    "📺 Full HD 1080p",
                    "📱 HD 720p (60fps)",
                    "📱 HD 720p",
                    "📱 SD 480p",
                    "⚡ Thấp 360p (Tiết kiệm dung lượng)",
                    "⚡ Nhỏ nhất 240p / 144p",
                    "🎵 Chỉ tải Âm thanh (Audio MP3/M4A)"
                ]

                entries_count = len(list(info.get('entries', []))) if is_playlist else 1

                result = {
                    "url": url,
                    "title": title,
                    "uploader": uploader,
                    "duration_sec": duration_sec,
                    "duration_str": cls.format_duration(duration_sec),
                    "thumbnail_url": thumbnail_url,
                    "platform": plat,
                    "is_playlist": is_playlist,
                    "playlist_count": entries_count,
                    "qualities": qualities_list
                }
                return True, result, "Lấy thông tin thành công!"

        # Fallback cho TikTok
        if plat == "TikTok":
            ok, res, msg = cls._extract_tiktok_fallback(url)
            if ok:
                return True, res, msg

        if plat == "Facebook":
            return False, None, "Video Facebook này yêu cầu phiên đăng nhập (Cookie).\n👉 Hãy chọn 'Tệp Cookie (.txt)' hoặc đóng trình duyệt Chrome/Edge rồi chọn lại để xác thực."

        return False, None, "Không thể lấy thông tin từ liên kết này. Vui lòng kiểm tra lại đường dẫn."

    @staticmethod
    def load_thumbnail_image(url: str, size: tuple = (200, 112)) -> Image.Image | None:
        """Tải ảnh thumbnail từ URL và resize phù hợp để hiển thị trên UI."""
        if not url:
            return None
        try:
            resp = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if resp.status_code == 200:
                img = Image.open(io.BytesIO(resp.content))
                img = img.convert("RGBA")
                img.thumbnail(size, Image.Resampling.LANCZOS)
                return img
        except Exception:
            pass
        return None
