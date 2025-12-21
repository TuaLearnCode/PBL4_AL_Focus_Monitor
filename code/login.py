import customtkinter as ctk
import database
import email_service
from PIL import Image, ImageFilter
import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

REMEMBER_FILE = "remember.txt"


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="#ffffff")
        self.configure(fg_color="#abeddf")
        self.on_login_success = on_login_success
        self.alpha = 0.0


        # ===== BACKGROUND =====
        try:
            img = Image.open("image/image.png").resize((1200, 900))
            img = img.filter(ImageFilter.GaussianBlur(2))
            bg_img = ctk.CTkImage(img, size=(1200, 900))
            bg = ctk.CTkLabel(master, image=bg_img, text="")
            bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        except:
            master.configure(fg_color="#FFFFFF")

        # ===== CARD =====
        self.card = ctk.CTkFrame(master, width=420, height=430, fg_color="#a3edee")
        self.card.place(relx=0.5, rely=0.55, anchor="center")
        self.card.pack_propagate(False)

        ctk.CTkLabel(
            self.card,
            text="Hệ thống giám sát ATT",   
            font=("Segoe UI", 26, "bold"), 
            text_color="#ef4385"
        ).pack(pady=(35, 5))

        ctk.CTkLabel(
            self.card,
            text="Đăng nhập để tiếp tục",
            text_color="gray"
        ).pack(pady=(0, 25))

        # ===== USERNAME =====
        self.username_entry = ctk.CTkEntry(
            self.card, placeholder_text="Tên đăng nhập", width=280, height=45
        )
        self.username_entry.pack(pady=10)

        # ===== PASSWORD =====
        pw_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        pw_frame.pack(pady=10)

        self.password_entry = ctk.CTkEntry(
            pw_frame, placeholder_text="Mật khẩu", show="*", width=240, height=45
        )
        self.password_entry.pack(side="left", padx=(0, 5))

        self.show_pass = False
        ctk.CTkButton(
            pw_frame, text="👁", text_color="#000000", width=35, height=45, hover_color="#e7d40e",
            command=self.toggle_password

        ).pack(side="left")

        # ===== REMEMBER =====
        self.remember_var = ctk.BooleanVar()
        ctk.CTkCheckBox(
            self.card, text="Ghi nhớ đăng nhập", variable=self.remember_var
        ).pack(pady=(5,5))

        self.error_label = ctk.CTkLabel(self.card, text="", text_color="red")
        self.error_label.pack()

        ctk.CTkButton(
            self.card, text="Đăng nhập",
            width=150, height=45, text_color="#000000",
            font=("Segoe UI", 14, "bold"), fg_color="#9a9ce9", 
            command=self.attempt_login
        ).pack(pady=20)

        ctk.CTkButton(
            self.card,
            text="Quên mật khẩu?",
            fg_color="transparent",
            text_color="#fe330f",
            hover=False,            
            command=self.open_forgot_password
        ).pack()

        self.load_remembered_user()
        self.username_entry.focus()
        master.bind("<Return>", lambda e: self.attempt_login())

    # ================= FUNCTIONS =================
    def toggle_password(self):
        self.show_pass = not self.show_pass
        self.password_entry.configure(show="" if self.show_pass else "*")

    def load_remembered_user(self):
        if os.path.exists(REMEMBER_FILE):
            with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                self.username_entry.insert(0, f.read().strip())
                self.remember_var.set(True)

    def save_remembered_user(self, username):
        if self.remember_var.get():
            with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
                f.write(username)

    def attempt_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()

        if not u or not p:
            self.error_label.configure(text="Vui lòng nhập đầy đủ")
            return

        ok, res = database.verify_account(u, p)
        if ok:
            self.save_remembered_user(u)
            self.on_login_success(res)
        else:
            self.error_label.configure(text=res)

    # ================= RESET PASSWORD =================
    def open_forgot_password(self):
        win = ctk.CTkToplevel(self)
        win.title("Quên mật khẩu")
        win.geometry("360x360")
        win.grab_set()

        ctk.CTkLabel(win, text="Đặt lại mật khẩu", font=("Segoe UI", 18, "bold")).pack(pady=15)

        email_entry = ctk.CTkEntry(win, placeholder_text="Email đã đăng ký")
        email_entry.pack(pady=10)

        otp_entry = ctk.CTkEntry(win, placeholder_text="OTP")
        otp_entry.pack(pady=5)

        new_pw_entry = ctk.CTkEntry(win, placeholder_text="Mật khẩu mới", show="*")
        new_pw_entry.pack(pady=5)

        msg = ctk.CTkLabel(win, text="", text_color="red")
        msg.pack(pady=5)

        def send_otp():
            try:
                otp = database.create_reset_code(email_entry.get().strip())
                email_service.send_reset_email(email_entry.get().strip(), otp)
                msg.configure(text="Đã gửi OTP", text_color="green")
            except Exception as e:
                msg.configure(text=str(e))

        def reset_pw():
            if not database.verify_reset_code(
                email_entry.get().strip(), otp_entry.get().strip()
            ):
                msg.configure(text="OTP không hợp lệ")
                return
            database.reset_password(email_entry.get().strip(), new_pw_entry.get().strip())
            msg.configure(text="Đổi mật khẩu thành công", text_color="green")
            win.after(1500, win.destroy)

        ctk.CTkButton(win, text="Gửi OTP", command=send_otp).pack(pady=10)
        ctk.CTkButton(win, text="Đặt lại mật khẩu", command=reset_pw).pack(pady=10)
