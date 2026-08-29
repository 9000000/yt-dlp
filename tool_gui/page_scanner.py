"""
Module Quét & Trích Xuất Toàn Bộ Video Trên Trang Web (Page Video Scanner).
Hỗ trợ quét trang web bất kỳ (kênh YouTube, playlist, trang tin tức, blog, Facebook, TikTok) 
để tìm ra toàn bộ video có trên trang kèm đầy đủ Tiêu đề, Tác giả, Thời lượng và Ảnh Thumbnail xem trước.
"""

import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from tool_gui.url_detector import URLDetector

class PageVideoScanner:
    """Quét và trích xuất tất cả liên kết video trên một trang web."""

    @staticmethod
    def scan_webpage_for_videos(page_url: str, cookie_browser: str = "none", cookie_file: str = "", dns_servers: list = None) -> tuple[bool, list, str]:
        """
        Quét URL trang web và trả về danh sách tất cả các video tìm thấy kèm Thumbnail.
        Mỗi item: {url, title, uploader, platform, duration_str, thumbnail_url}
        """
        if not URLDetector.is_valid_url(page_url):
            return False, [], "Đường dẫn trang web không hợp lệ."

        results = []
        seen_urls = set()

        # 1. Thử dùng yt-dlp với flat-playlist trước (rất mạnh đối với YouTube channel/playlist, TikTok profile, Facebook page)
        if yt_dlp:
            try:
                ydl_opts = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                    'playlistend': 50,  # Giới hạn 50 video đầu để quét nhanh
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
                    }
                }
                if dns_servers:
                    ydl_opts['dns_servers'] = dns_servers
                if cookie_file:
                    ydl_opts['cookiefile'] = cookie_file
                elif cookie_browser and cookie_browser not in ["none", "file", ""]:
                    ydl_opts['cookiesfrombrowser'] = (cookie_browser,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(page_url, download=False)
                    if info:
                        entries = info.get('entries')
                        if entries:
                            for entry in entries:
                                if not entry:
                                    continue
                                v_url = entry.get('url') or entry.get('webpage_url')
                                v_id = entry.get('id')
                                if not v_url:
                                    if v_id and 'youtube' in page_url:
                                        v_url = f"https://www.youtube.com/watch?v={v_id}"
                                    else:
                                        continue

                                if v_url not in seen_urls:
                                    seen_urls.add(v_url)
                                    dur = entry.get('duration')
                                    dur_str = URLDetector.format_duration(dur) if dur else "--:--"
                                    
                                    # Lấy thumbnail
                                    thumbs = entry.get('thumbnails') or []
                                    thumb_url = entry.get('thumbnail') or (thumbs[-1].get('url') if thumbs else "")
                                    if not thumb_url and v_id:
                                        thumb_url = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

                                    results.append({
                                        "url": v_url,
                                        "title": entry.get('title') or "Video không tiêu đề",
                                        "uploader": entry.get('uploader') or entry.get('channel') or "--",
                                        "platform": URLDetector.detect_platform(v_url),
                                        "duration_str": dur_str,
                                        "thumbnail_url": thumb_url
                                    })

                        elif info.get('url') or info.get('webpage_url'):
                            single_url = info.get('webpage_url') or info.get('url') or page_url
                            v_id = info.get('id')
                            if single_url not in seen_urls:
                                seen_urls.add(single_url)
                                dur = info.get('duration')
                                thumbs = info.get('thumbnails') or []
                                thumb_url = info.get('thumbnail') or (thumbs[-1].get('url') if thumbs else "")
                                if not thumb_url and v_id:
                                    thumb_url = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

                                results.append({
                                    "url": single_url,
                                    "title": info.get('title') or "Video đơn",
                                    "uploader": info.get('uploader') or "--",
                                    "platform": URLDetector.detect_platform(single_url),
                                    "duration_str": URLDetector.format_duration(dur) if dur else "--:--",
                                    "thumbnail_url": thumb_url
                                })

            except Exception:
                pass

        # 2. Quét HTML DOM qua BeautifulSoup nếu ít kết quả
        if len(results) < 2:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept-Language": "vi,en;q=0.9"
                }
                resp = requests.get(page_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Tìm ảnh đại diện trang nếu có
                    page_thumb = ""
                    og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
                    if og_img and og_img.get("content"):
                        page_thumb = og_img["content"]

                    # Tìm các thẻ a href
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        full_url = urllib.parse.urljoin(page_url, href)

                        if URLDetector.is_valid_url(full_url) and full_url not in seen_urls:
                            plat = URLDetector.detect_platform(full_url)
                            is_video_link = False
                            v_thumb = page_thumb

                            if "youtube.com/watch" in full_url or "youtu.be/" in full_url or "youtube.com/shorts/" in full_url:
                                is_video_link = True
                                match = re.search(r"(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", full_url)
                                if match:
                                    v_thumb = f"https://i.ytimg.com/vi/{match.group(1)}/hqdefault.jpg"
                            elif "tiktok.com/@" in full_url and "/video/" in full_url:
                                is_video_link = True
                            elif "facebook.com/" in full_url and ("/videos/" in full_url or "/reel/" in full_url or "/watch/" in full_url):
                                is_video_link = True
                            elif "bilibili.com/video/" in full_url:
                                is_video_link = True
                            elif full_url.endswith((".mp4", ".mkv", ".webm", ".m3u8")):
                                is_video_link = True

                            if is_video_link:
                                seen_urls.add(full_url)
                                link_text = a.get_text().strip() or a.get("title") or "Video tìm thấy trên trang"
                                
                                # Tìm ảnh thumbnail con trong thẻ a nếu có
                                img_child = a.find("img")
                                if img_child and img_child.get("src"):
                                    v_thumb = urllib.parse.urljoin(page_url, img_child["src"])

                                results.append({
                                    "url": full_url,
                                    "title": link_text[:80],
                                    "uploader": "--",
                                    "platform": plat,
                                    "duration_str": "--:--",
                                    "thumbnail_url": v_thumb
                                })

                    # Tìm các thẻ iframe embed
                    for iframe in soup.find_all("iframe", src=True):
                        src = iframe["src"]
                        full_src = urllib.parse.urljoin(page_url, src)
                        if ("youtube.com/embed/" in full_src or "player.vimeo.com" in full_src or "facebook.com/plugins/video" in full_src) and full_src not in seen_urls:
                            seen_urls.add(full_src)
                            v_thumb = page_thumb
                            match = re.search(r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})", full_src)
                            if match:
                                v_thumb = f"https://i.ytimg.com/vi/{match.group(1)}/hqdefault.jpg"

                            results.append({
                                "url": full_src,
                                "title": iframe.get("title") or "Video Iframe nhúng",
                                "uploader": "--",
                                "platform": URLDetector.detect_platform(full_src),
                                "duration_str": "--:--",
                                "thumbnail_url": v_thumb
                            })

            except Exception:
                pass

        if results:
            return True, results, f"Đã quét thành công và tìm thấy {len(results)} video trên trang!"
        return False, [], "Không tìm thấy video nào trên trang web này. Vui lòng kiểm tra lại URL."

    @staticmethod
    def search_videos_by_keyword(keyword: str, max_results: int = 15, platform: str = "YouTube", dns_servers: list = None) -> tuple[bool, list, str]:
        """
        Tìm kiếm video theo từ khóa (mặc định YouTube hoặc đa nền tảng).
        """
        if not keyword or not keyword.strip():
            return False, [], "Vui lòng nhập từ khóa tìm kiếm."

        if not yt_dlp:
            return False, [], "Thư viện yt-dlp chưa sẵn sàng."

        results = []
        try:
            search_query = f"ytsearch{max_results}:{keyword.strip()}"
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
                }
            }
            if dns_servers:
                ydl_opts['dns_servers'] = dns_servers

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if not entry:
                            continue
                        v_id = entry.get('id')
                        v_url = entry.get('url') or (f"https://www.youtube.com/watch?v={v_id}" if v_id else None)
                        if not v_url:
                            continue

                        dur = entry.get('duration')
                        dur_str = URLDetector.format_duration(dur) if dur else "--:--"
                        thumbs = entry.get('thumbnails') or []
                        thumb_url = entry.get('thumbnail') or (thumbs[-1].get('url') if thumbs else "")
                        if not thumb_url and v_id:
                            thumb_url = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

                        results.append({
                            "url": v_url,
                            "title": entry.get('title') or "Không có tiêu đề",
                            "uploader": entry.get('uploader') or entry.get('channel') or "--",
                            "platform": "YouTube",
                            "duration_str": dur_str,
                            "thumbnail_url": thumb_url,
                            "view_count": entry.get('view_count', 0)
                        })

            if results:
                return True, results, f"Tìm thấy {len(results)} kết quả cho từ khóa '{keyword}'!"
            return False, [], "Không tìm thấy kết quả nào."

        except Exception as e:
            return False, [], f"Lỗi khi tìm kiếm: {str(e)}"
