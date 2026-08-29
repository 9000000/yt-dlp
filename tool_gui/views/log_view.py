"""
Màn hình Nhật Ký Hoạt Động (Logs View).
Ghi lại chi tiết tiến trình phân tích, tải video và gọi lệnh FFmpeg 100% Tiếng Việt.
"""

import time
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import filedialog

class LogView(ctk.CTkFrame):
    """Giao diện hiển thị nhật ký thời gian thực."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(header, text="📜 NHẬT KÝ HOẠT ĐỘNG THỜI GIAN THỰC", font=("Segoe UI", 15, "bold"))
        title.pack(side="left")

        # Nút thao tác
        copy_btn = ctk.CTkButton(header, text="📋 Sao chép", width=90, height=32, command=self.on_copy, fg_color="#64748B", hover_color="#475569")
        copy_btn.pack(side="right", padx=(5, 0))

        clear_btn = ctk.CTkButton(header, text="🧹 Xóa log", width=90, height=32, command=self.on_clear, fg_color="#EF4444", hover_color="#DC2626")
        clear_btn.pack(side="right", padx=(5, 0))

        export_btn = ctk.CTkButton(header, text="💾 Xuất file", width=90, height=32, command=self.on_export, fg_color="#3B82F6", hover_color="#2563EB")
        export_btn.pack(side="right", padx=(5, 0))

        # Textbox hiển thị logs
        self.log_text = ctk.CTkTextbox(self, font=("Consolas", 11), wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def append_log(self, msg: str):
        """Thêm một dòng log kèm dấu thời gian."""
        timestamp = time.strftime("[%H:%M:%S]")
        line = f"{timestamp} {msg}\n"
        self.log_text.insert("end", line)
        self.log_text.see("end")

    def on_copy(self):
        """Sao chép toàn bộ nhật ký vào clipboard."""
        val = self.log_text.get("1.0", "end").strip()
        if val:
            self.clipboard_clear()
            self.clipboard_append(val)
            msgbox.showinfo("Thông báo", "Đã sao chép toàn bộ nhật ký vào khay nhớ tạm!")

    def on_clear(self):
        """Xóa trắng khung nhật ký."""
        self.log_text.delete("1.0", "end")

    def on_export(self):
        """Lưu file nhật ký ra tệp text."""
        val = self.log_text.get("1.0", "end").strip()
        if not val:
            msgbox.showwarning("Cảnh báo", "Nhật ký hiện đang rỗng!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(val)
                msgbox.showinfo("Thành công", f"Đã xuất nhật ký ra tệp:\n{path}")
            except Exception as e:
                msgbox.showerror("Lỗi", f"Không thể lưu file: {e}")
