"""
Module Quản lý Bản quyền và Xác thực Thiết bị (License Manager).
Hỗ trợ tạo Machine ID phần cứng, xác thực License Key bằng mật mã HMAC-SHA256,
lưu trữ và kiểm tra thời hạn bản quyền tự động.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import base64
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Khóa bí mật nội bộ để ký và xác thực bản quyền (Private Master Salt)
SECRET_SALT = b"ToolDL_Pro_2026_Secure_License_Master_Key_Secret!#@987"

class LicenseManager:
    """Quản lý thông tin bản quyền và thiết bị."""
    
    def __init__(self, app_dir=None):
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            # Nếu đang chạy dạng frozen executable hoặc script
            if getattr(sys, 'frozen', False):
                self.app_dir = Path(sys.executable).parent
            else:
                self.app_dir = Path(__file__).resolve().parent.parent

        # Thư mục lưu dữ liệu bản quyền (ưu tiên portable tại thư mục app, fallback APPDATA)
        self.license_file = self.app_dir / "license.dat"
        if not self.is_writable(self.app_dir):
            app_data = Path(os.getenv('APPDATA', os.path.expanduser("~"))) / "ToolDL"
            app_data.mkdir(parents=True, exist_ok=True)
            self.license_file = app_data / "license.dat"

        self._cached_machine_id = None
        self._license_info = None

    @staticmethod
    def is_writable(path: Path) -> bool:
        """Kiểm tra quyền ghi vào thư mục."""
        try:
            test_file = path / ".test_write"
            test_file.touch(exist_ok=True)
            test_file.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def get_machine_id(self) -> str:
        """Tạo Machine ID duy nhất cố định dựa trên phần cứng máy tính."""
        if self._cached_machine_id:
            return self._cached_machine_id

        raw_ids = []
        # 1. Windows MachineGuid từ Registry
        if platform.system() == "Windows":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                    guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                    if guid:
                        raw_ids.append(f"guid:{guid.strip()}")
            except Exception:
                pass

            # 2. Motherboard UUID qua PowerShell CIM
            try:
                cmd = 'powershell -NoProfile -Command "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"'
                out = subprocess.check_output(cmd, shell=True, text=True, timeout=3).strip()
                if out and out != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
                    raw_ids.append(f"mb:{out}")
            except Exception:
                pass

            # 3. CPU ID
            try:
                cmd = 'powershell -NoProfile -Command "(Get-CimInstance -Class Win32_Processor).ProcessorId"'
                out = subprocess.check_output(cmd, shell=True, text=True, timeout=3).strip()
                if out:
                    raw_ids.append(f"cpu:{out}")
            except Exception:
                pass

        # Fallback node + platform info
        if not raw_ids:
            import uuid
            node = uuid.getnode()
            raw_ids.append(f"node:{node}-{platform.node()}-{platform.processor()}")

        combined = "|".join(raw_ids)
        digest = hashlib.sha256(combined.encode('utf-8')).hexdigest().upper()
        # Định dạng gọn: TDL-XXXX-XXXX-XXXX
        short_id = f"TDL-{digest[:4]}-{digest[4:8]}-{digest[8:12]}"
        self._cached_machine_id = short_id
        return short_id

    @staticmethod
    def _create_signature(payload_str: str) -> str:
        """Tạo chữ ký HMAC-SHA256 cho chuỗi dữ liệu."""
        h = hmac.new(SECRET_SALT, payload_str.encode('utf-8'), hashlib.sha256)
        return h.hexdigest()[:16].upper()

    @classmethod
    def generate_license_key(cls, machine_id: str = "ALL", days_valid: int = 0) -> str:
        """
        Tạo License Key hợp lệ (Gói Bản Quyền Chính Thức Đầy Đủ).
        - machine_id: "ALL" (dùng cho mọi máy) hoặc Mã Machine ID cụ thể (ví dụ: TDL-A1B2-C3D4-E5F6).
        - days_valid: 0 là vĩnh viễn (Lifetime), >0 là số ngày sử dụng.
        """
        now = int(time.time())
        exp_time = (now + days_valid * 86400) if days_valid > 0 else 0
        
        payload = {
            "m": machine_id.strip().upper(),
            "e": exp_time,
            "t": "FULL",
            "i": now
        }
        
        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
        
        sig = cls._create_signature(payload_b64)
        raw_key = f"{payload_b64}.{sig}"
        return raw_key

    def verify_key(self, key_str: str) -> tuple[bool, str, dict | None]:
        """
        Xác thực License Key.
        Trả về (is_valid, message, details).
        """
        if not key_str or not isinstance(key_str, str):
            return False, "Vui lòng nhập License Key hợp lệ.", None

        key_str = key_str.strip()
        if "." not in key_str:
            return False, "Định dạng License Key không đúng.", None

        try:
            parts = key_str.split(".")
            if len(parts) != 2:
                return False, "Cấu trúc License Key không hợp lệ.", None

            payload_b64, sig = parts[0], parts[1]
            
            # Kiểm tra chữ ký
            expected_sig = self._create_signature(payload_b64)
            if not hmac.compare_digest(sig, expected_sig):
                return False, "License Key không hợp lệ hoặc đã bị chỉnh sửa.", None

            # Giải mã payload
            missing_padding = len(payload_b64) % 4
            if missing_padding:
                payload_b64 += '=' * (4 - missing_padding)
                
            payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
            payload = json.loads(payload_json)

            req_machine = payload.get("m", "ALL")
            exp_time = payload.get("e", 0)
            issue_time = payload.get("i", 0)

            # Kiểm tra Machine ID
            current_machine = self.get_machine_id()
            if req_machine != "ALL" and req_machine != current_machine:
                return False, f"Key này chỉ dành cho máy có mã: {req_machine}\nMáy hiện tại: {current_machine}", None

            # Kiểm tra thời hạn
            now = int(time.time())
            if exp_time != 0 and now > exp_time:
                exp_dt = datetime.fromtimestamp(exp_time).strftime("%d/%m/%Y %H:%M")
                return False, f"License Key đã hết hạn vào ngày {exp_dt}.", None

            # Định dạng hạn sử dụng
            if exp_time == 0:
                expiry_str = "Vĩnh viễn (Lifetime)"
            else:
                exp_dt = datetime.fromtimestamp(exp_time).strftime("%d/%m/%Y %H:%M")
                days_left = max(0, int((exp_time - now) / 86400))
                expiry_str = f"{exp_dt} (Còn {days_left} ngày)"

            details = {
                "key": key_str,
                "machine_id": req_machine,
                "type": "Chính Thức (Full Tính Năng)",
                "expires_at": exp_time,
                "expires_str": expiry_str,
                "issued_at": issue_time
            }
            return True, "Kích hoạt bản quyền thành công!", details

        except Exception as e:
            return False, f"Lỗi xác thực Key: {str(e)}", None

    def activate(self, key_str: str) -> tuple[bool, str]:
        """Kích hoạt và lưu Key vào tệp bản quyền."""
        valid, msg, details = self.verify_key(key_str)
        if not valid or not details:
            return False, msg

        try:
            enc_data = base64.b64encode(json.dumps(details).encode('utf-8')).decode('utf-8')
            with open(self.license_file, "w", encoding="utf-8") as f:
                f.write(enc_data)
            self._license_info = details
            return True, f"Kích hoạt bản quyền thành công! Hạn dùng: {details['expires_str']}"
        except Exception as e:
            return False, f"Không thể lưu thông tin kích hoạt: {str(e)}"

    def check_license(self) -> tuple[bool, str, dict | None]:
        """Kiểm tra trạng thái bản quyền hiện tại đã lưu."""
        if not self.license_file.exists():
            return False, "Chưa kích hoạt bản quyền.", None

        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return False, "Tệp bản quyền rỗng.", None

            data_json = base64.b64decode(content.encode('utf-8')).decode('utf-8')
            saved_details = json.loads(data_json)
            key_str = saved_details.get("key", "")

            # Xác thực lại tính hợp lệ của key đã lưu
            valid, msg, details = self.verify_key(key_str)
            if valid:
                self._license_info = details
                return True, "Bản quyền hợp lệ.", details
            else:
                return False, msg, None

        except Exception as e:
            return False, f"Lỗi đọc bản quyền: {str(e)}", None

    def deactivate(self) -> bool:
        """Xóa bản quyền đã kích hoạt."""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            self._license_info = None
            return True
        except Exception:
            return False

    @property
    def license_info(self) -> dict | None:
        return self._license_info
