import customtkinter as ctk
from tkinter import ttk, messagebox
import database
from PIL import Image
from tkcalendar import DateEntry
from datetime import datetime
import os, shutil, uuid
from tkcalendar import Calendar
from tkinter import filedialog

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class HocSinhFrame(ctk.CTkFrame):
    """
    Quản lý học sinh – phiên bản customtkinter
    """

    def __init__(self, parent, user_info, on_navigate):
        super().__init__(parent, fg_color="#ffffff")
        self.pack(fill="both", expand=True)

        self.user_info = user_info
        self.on_navigate = on_navigate

        self.create_widgets()
        self.load_students()

    # ==================================================
    def create_widgets(self):

        # ================= HEADER =================
        header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#aeeee0")
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkButton(
            header,
            text="← Quay lại",
            width=90,
            text_color="#ffffff",
            fg_color="#9A9CE9",
            command=lambda: self.on_navigate("home")
        ).place(x=20, rely=0.5, anchor="w")

        ctk.CTkLabel(
            header,
            text="QUẢN LÝ HỌC SINH",
            text_color="#ef4385",
            font=("Segoe UI", 20, "bold")
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ================= TOOLBAR =================
        toolbar = ctk.CTkFrame(self, height=60, fg_color="#a3dcef")
        toolbar.pack(fill="x", padx=15, pady=(10, 5))
        toolbar.pack_propagate(False)

            # Thêm nút "Thêm học sinh"
        ctk.CTkButton(
            toolbar,
            text="➕ Thêm học sinh",
            width=120,
            text_color="#ffffff",
            fg_color="#28a745",
            command=self.add_new_student
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            toolbar,
            text="🔄 Làm mới",
            width=90,
            text_color="#000000",
            fg_color="#64c4c3",
            command=self.load_students
        ).pack(side="left", padx=10)

        ctk.CTkLabel(toolbar, text="Tìm kiếm:").pack(side="left", padx=(20, 5))
        self.search_entry = ctk.CTkEntry(toolbar, width=200, placeholder_text="Tên học sinh", border_width=2, border_color="#e74c3c")
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_students())

        ctk.CTkButton(
            toolbar,
            text="✖",
            width=40,
            text_color="#000000",
            fg_color="#e73a0f",
            hover_color="#971A1A",
            command=self.clear_search
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            toolbar,
            text="Lớp:",
            font=("Segoe UI", 13)
        ).pack(side="left", padx=(20, 5))

        style = ttk.Style()
        style.configure(
            "BigFont.TCombobox",
            font=("Segoe UI", 16)
        )

        self.class_filter = ttk.Combobox(
            toolbar,
            state="readonly",
            width=20,
            height=20,
            style="BigFont.TCombobox"
        )
        self.class_filter.pack(side="left")
        self.class_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_by_class())

        # ================= TABLE =================
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        columns = ("ID", "Họ tên", "Lớp", "Giới tính", "Ngày sinh", "👁 Xem","✏️ Sửa", "🗑 Xóa")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=30)
        self.tree.column("Họ tên", width=200, anchor="w")
        self.tree.column("Lớp", width=100)
        self.tree.column("Giới tính", width=100)
        self.tree.column("Ngày sinh", width=120)
        self.tree.column("👁 Xem", width=70)
        self.tree.column("✏️ Sửa", width=80)
        self.tree.column("🗑 Xóa", width=70)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        self.tree.bind("<Button-1>", self.on_tree_click)

        style = ttk.Style()
        style.configure("Treeview", rowheight=50, font=("Segoe UI", 20), background="#9db899")
        style.configure("Treeview.Heading", font=("Segoe UI", 22, "bold"), background="#9db899")

        self.tree.tag_configure("even", background="#ffcdaa")
        self.tree.tag_configure("odd", background="#ee897f")

        # ================= FOOTER =================
        footer = ctk.CTkFrame(self, height=60, fg_color="#aeeee0")
        footer.pack(fill="x", padx=15, pady=(5, 15))
        footer.pack_propagate(False)

        self.stats_label = ctk.CTkLabel(footer, text="Tổng số học sinh: 0")
        self.stats_label.pack(side="right", padx=20)

    # ==================================================
    def load_students(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            students = database.get_all_students()
            classes = set()

            for i, s in enumerate(students):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", values=(
                    s["student_id"],
                    s["name"],
                    s["class_name"],
                    s["gender"],
                    self._fmt_date(s["birthday"]),
                    "👁 Xem",
                    "✏️ Sửa",
                    "🗑 Xóa"
                ), tags=(tag,))
                classes.add(s["class_name"])

            self.class_filter["values"] = ["Tất cả"] + sorted(classes)
            self.class_filter.current(0)

            self.stats_label.configure(text=f"Tổng số học sinh: {len(students)}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu:\n{e}")

    # ================= CLICK ACTION =================
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if not row:
            return

        item = self.tree.item(row)
        student_id = item["values"][0]

        # Cột 6 = "Cập nhật" | Cột 7 = "Xóa"
        if column == "#6":      # 👁 Xem
            self.view_student(student_id)
        elif column == "#7":    # ✏️ Sửa
            self.edit_student(student_id)
        elif column == "#8":    # 🗑 Xóa
            self.delete_student(student_id)

    # ==================================================
    def search_students(self):
        text = self.search_entry.get().strip().lower()
        selected_class = self.class_filter.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        students = database.get_all_students()
        if text:
            students = [s for s in students if text in s["name"].lower()]
        if selected_class and selected_class != "Tất cả":
            students = [s for s in students if s["class_name"] == selected_class]

        for i, s in enumerate(students):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=(
                s["student_id"],
                s["name"],
                s["class_name"],
                s["gender"],
                self._fmt_date(s["birthday"]),
                self._fmt_datetime(s["created_at"]),
                "👁 Xem",
                "✏️ Sửa",
                "🗑 Xóa"
            ), tags=(tag,))

        self.stats_label.configure(text=f"Tổng số học sinh: {len(students)}")

    # ==================================================
    def filter_by_class(self):
        self.search_students()

    # ==================================================
    def clear_search(self):
        self.search_entry.delete(0, "end")
        self.class_filter.current(0)
        self.load_students()

    # ==================================================
    
    # ================= CREATE =================
    def add_new_student(self):
        # ===== DIALOG =====
        dialog = ctk.CTkToplevel(self)
        dialog.title("Thêm học sinh mới")
        dialog.geometry("400x630")
        dialog.grab_set()

        # ===== BACKGROUND =====
        bg = ctk.CTkFrame(dialog, fg_color="#afe9f7")
        bg.pack(fill="both", expand=True)

        # ===== TITLE =====
        ctk.CTkLabel(
            bg,
            text="THÊM HỌC SINH MỚI",
            text_color="#28a745",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=15)

        # ===== FORM =====
        form = ctk.CTkFrame(bg, fg_color="transparent")
        form.pack(fill="x", padx=30)

        # =====================================================
        # ===================== AVATAR ========================
        # =====================================================
        avatar_path = {"value": None}

        avatar_box = ctk.CTkFrame(form, fg_color="transparent")
        avatar_box.pack(fill="x", pady=(5, 15))

        avatar_img_label = ctk.CTkLabel(
            avatar_box,
            text="(Chưa có ảnh hồ sơ)",
            text_color="#888"
        )
        avatar_img_label.pack(pady=10)

        def choose_avatar():
            path = filedialog.askopenfilename(
                title="Chọn ảnh hồ sơ",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
            )
            if path:
                avatar_path["value"] = path
                img = ctk.CTkImage(
                    light_image=Image.open(path),
                    size=(140, 140)
                )
                avatar_img_label.configure(image=img, text="")
                dialog.avatar_img = img  # giữ reference

        ctk.CTkButton(
            avatar_box,
            text="📁 Chọn ảnh",
            width=120,
            command=choose_avatar
        ).pack(pady=5)

        # =====================================================
        # ================= INPUT HELPERS =====================
        # =====================================================
        def label(text):
            ctk.CTkLabel(form, text=text, font=("Segoe UI", 12))\
                .pack(anchor="w", pady=(8, 4))

        # ===== HỌ TÊN =====
        label("Họ tên:")
        name_entry = ctk.CTkEntry(form)
        name_entry.pack(fill="x")

        # ===== LỚP =====
        label("Lớp:")
        class_entry = ctk.CTkEntry(form)
        class_entry.pack(fill="x")

        # ===== GIỚI TÍNH =====
        label("Giới tính:")
        gender_var = ctk.StringVar(value="Nam")
        gf = ctk.CTkFrame(form, fg_color="transparent")
        gf.pack(anchor="w", pady=(0, 5))
        ctk.CTkRadioButton(gf, text="Nam", variable=gender_var, value="Nam").pack(side="left", padx=10)
        ctk.CTkRadioButton(gf, text="Nữ", variable=gender_var, value="Nữ").pack(side="left", padx=10)

        # ===== NGÀY SINH =====
        label("Ngày sinh:")
        date_row = ctk.CTkFrame(form, fg_color="transparent")
        date_row.pack(anchor="w")

        date_var = ctk.StringVar()

        date_entry = ctk.CTkEntry(
            date_row,
            textvariable=date_var,
            width=220,
            height=38
        )
        date_entry.pack(side="left")

        def open_calendar():
            cal = ctk.CTkToplevel(dialog)
            cal.title("Chọn ngày")
            cal.geometry("250x190")
            cal.grab_set()

            cal_widget = Calendar(cal, date_pattern="yyyy-mm-dd")
            cal_widget.pack(padx=10, pady=10)

            def select():
                date_var.set(cal_widget.get_date())
                cal.destroy()

            ctk.CTkButton(cal, text="Chọn", command=select).pack(pady=5)

        ctk.CTkButton(
            date_row,
            text="📅",
            width=40,
            height=38,
            command=open_calendar
        ).pack(side="left", padx=5)

        # =====================================================
        # ===================== BUTTON ========================
        # =====================================================
        btn_frame = ctk.CTkFrame(bg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)

        def save():
            name = name_entry.get().strip()
            cls = class_entry.get().strip()
            gender = gender_var.get()
            birthday = date_var.get().strip()
            avatar_src = avatar_path["value"]

            if not name or not cls:
                messagebox.showwarning("Cảnh báo", "Họ tên và lớp không được để trống!")
                return

            profile_avatar_url = None
            if avatar_src:
                avatar_dir = os.path.join(os.path.dirname(__file__), "student_avatars")
                os.makedirs(avatar_dir, exist_ok=True)

                ext = os.path.splitext(avatar_src)[1]
                filename = f"profile_{uuid.uuid4().hex}{ext}"
                dest = os.path.join(avatar_dir, filename)

                try:
                    shutil.copy2(avatar_src, dest)
                    profile_avatar_url = f"student_avatars/{filename}"
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Lưu ảnh thất bại:\n{e}")
                    return

            ok, msg = database.add_student(
                name=name,
                class_name=cls,
                gender=gender,
                birthday=birthday,
                profile_avatar_url=profile_avatar_url
            )

            if ok:
                messagebox.showinfo("Thành công", "Đã thêm học sinh mới")
                dialog.destroy()
                self.load_students()
            else:
                messagebox.showerror("Lỗi", msg)

        ctk.CTkButton(
            btn_frame,
            text="💾 Lưu",
            fg_color="#28a745",
            command=save
        ).pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(
            btn_frame,
            text="✖ Hủy",
            fg_color="#dc3545",
            command=dialog.destroy
        ).pack(side="left", padx=10, fill="x", expand=True)


    def view_student(self, student_id):
        student = database.get_student_by_id(student_id)
        if not student:
            messagebox.showerror("Lỗi", "Không tìm thấy học sinh")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Thông tin học sinh")
        dialog.geometry("400x470") #rộng*cao
        dialog.grab_set()

        # ===== BACKGROUND (QUAN TRỌNG) =====
        bg = ctk.CTkFrame(dialog, fg_color="#afe9f7")
        bg.pack(fill="both", expand=True)

        # ===== TITLE =====
        ctk.CTkLabel(
            bg,
            text="THÔNG TIN HỌC SINH",
            font=("Segoe UI", 16, "bold"),
            text_color="#1e90ff"
        ).pack(pady=5)

        # ===== CONTENT FRAME =====
        frame = ctk.CTkFrame(bg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30)

        # ===== AVATAR =====
        avatar_path = student.get("profile_avatar_url")
        if avatar_path and os.path.exists(avatar_path):
            img = ctk.CTkImage(
                light_image=Image.open(avatar_path),
                size=(140, 140)
            )
            ctk.CTkLabel(frame, image=img, text="").pack(pady=10)
            dialog.avatar_img = img  # giữ reference
        else:
            ctk.CTkLabel(frame, text="(Chưa có ảnh hồ sơ)", text_color="#666").pack(pady=10)

        # ===== INFO BOX (NỀN ĐỎ) =====
        info_box = ctk.CTkFrame(
            bg,
            fg_color="#ffe6e6",
            corner_radius=12
        )
        info_box.pack(fill="x", padx=25, pady=5)

        def info_row(label, value):
            row = ctk.CTkFrame(info_box, fg_color="transparent")
            row.pack(anchor="w", padx=20, pady=5)

            ctk.CTkLabel(
                row,
                text=label,
                font=("Segoe UI", 12, "bold"),
                width=70,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value,
                font=("Segoe UI", 12),
                anchor="w"
            ).pack(side="left")

        info_row("ID:", str(student["student_id"]))
        info_row("Họ tên:", student["name"])
        info_row("Lớp:", student["class_name"])
        info_row("Giới tính:", student["gender"])
        info_row("Ngày sinh:", self._fmt_date(student["birthday"]))

        # ===== CLOSE BUTTON =====
        ctk.CTkButton(
            bg,
            text="Đóng",
            command=dialog.destroy,
            fg_color="#f14c10"
        ).pack(pady=20)

    # ==================================================
    def edit_student(self, student_id):
        student = database.get_student_by_id(student_id)
        if not student:
            messagebox.showerror("Lỗi", "Không tìm thấy học sinh")
            return

        # ===== DIALOG =====
        dialog = ctk.CTkToplevel(self)
        dialog.title("Cập nhật học sinh")
        dialog.geometry("400x630")
        dialog.grab_set()

        # ===== BACKGROUND =====
        bg = ctk.CTkFrame(dialog, fg_color="#afe9f7")
        bg.pack(fill="both", expand=True)

        # ===== TITLE =====
        ctk.CTkLabel(
            bg,
            text="CẬP NHẬT HỌC SINH",
            text_color="#1ED14B",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=15)

        # ===== FORM =====
        form = ctk.CTkFrame(bg, fg_color="transparent")
        form.pack(fill="x", padx=30)

        # ===== AVATAR =====
        avatar_path = {"value": None}

        avatar_box = ctk.CTkFrame(form, fg_color="transparent")
        avatar_box.pack(fill="x", pady=(5, 15))

        current_avatar = student.get("profile_avatar_url")
        if current_avatar and os.path.exists(current_avatar):
            img = ctk.CTkImage(
                light_image=Image.open(current_avatar),
                size=(140, 140)
            )
            avatar_img_label = ctk.CTkLabel(avatar_box, image=img, text="")
            avatar_img_label.pack(pady=5)
            dialog.avatar_img = img
        else:
            avatar_img_label = ctk.CTkLabel(
                avatar_box,
                text="(Chưa có ảnh hồ sơ)",
                text_color="#888"
            )
            avatar_img_label.pack(pady=10)

        def choose_avatar():
            path = filedialog.askopenfilename(
                title="Chọn ảnh hồ sơ",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
            )
            if path:
                avatar_path["value"] = path
                new_img = ctk.CTkImage(
                    light_image=Image.open(path),
                    size=(140, 140)
                )
                avatar_img_label.configure(image=new_img, text="")
                dialog.avatar_img = new_img

        ctk.CTkButton(
            avatar_box,
            text="📁 Đổi ảnh",
            width=120,
            command=choose_avatar
        ).pack(pady=5)

        # ===== INPUT HELPERS =====
        def label(text):
            ctk.CTkLabel(form, text=text, font=("Segoe UI", 12)).pack(anchor="w", pady=(8, 4))

        # ===== HỌ TÊN =====
        label("Họ tên:")
        name_entry = ctk.CTkEntry(form)
        name_entry.insert(0, student["name"])
        name_entry.pack(fill="x")

        # ===== LỚP =====
        label("Lớp:")
        class_entry = ctk.CTkEntry(form)
        class_entry.insert(0, student["class_name"])
        class_entry.pack(fill="x")

        # ===== GIỚI TÍNH =====
        label("Giới tính:")
        gender_var = ctk.StringVar(value=student["gender"])
        gf = ctk.CTkFrame(form, fg_color="transparent")
        gf.pack(anchor="w", pady=(0, 5))
        ctk.CTkRadioButton(gf, text="Nam", variable=gender_var, value="Nam").pack(side="left", padx=10)
        ctk.CTkRadioButton(gf, text="Nữ", variable=gender_var, value="Nữ").pack(side="left", padx=10)

        # ===== NGÀY SINH =====
        label("Ngày sinh:")
        date_row = ctk.CTkFrame(form, fg_color="transparent")
        date_row.pack(anchor="w")

        date_var = ctk.StringVar(value=student["birthday"])

        date_entry = ctk.CTkEntry(
            date_row,
            textvariable=date_var,
            width=220,
            height=38
        )
        date_entry.pack(side="left")

        def open_calendar():
            cal = ctk.CTkToplevel(dialog)
            cal.title("Chọn ngày")
            cal.geometry("250x190")
            cal.grab_set()

            cal_widget = Calendar(cal, date_pattern="yyyy-mm-dd")
            cal_widget.pack(padx=10, pady=10)

            def select():
                date_var.set(cal_widget.get_date())
                cal.destroy()

            ctk.CTkButton(cal, text="Chọn", command=select).pack(pady=5)

        ctk.CTkButton(
            date_row,
            text="📅",
            width=40,
            height=38,
            command=open_calendar
        ).pack(side="left", padx=5)

        # ===== BUTTON =====
        btn_frame = ctk.CTkFrame(bg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)

        def save():
            name = name_entry.get().strip()
            cls = class_entry.get().strip()
            gender = gender_var.get()
            birthday = date_var.get()
            avatar_src = avatar_path["value"]

            if not name or not cls:
                messagebox.showwarning("Cảnh báo", "Họ tên và lớp không được để trống!")
                return

            ok, msg = database.update_student(
                student_id,
                name,
                cls,
                gender,
                birthday
            )
            if not ok:
                messagebox.showerror("Lỗi", msg)
                return

            if avatar_src:
                avatar_dir = os.path.join(os.path.dirname(__file__), "student_avatars")
                os.makedirs(avatar_dir, exist_ok=True)

                ext = os.path.splitext(avatar_src)[1]
                filename = f"profile_{uuid.uuid4().hex}{ext}"
                dest = os.path.join(avatar_dir, filename)

                try:
                    shutil.copy2(avatar_src, dest)
                    database.update_student_profile_avatar(
                        student_id,
                        f"student_avatars/{filename}"
                    )
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Lưu ảnh thất bại:\n{e}")
                    return

            messagebox.showinfo("Thành công", "Cập nhật học sinh thành công!")
            dialog.destroy()
            self.load_students()

        ctk.CTkButton(
            btn_frame,
            text="💾 Lưu",
            fg_color="#0A8F8D",
            command=save
        ).pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(
            btn_frame,
            text="✖ Hủy",
            fg_color="#e73a0f",
            command=dialog.destroy
        ).pack(side="left", padx=10, fill="x", expand=True)


# ==================================================
        # ================= DELETE =================
    def delete_student(self, student_id):
        student = database.get_student_by_id(student_id)
        if not student:
            messagebox.showerror("Lỗi", "Không tìm thấy học sinh")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Xóa học sinh")
        dialog.geometry("400x550")
        dialog.grab_set()

        # ===== TITLE =====
        ctk.CTkLabel(dialog, text="⚠️ XÁC NHẬN XÓA HỌC SINH", font=("Segoe UI", 16, "bold"), text_color="#e73a0f").pack(pady=15)
           # ===== SUBTITLE =====
        ctk.CTkLabel(dialog, text="Hành động này sẽ xóa các dữ liệu liên quan khác của học sinh này", font=("Segoe UI", 10), text_color="#ff6b35").pack(pady=(0, 10))

        # ===== AVATAR HỌC SINH =====
        avatar_path = student.get("profile_avatar_url")

        avatar_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        avatar_frame.pack(pady=(5, 10))

        if avatar_path and os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path)
                avatar_img = ctk.CTkImage(light_image=img, size=(120, 120))
                avatar_label = ctk.CTkLabel(avatar_frame, image=avatar_img, text="")
                avatar_label.pack()
                # giữ reference để không bị mất ảnh
                dialog.avatar_img = avatar_img
            except Exception:
                ctk.CTkLabel(
                    avatar_frame,
                    text="(Không thể tải ảnh hồ sơ)",
                    text_color="#888"
                ).pack()
        else:
            ctk.CTkLabel(
                avatar_frame,
                text="(Chưa có ảnh hồ sơ)",
                text_color="#888"
            ).pack()
        info_frame = ctk.CTkFrame(dialog, fg_color="#ffe6e6", corner_radius=10)
        info_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Hiển thị thông tin học sinh
                # Hiển thị thông tin học sinh
        ctk.CTkLabel(info_frame, text="Thông tin học sinh:", font=("Segoe UI", 12, "bold"), text_color="#000000").pack(anchor="w", padx=15, pady=(15, 5))

        # Sử dụng grid để căn chỉnh thẳng hàng
        info_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_grid.pack(fill="x", padx=15, pady=10)

        # Row 1: ID
        ctk.CTkLabel(info_grid, text="ID:", font=("Segoe UI", 11, "bold"), text_color="#000000").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ctk.CTkLabel(info_grid, text=str(student['student_id']), font=("Segoe UI", 11), text_color="#000000").grid(row=0, column=1, sticky="w")

        # Row 2: Họ tên
        ctk.CTkLabel(info_grid, text="Họ tên:", font=("Segoe UI", 11, "bold"), text_color="#000000").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        ctk.CTkLabel(info_grid, text=student['name'], font=("Segoe UI", 11), text_color="#000000").grid(row=1, column=1, sticky="w", pady=(5, 0))

        # Row 3: Lớp
        ctk.CTkLabel(info_grid, text="Lớp:", font=("Segoe UI", 11, "bold"), text_color="#000000").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        ctk.CTkLabel(info_grid, text=student['class_name'], font=("Segoe UI", 11), text_color="#000000").grid(row=2, column=1, sticky="w", pady=(5, 0))

        # Row 4: Giới tính
        ctk.CTkLabel(info_grid, text="Giới tính:", font=("Segoe UI", 11, "bold"), text_color="#000000").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        ctk.CTkLabel(info_grid, text=student['gender'], font=("Segoe UI", 11), text_color="#000000").grid(row=3, column=1, sticky="w", pady=(5, 0))

        # Row 5: Ngày sinh
        ctk.CTkLabel(info_grid, text="Ngày sinh:", font=("Segoe UI", 11, "bold"), text_color="#000000").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        birthday_text = student['birthday'].strftime('%Y-%m-%d') if student['birthday'] else 'Chưa cập nhật'
        ctk.CTkLabel(info_grid, text=birthday_text, font=("Segoe UI", 11), text_color="#000000").grid(row=4, column=1, sticky="w", pady=(5, 0))

        # ===== BUTTONS =====
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=20)

        def confirm_delete():
            ok, msg = database.delete_student(student_id)
            if ok:
                messagebox.showinfo("Thành công", msg)
                dialog.destroy()
                self.load_students()
            else:
                messagebox.showerror("Lỗi", f"Xóa thất bại:\n{msg}")

        ctk.CTkButton(
            button_frame,
            text="✖ XÓA",
            command=confirm_delete,
            fg_color="#e73a0f",
            hover_color="#971A1A",
            text_color="#ffffff"
        ).pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(
            button_frame,
            text="← Hủy",
            command=dialog.destroy,
            fg_color="#9093EC",
            text_color="#ffffff"
        ).pack(side="left", padx=10, fill="x", expand=True)

    # ==================================================
    def _fmt_date(self, d):
        return d.strftime("%Y-%m-%d") if d else ""

    def _fmt_datetime(self, d):
        return d.strftime("%Y-%m-%d %H:%M") if d else ""