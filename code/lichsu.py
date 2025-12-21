import customtkinter as ctk
from tkinter import ttk, messagebox
import database
from datetime import datetime
from tkcalendar import Calendar

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class LichSuFrame(ctk.CTkFrame):
    """
    Lịch sử các buổi học – có:
    - Cột Thời lượng
    - Lọc theo khoảng thời gian
    """

    def __init__(self, parent, user_info, on_navigate, on_view_detail):
        super().__init__(parent, fg_color="#ffffff")
        self.pack(fill="both", expand=True)

        self.user_info = user_info
        self.on_navigate = on_navigate
        self.on_view_detail = on_view_detail

        self.create_widgets()
        self.load_sessions()

    # ==================================================
    def create_widgets(self):

        # ================= HEADER =================
        header = ctk.CTkFrame(self, height=90, corner_radius=0, fg_color="#aeeee0")
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header,
            text="← Quay lại",
            width=90,
            fg_color="#6A6EEF",
            command=lambda: self.on_navigate("home")
        ).place(x=15, rely=0.5, anchor="w")

        ctk.CTkLabel(
            header,
            text="LỊCH SỬ CÁC BUỔI HỌC",
            font=("Segoe UI", 20, "bold"),
            text_color="#ef4385"
        ).place(relx=0.5, rely=0.2, anchor="center")

        # ===== FILTER DATE =====
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.place(relx=0.5, rely=0.65, anchor="center")

        self.from_date_var = ctk.StringVar()
        self.to_date_var = ctk.StringVar()

        def date_picker(parent, var):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            entry = ctk.CTkEntry(row, textvariable=var, width=140, height=32)
            entry.pack(side="left")

            def open_calendar():
                cal = ctk.CTkToplevel(self)
                cal.title("Chọn ngày")
                cal.geometry("250x190")
                cal.grab_set()

                cal_widget = Calendar(cal, date_pattern="yyyy-mm-dd")
                cal_widget.pack(padx=10, pady=10)

                def select():
                    var.set(cal_widget.get_date())
                    cal.destroy()

                ctk.CTkButton(cal, text="Chọn", command=select).pack(pady=5)

            ctk.CTkButton(row, text="📅", width=32, command=open_calendar).pack(side="left", padx=5)
            return row

        ctk.CTkLabel(filter_frame, text="Từ:").pack(side="left", padx=5)
        date_picker(filter_frame, self.from_date_var).pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Đến:").pack(side="left", padx=5)
        date_picker(filter_frame, self.to_date_var).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="🔍 Lọc",
            fg_color="#28a745",
            width=70,
            command=self.filter_by_date
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            filter_frame,
            text="✖ Reset",
            fg_color="#e73a0f",
            width=80,
            command=self.reset_filter
        ).pack(side="left")

        # ================= TABLE =================
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        columns = ("ID", "Lớp", "Bắt đầu", "Kết thúc", "Thời lượng", "👁 Xem", "🗑 Xóa")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=40)
        self.tree.column("Lớp", width=180, anchor="w")
        self.tree.column("Bắt đầu", width=170)
        self.tree.column("Kết thúc", width=170)
        self.tree.column("Thời lượng", width=170)
        self.tree.column("👁 Xem", width=80)
        self.tree.column("🗑 Xóa", width=80)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", rowheight=50, font=("Segoe UI", 18))
        style.configure("Treeview.Heading", font=("Segoe UI", 20, "bold"))

        self.tree.tag_configure("even", background="#ffcdaa")
        self.tree.tag_configure("odd", background="#ee897f")

        self.tree.bind("<Button-1>", self.on_tree_click)

        self.stats_label = ctk.CTkLabel(self, text="Tổng số buổi học: 0", font=("Segoe UI", 14, "bold"), fg_color="#aeeee0")
        self.stats_label.pack(anchor="e", padx=30, pady=(0, 10))

    # ==================================================
    def load_sessions(self, where_sql="", params=()):
        self.tree.delete(*self.tree.get_children())

        conn = database.get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"""
            SELECT seasion_id, class_name, start_time, end_time
            FROM seasion
            {where_sql}
            ORDER BY start_time DESC
        """, params)

        rows = cursor.fetchall()

        for i, s in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "",
                "end",
                values=(
                    s["seasion_id"],
                    s["class_name"],
                    self._fmt(s["start_time"]),
                    self._fmt(s["end_time"]),
                    self._duration(s["start_time"], s["end_time"]),
                    "👁 Xem",
                    "🗑 Xóa"
                ),
                tags=(tag,)
            )

        self.stats_label.configure(text=f"Tổng số buổi học: {len(rows)}")

        cursor.close()
        conn.close()

    # ==================================================
    def filter_by_date(self):
        f = self.from_date_var.get()
        t = self.to_date_var.get()

        if not f or not t:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn đủ từ ngày và đến ngày")
            return

        self.load_sessions(
            "WHERE start_time BETWEEN %s AND %s",
            (f + " 00:00:00", t + " 23:59:59")
        )

    def reset_filter(self):
        self.from_date_var.set("")
        self.to_date_var.set("")

        self.load_sessions()

    # ==================================================
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row:
            return

        seasion_id, class_name = self.tree.item(row)["values"][:2]

        if col == "#6":
            self.on_view_detail(seasion_id)

        elif col == "#7":
            if messagebox.askyesno(
                "Xác nhận",
                f"Xóa buổi học ID {seasion_id} - Lớp {class_name}?"
            ):
                self._delete_session(seasion_id)

    # ==================================================
    def _delete_session(self, seasion_id):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM seasion WHERE seasion_id = %s", (seasion_id,))
        conn.commit()
        cursor.close()
        conn.close()
        self.load_sessions()

    # ==================================================
    def _fmt(self, dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""

    def _duration(self, start, end):
        if not start or not end:
            return ""
        delta = end - start
        total = int(delta.total_seconds())

        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60

        if h > 0:
            return f"{h} giờ {m} phút {s} giây"
        if m > 0:
            return f"{m} phút {s} giây"
        return f"{s} giây"
