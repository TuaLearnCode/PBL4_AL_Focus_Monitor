import customtkinter as ctk
from tkinter import ttk, messagebox
import database
from datetime import datetime

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ChiTietFrame(ctk.CTkFrame):
    """
    Màn hình chi tiết buổi học
    Giao diện đồng bộ với HocSinhFrame
    """

    def __init__(self, parent, user_info, seasion_id, on_navigate):
        super().__init__(parent, fg_color="#ffffff")
        self.pack(fill="both", expand=True)

        self.parent = parent
        self.user_info = user_info
        self.seasion_id = seasion_id
        self.on_navigate = on_navigate
        self.seasion_info = None

        self.create_widgets()
        self.load_session_info()
        self.load_focus_records()

    # ==================================================
    # UI
    # ==================================================
    def create_widgets(self):

        # ================= HEADER =================
        header = ctk.CTkFrame(self, height=80, fg_color="#aeeee0", corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header,
            text="← Quay lại",
            width=100,
            fg_color="#9A9CE9",
            text_color="#ffffff",
            command=lambda: self.on_navigate("lichsu")
        ).place(x=20, rely=0.5, anchor="w")

        self.title_label = ctk.CTkLabel(
            header,
            text="CHI TIẾT BUỔI HỌC",
            font=("Segoe UI", 20, "bold"),
            text_color="#ef4385"
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")

        # ================= INFO CARD =================
        info_card = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=16)
        info_card.pack(fill="x", padx=20, pady=(20, 10))

        info_grid = ctk.CTkFrame(info_card, fg_color="transparent")
        info_grid.pack(padx=20, pady=15)

        labels = [
            "ID buổi học:",
            "Lớp:",
            "Thời gian bắt đầu:",
            "Thời gian kết thúc:",
            "Ngày tạo:"
        ]

        self.info_labels = {}

        for i, text in enumerate(labels):
            ctk.CTkLabel(
                info_grid,
                text=text,
                font=("Segoe UI", 13, "bold"),
                text_color="#34495e"
            ).grid(row=i, column=0, sticky="w", padx=(0, 20), pady=6)

            value = ctk.CTkLabel(
                info_grid,
                text="Đang tải...",
                font=("Segoe UI", 13),
                text_color="#2c3e50"
            )
            value.grid(row=i, column=1, sticky="w", pady=6)

            self.info_labels[text] = value

        # ================= TOOLBAR =================
        toolbar = ctk.CTkFrame(self, height=55, fg_color="#a3dcef")
        toolbar.pack(fill="x", padx=20, pady=10)
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar,
            text="Danh sách điểm danh & đánh giá tập trung",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            toolbar,
            text="🔄 Làm mới",
            width=120,
            fg_color="#64c4c3",
            text_color="#000000",
            command=self.load_focus_records
        ).pack(side="right", padx=20)

        # ================= TABLE =================
        table_frame = ctk.CTkFrame(self, fg_color="#ffffff")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = (
            "STT", "Tên học sinh", "Lớp",
            "Có mặt", "Điểm tập trung", "Đánh giá", "Ghi chú"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("STT", width=20)
        self.tree.column("Tên học sinh", width=220, anchor="w")
        self.tree.column("Lớp", width=100)
        self.tree.column("Có mặt", width=80)
        self.tree.column("Điểm tập trung", width=120)
        self.tree.column("Đánh giá", width=120)
        self.tree.column("Ghi chú", width=260, anchor="w")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 18), rowheight=45)
        style.configure("Treeview.Heading", font=("Segoe UI", 20, "bold"))

        self.tree.tag_configure("present", background="#d5f4e6")
        self.tree.tag_configure("absent", background="#fadbd8")
        self.tree.tag_configure("odd", background="#f6f8fa")
        self.tree.tag_configure("even", background="#ffffff")

        # ================= STATS =================
        stats = ctk.CTkFrame(self, height=55, fg_color="#a3dcef")
        stats.pack(fill="x", padx=20, pady=(5, 20))
        stats.pack_propagate(False)

        self.total_label = ctk.CTkLabel(stats, text="Tổng: 0", font=("Segoe UI", 13, "bold"))
        self.total_label.pack(side="left", padx=20)

        self.present_label = ctk.CTkLabel(stats, text="Có mặt: 0", font=("Segoe UI", 13, "bold"), text_color="#27ae60")
        self.present_label.pack(side="left", padx=20)

        self.absent_label = ctk.CTkLabel(stats, text="Vắng: 0", font=("Segoe UI", 13, "bold"), text_color="#e74c3c")
        self.absent_label.pack(side="left", padx=20)

        self.avg_label = ctk.CTkLabel(stats, text="Điểm TB: 0", font=("Segoe UI", 13, "bold"), text_color="#3498db")
        self.avg_label.pack(side="right", padx=20)

    # ==================================================
    # DATA
    # ==================================================
    def load_session_info(self):
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT seasion_id, class_name, start_time, end_time, created_at
                FROM seasion WHERE seasion_id = %s
            """, (self.seasion_id,))

            self.seasion_info = cursor.fetchone()
            cursor.close()
            conn.close()

            if not self.seasion_info:
                messagebox.showerror("Lỗi", "Không tìm thấy buổi học!")
                self.on_navigate("lichsu")
                return

            self.info_labels["ID buổi học:"].configure(text=str(self.seasion_info["seasion_id"]))
            self.info_labels["Lớp:"].configure(text=self.seasion_info["class_name"])

            self.info_labels["Thời gian bắt đầu:"].configure(
                text=self._fmt(self.seasion_info["start_time"])
            )
            self.info_labels["Thời gian kết thúc:"].configure(
                text=self._fmt(self.seasion_info["end_time"])
            )
            self.info_labels["Ngày tạo:"].configure(
                text=self._fmt(self.seasion_info["created_at"])
            )

            self.title_label.configure(
                text=f"CHI TIẾT BUỔI HỌC - {self.seasion_info['class_name']}"
            )

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải thông tin:\n{e}")

    def load_focus_records(self):
        self.tree.delete(*self.tree.get_children())

        try:
            conn = database.get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT fr.appear, fr.focus_point, fr.rate, fr.note,
                       s.name, s.class_name
                FROM focus_record fr
                JOIN student s ON fr.student_id = s.student_id
                WHERE fr.seasion_id = %s
                ORDER BY s.name
            """, (self.seasion_id,))

            records = cursor.fetchall()
            cursor.close()
            conn.close()

            total = len(records)
            present = sum(1 for r in records if r["appear"])
            absent = total - present
            avg = sum(r["focus_point"] for r in records if r["appear"]) / present if present else 0

            for i, r in enumerate(records, start=1):
                tag = "present" if r["appear"] else "absent"
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        i, r["name"], r["class_name"],
                        "✓" if r["appear"] else "✗",
                        r["focus_point"], r["rate"],
                        r["note"] or ""
                    ),
                    tags=(tag,)
                )

            self.total_label.configure(text=f"Tổng: {total}")
            self.present_label.configure(text=f"Có mặt: {present}")
            self.absent_label.configure(text=f"Vắng: {absent}")
            self.avg_label.configure(text=f"Điểm TB: {avg:.1f}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu:\n{e}")

    # ==================================================
    def _fmt(self, dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
