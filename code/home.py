import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter


# ================= GLOBAL CONFIG =================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class HomeFrame(ctk.CTkFrame):
    """
    Trang chủ (Home) – customtkinter
    """

    def __init__(self, parent, user_info, on_navigate, on_logout=None):
        super().__init__(parent, fg_color="#ffffff")
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.user_info = user_info
        self.on_navigate = on_navigate
        self.on_logout = on_logout

        # ================= BACKGROUND =================
        self.init_background()

        # ================= CONTENT =================
        self.create_widgets()

    # ==================================================
    def init_background(self):
        """Khởi tạo ảnh nền toàn màn hình"""

        try:
            img = Image.open("image/image2.png").resize((1200, 900))
            img = img.filter(ImageFilter.GaussianBlur(2))
            bg_img = ctk.CTkImage(img, size=(1200, 900))
            bg = ctk.CTkLabel(self, image=bg_img, text="")
            bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        except:
            self.configure(fg_color="#FFFFFF")

    # ==================================================
    def create_widgets(self):

        # ================= HEADER =================
        header = ctk.CTkFrame(
            self,
            height=80,
            fg_color="#a3edee",
            corner_radius=0
        )
        header.place(relx=0, rely=0, relwidth=1)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="HỆ THỐNG ĐIỂM DANH & GIÁM SÁT SỰ TẬP TRUNG",
            font=("Segoe UI", 20, "bold"),
            text_color="#ef4385"
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkButton(
            header,
            text="Đăng xuất",
            width=100,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.logout
        ).place(relx=0.98, rely=0.5, anchor="e")

        # ================= MAIN =================
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.place(relx=0.5, rely=0.52, anchor="center")

        center = ctk.CTkFrame(
            main,
            width=300,
            height=380,
            fg_color="#ffffff",
        )
        center.pack()
        center.pack_propagate(False)

        self.create_main_button(
            center,
            text="📝 TẠO BUỔI HỌC",
            fg_color="#7bed9f",
            command=lambda: self.on_navigate("camera")
        ).pack(padx=40, pady=(30, 15), fill="x")

        self.create_main_button(
            center,
            text="📚 LỊCH SỬ BUỔI HỌC",
            fg_color="#ff6b81",
            command=lambda: self.on_navigate("lichsu")
        ).pack(padx=40, pady=15, fill="x")

        self.create_main_button(
            center,
            text="👥 QUẢN LÝ HỌC SINH",
            fg_color="#dcf842",
            command=lambda: self.on_navigate("hocsinh")
        ).pack(padx=40, pady=(15, 15), fill="x")

        self.create_main_button(
            center,
            text="📊 THỐNG KÊ",
            fg_color="#b148aa",
            command=lambda: self.on_navigate("thongke")
        ).pack(padx=40, pady=(15, 15), fill="x")

        # ================= FOOTER =================
        footer = ctk.CTkFrame(
            self,
            height=40,
            fg_color="#a3edee",
            corner_radius=0
        )
        footer.place(relx=0, rely=1, relwidth=1, anchor="sw")
        footer.pack_propagate(False)

        ctk.CTkLabel(
            footer,
            text="© 2025 Hệ thống Giám sát ATT – Phiên bản 1.0",
            text_color="gray",
            font=("Segoe UI", 10)
        ).pack(pady=8)

    # ==================================================
    def create_main_button(self, parent, text, command, fg_color):
        return ctk.CTkButton(
            parent,
            text=text,
            height=55,
            width=200,
            corner_radius=12,
            font=("Segoe UI", 15, "bold"),
            fg_color=fg_color,
            text_color="#000000",
            command=command
        )

    # ==================================================
    def logout(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn đăng xuất?"):
            if self.on_logout:
                self.on_logout()
