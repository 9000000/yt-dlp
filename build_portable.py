"""
Script Đóng Gói Ứng Dụng Thành Bản Portable ZIP Độc Lập (Build Portable Package).
Sử dụng PyInstaller đóng gói toàn bộ mã nguồn, thư viện, Trình duyệt Web, PO Token Plugin và FFmpeg thành file ToolDL_Portable.zip.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

# Đảm bảo UTF-8 output trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
PORTABLE_APP_DIR = DIST_DIR / "ToolDL"
OUTPUT_ZIP = DIST_DIR / "ToolDL_Portable.zip"

def log(msg: str):
    print(f"[*] {msg}")

def ensure_ffmpeg():
    """Kiểm tra và chuẩn bị sẵn FFmpeg trong thư mục bin/ trước khi đóng gói."""
    bin_dir = ROOT_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = bin_dir / "ffmpeg.exe"

    if not ffmpeg_exe.exists():
        log("Chưa phát hiện FFmpeg trong bin/, đang tự động tải bản dựng mới nhất...")
        from tool_gui.updater import UpdaterManager
        up = UpdaterManager(ROOT_DIR)
        success, msg = up.download_and_install_ffmpeg()
        if success:
            log("✅ Đã chuẩn bị sẵn FFmpeg thành công.")
        else:
            log(f"⚠️ Cảnh báo: Không thể tải sẵn FFmpeg ({msg}). Ứng dụng sẽ tự tải khi người dùng mở lần đầu.")
    else:
        log("✅ FFmpeg đã có sẵn trong thư mục bin/.")

def run_pyinstaller():
    """Chạy PyInstaller để đóng gói thành thư mục ứng dụng độc lập."""
    log("Bắt đầu biên dịch ứng dụng bằng PyInstaller...")

    if PORTABLE_APP_DIR.exists():
        shutil.rmtree(PORTABLE_APP_DIR, ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=ToolDL",
        "--noconsole",
        "--onedir",
        "--clean",
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
        str(ROOT_DIR / "run_gui.py")
    ]

    log(f"Đang thực thi lệnh đóng gói...")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        raise Exception("Quá trình đóng gói PyInstaller thất bại!")

    log("✅ Biên dịch PyInstaller hoàn tất.")

def copy_assets():
    """Sao chép các phụ trợ cần thiết vào thư mục đóng gói."""
    log("Đang sao chép phụ trợ FFmpeg và tài liệu vào gói Portable...")

    # 1. Sao chép thư mục bin/ (chứa ffmpeg.exe & ffprobe.exe)
    src_bin = ROOT_DIR / "bin"
    if src_bin.exists():
        for dst_bin in [PORTABLE_APP_DIR / "bin", PORTABLE_APP_DIR / "_internal" / "bin"]:
            if dst_bin.exists():
                shutil.rmtree(dst_bin)
            shutil.copytree(src_bin, dst_bin)
        log("✅ Đã sao chép FFmpeg & FFprobe vào gói đóng gói.")

    # 2. Sao chép thư mục yt_dlp_plugins/ nếu có
    src_plugins = ROOT_DIR / "yt_dlp_plugins"
    if src_plugins.exists():
        for dst_plugins in [PORTABLE_APP_DIR / "yt_dlp_plugins", PORTABLE_APP_DIR / "_internal" / "yt_dlp_plugins"]:
            if dst_plugins.exists():
                shutil.rmtree(dst_plugins)
            shutil.copytree(src_plugins, dst_plugins)

    # 3. Sao chép public.key và config.json nếu có
    for data_file in ["public.key", "config.json"]:
        src_f = ROOT_DIR / data_file
        if src_f.exists():
            shutil.copy2(src_f, PORTABLE_APP_DIR / data_file)
            int_dir = PORTABLE_APP_DIR / "_internal"
            if int_dir.exists():
                shutil.copy2(src_f, int_dir / data_file)

    # 4. Tạo file Hướng dẫn sử dụng
    readme_txt = PORTABLE_APP_DIR / "HUONG_DAN_SU_DUNG.txt"
    with open(readme_txt, "w", encoding="utf-8") as f:
        f.write("""========================================================================
             TOOLDL PRO - PHẦN MỀM TẢI VIDEO ĐA NĂNG PORTABLE
========================================================================

1. CÁCH SỬ DỤNG:
   - Nhấp đúp vào tệp "ToolDL.exe" để mở phần mềm.
   - Không cần cài đặt bất kỳ môi trường hay phần mềm nào khác!

2. KÍCH HOẠT BẢN QUYỀN (LẦN ĐẦU SỬ DỤNG):
   - Mở phần mềm, sao chép "Mã thiết bị (Machine ID)".
   - Gửi mã cho Quản trị viên để nhận mã kích hoạt (License Key).
   - Dán mã Key vào ô và bấm "KÍCH HOẠT BẢN QUYỀN NGAY".

3. TÍNH NĂNG NỔI BẬT:
   - Tìm kiếm video trực tiếp theo từ khóa & Chọn nhiều video tải hàng loạt.
   - Tích hợp Trình duyệt Web & Quét toàn bộ video trên trang.
   - Tự động nhận diện link video từ khay nhớ tạm (Clipboard).
   - Tải video 8K / 4K / 1080p / Âm thanh MP3 320kbps từ YouTube, TikTok,
     Facebook, Instagram, Bilibili, Douyin và hơn 1000 trang web khác.
   - Đã tích hợp sẵn bộ xử lý FFmpeg bản mới nhất.
   - Tự động chống chặn YouTube Botguard (PO Token Provider) & TikTok HD.
   - Tự động kiểm tra và cập nhật phụ trợ.

Chúc bạn có trải nghiệm tuyệt vời cùng ToolDL Pro!
========================================================================
""")

    log("✅ Đã sao chép đầy đủ phụ trợ và tài liệu hướng dẫn.")

def create_zip():
    """Nén thư mục thành file ZIP duy nhất để phân phối."""
    log(f"Đang nén toàn bộ thành file ZIP: {OUTPUT_ZIP.name}...")

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(PORTABLE_APP_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(PORTABLE_APP_DIR)
                zipf.write(file_path, arcname)

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    log(f"🎉 ĐÃ TẠO THÀNH CÔNG GÓI PORTABLE ZIP!")
    log(f"📁 Đường dẫn: {OUTPUT_ZIP}")
    log(f"📦 Dung lượng: {size_mb:.2f} MB")

def main():
    print("=" * 60)
    print("      TRÌNH ĐÓNG GÓI TOOLDL PRO PORTABLE ZIP")
    print("=" * 60)

    try:
        ensure_ffmpeg()
        run_pyinstaller()
        copy_assets()
        create_zip()
        print("\n" + "=" * 60)
        print("✅ HOÀN TẤT ĐÓNG GÓI BẢN PORTABLE CHẠY NGAY KHÔNG CẦN CÀI ĐẶT!")
        print(f"👉 File ZIP phân phối: {OUTPUT_ZIP}")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình đóng gói: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
