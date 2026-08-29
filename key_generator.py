"""
Công Cụ Tạo License Key Bản Quyền (ToolDL Key Generator)
Tương thích 100% với Android (Termux, Pydroid 3, QPython), Windows, macOS và Linux.
Hoạt động hoàn toàn độc lập, không yêu cầu cài thêm bất kỳ thư viện ngoài nào.
"""

import sys
import os
import json
import time
import hmac
import hashlib
import base64
import argparse
from pathlib import Path

# Đảm bảo UTF-8 cho console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Khóa bí mật nội bộ đồng bộ với license_manager.py
SECRET_SALT = b"ToolDL_Pro_2026_Secure_License_Master_Key_Secret!#@987"

class StandaloneLicenseGenerator:
    """Bộ tạo License Key độc lập không phụ thuộc thư mục dự án."""

    @staticmethod
    def _create_signature(payload_str: str) -> str:
        h = hmac.new(SECRET_SALT, payload_str.encode('utf-8'), hashlib.sha256)
        return h.hexdigest()[:16].upper()

    @classmethod
    def generate_license_key(cls, machine_id: str = "ALL", days_valid: int = 0) -> str:
        """
        Tạo License Key hợp lệ.
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
        return f"{payload_b64}.{sig}"

def copy_to_clipboard_safe(text: str):
    """Sao chép an toàn vào khay nhớ tạm mà không làm sập ứng dụng trên Android."""
    # 1. Thử Termux API trên Android
    if shutil_which("termux-clipboard-set"):
        try:
            import subprocess
            p = subprocess.Popen(["termux-clipboard-set"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode('utf-8'))
            print(" 📋 Đã tự động sao chép Key vào Clipboard Android!")
            return
        except Exception:
            pass

    # 2. Thử Tkinter trên Windows / Desktop
    if sys.platform == "win32":
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            print(" 📋 Đã tự động sao chép Key vào Clipboard!")
        except Exception:
            pass

def shutil_which(cmd: str) -> bool:
    try:
        import shutil
        return bool(shutil.which(cmd))
    except Exception:
        return False

def interactive_menu():
    """Vòng lặp menu dòng lệnh tương tác trên Android và máy tính."""
    while True:
        print("\n" + "=" * 58)
        print("   🔑 TRÌNH TẠO MÃ KÍCH HOẠT BẢN QUYỀN TOOLDL PRO")
        print("   📱 Hỗ trợ: Android, Windows, macOS, Linux")
        print("=" * 58)
        
        # 1. Machine ID
        print("\n1. Đối tượng áp dụng:")
        print("   [1] Dùng cho mọi máy tính (Universal Key)")
        print("   [2] Khóa theo Machine ID của khách (Locked Key)")
        print("   [0] Thoát")
        choice_m = input("   👉 Lựa chọn [1/2/0] (mặc định 1): ").strip()
        
        if choice_m == "0":
            print("👋 Tạm biệt!")
            break

        if choice_m == "2":
            machine_id = input("   👉 Nhập Machine ID của khách (VD: TDL-A1B2-C3D4-E5F6): ").strip()
            if not machine_id:
                print("   ⚠️ Không nhập Machine ID, chuyển sang chế độ ALL.")
                machine_id = "ALL"
        else:
            machine_id = "ALL"

        # 2. Thời hạn
        print("\n2. Thời hạn sử dụng:")
        print("   [1] Vĩnh viễn (Lifetime)")
        print("   [2] 7 ngày (Dùng thử)")
        print("   [3] 30 ngày (1 tháng)")
        print("   [4] 90 ngày (3 tháng)")
        print("   [5] 365 ngày (1 năm)")
        print("   [6] Tùy chỉnh số ngày")
        choice_d = input("   👉 Lựa chọn [1-6] (mặc định 1): ").strip()

        days_map = {"1": 0, "2": 7, "3": 30, "4": 90, "5": 365}
        if choice_d in days_map:
            days = days_map[choice_d]
        elif choice_d == "6":
            try:
                days = int(input("   👉 Nhập số ngày hợp lệ: ").strip())
            except ValueError:
                days = 30
        else:
            days = 0

        # Tạo Key
        key = StandaloneLicenseGenerator.generate_license_key(machine_id, days)
        
        print("\n" + "=" * 58)
        print(" ✅ ĐÃ TẠO KEY THÀNH CÔNG:")
        print("-" * 58)
        print(f" 🔑 KEY        : {key}")
        print("-" * 58)
        print(f" 📌 Áp dụng    : {machine_id}")
        print(f" ⏳ Hạn sử dụng: {'Vĩnh viễn (Lifetime)' if days == 0 else f'{days} ngày'}")
        print(f" ⭐ Bản quyền  : Gói Đầy Đủ (Full Pro)")
        print("=" * 58)

        copy_to_clipboard_safe(key)

        print("\n" + "-" * 58)
        ans = input("👉 Nhấn Enter để tiếp tục tạo key khác (hoặc gõ 'q' để thoát): ").strip().lower()
        if ans == 'q':
            print("👋 Tạm biệt!")
            break

def launch_gui():
    """Giao diện đồ họa trực quan (GUI) dành cho Windows Desktop."""
    import customtkinter as ctk
    import tkinter.messagebox as msgbox

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("ToolDL Pro - Key Generator")
    root.geometry("540x440")
    root.resizable(False, False)

    title_lbl = ctk.CTkLabel(root, text="🔑 ToolDL Pro Key Generator", font=("Segoe UI", 20, "bold"), text_color=("#3B82F6", "#60A5FA"))
    title_lbl.pack(pady=(20, 10))

    frame = ctk.CTkFrame(root, corner_radius=10)
    frame.pack(padx=20, pady=10, fill="both", expand=True)

    # Machine ID
    m_lbl = ctk.CTkLabel(frame, text="Mã Machine ID (nhập 'ALL' cho mọi máy):", font=("Segoe UI", 12, "bold"))
    m_lbl.pack(anchor="w", padx=20, pady=(15, 2))
    m_entry = ctk.CTkEntry(frame, placeholder_text="ALL hoặc TDL-XXXX-XXXX-XXXX", font=("Consolas", 12), height=34)
    m_entry.insert(0, "ALL")
    m_entry.pack(fill="x", padx=20, pady=(0, 12))

    # Duration
    d_lbl = ctk.CTkLabel(frame, text="Thời hạn bản quyền:", font=("Segoe UI", 12, "bold"))
    d_lbl.pack(anchor="w", padx=20, pady=(5, 2))
    d_combo = ctk.CTkComboBox(frame, values=["Vĩnh viễn (Lifetime)", "7 ngày (Trial)", "30 ngày (1 tháng)", "90 ngày (3 tháng)", "365 ngày (1 năm)"], font=("Segoe UI", 12), height=34)
    d_combo.set("Vĩnh viễn (Lifetime)")
    d_combo.pack(fill="x", padx=20, pady=(0, 15))

    # Result Key Entry
    res_entry = ctk.CTkEntry(frame, placeholder_text="Key sẽ xuất hiện ở đây sau khi bấm tạo...", font=("Consolas", 12, "bold"), height=36)
    res_entry.pack(fill="x", padx=20, pady=(5, 12))

    def on_generate():
        m_val = m_entry.get().strip() or "ALL"
        dur_str = d_combo.get()
        days_map = {
            "Vĩnh viễn (Lifetime)": 0,
            "7 ngày (Trial)": 7,
            "30 ngày (1 tháng)": 30,
            "90 ngày (3 tháng)": 90,
            "365 ngày (1 năm)": 365
        }
        days = days_map.get(dur_str, 0)

        key = StandaloneLicenseGenerator.generate_license_key(m_val, days)
        res_entry.delete(0, "end")
        res_entry.insert(0, key)
        root.clipboard_clear()
        root.clipboard_append(key)
        msgbox.showinfo("Thành công", f"Đã tạo Key và tự động sao chép vào Clipboard:\n\n{key}")

    gen_btn = ctk.CTkButton(frame, text="✨ TẠO LICENSE KEY NGAY", command=on_generate, height=42, font=("Segoe UI", 13, "bold"), fg_color="#059669", hover_color="#047857", corner_radius=8)
    gen_btn.pack(fill="x", padx=20, pady=(5, 10))

    root.mainloop()

def main():
    try:
        parser = argparse.ArgumentParser(description="ToolDL License Key Generator")
        parser.add_argument("-m", "--machine", default="", help="Mã Machine ID của máy khách (hoặc 'ALL' cho mọi máy)")
        parser.add_argument("-d", "--days", type=int, default=0, help="Số ngày sử dụng (0 = Vĩnh viễn / Lifetime)")
        parser.add_argument("-c", "--count", type=int, default=1, help="Số lượng key cần tạo")
        parser.add_argument("--gui", action="store_true", help="Bắt buộc mở giao diện đồ họa Tkinter")

        args = parser.parse_args()

        # 1. Nếu truyền tham số -m -> In key ra ngay
        if args.machine:
            print("\n" + "=" * 50)
            print("      CÔNG CỤ TẠO LICENSE KEY - TOOLDL")
            print("=" * 50)
            print(f"Machine ID : {args.machine}")
            print(f"Thời hạn   : {'Vĩnh viễn (Lifetime)' if args.days == 0 else f'{args.days} ngày'}")
            print(f"Số lượng   : {args.count}")
            print("-" * 50)

            for i in range(args.count):
                key = StandaloneLicenseGenerator.generate_license_key(
                    machine_id=args.machine,
                    days_valid=args.days
                )
                print(f"Key [{i+1}]: {key}")
            print("=" * 50 + "\n")
            return

        # 2. Nếu ở trên Windows và có CustomTkinter (hoặc người dùng chọn --gui) -> Mở GUI
        if (sys.platform == "win32" or args.gui) and not os.getenv("ANDROID_ROOT"):
            try:
                import customtkinter
                launch_gui()
                return
            except Exception:
                pass

        # 3. Mặc định trên Android / Linux / macOS / Server: Chạy menu tương tác CLI
        interactive_menu()

    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        try:
            input("\n👉 Nhấn Enter để thoát...")
        except Exception:
            pass

if __name__ == "__main__":
    main()
