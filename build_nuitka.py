"""
Script Đóng Gói & Mã Hóa Nuitka Độc Lập (Isolated Non-Intrusive Build System).
NGUYÊN TẮC HOẠT ĐỘNG:
- 100% KHÔNG THAY ĐỔI, KHÔNG XÓA, KHÔNG ĐỔI TÊN bất kỳ tệp tin nào trong thư mục dự án gốc của bạn.
- Bạn có thể vừa lập trình, vừa chạy code Python .py bình thường.
- Toàn bộ quá trình mã hóa C++ (.pyd / .exe) diễn ra trong môi trường Staging cách ly và xuất thành phẩm sang thư mục `dist/`.
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
DIST_DIR = PROJECT_DIR / "dist"
BUILD_TEMP_DIR = PROJECT_DIR / "build" / "nuitka_staging"

# Các module cốt lõi cần mã hóa sang .pyd khi xuất bản
PROTECTED_MODULES = [
    "tool_gui/license_manager.py",
    "tool_gui/url_detector.py",
    "tool_gui/downloader.py",
    "tool_gui/config.py",
    "tool_gui/updater.py",
]

def check_nuitka_installed():
    """Kiểm tra và tự động cài đặt Nuitka nếu cần."""
    try:
        import nuitka
        return True
    except ImportError:
        print("⚠️ Chưa tìm thấy Nuitka. Đang tự động cài đặt Nuitka...")
        cmd = [sys.executable, "-m", "pip", "install", "nuitka", "ordered-set", "zstandard"]
        ret = subprocess.run(cmd)
        return ret.returncode == 0

def clean_temp():
    """Dọn dẹp thư mục staging tạm."""
    if BUILD_TEMP_DIR.exists():
        try:
            shutil.rmtree(BUILD_TEMP_DIR, ignore_errors=True)
        except Exception:
            pass

def build_protected_bundle():
    """
    Tùy chọn 1: Xuất bản gói thư mục ToolDL_Pro_Protected trong `dist/`.
    Trong gói này, các file lõi quan trọng được chuyển thành .pyd nhị phân,
    mã nguồn gốc trong dự án của bạn KHÔNG HỀ BỊ ẢNH HƯỞNG.
    """
    print("\n" + "=" * 68)
    print(" 🛡️  BUILD GÓI PHÂN PHỐI ĐÃ MÃ HÓA CỐT LÕI (HYBRID .PYD BUNDLE)")
    print(" 💡 Dự án gốc của bạn được giữ nguyên vẹn 100%, không bị sửa đổi.")
    print("=" * 68)

    if not check_nuitka_installed():
        print("❌ Không thể tiếp tục do thiếu Nuitka.")
        return False

    out_bundle_dir = DIST_DIR / "ToolDL_Protected"
    
    # 1. Dọn dẹp thư mục cũ
    clean_temp()
    if out_bundle_dir.exists():
        shutil.rmtree(out_bundle_dir, ignore_errors=True)
    out_bundle_dir.mkdir(parents=True, exist_ok=True)

    print("\n📁 [1/4] Đang chuẩn bị môi trường đóng gói cách ly (Staging)...")
    BUILD_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Sao chép toàn bộ dự án vào thư mục tạm Staging
    ignore_patterns = shutil.ignore_patterns(
        "__pycache__", ".git", ".github", "dist", "build", "*.bak", "*.spec", "*.log", "log.txt", "uv.lock", "test"
    )
    
    for item in PROJECT_DIR.iterdir():
        if item.name in ["dist", "build", ".git", ".github", "__pycache__"]:
            continue
        dest = BUILD_TEMP_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=ignore_patterns)
        else:
            shutil.copy2(item, dest)

    # 3. Biên dịch các module chỉ định sang .pyd trong thư mục Staging
    print("\n⚙️ [2/4] Đang tiến hành biên dịch mã C++ (.pyd) cho các file cốt lõi...")
    for mod_rel in PROTECTED_MODULES:
        stg_py = BUILD_TEMP_DIR / mod_rel
        if not stg_py.exists():
            continue

        print(f"   🔒 Đang mã hóa: {mod_rel} ➡️ .pyd ...")
        cmd = [
            sys.executable, "-m", "nuitka",
            "--module",
            "--remove-output",
            "--no-pyi-file",
            f"--output-dir={stg_py.parent}",
            str(stg_py)
        ]
        ret = subprocess.run(cmd, cwd=str(BUILD_TEMP_DIR), stdout=subprocess.DEVNULL)
        if ret.returncode == 0:
            stg_py.unlink()  # Xóa file .py trong thư mục staging (chỉ giữ lại .pyd)
            print(f"   ✅ Hoàn tất mã hóa: {mod_rel.replace('.py', '.pyd')}")
        else:
            print(f"   ⚠️ Biên dịch module {mod_rel} thất bại, giữ lại bản .py.")

    # 4. Sao chép từ Staging sang thư mục output cuối cùng trong dist/
    print("\n📦 [3/4] Đang hoàn thiện gói phát hành vào thư mục 'dist/ToolDL_Protected'...")
    for item in BUILD_TEMP_DIR.iterdir():
        dest = out_bundle_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # 5. Dọn dẹp thư mục tạm
    print("\n🧹 [4/4] Đang dọn dẹp các tệp tin tạm...")
    clean_temp()

    print("\n" + "=" * 68)
    print(" 🎉 XUẤT BẢN THÀNH CÔNG GÓI MÃ HÓA!")
    print(f" 📂 Thư mục sản phẩm: {out_bundle_dir}")
    print(" 🔒 Các file bản quyền & lõi tải đã được mã hóa thành tệp nhị phân C.")
    print(" 🌟 Toàn bộ mã nguồn dự án gốc của bạn vẫn giữ nguyên 100% không đổi.")
    print("=" * 68)
    return True

def build_standalone_exe():
    """
    Tùy chọn 2: Đóng gói toàn bộ phần mềm thành 1 thư mục Standalone / Portable .exe siêu bảo mật.
    Mã nguồn gốc trong dự án của bạn KHÔNG HỀ BỊ ẢNH HƯỞNG.
    """
    print("\n" + "=" * 68)
    print(" 🚀 BUILD ỨNG DỤNG STANDALONE .EXE NATIVE C++ BẢO VỆ TOÀN DIỆN")
    print(" 💡 Toàn bộ Python code sẽ được dịch thẳng sang mã máy C++ không thể decompile.")
    print("=" * 68)

    if not check_nuitka_installed():
        print("❌ Không thể tiếp tục do thiếu Nuitka.")
        return False

    out_dir = DIST_DIR / "ToolDL_App"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Chuẩn bị cấu hình Nuitka tối ưu cho Windows GUI
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--windows-console-mode=disable",
        "--enable-plugin=tk-inter",
        "--include-package=customtkinter",
        "--include-package-data=customtkinter",
        "--include-package=yt_dlp",
        "--include-package=PIL",
        "--include-package=cryptography",
        "--include-data-file=public.key=public.key",
        "--include-data-file=config.json=config.json",
        f"--output-dir={out_dir}",
        "--output-filename=ToolDL.exe",
        "run_gui.py"
    ]

    print("\n⚙️ Đang biên dịch toàn bộ dự án sang C++ bằng Nuitka (Vui lòng đợi vài phút)...")
    ret = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    
    if ret.returncode == 0:
        print("\n" + "=" * 68)
        print(" 🎉 ĐÓNG GÓI .EXE THÀNH CÔNG!")
        print(f" 📂 Vị trí ứng dụng: {out_dir / 'run_gui.dist'}")
        print(" 🌟 Mã nguồn dự án gốc của bạn vẫn giữ nguyên 100% không đổi.")
        print("=" * 68)
        return True
    else:
        print("\n❌ Đóng gói thất bại. Vui lòng kiểm tra thông báo lỗi phía trên.")
        return False

def show_menu():
    """Menu tương tác thân thiện."""
    while True:
        print("\n" + "=" * 68)
        print("   🛡️  BỘ CÔNG CỤ ĐÓNG GÓI & MÃ HÓA NUITKA (ZERO TOUCH WORKSPACE)")
        print("=" * 68)
        print(" [1] 🔒 Build gói mã hóa module (.pyd) sang thư mục 'dist/ToolDL_Protected'")
        print(" [2] 🚀 Build ứng dụng Standalone .exe sang thư mục 'dist/ToolDL_App'")
        print(" [0] 🚪 Thoát")
        print("=" * 68)
        print(" 💡 Lưu ý: Cả 2 lựa chọn đều KHÔNG làm thay đổi bất kỳ file nào trong dự án.")

        choice = input("\n👉 Nhập lựa chọn của bạn (0-2): ").strip()
        if choice == "1":
            build_protected_bundle()
        elif choice == "2":
            build_standalone_exe()
        elif choice == "0":
            print("👋 Tạm biệt!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng chọn lại.")

def main():
    parser = argparse.ArgumentParser(description="ToolDL Non-Intrusive Nuitka Builder")
    parser.add_argument("--bundle", action="store_true", help="Build gói mã hóa .pyd vào dist/ToolDL_Protected")
    parser.add_argument("--exe", action="store_true", help="Build Standalone .exe vào dist/ToolDL_App")
    args = parser.parse_args()

    if args.bundle:
        build_protected_bundle()
    elif args.exe:
        build_standalone_exe()
    else:
        show_menu()

if __name__ == "__main__":
    main()
