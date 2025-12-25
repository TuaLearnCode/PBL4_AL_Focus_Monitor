from tkcalendar import Calendar
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import database
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import customtkinter as ctk
import csv
import os
from datetime import datetime

# ======================= GLOBAL CONFIG =======================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ThongKeFrame(ctk.CTkFrame):
    """
    Màn hình thống kê học sinh
    """
    def __init__(self, parent, user_info, on_navigate):
        super().__init__(parent, fg_color="#ffffff")
        self.pack(fill="both", expand=True)

        self.user_info = user_info
        self.on_navigate = on_navigate

        self.current_class = "A"   # ⭐ MẶC ĐỊNH LỚP A

        self.create_widgets()


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
            fg_color="#767AF1",
            command=lambda: self.on_navigate("home")
        ).place(x=20, rely=0.5, anchor="w")

        ctk.CTkLabel(
            header,
            text="THỐNG KÊ",
            text_color="#ef4385",
            font=("Segoe UI", 20, "bold")
        ).place(relx=0.5, rely=0.5, anchor="center")

        # === TABS (CustomTkinter) ===
        self.tabview = ctk.CTkTabview(
            self,
            height=700,                 # ⬅ tăng chiều cao toàn bộ tab
            corner_radius=10,
            fg_color="#eaf7f6",
            segmented_button_fg_color="#5cc5c3",
            segmented_button_selected_color="#f8f8f8",
            segmented_button_selected_hover_color="#8fdbd7",
            segmented_button_unselected_color="#64c4c3",
            segmented_button_unselected_hover_color="#6bb7b3",
        )
        # 👉 Làm tab cao hơn
        self.tabview._segmented_button.configure(height=70)
        self.tabview._segmented_button.configure(
            text_color="#D61818",              # chữ tab chưa chọn
            text_color_disabled="#E12323",     # phòng khi bị disable
        )
        # Tab 1: Thống kê học sinh
        self.student_tab = self.tabview.add("📚 Thống kê học sinh")

        # Tab 2: Thống kê buổi học
        self.session_tab = self.tabview.add("📅 Thống kê buổi học")
       
        self.create_student_tab()
        self.create_session_tab()
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(5, 5))


    def create_student_tab(self):
        """Tạo giao diện tab thống kê học sinh (CustomTkinter)"""

        # === FILTER FRAME ===
        filter_frame = ctk.CTkFrame(
            self.student_tab,
            fg_color="#ffffff",
            corner_radius=12
        )
        filter_frame.pack(fill="x", padx=10, pady=5)

        # ===== ROW 1 =====
        row1 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(10, 5))

        # ===== DATE FILTER (TỪ - ĐẾN) =====
        ctk.CTkLabel(row1, text="Từ:", font=("Segoe UI", 14, "bold")).pack(
            side="left", padx=(0, 5)
        )

        self.from_date_var = ctk.StringVar()
        self.to_date_var = ctk.StringVar()

        def date_picker(parent, var):
            row = ctk.CTkFrame(parent, fg_color="transparent")

            entry = ctk.CTkEntry(
                row,
                textvariable=var,
                width=130,
                height=32
            )
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

            ctk.CTkButton(
                row,
                text="📅",
                width=32,
                command=open_calendar
            ).pack(side="left", padx=5)

            return row

        date_picker(row1, self.from_date_var).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(row1, text="Đến:", font=("Segoe UI", 14, "bold")).pack(
            side="left", padx=(0, 5)
        )

        date_picker(row1, self.to_date_var).pack(side="left", padx=(0, 20))

        # ===== BUTTONS =====
        ctk.CTkButton(
            row1,
            text="🔍 Lọc",
            width=70,
            fg_color="#28a745",
            text_color="#000000",
            command=self.filter_by_date
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            row1,
            text="🔄 Làm mới",
            width=80,
            fg_color="#c5ef2f",
            text_color="#000000",
            command=self.reset_filter
        ).pack(side="left")

        # ===== ROW 2 =====
        row2 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(row2, text="🔍 Tìm kiếm học sinh:", font=("Segoe UI", 12, "bold")).pack(
            side="left", padx=(0, 8)
        )

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.on_search_change())

        self.search_entry = ctk.CTkEntry(
            row2,
            width=220,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            row2,
            text="✕",
            width=40,
            fg_color="#e74c3c",
            text_color="#000000",
            command=self.clear_search
        ).pack(side="left")

        # === MAIN CONTENT ===
        main_frame = ctk.CTkFrame(self.student_tab, fg_color="transparent")
        main_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        self.student_tab.grid_rowconfigure(0, weight=1)
        self.student_tab.grid_columnconfigure(0, weight=1)

        main_frame.grid_columnconfigure(0, weight=1, uniform="group")
        main_frame.grid_columnconfigure(1, weight=1, uniform="group")
        main_frame.grid_rowconfigure(0, weight=1)
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5)
        )

        right_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 0)
        )

        # === TOP STUDENTS ===
        top_frame = ctk.CTkFrame(left_frame, fg_color="#efb9b9", corner_radius=12)
        top_frame.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(
            top_frame,
            text="🏆 TOP HỌC SINH XUẤT SẮC",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        tree_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("rank", "name", "sessions", "avg_focus", "attendance_count")
        self.top_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

                # ==== TĂNG KÍCH THƯỚC CHỮ + DÒNG ====
        style = ttk.Style()
        style.configure(
            "Treeview",
            font=("Segoe UI", 14),     # chữ to hơn
            rowheight=30               # chiều cao mỗi dòng
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 13, "bold")
        )

        self.top_tree.configure(style="Treeview")

        self.top_tree.heading("rank", text="Hạng")
        self.top_tree.heading("name", text="Họ tên")
        self.top_tree.heading("sessions", text="Số buổi")
        self.top_tree.heading("avg_focus", text="Điểm TB")
        self.top_tree.heading("attendance_count", text="Có mặt")

        self.top_tree.column("rank", width=10, anchor="center")
        self.top_tree.column("name", width=120, anchor="w")
        self.top_tree.column("sessions", width=20, anchor="center")
        self.top_tree.column("avg_focus", width=30, anchor="center")
        self.top_tree.column("attendance_count", width=30, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.top_tree.yview)
        self.top_tree.configure(yscrollcommand=scrollbar.set)

        self.top_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.all_students = []

        # === STATS ===
        stats_frame = ctk.CTkFrame(left_frame, fg_color="#e7b0b0", corner_radius=12)
        stats_frame.pack(fill="x")

        ctk.CTkLabel(
            stats_frame,
            text="📈 THỐNG KÊ TỔNG QUAN",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        self.stats_text = ctk.CTkTextbox(
            stats_frame,
            height=200,
            font=("Segoe UI", 11)
        )
        self.stats_text.pack(fill="x", padx=10, pady=(0, 10))
        self.stats_text.configure(state="disabled")

        # === CHART ===
        chart_frame = ctk.CTkFrame(right_frame, fg_color="#ffffff", corner_radius=12)
        chart_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            chart_frame,
            text="📊 BIỂU ĐỒ PHÂN BỐ MỨC ĐỘ TẬP TRUNG",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        self.chart_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
       
        today = datetime.now().date().strftime("%Y-%m-%d")
        self.from_date_var.set(today)
        self.to_date_var.set(today)

    def update_student_stats(self, total_students, total_sessions, avg_focus):
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")

        content = (
            f"👩‍🎓 Tổng số học sinh: {total_students}\n"
            f"📚 Tổng số buổi học: {total_sessions}\n"
            f"🎯 Điểm tập trung trung bình: {avg_focus:.2f}\n"
        )

        self.stats_text.insert("end", content)
        self.stats_text.configure(state="disabled")


    # --- Thay thế / chèn vào class của bạn ---

    def create_session_tab(self):
        """Tạo giao diện tab thống kê buổi học (sửa lỗi packing/scrollbar + style)"""

        self.session_from_date_var = ctk.StringVar()
        self.session_to_date_var = ctk.StringVar()

        today = datetime.now().strftime("%Y-%m-%d")
        self.session_from_date_var.set(today)
        self.session_to_date_var.set(today)

        # ================= FILTER FRAME =================
        filter_frame = ctk.CTkFrame(self.session_tab, fg_color="#ffffff", corner_radius=12)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # ---------- ROW 1 ----------
        row1 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(row1, text="Từ:", font=("Segoe UI", 14, "bold")).pack(side="left", padx=(0, 5))

        def date_picker(parent, var):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            entry = ctk.CTkEntry(row, textvariable=var, width=130, height=32)
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

        date_picker(row1, self.session_from_date_var).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(row1, text="Đến:", font=("Segoe UI", 14, "bold")).pack(side="left", padx=(0, 5))
        date_picker(row1, self.session_to_date_var).pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            row1,
            text="🔍 Lọc",
            width=70,
            fg_color="#28a745",
            text_color="#000000",
            command=self.on_session_filter_change
        ).pack(side="left", padx=(5, 5))

        ctk.CTkLabel(row1, text="Sắp xếp:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 8))

        self.sort_combo = ctk.CTkComboBox(
            row1,
            width=200,
            values=[
                "Thời gian mới nhất",
                "Thời gian cũ nhất",
                "Điểm TB cao nhất",
                "Điểm TB thấp nhất"
            ],
            command=lambda _: self.on_session_filter_change()
        )
        self.sort_combo.set("Thời gian mới nhất")
        self.sort_combo.pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            row1,
            text="🔄 Làm mới",
            width=90,
            fg_color="#c5ef2f",
            text_color="#000000",
            command=self.on_session_filter_change
        ).pack(side="left")

        # ================= MAIN CONTENT =================
        main_frame = ctk.CTkFrame(self.session_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # QUAN TRỌNG
        main_frame.grid_columnconfigure(0, weight=1, uniform="stats")
        main_frame.grid_columnconfigure(1, weight=1, uniform="stats")
        main_frame.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")

        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # ================= LEFT: DANH SÁCH BUỔI HỌC =================
        session_frame = ctk.CTkFrame(left_frame, fg_color="#efb9b9", corner_radius=12)
        session_frame.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(
            session_frame,
            text="📅 DANH SÁCH BUỔI HỌC",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        tree_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("date", "time", "total", "present", "avg", "rating")
        self.session_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        # tạo style riêng (không đè style treeview khác)
        session_style = ttk.Style()
        session_style.configure("Session.Treeview", font=("Segoe UI", 13), rowheight=32)
        session_style.configure("Session.Treeview.Heading", font=("Segoe UI", 13, "bold"))

        self.session_tree.configure(style="Session.Treeview")

        self.session_tree.heading("date", text="Ngày")
        self.session_tree.heading("time", text="Thời gian")
        self.session_tree.heading("total", text="Sĩ số")
        self.session_tree.heading("present", text="Có mặt")
        self.session_tree.heading("avg", text="Điểm TB")
        self.session_tree.heading("rating", text="Đánh giá")

        self.session_tree.column("date", width=110, anchor="center")
        self.session_tree.column("time", width=130, anchor="center")
        self.session_tree.column("total", width=80, anchor="center")
        self.session_tree.column("present", width=80, anchor="center")
        self.session_tree.column("avg", width=90, anchor="center")
        self.session_tree.column("rating", width=120, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.session_tree.yview)
        self.session_tree.configure(yscrollcommand=scrollbar.set)

        # IMPORTANT: pack tree để fill cả diện tích (trước đây chỉ fill x dẫn đến bảng rất nhỏ)
        self.session_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # binding double-click (ví dụ mở chi tiết buổi)
        self.session_tree.bind("<Double-1>", self.on_session_double_click)

        # ================= STATS =================
        stats_frame = ctk.CTkFrame(left_frame, fg_color="#e7b0b0", corner_radius=12)
        stats_frame.pack(fill="x")

        ctk.CTkLabel(
            stats_frame,
            text="📈 THỐNG KÊ TỔNG QUAN",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        self.session_stats_text = ctk.CTkTextbox(
            stats_frame,
            height=160,
            font=("Segoe UI", 11)
        )
        self.session_stats_text.pack(fill="x", padx=10, pady=(0, 10))
        self.session_stats_text.configure(state="disabled")

        # ================= RIGHT: CHART =================
        chart_frame = ctk.CTkFrame(right_frame, fg_color="#ffffff", corner_radius=12)
        chart_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            chart_frame,
            text="📊 BIỂU ĐỒ PHÂN BỐ MỨC ĐỘ",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        self.session_chart_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self.session_chart_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # load data ban đầu
        self.on_session_filter_change()


    def on_session_double_click(self, event):
        """Ví dụ hiển thị chi tiết khi double-click một row"""
        item = self.session_tree.selection()
        if not item:
            return
        vals = self.session_tree.item(item[0], "values")
        # Bạn có thể mở modal hiển thị chi tiết; ở đây tạm show messagebox
        try:
            date, time, total, present, avg, rating = vals
            messagebox.showinfo("Chi tiết buổi",
                f"Ngày: {date}\nThời gian: {time}\nSĩ số: {total}\nCó mặt: {present}\nĐiểm TB: {avg}\nĐánh giá: {rating}"
            )
        except Exception:
            pass


    def on_session_filter_change(self):
        """Được gọi khi user bấm Lọc / Làm mới / đổi sort"""
        from_date = self.session_from_date_var.get()
        to_date = self.session_to_date_var.get()
        sort_by = self.sort_combo.get() if hasattr(self, "sort_combo") else "Thời gian mới nhất"

        # validate cơ bản
        if not from_date or not to_date:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đủ Từ ngày và Đến ngày")
            return

        # gọi load_sessions (thực tế thay bằng truy vấn DB)
        self.load_sessions(from_date, to_date, sort_by)


    def load_sessions(self, from_date, to_date, sort_by):
        """
        Hàm mock: tải danh sách buổi học theo from/to và sắp xếp.
        Thay phần này bằng query CSDL của bạn.
        """

        # ---- MOCK DATA ----
        # Thực tế: lấy từ DB theo where date between from_date and to_date
        mock = [
            {"date":"2025-12-25","time":"08:00-09:00","total":32,"present":30,"avg":7.8,"rating":"Tốt"},
            {"date":"2025-12-24","time":"10:00-11:00","total":32,"present":28,"avg":6.5,"rating":"Khá"},
            {"date":"2025-12-23","time":"13:00-14:00","total":32,"present":31,"avg":8.2,"rating":"Rất tốt"},
            # ... thêm dữ liệu thử nếu cần
        ]

        # lọc theo khoảng ngày (nếu cần convert)
        try:
            fd = datetime.strptime(from_date, "%Y-%m-%d").date()
            td = datetime.strptime(to_date, "%Y-%m-%d").date()
            filtered = []
            for s in mock:
                d = datetime.strptime(s["date"], "%Y-%m-%d").date()
                if fd <= d <= td:
                    filtered.append(s)
        except Exception:
            filtered = mock[:]  # nếu parse lỗi thì trả hết

        # sắp xếp
        if sort_by == "Thời gian mới nhất":
            filtered.sort(key=lambda x: (x["date"], x["time"]), reverse=True)
        elif sort_by == "Thời gian cũ nhất":
            filtered.sort(key=lambda x: (x["date"], x["time"]))
        elif sort_by == "Điểm TB cao nhất":
            filtered.sort(key=lambda x: float(x["avg"]), reverse=True)
        elif sort_by == "Điểm TB thấp nhất":
            filtered.sort(key=lambda x: float(x["avg"]))
        else:
            filtered.sort(key=lambda x: (x["date"], x["time"]), reverse=True)

        # cập nhật Treeview
        for r in self.session_tree.get_children():
            self.session_tree.delete(r)

        for i, s in enumerate(filtered, start=1):
            self.session_tree.insert("", "end", values=(
                s["date"], s["time"], s["total"], s["present"], f"{s['avg']:.2f}", s["rating"]
            ))

        # cập nhật thống kê tóm tắt
        total_sessions = len(filtered)
        avg_focus = sum([float(s["avg"]) for s in filtered]) / total_sessions if total_sessions > 0 else 0.0
        self.update_session_stats(total_sessions, avg_focus)


    def update_session_stats(self, total_sessions, avg_focus):
        """Update khung thống kê buổi học"""
        self.session_stats_text.configure(state="normal")
        self.session_stats_text.delete("1.0", "end")
        content = (
            f"📚 Tổng số buổi hiển thị: {total_sessions}\n"
            f"🎯 Điểm tập trung trung bình (khoảng chọn): {avg_focus:.2f}\n"
        )
        self.session_stats_text.insert("end", content)
        self.session_stats_text.configure(state="disabled")



    def load_classes(self,from_date, to_date):
        self.current_class = "A"
            # ví dụ dữ liệu lấy từ DB
        total_students = 32
        total_sessions = 120
        avg_focus = 7.85
        self.load_statistics(
            from_date=self.from_date_var.get(),
            to_date=self.to_date_var.get()
        )
        self.update_student_stats(
            total_students,
            total_sessions,
            avg_focus
        )

    def filter_by_date(self):
        from_date = self.from_date_var.get()
        to_date = self.to_date_var.get()

        if not from_date or not to_date:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đủ Từ ngày và Đến ngày")
            return

        self.load_statistics(from_date, to_date)



    def reset_filter(self):
        today = datetime.now().date().strftime("%Y-%m-%d")
        self.from_date_var.set(today)
        self.to_date_var.set(today)
        self.load_statistics(from_date=today, to_date=today)


    def load_statistics(self, from_date=None, to_date=None):
        """Load dữ liệu thống kê"""
        conn = database.get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)

            # Tính toán khoảng thời gian
            date_filter = ""
            params = [self.current_class]

            if from_date and to_date:
                date_filter = "AND s.start_time BETWEEN %s AND %s"
                params.extend([
                    from_date + " 00:00:00",
                    to_date + " 23:59:59"
                ])

            # Query top học sinh
# --- CHỈNH SỬA QUERY TOP HỌC SINH ---
            # Logic cũ: ELSE NULL (Vắng mặt không bị chia trung bình)
            # Logic mới: ELSE 0 (Vắng mặt tính là 0 điểm và vẫn chia trung bình)
            query_top = f"""
            SELECT 
                st.student_id,
                st.name,
                COUNT(DISTINCT f.seasion_id) as total_sessions,
                ROUND(AVG(CASE WHEN f.appear = 1 THEN f.focus_point ELSE NULL END), 1) as avg_focus, 
                SUM(CASE WHEN f.appear = 1 THEN 1 ELSE 0 END) as attendance_count 
            FROM student st
            LEFT JOIN focus_record f ON st.student_id = f.student_id
            LEFT JOIN seasion s ON f.seasion_id = s.seasion_id
            WHERE st.class_name = %s {date_filter}
            GROUP BY st.student_id, st.name
            ORDER BY avg_focus DESC, attendance_count DESC
            LIMIT 20
            """

            cursor.execute(query_top, params)
            top_students = cursor.fetchall()

            # Lưu danh sách đầy đủ để lọc
            self.all_students = top_students

            # Hiển thị danh sách học sinh
            self.display_top_students(top_students)

            # --- CHỈNH SỬA QUERY THỐNG KÊ TỔNG QUAN ---
            # Cũng áp dụng logic ELSE 0 cho avg_focus_all
            query_stats = f"""
            SELECT 
                COUNT(DISTINCT s.seasion_id) as total_sessions,
                COUNT(DISTINCT st.student_id) as total_students,
                COUNT(CASE WHEN f.appear = 1 THEN 1 END) as total_attendance,
                ROUND(AVG(CASE WHEN f.appear = 1 THEN f.focus_point ELSE 0 END), 1) as avg_focus_all,
                COUNT(CASE WHEN f.rate = 'Cao độ' THEN 1 END) as count_cao_do,
                COUNT(CASE WHEN f.rate = 'Tốt' THEN 1 END) as count_tot,
                COUNT(CASE WHEN f.rate = 'Trung bình' THEN 1 END) as count_trung_binh,
                COUNT(CASE WHEN f.rate = 'Thấp' THEN 1 END) as count_thap
            FROM seasion s
            LEFT JOIN focus_record f ON s.seasion_id = f.seasion_id
            LEFT JOIN student st ON f.student_id = st.student_id
            WHERE s.class_name = %s {date_filter}
            """
            cursor.execute(query_stats, params)
            stats = cursor.fetchone()

            # Hiển thị thống kê tổng quan
            self.display_general_stats(stats)

            # Hiển thị biểu đồ
            self.display_chart(stats)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải thống kê: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cursor.close()
            conn.close()

    def display_top_students(self, students):
        """Hiển thị danh sách top học sinh"""
        # Xóa dữ liệu cũ
        for item in self.top_tree.get_children():
            self.top_tree.delete(item)

        # Thêm dữ liệu mới
        for rank, student in enumerate(students, start=1):
            avg_focus = student['avg_focus'] if student['avg_focus'] is not None else 0
            attendance = student['attendance_count'] if student['attendance_count'] is not None else 0

            # Thêm biểu tượng cho top 3
            rank_display = rank
            if rank == 1:
                rank_display = "🥇"
            elif rank == 2:
                rank_display = "🥈"
            elif rank == 3:
                rank_display = "🥉"

            self.top_tree.insert(
                '',
                'end',
                values=(
                    rank_display,
                    student['name'],
                    student['total_sessions'],
                    f"{avg_focus:.1f}",
                    int(attendance)
                ),
                tags=(f"rank_{rank}",)
            )

        # Tô màu cho top 3
        self.top_tree.tag_configure('rank_1', background='#ffd700')
        self.top_tree.tag_configure('rank_2', background='#c0c0c0')
        self.top_tree.tag_configure('rank_3', background='#cd7f32')

    def on_search_change(self, *args):
        """Xử lý khi thay đổi nội dung tìm kiếm"""
        search_text = self.search_var.get().strip().lower()

        if not search_text:
            # Nếu không có từ khóa, hiển thị tất cả
            self.display_top_students(self.all_students)
        else:
            # Lọc học sinh theo tên
            filtered_students = [
                student for student in self.all_students
                if search_text in student['name'].lower()
            ]
            self.display_top_students(filtered_students)

    def clear_search(self):
        """Xóa nội dung tìm kiếm"""
        self.search_var.set('')
        self.search_entry.focus_set()

    def display_general_stats(self, stats):
        period_text = f"{self.from_date_var.get()} → {self.to_date_var.get()}"
        """Hiển thị thống kê tổng quan"""

        self.stats_text.configure(state="normal")
        self.stats_text.delete("0.0", "end")

        if not stats or stats["total_sessions"] == 0:
            self.stats_text.insert("end", "Chưa có dữ liệu trong khoảng thời gian này.")
            self.stats_text.configure(state="disabled")
            return

        total_sessions = stats["total_sessions"] or 0
        total_students = stats["total_students"] or 0
        total_attendance = stats["total_attendance"] or 0
        avg_focus = stats["avg_focus_all"] or 0

        # Tính tỷ lệ có mặt
        if total_sessions > 0 and total_students > 0:
            attendance_count = (total_attendance * 100.0) / (total_sessions * total_students)
        else:
            attendance_count = 0

        stats_content = f"""
    📅 Khoảng thời gian: {period_text}
    🏫 Lớp: {self.current_class}
    📊 Số liệu:
    • Tổng số buổi học: {total_sessions}
    • Tổng số học sinh: {total_students}
    • Tổng lượt có mặt: {total_attendance}
    • Tỷ lệ có mặt trung bình: {attendance_count:.1f}%
    • Điểm tập trung trung bình: {avg_focus:.1f}/100
    🎯 Phân loại mức độ tập trung:
    • Cao độ: {stats['count_cao_do']} lượt
    • Tốt: {stats['count_tot']} lượt
    • Trung bình: {stats['count_trung_binh']} lượt
    • Thấp: {stats['count_thap']} lượt
    """

        self.stats_text.insert("end", stats_content)
        self.stats_text.configure(state="disabled")


    def display_chart(self, stats):
        """Hiển thị biểu đồ phân bố"""

        # Xóa biểu đồ cũ
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        if not stats or stats["total_sessions"] == 0:
            ctk.CTkLabel(
                self.chart_container,
                text="Chưa có dữ liệu để hiển thị biểu đồ",
                font=("Segoe UI", 12, "italic"),
                text_color="#7f8c8d"
            ).pack(expand=True)
            return

        # Dữ liệu biểu đồ
        categories = ["Cao độ", "Tốt", "Trung bình", "Thấp"]
        values = [
            stats["count_cao_do"] or 0,
            stats["count_tot"] or 0,
            stats["count_trung_binh"] or 0,
            stats["count_thap"] or 0
        ]
        colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]

        # Tạo biểu đồ
        fig = Figure(figsize=(6, 4), facecolor="white")
        ax = fig.add_subplot(111)

        bars = ax.bar(
            categories,
            values,
            color=colors,
            alpha=0.85,
            edgecolor="black",
            linewidth=1.2
        )

        # Hiển thị số trên cột
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                str(int(value)),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        ax.set_ylabel("Số lượt", fontsize=11, fontweight="bold")
        ax.set_xlabel("Mức độ tập trung", fontsize=11, fontweight="bold")
        ax.set_title("Phân bố mức độ tập trung", fontsize=12, fontweight="bold", pad=12)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        fig.tight_layout(pad=2)

        # Nhúng vào CustomTkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def on_session_filter_change(self, event=None):
        """Xử lý khi thay đổi bộ lọc của tab buổi học"""
        self.load_session_statistics()

    def load_session_statistics(self, from_date=None, to_date=None):
        """Load thống kê buổi học theo khoảng ngày (mặc định lớp A)"""

        current_class = "A"
        sort_map = {
            "Thời gian mới nhất": "s.start_time DESC",
            "Thời gian cũ nhất": "s.start_time ASC",
            "Điểm TB cao nhất": "avg_score DESC",
            "Điểm TB thấp nhất": "avg_score ASC"
        }
        sort_option = self.sort_combo.get()
        order_by = sort_map.get(sort_option, "s.start_time DESC")

        if not from_date or not to_date:
            from_date = self.session_from_date_var.get()
            to_date = self.session_to_date_var.get()

        conn = database.get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)

            # --- Xây date_filter và date params ---
            date_filter = ""
            date_params = []
            if from_date and to_date:
                date_filter = "AND s.start_time BETWEEN %s AND %s"
                date_params = [from_date + " 00:00:00", to_date + " 23:59:59"]

            # ================== QUERY SESSIONS (params_sessions) ==================
            params_sessions = [current_class] + date_params

            query_sessions = f"""
            SELECT 
                s.seasion_id,
                s.start_time,
                s.end_time,
                (
                    SELECT COUNT(*) 
                    FROM student st 
                    WHERE st.class_name = s.class_name
                ) AS total_students,
                SUM(CASE WHEN f.appear = 1 THEN 1 ELSE 0 END) AS present_count,
                ROUND(AVG(CASE WHEN f.appear = 1 THEN f.focus_point ELSE 0 END), 1) AS avg_score
            FROM seasion s
            LEFT JOIN focus_record f ON f.seasion_id = s.seasion_id 
            WHERE s.class_name = %s {date_filter}
            GROUP BY s.seasion_id
            ORDER BY {order_by}
            """

            cursor.execute(query_sessions, params_sessions)
            sessions = cursor.fetchall()
            self.display_sessions(sessions)

            # ================== QUERY STATS (params_stats) ==================
            # query_stats có 2 chỗ %s cho class_name + có thể có 2 chỗ %s cho date range (ở inner subquery)
            params_stats = [current_class, current_class] + date_params

            query_stats = f"""
            SELECT 
                COUNT(*) AS total_sessions,
                (SELECT COUNT(*) FROM student WHERE class_name = %s) AS total_students,
                ROUND(AVG(session_avg), 1) AS overall_avg,
                SUM(session_avg >= 80) AS excellent_sessions,
                SUM(session_avg BETWEEN 60 AND 79) AS good_sessions,
                SUM(session_avg BETWEEN 40 AND 59) AS average_sessions,
                SUM(session_avg < 40) AS poor_sessions
            FROM (
                SELECT 
                    ROUND(AVG(CASE WHEN f.appear = 1 THEN f.focus_point ELSE 0 END), 1) AS session_avg
                FROM seasion s
                LEFT JOIN focus_record f ON f.seasion_id = s.seasion_id
                WHERE s.class_name = %s {date_filter}
                GROUP BY s.seasion_id
            ) t
            """

            cursor.execute(query_stats, params_stats)
            stats = cursor.fetchone()

            # Hiển thị dữ liệu
            self.display_session_stats(
                stats,
                f"{from_date} → {to_date}",
                current_class
            )

            self.display_session_chart(stats)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải thống kê buổi học:\n{e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                cursor.close()
            except:
                pass
            conn.close()
        
    def reset_session_filter(self):
        today = datetime.now().date().strftime("%Y-%m-%d")
        self.session_from_date_var.set(today)
        self.session_to_date_var.set(today)
        self.load_session_statistics(today, today)

    def display_sessions(self, sessions):
        """Hiển thị danh sách buổi học"""

        # Xóa dữ liệu cũ
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)

        # Thêm dữ liệu mới
        for session in sessions:
            avg_score = session["avg_score"] if session["avg_score"] is not None else 0

            # Đánh giá buổi học dựa trên điểm trung bình
            if avg_score >= 80:
                rating = "Cao độ"
                tag = "excellent"
            elif avg_score >= 60:
                rating = "Tốt"
                tag = "good"
            elif avg_score >= 40:
                rating = "Trung bình"
                tag = "average"
            else:
                rating = "Thấp"
                tag = "poor"

            # Format ngày & thời gian
            if session["start_time"] and session["end_time"]:
                date_str = session["start_time"].strftime("%Y-%m-%d")
                time_str = (
                    f"{session['start_time'].strftime('%H:%M')} - "
                    f"{session['end_time'].strftime('%H:%M')}"
                )
            else:
                date_str = "-"
                time_str = "-"

            # Insert vào Treeview
            # Lưu seasion_id ở iid để tiện mở ChiTietFrame
            self.session_tree.insert(
                "",
                "end",
                iid=str(session["seasion_id"]),
                values=(
                    date_str,
                    time_str,
                    session["total_students"],
                    session["present_count"],
                    f"{avg_score:.1f}",
                    rating
                ),
                tags=(tag,)
            )

        # ===== CẤU HÌNH MÀU THEO MỨC ĐỘ =====
        self.session_tree.tag_configure("excellent", background="#d5f4e6")  # Xanh lá
        self.session_tree.tag_configure("good", background="#d6eaf8")       # Xanh dương
        self.session_tree.tag_configure("average", background="#fef5e7")   # Vàng nhạt
        self.session_tree.tag_configure("poor", background="#fadbd8")      # Đỏ nhạt


    def display_session_stats(self, stats, period_text, class_name):
        """Hiển thị thống kê tổng quan buổi học"""

        self.session_stats_text.configure(state='normal')
        self.session_stats_text.delete('1.0', 'end')

        if not stats or stats['total_sessions'] == 0:
            self.session_stats_text.insert(
                'end',
                "⚠️ Chưa có dữ liệu buổi học trong khoảng thời gian đã chọn."
            )
            self.session_stats_text.configure(state='disabled')
            return

        total_sessions = stats.get('total_sessions', 0)
        total_students = stats.get('total_students', 0)
        overall_avg = stats.get('overall_avg', 0) or 0

        excellent = stats.get('excellent_sessions', 0)
        good = stats.get('good_sessions', 0)
        average = stats.get('average_sessions', 0)
        poor = stats.get('poor_sessions', 0)

        stats_content = f"""
    📅 Khoảng thời gian: {period_text}
    🏫 Lớp: {class_name}

    📊 TỔNG QUAN
    • Tổng số buổi học: {total_sessions}
    • Sĩ số lớp: {total_students} học sinh
    • Điểm tập trung trung bình: {overall_avg:.1f} / 100

    🎯 PHÂN LOẠI BUỔI HỌC
    • Cao độ (≥ 80): {excellent} buổi
    • Tốt (60 – 79): {good} buổi
    • Trung bình (40 – 59): {average} buổi
    • Thấp (< 40): {poor} buổi
    """

        self.session_stats_text.insert('end', stats_content.strip())
        self.session_stats_text.configure(state='disabled')


    def display_session_chart(self, stats):
        """Hiển thị biểu đồ phân bố buổi học"""

        # Xóa biểu đồ cũ
        for widget in self.session_chart_container.winfo_children():
            widget.destroy()

        if not stats or stats['total_sessions'] == 0:
            ctk.CTkLabel(
                self.session_chart_container,
                text="📉 Chưa có dữ liệu để hiển thị biểu đồ",
                font=("Segoe UI", 13),
                text_color="gray"
            ).pack(expand=True)
            return

        categories = ['Cao độ', 'Tốt', 'Trung bình', 'Thấp']
        values = [
            stats.get('excellent_sessions', 0),
            stats.get('good_sessions', 0),
            stats.get('average_sessions', 0),
            stats.get('poor_sessions', 0)
        ]

        colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c']

        fig = Figure(figsize=(6, 4), facecolor='white')
        ax = fig.add_subplot(111)

        bars = ax.bar(
            categories,
            values,
            color=colors,
            alpha=0.85,
            edgecolor='#2c3e50',
            linewidth=1.2
        )

        # Ghi số lên cột
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                str(value),
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )

        ax.set_ylabel('Số buổi', fontsize=11, fontweight='bold')
        ax.set_xlabel('Mức độ tập trung', fontsize=11, fontweight='bold')
        ax.set_title(
            f"Phân bố {stats['total_sessions']} buổi học",
            fontsize=13,
            fontweight='bold',
            pad=12
        )

        ax.grid(axis='y', linestyle='--', alpha=0.3)
        fig.tight_layout(pad=2)

        canvas = FigureCanvasTkAgg(fig, master=self.session_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)



# Test frame nếu chạy riêng file này
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Test Thống Kê Frame")
    root.geometry("1200x800")

    # Mock user info và callback
    test_user = {"username": "admin"}

    def test_navigate(page):
        print(f"Điều hướng đến: {page}")

    frame = ThongKeFrame(root, test_user, test_navigate)
    frame.pack(fill=tk.BOTH, expand=True)

    root.mainloop()