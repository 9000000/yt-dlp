"""
Module Nhận Diện Nền Tảng & Trích Xuất Metadata Video/Playlist.
Hỗ trợ YouTube, TikTok, Facebook, Instagram, Bilibili, Douyin, X (Twitter), Pinterest, v.v.
Tích hợp bypass Botguard YouTube (PO Token) và fallback đa luồng chống khóa Cookie trình duyệt.
"""

import os
import re
import time
import requests
from io import BytesIO
from PIL import Image

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

class QuietYTDLPLogger:
    """Bộ ghi log yên lặng ngăn yt-dlp in lỗi khóa cookie ra màn hình."""
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class URLDetector:
    """Lớp tiện ích phân tích URL, nhận diện nền tảng và lấy thông tin video."""

    PLATFORMS = {
        "YouTube": [r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)"],
        "TikTok": [r"(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com|vt\.tiktok\.com)"],
        "Facebook": [r"(?:https?:\/\/)?(?:www\.|m\.|web\.|fb\.)?(?:facebook\.com|fb\.watch|fb\.me)"],
        "Instagram": [r"(?:https?:\/\/)?(?:www\.)?instagram\.com"],
        "Bilibili": [r"(?:https?:\/\/)?(?:www\.)?bilibili\.com"],
        "Douyin": [r"(?:https?:\/\/)?(?:www\.)?douyin\.com"],
        "X / Twitter": [r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)"],
        "Pinterest": [r"(?:https?:\/\/)?(?:www\.)?(?:pinterest\.com|pin\.it)"],
        "Vimeo": [r"(?:https?:\/\/)?(?:www\.)?vimeo\.com"],
        "SoundCloud": [r"(?:https?:\/\/)?(?:www\.)?soundcloud\.com"],
    }

    @classmethod
    def is_valid_url(cls, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False
        pattern = r"^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/.*)?$"
        return bool(re.match(pattern, text.strip()))

    @classmethod
    def detect_platform(cls, url: str) -> str:
        if not url:
            return "Không xác định"
        for name, patterns in cls.PLATFORMS.items():
            for p in patterns:
                if re.search(p, url, re.IGNORECASE):
                    return name
        return "Đa nền tảng"

    @staticmethod
    def format_duration(seconds: int | float | None) -> str:
        if seconds is None or seconds < 0:
            return "--:--"
        try:
            sec = int(seconds)
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            if h > 0:
                return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"
        except Exception:
            return "--:--"

    @staticmethod
    def load_thumbnail_image(url: str, size: tuple[int, int] = (240, 135)) -> Image.Image | None:
        if not url:
            return None
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                img = img.convert("RGB")
                img.thumbnail(size, Image.Resampling.LANCZOS)
                return img
        except Exception:
            pass
        return None

    @classmethod
    def _extract_tiktok_fallback(cls, url: str) -> tuple[bool, dict | None, str]:
        try:
            api_url = "https://www.tikwm.com/api/"
            resp = requests.post(api_url, data={"url": url, "hd": 1}, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and "data" in data:
                    d = data["data"]
                    title = d.get("title") or "Video TikTok không tiêu đề"
                    author = d.get("author", {}).get("nickname", "Không rõ tác giả")
                    duration = d.get("duration", 0)
                    cover = d.get("cover") or d.get("origin_cover")
                    play_url = d.get("hdplay") or d.get("play")
                    if play_url and not play_url.startswith("http"):
                        play_url = "https://www.tikwm.com" + play_url

                    music_url = d.get("music")
                    if music_url and not music_url.startswith("http"):
                        music_url = "https://www.tikwm.com" + music_url

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
    def fetch_metadata(
        cls,
        url: str,
        cookie_browser: str = "none",
        cookie_file: str = "",
        pot_enabled: bool = True,
        pot_provider_url: str = ""
    ) -> tuple[bool, dict | None, str]:
        """
        Trích xuất thông tin chi tiết video/playlist từ URL bằng yt-dlp và bộ giải mã phụ trợ.
        Tự động xử lý ngoại lệ cookie và PO Token.
        """
        plat = cls.detect_platform(url)

        if yt_dlp:
            base_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'skip_download': True,
                'ignoreerrors': False,
                'logger': QuietYTDLPLogger(),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept-Language': 'vi,en;q=0.9',
                    'Sec-Fetch-Mode': 'navigate'
                }
            }

            # Tích hợp YouTube Botguard / PO Token Provider & Multi-client fallback
            if ("youtube.com" in url.lower() or "youtu.be" in url.lower()) and pot_enabled:
                extractor_args = {
                    'youtube': {
                        'player_client': ['web', 'android', 'ios']
                    }
                }
                if pot_provider_url and pot_provider_url.startswith("http"):
                    extractor_args['youtubepot-bgutil'] = {
                        'base_url': [pot_provider_url]
                    }
                base_opts['extractor_args'] = extractor_args

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

            # 2. Thử với Cookie trình duyệt nếu được chọn (tự động bỏ qua nếu trình duyệt đang khóa db)
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
                    "⚡ Thấp (360p)",
                    "⚡ Tiết kiệm dữ liệu (240p/144p)",
                    "🎵 Chỉ lấy Âm thanh (MP3 / M4A)"
                ]

                result = {
                    "url": url,
                    "title": title,
                    "uploader": uploader,
                    "duration_sec": duration_sec,
                    "duration_str": cls.format_duration(duration_sec),
                    "thumbnail_url": thumbnail_url,
                    "platform": plat,
                    "is_playlist": is_playlist,
                    "playlist_count": len(info.get('entries', [])) if is_playlist else 1,
                    "qualities": qualities_list,
                    "formats": info.get('formats', [])
                }
                return True, result, "Phân tích thông tin thành công!"

        # Fallback cho TikTok
        if plat == "TikTok":
            ok, res, msg = cls._extract_tiktok_fallback(url)
            if ok:
                return True, res, msg

        clean_err = last_err if last_err else "Không thể kết nối hoặc bóc tách thông tin từ đường dẫn này."
        if "could not copy" in clean_err.lower() or "database" in clean_err.lower():
            clean_err = "Trình duyệt đang mở nên tệp Cookie bị khóa.\n👉 Hãy tắt trình duyệt hoặc chọn 'Không dùng Cookie' / 'Tệp Cookie (.txt)' để tiếp tục."

        return False, None, clean_err
