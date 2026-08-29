"""
Công cụ Tạo License Key Bản Quyền (ToolDL Key Generator)
Dành riêng cho Quản trị viên / Nhà phát triển để cấp mã kích hoạt (Gói Bản Quyền Đầy Đủ Duy Nhất).
"""

import sys
import argparse
from pathlib import Path

# Đảm bảo import được tool_gui
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tool_gui.license_manager import LicenseManager

def cli_generator():
    parser = argparse.ArgumentParser(description="ToolDL License Key Generator")
    parser.add_argument("-m", "--machine", default="ALL", help="Mã Machine ID của máy khách (hoặc 'ALL' cho mọi máy)")
    parser.add_argument("-d", "--days", type=int, default=0, help="Số ngày sử dụng (0 = Vĩnh viễn / Lifetime)")
    parser.add_argument("-c", "--count", type=int, default=1, help="Số lượng key cần tạo")
    parser.add_argument("--gui", action="store_true", help="Mở giao diện đồ họa tạo Key")

    args = parser.parse_args()

    if args.gui:
        launch_gui()
        return

    # Nếu không truyền tham số nào, mở menu tương tác
    if len(sys.argv) == 1:
        interactive_menu()
        return

    print("\n" + "=" * 50)
    print("      CÔNG CỤ TẠO LICENSE KEY - TOOLDL")
    print("=" * 50)
    print(f"Machine ID : {args.machine}")
    print(f"Thời hạn   : {'Vĩnh viễn (Lifetime)' if args.days == 0 else f'{args.days} ngày'}")
    print(f"Bản quyền  : Đầy đủ (Full Tính Năng)")
    print(f"Số lượng   : {args.count}")
    print("-" * 50)

    for i in range(args.count):
        key = LicenseManager.generate_license_key(
            machine_id=args.machine,
            days_valid=args.days
        )
        print(f"Key [{i+1}]: {key}")
    print("=" * 50 + "\n")

def interactive_menu():
    print("\n" + "=" * 50)
    print("       TRÌNH TẠO MÃ KÍCH HOẠT TOOLDL")
    print("=" * 50)
    
    # 1. Machine ID
    print("\n1. Đối tượng áp dụng:")
    print("   [1] Dùng cho mọi máy tính (Universal Key)")
    print("   [2] Khóa theo Machine ID của khách (Locked Key)")
    choice_m = input("   👉 Lựa chọn [1/2] (mặc định 1): ").strip()
    
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

    # Tạo Key (Gói duy nhất)
    key = LicenseManager.generate_license_key(machine_id, days)
    
    print("\n" + "=" * 50)
    print("✅ ĐÃ TẠO KEY THÀNH CÔNG:")
    print("-" * 50)
    print(f"🔑 LICENSE KEY : {key}")
    print("-" * 50)
    print(f"📌 Áp dụng     : {machine_id}")
    print(f"⏳ Hạn sử dụng : {'Vĩnh viễn' if days == 0 else f'{days} ngày'}")
    print(f"⭐ Bản quyền   : Đầy đủ (Full Tính Năng)")
    print("=" * 50 + "\n")

    # Tự động copy vào clipboard nếu có tkinter
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(key)
        r.update()
        r.destroy()
        print("📋 Đã tự động copy Key vào Clipboard (Khay nhớ tạm)!")
    except Exception:
        pass

def launch_gui():
    import customtkinter as ctk
    import tkinter.messagebox as msgbox

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("ToolDL - Key Generator")
    root.geometry("520x400")
    root.resizable(False, False)

    title_lbl = ctk.CTkLabel(root, text="🔑 ToolDL Key Generator", font=("Segoe UI", 20, "bold"))
    title_lbl.pack(pady=(20, 10))

    frame = ctk.CTkFrame(root)
    frame.pack(padx=20, pady=10, fill="both", expand=True)

    # Machine ID
    m_lbl = ctk.CTkLabel(frame, text="Mã Machine ID (nhập 'ALL' cho mọi máy):", font=("Segoe UI", 12))
    m_lbl.pack(anchor="w", padx=20, pady=(15, 2))
    m_entry = ctk.CTkEntry(frame, placeholder_text="ALL hoặc TDL-XXXX-XXXX-XXXX")
    m_entry.insert(0, "ALL")
    m_entry.pack(fill="x", padx=20, pady=(0, 12))

    # Duration
    d_lbl = ctk.CTkLabel(frame, text="Thời hạn bản quyền:", font=("Segoe UI", 12))
    d_lbl.pack(anchor="w", padx=20, pady=(5, 2))
    d_combo = ctk.CTkComboBox(frame, values=["Vĩnh viễn (Lifetime)", "7 ngày (Trial)", "30 ngày (1 tháng)", "90 ngày (3 tháng)", "365 ngày (1 năm)"])
    d_combo.set("Vĩnh viễn (Lifetime)")
    d_combo.pack(fill="x", padx=20, pady=(0, 15))

    # Result Key Entry
    res_entry = ctk.CTkEntry(frame, placeholder_text="Key sẽ xuất hiện ở đây...", font=("Segoe UI", 11, "bold"))
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

        key = LicenseManager.generate_license_key(m_val, days)
        res_entry.delete(0, "end")
        res_entry.insert(0, key)
        root.clipboard_clear()
        root.clipboard_append(key)
        msgbox.showinfo("Thành công", f"Đã tạo Key và copy vào Clipboard:\n\n{key}")

    gen_btn = ctk.CTkButton(frame, text="✨ TẠO LICENSE KEY", command=on_generate, height=38, font=("Segoe UI", 13, "bold"), fg_color="#2563EB", hover_color="#1D4ED8")
    gen_btn.pack(pady=(5, 10))

    root.mainloop()

if __name__ == "__main__":
    cli_generator()
