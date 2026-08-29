"""
Module Quản lý & Tự động Cập nhật Phụ trợ (FFmpeg & yt-dlp Updater).
Tự động phát hiện, tải về, giải nén và cập nhật FFmpeg / yt-dlp.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import threading
import subprocess
import requests
from pathlib import Path

# URL tải bản dựng FFmpeg mới nhất cho Windows 64-bit
FFMPEG_URL_YTDLP = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_URL_GYAN = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
YTDLP_PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"

class UpdaterManager:
    """Quản lý phụ trợ FFmpeg và bộ công cụ tải yt-dlp."""

    def __init__(self, app_dir=None):
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            if getattr(sys, 'frozen', False):
                self.app_dir = Path(sys.executable).parent
            else:
                self.app_dir = Path(__file__).resolve().parent.parent

        self.bin_dir = self.app_dir / "bin"
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_exe = self.bin_dir / "ffmpeg.exe"
        self.ffprobe_exe = self.bin_dir / "ffprobe.exe"

    def get_ffmpeg_path(self) -> str | None:
        """
        Lấy đường dẫn FFmpeg:
        1. Ưu tiên thư mục bin/ nội bộ của app.
        2. Sau đó kiểm tra trong PATH hệ thống.
        """
        if self.ffmpeg_exe.exists():
            return str(self.ffmpeg_exe)

        # Kiểm tra PATH hệ thống
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg

        return None

    def is_ffmpeg_installed(self) -> bool:
        """Kiểm tra xem FFmpeg đã sẵn sàng hoạt động hay chưa."""
        return self.get_ffmpeg_path() is not None

    def get_ffmpeg_version(self) -> str:
        """Lấy phiên bản FFmpeg hiện tại."""
        path = self.get_ffmpeg_path()
        if not path:
            return "Chưa cài đặt"
        try:
            res = subprocess.run(
                [path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                timeout=5
            )
            first_line = res.stdout.splitlines()[0] if res.stdout else "Không xác định"
            return first_line.replace("ffmpeg version", "").strip().split(" ")[0]
        except Exception as e:
            return f"Đã phát hiện ({path})"

    def get_ytdlp_version(self) -> str:
        """Lấy phiên bản yt-dlp hiện tại đang sử dụng."""
        try:
            import yt_dlp.version
            return yt_dlp.version.__version__
        except Exception:
            return "Không xác định"

    def check_ytdlp_latest_version(self) -> tuple[bool, str]:
        """
        Kiểm tra phiên bản yt-dlp mới nhất từ máy chủ PyPI.
        Trả về (has_update, latest_version_string).
        """
        try:
            resp = requests.get(YTDLP_PYPI_URL, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                latest_ver = data.get("info", {}).get("version", "")
                current_ver = self.get_ytdlp_version()
                if latest_ver and current_ver:
                    has_update = (latest_ver > current_ver)
                    return has_update, latest_ver
            return False, "Không thể kiểm tra"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"

    def download_and_install_ffmpeg(self, progress_callback=None, status_callback=None) -> tuple[bool, str]:
        """
        Tự động tải về và giải nén FFmpeg cho Windows vào thư mục bin/.
        progress_callback: hàm nhận số thực (0.0 -> 1.0)
        status_callback: hàm nhận chuỗi thông báo trạng thái
        """
        urls = [FFMPEG_URL_YTDLP, FFMPEG_URL_GYAN]
        temp_zip = None

        for url in urls:
            try:
                if status_callback:
                    status_callback(f"Đang kết nối máy chủ tải FFmpeg ({url.split('/')[2]})...")

                resp = requests.get(url, stream=True, timeout=20)
                if resp.status_code != 200:
                    continue

                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                temp_zip = temp_file.name

                if status_callback:
                    status_callback("Đang tải tệp nén FFmpeg (khoảng 30-40 MB)...")

                with open(temp_zip, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and progress_callback:
                                frac = downloaded / total_size
                                progress_callback(frac)

                if status_callback:
                    status_callback("Đang giải nén các tệp thực thi ffmpeg.exe & ffprobe.exe...")

                # Giải nén tìm ffmpeg.exe và ffprobe.exe
                found_ffmpeg = False
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        filename = os.path.basename(file_info.filename).lower()
                        if filename in ["ffmpeg.exe", "ffprobe.exe"]:
                            # Giải nén trực tiếp vào thư mục bin/
                            target_path = self.bin_dir / filename
                            with zip_ref.open(file_info) as source, open(target_path, "wb") as target:
                                shutil.copyfileobj(source, target)
                            found_ffmpeg = True

                # Xóa tệp tạm
                try:
                    os.unlink(temp_zip)
                except Exception:
                    pass

                if found_ffmpeg and self.ffmpeg_exe.exists():
                    if progress_callback:
                        progress_callback(1.0)
                    if status_callback:
                        status_callback("✅ Cài đặt FFmpeg hoàn tất thành công!")
                    return True, "Cài đặt FFmpeg thành công!"
                else:
                    continue

            except Exception as e:
                if temp_zip and os.path.exists(temp_zip):
                    try:
                        os.unlink(temp_zip)
                    except Exception:
                        pass
                continue

        return False, "Không thể tải FFmpeg từ các máy chủ nguồn. Vui lòng kiểm tra kết nối mạng."

    def update_ytdlp(self, status_callback=None) -> tuple[bool, str]:
        """Cập nhật thư viện yt-dlp lên phiên bản mới nhất."""
        try:
            if status_callback:
                status_callback("Đang cập nhật yt-dlp qua pip...")

            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                timeout=60
            )

            if res.returncode == 0:
                if status_callback:
                    status_callback("✅ Đã cập nhật yt-dlp thành công!")
                return True, "Cập nhật yt-dlp thành công!"
            else:
                err_msg = res.stderr or res.stdout
                return False, f"Lỗi cập nhật: {err_msg[:200]}"
        except Exception as e:
            return False, f"Lỗi khi cập nhật yt-dlp: {str(e)}"
