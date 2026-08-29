"""
Màn hình Kích hoạt Bản quyền (Activation View).
Hiển thị giao diện nhập License Key và kiểm tra Machine ID toàn bộ bằng Tiếng Việt.
"""

import customtkinter as ctk
import tkinter.messagebox as msgbox
from tool_gui.license_manager import LicenseManager

class ActivationView(ctk.CTkFrame):
    """Giao diện kích hoạt bản quyền ứng dụng."""

    def __init__(self, master, license_manager: LicenseManager, on_activated_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.license_manager = license_manager
        self.on_activated_callback = on_activated_callback

        self.setup_ui()

    def setup_ui(self):
        # Thiết lập khung căn giữa
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        center_card = ctk.CTkFrame(self, corner_radius=16, fg_color=("#F1F5F9", "#1E293B"), border_width=1, border_color=("#CBD5E1", "#334155"))
        center_card.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        center_card.grid_columnconfigure(0, weight=1)

        # 1. Tiêu đề
        title_icon = ctk.CTkLabel(center_card, text="🛡️", font=("Segoe UI", 48))
        title_icon.pack(pady=(30, 5))

        title_lbl = ctk.CTkLabel(
            center_card,
            text="KÍCH HOẠT BẢN QUYỀN TOOLDL",
            font=("Segoe UI", 22, "bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        title_lbl.pack(pady=(0, 5))

        sub_lbl = ctk.CTkLabel(
            center_card,
            text="Vui lòng nhập License Key hợp lệ để sử dụng đầy đủ các tính năng.",
            font=("Segoe UI", 13),
            text_color=("#64748B", "#94A3B8")
        )
        sub_lbl.pack(pady=(0, 20))

        # 2. Khung Machine ID
        m_frame = ctk.CTkFrame(center_card, fg_color=("#E2E8F0", "#0F172A"), corner_radius=10)
        m_frame.pack(fill="x", padx=40, pady=(0, 15))

        m_title = ctk.CTkLabel(m_frame, text="Mã thiết bị của bạn (Machine ID):", font=("Segoe UI", 12, "bold"))
        m_title.pack(anchor="w", padx=15, pady=(10, 4))

        m_inner = ctk.CTkFrame(m_frame, fg_color="transparent")
        m_inner.pack(fill="x", padx=15, pady=(0, 10))

        machine_id = self.license_manager.get_machine_id()
        self.m_entry = ctk.CTkEntry(m_inner, font=("Consolas", 14, "bold"), height=36, corner_radius=8)
        self.m_entry.insert(0, machine_id)
        self.m_entry.configure(state="readonly")
        self.m_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        copy_btn = ctk.CTkButton(
            m_inner,
            text="📋 Sao chép mã máy",
            width=140,
            height=36,
            command=self.copy_machine_id,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=("Segoe UI", 12, "bold")
        )
        copy_btn.pack(side="right")

        # 3. Khung Nhập Key
        k_frame = ctk.CTkFrame(center_card, fg_color=("#E2E8F0", "#0F172A"), corner_radius=10)
        k_frame.pack(fill="x", padx=40, pady=(0, 15))

        k_title = ctk.CTkLabel(k_frame, text="Nhập mã bản quyền (License Key):", font=("Segoe UI", 12, "bold"))
        k_title.pack(anchor="w", padx=15, pady=(10, 4))

        k_inner = ctk.CTkFrame(k_frame, fg_color="transparent")
        k_inner.pack(fill="x", padx=15, pady=(0, 10))

        self.k_entry = ctk.CTkEntry(k_inner, placeholder_text="Dán mã License Key tại đây...", font=("Segoe UI", 12), height=36, corner_radius=8)
        self.k_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        paste_btn = ctk.CTkButton(
            k_inner,
            text="📥 Dán từ khay nhớ",
            width=140,
            height=36,
            command=self.paste_key,
            fg_color="#64748B",
            hover_color="#475569",
            font=("Segoe UI", 12)
        )
        paste_btn.pack(side="right")

        # 4. Nhãn thông báo kết quả
        self.status_lbl = ctk.CTkLabel(center_card, text="", font=("Segoe UI", 12, "bold"), text_color="#EF4444")
        self.status_lbl.pack(pady=(0, 10))

        # 5. Nút Kích hoạt
        self.act_btn = ctk.CTkButton(
            center_card,
            text="🚀 KÍCH HOẠT BẢN QUYỀN NGAY",
            height=46,
            command=self.on_activate_clicked,
            font=("Segoe UI", 14, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=10
        )
        self.act_btn.pack(fill="x", padx=40, pady=(0, 15))

        # 6. Ghi chú hỗ trợ
        note_lbl = ctk.CTkLabel(
            center_card,
            text="💡 Hãy gửi Mã thiết bị (Machine ID) cho người quản trị để nhận Key kích hoạt.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8")
        )
        note_lbl.pack(pady=(0, 25))

    def copy_machine_id(self):
        """Sao chép Machine ID vào clipboard."""
        mid = self.m_entry.get()
        self.clipboard_clear()
        self.clipboard_append(mid)
        self.status_lbl.configure(text="✅ Đã sao chép Machine ID vào khay nhớ tạm!", text_color="#10B981")

    def paste_key(self):
        """Dán key từ clipboard vào ô nhập."""
        try:
            val = self.clipboard_get().strip()
            self.k_entry.delete(0, "end")
            self.k_entry.insert(0, val)
        except Exception:
            pass

    def on_activate_clicked(self):
        """Xử lý kích hoạt key."""
        key = self.k_entry.get().strip()
        if not key:
            self.status_lbl.configure(text="⚠️ Vui lòng nhập mã kích hoạt trước khi bấm Kích hoạt.", text_color="#EF4444")
            return

        success, msg = self.license_manager.activate(key)
        if success:
            self.status_lbl.configure(text=f"✅ {msg}", text_color="#10B981")
            msgbox.showinfo("Thành công", f"Chúc mừng! {msg}")
            if self.on_activated_callback:
                self.on_activated_callback()
        else:
            self.status_lbl.configure(text=f"❌ {msg}", text_color="#EF4444")
