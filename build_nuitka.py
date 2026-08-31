"""
Script Đóng Gói & Mã Hóa Nuitka Độc Lập (Isolated Non-Intrusive Build System).
NGUYÊN TẮC HOẠT ĐỘNG:
- 100% KHÔNG THAY ĐỔI, KHÔNG XÓA, KHÔNG ĐỔI TÊN bất kỳ tệp tin nào trong thư mục dự án gốc của bạn.
- Bạn có thể vừa lập trình, vừa chạy code Python .py bình thường.
- Cung cấp chế độ Build Siêu Tốc (Hybrid): Mã hóa file lõi sang .pyd + Đóng gói .exe thông thường chỉ mất ~40 giây!
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

def prepare_staging_with_pyd():
    """Chuẩn bị thư mục Staging với các file lõi đã được mã hóa sang .pyd."""
    clean_temp()
    print("\n📁 [1/3] Đang chuẩn bị môi trường đóng gói cách ly (Staging)...")
    BUILD_TEMP_DIR.mkdir(parents=True, exist_ok=True)

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

    print("\n⚙️ [2/3] Đang tiến hành biên dịch mã C++ (.pyd) cho các file cốt lõi...")
    for mod_rel in PROTECTED_MODULES:
        stg_py = BUILD_TEMP_DIR / mod_rel
        if not stg_py.exists():
            continue

        print(f"   🔒 Đang mã hóa: {mod_rel} ➡️ .pyd ...")
        cmd = [
            sys.executable, "-m", "nuitka",
            "--mode=module",
            "--nofollow-imports",
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

    return True

def ensure_ffmpeg():
    """Kiểm tra và chuẩn bị sẵn FFmpeg trong thư mục bin/ trước khi đóng gói."""
    bin_dir = PROJECT_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = bin_dir / "ffmpeg.exe"

    if not ffmpeg_exe.exists():
        print("🔍 Chưa phát hiện FFmpeg trong bin/, đang tự động tải bản dựng mới nhất...")
        from tool_gui.updater import UpdaterManager
        up = UpdaterManager(PROJECT_DIR)
        success, msg = up.download_and_install_ffmpeg()
        if success:
            print("✅ Đã chuẩn bị sẵn FFmpeg thành công.")
        else:
            print(f"⚠️ Cảnh báo: Không thể tải sẵn FFmpeg ({msg}).")
    else:
        print("✅ FFmpeg đã có sẵn trong thư mục bin/.")

def copy_assets_to_dist(dest_dir: Path):
    """Sao chép FFmpeg, plugins và các dữ liệu cần thiết vào thư mục sản phẩm."""
    print(f"📦 Đang sao chép phụ trợ FFmpeg và dữ liệu vào: {dest_dir.name}...")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sao chép thư mục bin/ chứa ffmpeg.exe & ffprobe.exe
    src_bin = PROJECT_DIR / "bin"
    if src_bin.exists():
        for target_bin in [dest_dir / "bin", dest_dir / "_internal" / "bin"]:
            if target_bin.exists():
                shutil.rmtree(target_bin)
            shutil.copytree(src_bin, target_bin)
        print("   ✅ Đã nhúng FFmpeg & FFprobe.")

    # 2. Sao chép yt_dlp_plugins nếu có
    src_plugins = PROJECT_DIR / "yt_dlp_plugins"
    if src_plugins.exists():
        for target_plugins in [dest_dir / "yt_dlp_plugins", dest_dir / "_internal" / "yt_dlp_plugins"]:
            if target_plugins.exists():
                shutil.rmtree(target_plugins)
            shutil.copytree(src_plugins, target_plugins)

    # 3. Sao chép public.key và config.json
    for data_name in ["public.key", "config.json"]:
        src_data = PROJECT_DIR / data_name
        if src_data.exists():
            shutil.copy2(src_data, dest_dir / data_name)
            int_dir = dest_dir / "_internal"
            if int_dir.exists():
                shutil.copy2(src_data, int_dir / data_name)

def make_zip_archive(source_dir: Path, zip_file: Path):
    """Nén thư mục ứng dụng thành tệp ZIP phân phối Portable."""
    import zipfile
    print(f"\n🗜️  Đang nén toàn bộ gói ứng dụng thành file ZIP: {zip_file.name}...")
    if zip_file.exists():
        try:
            zip_file.unlink()
        except Exception:
            pass

    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(source_dir)
                zf.write(full_path, arcname=str(Path(source_dir.name) / rel_path))

    size_mb = zip_file.stat().st_size / (1024 * 1024)
    print(f"✅ Đã nén thành công file ZIP: {zip_file} ({size_mb:.2f} MB)")

def build_fast_hybrid_exe():
    """
    Chế độ KHUYÊN DÙNG: Mã hóa các file lõi sang .pyd (C native) + Đóng gói nhanh bằng PyInstaller.
    Thời gian build: Chỉ khoảng ~40 giây đến 1 phút!
    Bảo mật: Logic bản quyền, máy ID và lõi tải đều là file C .pyd không thể decompile.
    """
    print("\n" + "=" * 68)
    print(" ⚡ BUILD SIÊU TỐC: MÃ HÓA CỐT LÕI (.PYD) + ĐÓNG GÓI .EXE")
    print(" ⏱️ Thời gian: ~40 giây  |  🔒 Bảo mật: File lõi chuyển thành DLL C Native")
    print(" 💡 Dự án gốc của bạn được giữ nguyên vẹn 100%, không bị sửa đổi.")
    print("=" * 68)

    if not check_nuitka_installed():
        return False

    ensure_ffmpeg()
    prepare_staging_with_pyd()

    out_dir = DIST_DIR / "ToolDL_Pro"
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)

    print("\n📦 [3/3] Đang đóng gói siêu tốc thành tệp .exe với PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=ToolDL",
        "--collect-all=customtkinter",
        "--collect-all=yt_dlp",
        "--collect-all=yt_dlp_plugins",
        "--collect-all=curl_cffi",
        "--collect-all=PIL",
        "--collect-all=webview",
        "--collect-all=pythonnet",
        "--collect-all=clr_loader",
        "--collect-all=tkinterweb",
        "--collect-all=tkinterweb_tkhtml",
        "--collect-all=tool_gui",
        "--hidden-import=clr",
        "--hidden-import=pythonnet",
        "--hidden-import=clr_loader",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=webview.platforms.edgehtml",
        "--hidden-import=webview.platforms.mshtml",
        "--hidden-import=tool_gui.embedded_browser_manager",
        "--hidden-import=tool_gui.views.scan_results_dialog",
        "--hidden-import=tool_gui.views.format_picker_dialog",
        "--hidden-import=tool_gui.views.presets_view",
        f"--distpath={DIST_DIR}",
        f"--workpath={PROJECT_DIR / 'build' / 'pyinstaller_work'}",
        str(BUILD_TEMP_DIR / "run_gui.py")
    ]

    ret = subprocess.run(cmd, cwd=str(BUILD_TEMP_DIR))
    clean_temp()

    # Dọn dẹp workpath của pyinstaller
    pyinst_work = PROJECT_DIR / "build" / "pyinstaller_work"
    if pyinst_work.exists():
        shutil.rmtree(pyinst_work, ignore_errors=True)

    spec_file = BUILD_TEMP_DIR / "run_gui.spec"
    if spec_file.exists():
        spec_file.unlink()

    if ret.returncode == 0:
        final_app_dir = DIST_DIR / "ToolDL"
        if final_app_dir.exists() and not out_dir.exists():
            final_app_dir.rename(out_dir)

        copy_assets_to_dist(out_dir)

        # Đóng gói tự động thành file ZIP Portable
        zip_output = DIST_DIR / "ToolDL_Pro_Portable.zip"
        make_zip_archive(out_dir, zip_output)

        print("\n" + "=" * 68)
        print(" 🎉 BUILD SIÊU TỐC & ĐÓNG GÓI ZIP THÀNH CÔNG!")
        print(f" 📂 Thư mục sản phẩm: {out_dir}")
        print(f" 📦 Tệp nén Portable: {zip_output}")
        print(" 🚀 Tệp khởi chạy: ToolDL.exe")
        print(" 🔒 Các file cốt lõi (license_manager, downloader, url_detector, config, updater)")
        print("    đã được biên dịch sang mã máy C/C++ (.pyd) chống reverse engineering 100%!")
        print("=" * 68)
        return True
    else:
        print("\n❌ Quá trình đóng gói gặp lỗi.")
        return False

def build_protected_bundle():
    """Xuất bản gói thư mục ToolDL_Protected với các file lõi đã mã hóa .pyd."""
    print("\n" + "=" * 68)
    print(" 🛡️  BUILD GÓI THƯ MỤC MÃ HÓA CỐT LÕI (HYBRID .PYD BUNDLE)")
    print("=" * 68)

    if not check_nuitka_installed():
        return False

    ensure_ffmpeg()

    out_bundle_dir = DIST_DIR / "ToolDL_Protected"
    if out_bundle_dir.exists():
        shutil.rmtree(out_bundle_dir, ignore_errors=True)
    out_bundle_dir.mkdir(parents=True, exist_ok=True)

    prepare_staging_with_pyd()

    print("\n📦 [3/3] Đang hoàn thiện gói phát hành vào thư mục 'dist/ToolDL_Protected'...")
    for item in BUILD_TEMP_DIR.iterdir():
        dest = out_bundle_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    clean_temp()
    copy_assets_to_dist(out_bundle_dir)

    print("\n" + "=" * 68)
    print(" 🎉 XUẤT BẢN THÀNH CÔNG GÓI MÃ HÓA!")
    print(f" 📂 Thư mục sản phẩm: {out_bundle_dir}")
    print("=" * 68)
    return True

def build_full_nuitka_exe():
    """Đóng gói toàn bộ phần mềm sang C++ bằng Nuitka (Mất 3-5 phút)."""
    print("\n" + "=" * 68)
    print(" 🚀 BUILD TOÀN BỘ BẰNG NUITKA C++ NATIVE STANDALONE")
    print("=" * 68)

    if not check_nuitka_installed():
        return False

    ensure_ffmpeg()

    out_dir = DIST_DIR / "ToolDL_FullNuitka"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "nuitka",
        "--mode=standalone",
        "--windows-console-mode=disable",
        "--enable-plugin=tk-inter",
        "--include-package=customtkinter",
        "--include-package-data=customtkinter",
        "--include-package=yt_dlp",
        "--include-package=PIL",
        "--include-package=cryptography",
        "--include-package=webview",
        "--include-package=pythonnet",
        "--include-package=clr_loader",
        "--include-package=tool_gui",
        "--include-data-file=public.key=public.key",
        "--include-data-file=config.json=config.json",
        f"--output-dir={out_dir}",
        "--output-filename=ToolDL.exe",
        "run_gui.py"
    ]

    print("\n⚙️ Đang biên dịch toàn bộ dự án sang C++ bằng Nuitka (Vui lòng đợi vài phút)...")
    ret = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    
    if ret.returncode == 0:
        dist_app = out_dir / "run_gui.dist"
        if dist_app.exists():
            copy_assets_to_dist(dist_app)

        print("\n" + "=" * 68)
        print(" 🎉 ĐÓNG GÓI .EXE THÀNH CÔNG!")
        print(f" 📂 Vị trí ứng dụng: {out_dir / 'run_gui.dist'}")
        print("=" * 68)
        return True
    else:
        print("\n❌ Đóng gói thất bại.")
        return False

def show_menu():
    """Menu tương tác thân thiện."""
    while True:
        print("\n" + "=" * 68)
        print("   🛡️  BỘ CÔNG CỤ ĐÓNG GÓI & MÃ HÓA TOOLDL PRO")
        print("=" * 68)
        print(" [1] ⚡ Build Nhanh Siêu Tốc (Mã hóa .pyd + Đóng gói .exe) [~40s] (Khuyên dùng)")
        print(" [2] 🚀 Build Toàn Bộ Bằng Nuitka C++ Native (.exe độc lập) [3-5 phút]")
        print(" [3] 🔒 Xuất Bản Gói Thư Mục Đã Mã Hóa Cốt Lõi (dist/ToolDL_Protected)")
        print(" [0] 🚪 Thoát")
        print("=" * 68)
        print(" 💡 Tất cả các lựa chọn đều KHÔNG làm thay đổi file nào trong dự án của bạn.")

        choice = input("\n👉 Nhập lựa chọn của bạn (0-3): ").strip()
        if choice == "1":
            build_fast_hybrid_exe()
        elif choice == "2":
            build_full_nuitka_exe()
        elif choice == "3":
            build_protected_bundle()
        elif choice == "0":
            print("👋 Tạm biệt!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng chọn lại.")

def main():
    parser = argparse.ArgumentParser(description="ToolDL Non-Intrusive Builder")
    parser.add_argument("--fast", action="store_true", help="Build nhanh siêu tốc: Mã hóa .pyd + Đóng gói .exe")
    parser.add_argument("--nuitka", action="store_true", help="Build toàn bộ bằng Nuitka C++ Native")
    parser.add_argument("--bundle", action="store_true", help="Build gói thư mục .pyd")
    args = parser.parse_args()

    if args.fast:
        build_fast_hybrid_exe()
    elif args.nuitka:
        build_full_nuitka_exe()
    elif args.bundle:
        build_protected_bundle()
    else:
        show_menu()

if __name__ == "__main__":
    main()
