"""
Module Quản lý Cấu hình Ứng dụng (Config Manager).
Lưu trữ và đồng bộ cài đặt người dùng vào config.json.
"""

import os
import sys
import json
from pathlib import Path

class ConfigManager:
    """Quản lý cài đặt cấu hình người dùng."""

    def __init__(self, app_dir=None):
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            if getattr(sys, 'frozen', False):
                self.app_dir = Path(sys.executable).parent
            else:
                self.app_dir = Path(__file__).resolve().parent.parent

        self.config_file = self.app_dir / "config.json"
        
        # Thư mục lưu video mặc định: ~/Downloads/ToolDL_Videos
        default_dl_dir = str(Path.home() / "Downloads" / "ToolDL_Videos")

        self.defaults = {
            "download_dir": default_dl_dir,
            "theme": "dark",  # dark, light, system
            "auto_detect_clipboard": True,
            "auto_check_updates": True,
            "default_quality": "🌟 Tốt nhất có thể (Chất lượng gốc cao nhất)",
            "default_format": "MP4 (Tương thích cao nhất)",
            "default_audio_format": "MP3 - 320 kbps (Cực cao - Studio Master)",
            "embed_subtitles": True,
            "sub_lang": "vi,en",
            "browser_cookie": "none",  # none, chrome, edge, firefox, brave, opera, file
            "cookie_file_path": "",
            "max_concurrent_downloads": 3
        }

        self.config = self.load()

    def load(self) -> dict:
        """Đọc file config.json hoặc tạo mới với giá trị mặc định."""
        cfg = dict(self.defaults)
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cfg.update(saved)
            except Exception as e:
                print(f"[Cấu hình] Lỗi khi đọc file config.json: {e}")
        else:
            self.save(cfg)
        return cfg

    def save(self, cfg_data: dict = None) -> bool:
        """Lưu cài đặt vào file config.json."""
        if cfg_data is not None:
            self.config = cfg_data
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Cấu hình] Lỗi khi ghi file config.json: {e}")
            return False

    def get(self, key: str, default=None):
        """Lấy giá trị cài đặt theo khóa."""
        return self.config.get(key, default)

    def set(self, key: str, value) -> bool:
        """Cập nhật giá trị và lưu lại."""
        self.config[key] = value
        return self.save()
