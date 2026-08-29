"""
Script Tự Động Mã Hóa và Đóng Gói Ứng Dụng Bằng Nuitka (C++ Native Compilation).
Cung cấp các chế độ:
1. [PYD] Mã hóa các module nhạy cảm (bản quyền, bóc tách link, tải đa luồng) thành file nhị phân C native (.pyd).
2. [EXE] Đóng gói toàn bộ phần mềm thành ứng dụng Portable / Standalone .exe siêu bảo mật.
3. [RESTORE] Khôi phục lại các file .py gốc từ bản sao lưu .bak.
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path

# Đảm bảo UTF-8 cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = Path(__file__).resolve().parent

# Danh sách các module quan trọng cần mã hóa sang .pyd
CRITICAL_MODULES = [
    "tool_gui/license_manager.py",
    "tool_gui/url_detector.py",
    "tool_gui/downloader.py",
    "tool_gui/config.py",
    "tool_gui/updater.py",
]

def check_nuitka_installed():
    """Kiểm tra và cài đặt Nuitka nếu chưa có."""
    try:
        import nuitka
        print("✅ Đã tìm thấy Nuitka trên hệ thống.")
        return True
    except ImportError:
        print("⚠️ Chưa tìm thấy Nuitka. Đang tự động cài đặt Nuitka...")
        cmd = [sys.executable, "-m", "pip", "install", "nuitka", "ordered-set", "zstandard"]
        ret = subprocess.run(cmd)
        if ret.returncode == 0:
            print("✅ Cài đặt Nuitka thành công!")
            return True
        else:
            print("❌ Cài đặt Nuitka thất bại. Vui lòng chạy lệnh: pip install nuitka")
            return False

def compile_modules_to_pyd(backup_py=True):
    """Biên dịch các file .py quan trọng thành .pyd (C-Extension) và xóa/ẩn mã nguồn .py."""
    print("\n" + "=" * 65)
    print(" 🛡️  CHẾ ĐỘ: MÃ HÓA CÁC FILE QUAN TRỌNG SANG .PYD NATIVE C")
    print("=" * 65)

    if not check_nuitka_installed():
        return False

    success_count = 0
    for mod_rel in CRITICAL_MODULES:
        py_path = PROJECT_DIR / mod_rel
        if not py_path.exists():
            print(f"⚠️ Bỏ qua {mod_rel} (Không tìm thấy tệp)")
            continue

        print(f"\n⚙️ Đang biên dịch: {mod_rel} ➡️ .pyd ...")
        
        # Thư mục chứa file
        target_dir = py_path.parent
        
        cmd = [
            sys.executable, "-m", "nuitka",
            "--module",
            "--remove-output",
            "--no-pyi-file",
            f"--output-dir={target_dir}",
            str(py_path)
        ]

        ret = subprocess.run(cmd, cwd=str(PROJECT_DIR))
        if ret.returncode == 0:
            print(f"✅ Biên dịch thành công: {mod_rel}")
            success_count += 1

            if backup_py:
                bak_path = py_path.with_suffix(".py.bak")
                if not bak_path.exists():
                    shutil.copy2(py_path, bak_path)
                    print(f"   📁 Đã sao lưu file gốc sang: {bak_path.name}")
                # Đổi tên hoặc xóa file .py gốc để Python tự động load file .pyd
                py_path.unlink()
                print(f"   🔒 Đã xóa file .py gốc (Hệ thống sẽ chạy trực tiếp từ .pyd)")
        else:
            print(f"❌ Biên dịch thất bại cho: {mod_rel}")

    print("\n" + "=" * 65)
    print(f" 🎉 HOÀN TẤT: Đã mã hóa {success_count}/{len(CRITICAL_MODULES)} module quan trọng!")
    print("=" * 65)
    return True

def restore_backup_py():
    """Khôi phục lại các file .py gốc từ .bak và xóa các file .pyd."""
    print("\n" + "=" * 65)
    print(" 🔄 KHÔI PHỤC LẠI MÃ NGUỒN GỐC (.PY) TỪ BẢN SAO LƯU (.BAK)")
    print("=" * 65)

    count = 0
    for mod_rel in CRITICAL_MODULES:
        py_path = PROJECT_DIR / mod_rel
        bak_path = py_path.with_suffix(".py.bak")
        
        if bak_path.exists():
            shutil.copy2(bak_path, py_path)
            bak_path.unlink()
            print(f"✅ Đã khôi phục: {py_path.name}")
            count += 1

        # Xóa các file .pyd tương ứng trong thư mục
        target_dir = py_path.parent
        stem = py_path.stem
        for pyd_file in target_dir.glob(f"{stem}*.pyd"):
            try:
                pyd_file.unlink()
                print(f"   🗑️ Đã xóa file nhị phân: {pyd_file.name}")
            except Exception:
                pass

    print(f"\n🎉 Đã khôi phục hoàn tất {count} file mã nguồn.")

def build_standalone_exe():
    """Đóng gói toàn bộ ứng dụng thành 1 thư mục Standalone / Portable .exe siêu bảo mật."""
    print("\n" + "=" * 65)
    print(" 🚀 CHẾ ĐỘ: ĐÓNG GÓI TOÀN BỘ PHẦN MỀM THÀNH .EXE NATIVE C++")
    print("=" * 65)

    if not check_nuitka_installed():
        return False

    out_dir = PROJECT_DIR / "dist" / "ToolDL_Nuitka"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--windows-disable-console",
        "--enable-plugin=tk-inter",
        "--include-package=customtkinter",
        "--include-package=yt_dlp",
        "--include-package=PIL",
        "--include-package=webview",
        "--include-data-file=public.key=public.key",
        "--include-data-file=config.json=config.json",
        f"--output-dir={out_dir}",
        "--output-filename=ToolDL.exe",
        "run_gui.py"
    ]

    print("⚙️ Đang tiến hành biên dịch toàn bộ mã nguồn bằng Nuitka (Quá trình này có thể mất vài phút)...")
    print("Lệnh chạy:", " ".join(cmd))
    
    ret = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    if ret.returncode == 0:
        print("\n" + "=" * 65)
        print(f" 🎉 ĐÓNG GÓI THÀNH CÔNG!")
        print(f" 📂 Thư mục chứa ứng dụng: {out_dir}")
        print("=" * 65)
        return True
    else:
        print("\n❌ Quá trình đóng gói gặp lỗi.")
        return False

def show_menu():
    """Hiển thị menu tương tác."""
    while True:
        print("\n" + "=" * 65)
        print("   🛡️  TOOL MÃ HÓA & ĐÓNG GÓI NUITKA CHO TOOLDL PRO")
        print("=" * 65)
        print(" [1] 🔒 Mã hóa các file quan trọng sang .pyd (Bảo vệ bản quyền & lõi tải)")
        print(" [2] 🔄 Khôi phục lại các file .py gốc từ bản sao lưu (.bak)")
        print(" [3] 🚀 Đóng gói toàn bộ ứng dụng thành 1 bản .exe Standalone Native C++")
        print(" [0] 🚪 Thoát")
        print("=" * 65)

        choice = input("👉 Nhập lựa chọn của bạn (0-3): ").strip()
        if choice == "1":
            compile_modules_to_pyd(backup_py=True)
        elif choice == "2":
            restore_backup_py()
        elif choice == "3":
            build_standalone_exe()
        elif choice == "0":
            print("👋 Tạm biệt!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng chọn lại.")

def main():
    parser = argparse.ArgumentParser(description="ToolDL Nuitka Obfuscator & Builder")
    parser.add_argument("--pyd", action="store_true", help="Mã hóa các file quan trọng sang .pyd")
    parser.add_argument("--restore", action="store_true", help="Khôi phục file .py từ .bak")
    parser.add_argument("--exe", action="store_true", help="Đóng gói toàn bộ ứng dụng thành Standalone .exe")
    args = parser.parse_args()

    if args.pyd:
        compile_modules_to_pyd(backup_py=True)
    elif args.restore:
        restore_backup_py()
    elif args.exe:
        build_standalone_exe()
    else:
        show_menu()

if __name__ == "__main__":
    main()
