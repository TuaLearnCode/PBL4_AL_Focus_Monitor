import os, time, threading, cv2, torch, numpy as np, tkinter as tk, textwrap
from ultralytics import YOLO
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk
# Thêm các thư viện cho PIL (vẽ tiếng Việt)
from PIL import Image, ImageTk, ImageDraw, ImageFont 
import re 
from tkinter import Toplevel 
from datetime import datetime 
import traceback
import customtkinter as ctk

# Cấu hình CustomTkinter
ctk.set_appearance_mode("light")      # "dark" | "light" | "system"
ctk.set_default_color_theme("blue")   # blue | green | dark-blue
from focus_manager import FocusScoreManager # << Đã import
import requests

# --- Import các file code của bạn ---
import database 
import os

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# >>> [SỬA 2] THÊM IMPORT MODULE AI <<<\
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# >>> [SỬA 2] THÊM IMPORT MODULE AI <<<<
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
import ai_summarizer

# (Các import lõi AI của bạn)
try:
    from recognition_engine import RecognitionEngine, UNKNOWN_NAME, iou_xyxy
    from behavior_analyzer import BieuCamAnalyzer
except ImportError as e:
    root_err = tk.Tk()
    root_err.withdraw()
    messagebox.showerror("Lỗi Import", f"Lỗi import trong camera.py: {e}\n\nHãy đảm bảo recognition_engine.py, behavior_analyzer.py ở cùng thư mục.")
    root_err.destroy()
    exit()

# ===== CẤU HÌNH (Đã chuyển từ app_main.py) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "weights", "yolov8s-face-lindevs.pt")
VIDEO_PATH = "" 
FONT_PATH = os.path.join(BASE_DIR, "..", "arial.ttf")

# --- CẤU HÌNH FONT CHỮ TIẾNG VIỆT ---

VIEW_W, VIEW_H  = 800, 600
CONF_THRES      = 0.45
TARGET_FPS      = 30.0

RECOG_ENABLED   = True
RECOG_THRES     = 0.60
RECOG_EVERY_N   = 1
FACE_MARGIN     = 0.15
DB_PATH_DEFAULT = "faces_db.npz" 
LOOP_VIDEO      = False

OUT_VIDEO_DEFAULT = "video_output.mp4" 
# =====================

# ===================================================================
# LỚP HỘP THOẠI TÙY CHỈNH (Không thay đổi)
# ... (Code EnrollmentDialog giữ nguyên)
# ===================================================================
class SelectStudentDialog(tk.Toplevel):
    """
    Dialog chọn học sinh có sẵn để đăng ký khuôn mặt
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Đăng kí khuôn mặt")
        self.geometry("520x1200")
        self.transient(parent)
        self.grab_set()

        self.result = None

        search_frame = tk.Frame(self)

        tk.Label(self, text="Chọn học sinh để đăng ký khuôn mặt", bg="#ffdddd",
                 font=("Segoe UI", 20, "bold"), fg="#941D17").pack(pady=10)

        #ô tìm kiếm
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            self,
            textvariable=self.search_var,
            bg="#FFCDAA",
            font=("Segoe UI", 18),   # tăng chiều cao bằng font
            relief="solid",
            bd=1
        )
        search_entry.pack(fill="x", padx=15, pady=5, ipady=6)  # ipady tăng chiều cao

        # ===== Placeholder =====
        placeholder = "🔍 Tìm kiếm theo tên..."

        search_entry.insert(0, placeholder)
        search_entry.config(fg="gray")

        def on_focus_in(event):
            if search_entry.get() == placeholder:
                search_entry.delete(0, "end")
                search_entry.config(fg="black")

        def on_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, placeholder)
                search_entry.config(fg="gray")

        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)

        # ===== Lọc khi gõ =====
        search_entry.bind("<KeyRelease>", self.refresh_list)

        columns = ("ID", "Họ tên", "Lớp", "Ngày sinh")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=13)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=60)
        self.tree.column("Họ tên", width=200, anchor="w")
        self.tree.column("Lớp", width=100)
        self.tree.column("Ngày sinh", width=120)

        self.tree.pack(fill="both", expand=True, padx=15, pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Chọn", width=10, command=self.confirm, bg="#148c1e").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Hủy", width=10, command=self.destroy, bg="#d8421d").pack(side="left")

        self.students = database.get_all_students()
        self.refresh_list()

        self.wait_window(self)

    def refresh_list(self, event=None):
        keyword = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())

        for s in self.students:
            name = s["name"].lower()

            if keyword and keyword not in name:
                continue

            self.tree.insert("", "end", values=(
                s["student_id"],
                s["name"],
                s["class_name"],
                s.get("birthday", "")   # thêm ngày sinh
            ))

    def confirm(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn học sinh!", parent=self)
            return
        self.result = self.tree.item(sel[0])["values"]
        self.destroy()

    def body(self, master):
        master.grid_columnconfigure(1, weight=1)
        
        # 1. Họ và tên
        tk.Label(master, text="Họ và tên:").grid(row=0, column=0, sticky='w', pady=2)
        self.e_name = tk.Entry(master, width=30)
        self.e_name.grid(row=0, column=1, columnspan=2, sticky='we', padx=5)

        # 3. Giới tính (Chuyển lên row 1)
        tk.Label(master, text="Giới tính:").grid(row=1, column=0, sticky='w', pady=2)
        self.v_gender = tk.StringVar(master)
        self.v_gender.set("Nam") # Giá trị mặc định
        gender_options = ["Nam", "Nữ", "Khác"]
        self.om_gender = ttk.Combobox(master, textvariable=self.v_gender, values=gender_options, state='readonly', width=10)
        self.om_gender.grid(row=1, column=1, sticky='w', padx=5)

        # 4. Ngày sinh (Chuyển lên row 2)
        tk.Label(master, text="Ngày sinh:").grid(row=2, column=0, sticky='w', pady=2)
        self.e_birthday = tk.Entry(master, width=12)
        self.e_birthday.insert(0, "YYYY-MM-DD")
        self.e_birthday.grid(row=2, column=1, sticky='w', padx=5)

        return self.e_name 

    def validate(self):
        self.name = self.e_name.get().strip()
        self.gender = self.v_gender.get()
        self.birthday = self.e_birthday.get().strip()

        if not self.name:
            messagebox.showerror("Lỗi", "Họ và tên không được để trống.", parent=self)
            return 0
        
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', self.birthday):
            messagebox.showerror("Lỗi", "Định dạng ngày sinh không hợp lệ. \nPhải là YYYY-MM-DD (ví dụ: 2000-01-30).", parent=self)
            return 0
        
        try:
            datetime.strptime(self.birthday, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Lỗi", "Ngày sinh không hợp lệ (ví dụ: 2000-02-31 là sai).", parent=self)
            return 0
            
        return 1

    def apply(self):
        self.result = {
            "name": self.name,
            "gender": self.gender,
            "birthday": self.birthday
        }
# ===================================================================
# KẾT THÚC LỚP DIALOG
# ===================================================================


class Camera(ctk.CTkFrame):
    """
    Đây là lớp Màn hình chính
    """
    def __init__(self, master, user_info, on_navigate):
        super().__init__(master, fg_color="#ffffff")
        self.pack(fill="both", expand=True)

        self.on_navigate = on_navigate
        self.user_info = user_info
        username = self.user_info.get("username", "User")

        self.root = master
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_app)


         # ==================================================
    # HEADER (giống hocsinh.py)
    # ==================================================
        header = ctk.CTkFrame(self, height=80, fg_color="#aeeee0", corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header,
            text="← Quay lại",
            width=100,
            fg_color="#7276E6",
            text_color="#ffffff",
            command=lambda: self.on_navigate("home")   # giữ callback cũ
        ).place(x=20, rely=0.5, anchor="w")

        ctk.CTkLabel(
            header,
            text="GIÁM SÁT BUỔI HỌC",
            font=("Segoe UI", 20, "bold"),
            text_color="#ef4385"
        ).place(relx=0.5, rely=0.5, anchor="center")

         # ==================================================
        # TOOLBAR (nút chức năng)
        # ==================================================
        toolbar = ctk.CTkFrame(self, height=60, fg_color="#a3dcef")
        toolbar.pack(fill="x", padx=15, pady=(10, 5))
        toolbar.pack_propagate(False)
        center_bar = ctk.CTkFrame(toolbar, fg_color="transparent")
        center_bar.pack(expand=True)

        self.btn_select_video = ctk.CTkButton(
            center_bar, text="Chọn video", command=self.select_video_file
        )
        self.btn_select_video.pack(side="left", padx=6)

        self.btn_video = ctk.CTkButton(
            center_bar, text="Phát Video", command=self.toggle_play_pause, state="disabled"
        )   
        self.btn_video.pack(side="left", padx=6)

        ctk.CTkButton(
            center_bar, text="Ghi video", command=self.toggle_record
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            center_bar, text="Đăng ký khuôn mặt", command=self.enroll_one
        ).pack(side="left", padx=6)

        self.btn_webcam = ctk.CTkButton(
            center_bar, text="Mở Webcam", command=self.toggle_webcam
        )
        self.btn_webcam.pack(side="left", padx=6)

        self.btn_esp32 = ctk.CTkButton(
            center_bar, text="ESP32 Camera", command=self.toggle_esp32,  fg_color="#1abc9c",      # màu nền (xanh ngọc)
            hover_color="#16a085",   # màu hover
            text_color="#ffffff",    # màu chữ
        )
        self.btn_esp32.pack(side="left", padx=6)

        # ==================================================
        # BODY (Video | Bảng)
        # ==================================================
        body = ctk.CTkFrame(self, fg_color="#ffffff")
        body.pack(fill="both", expand=True, padx=15, pady=10)

        # ---- Left: Video ----
        left = ctk.CTkFrame(body, fg_color="#ffffff", corner_radius=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.left_panel = tk.Canvas(left, bg="black")
        self.left_panel.pack(fill="both", expand=True, padx=10, pady=10)
        self.left_panel.bind("<Button-1>", self.on_click_face)

        # ---- Right: Table ----
        right = ctk.CTkFrame(body, fg_color="#c1e2ef", corner_radius=16)
        right.pack(side="right", fill="y")

        self.info_frame = right
        self.info_frame.configure(width=700)

        cols = ("ID", "STT", "Name", "Score", "Eyes", "Head", "Behavior")
        self.info_tree = ttk.Treeview(
            self.info_frame, columns=cols, show="headings", height=22
        )

        col_w = [50, 55, 140, 80, 150, 150, 320]
        for c, w in zip(cols, col_w):
            self.info_tree.heading(c, text=c)
            self.info_tree.column(c, width=w, anchor="w")

        self.info_vscroll = ttk.Scrollbar(
            self.info_frame, orient="vertical", command=self.info_tree.yview
        )
        self.info_tree.configure(yscrollcommand=self.info_vscroll.set)

        self.info_tree.pack(side="left", fill="both", expand=True)
        self.info_vscroll.pack(side="right", fill="y")

        # ---- Style Treeview (chữ to) ----
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            font=("Segoe UI", 16),
            rowheight=52
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 18, "bold")
        )

        try:
            self.info_tree.tag_configure("row_even", background="#ffffff")
            self.info_tree.tag_configure("row_odd", background="#f6f8fa")
            self.info_tree.tag_configure("has_alert", foreground="#8B0000")
            self.info_tree.tag_configure("continuation", foreground="#333333")
        except Exception:
            pass

    # ==================================================
    # STATUS BAR
    # ==================================================
        self.status = ctk.CTkLabel(
            self,
            text=f"Trạng thái: Sẵn sàng. Chào, {username}!",
            font=("Segoe UI", 12),
            fg_color="#adeef6",
        )
        self.status.pack(fill="x", padx=15, pady=(0, 10))

        # (Các biến khởi tạo khác giữ nguyên)
        self.cap = None
        self.running = False 
        self.mode = 'idle' 
        self.period = 1.0/TARGET_FPS
        self.paused = False 
        self.video_file_path = None 
        self.frame_lock = threading.Lock(); self.latest_frame = None
        self.det_lock = threading.Lock(); self.last_boxes=[]; self.last_scores=[]
        self.id_lock  = threading.Lock()
        self.last_names = [] 
        self.last_confs = []
        self.last_student_ids = [] 
        self.id_to_name_cache = {} 
        self.frame_count = 0
        self.force_recog_frames = 0; self.sticky = None; self.enrolling = False
        self.writer=None; self.recording=False; self.out_fps=TARGET_FPS; 
        self.out_path=OUT_VIDEO_DEFAULT 
        self.capture_thread_handle = None
        self.infer_thread_handle = None
        self.model = self.load_model(MODEL_PATH)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.recog = RecognitionEngine(self.device, recog_thres=RECOG_THRES, face_margin=FACE_MARGIN)
        self.analyzer = BieuCamAnalyzer()
        self.focus_manager = FocusScoreManager(base_score=0) 
        self.focus_logs = {}
        
        # (# === SỬA ĐỔI 1: Thêm cờ kiểm soát phân tích ===)
        # Cờ bật/tắt nhận diện hành vi (Mắt, Đầu)
        self.enable_behavior_analysis = False
        
        # ===== ESP32 CONFIG =====
       # self.esp32_url = "http://172.20.10.2/capture"  # ĐỔI IP wifi ông nhã
        self.esp32_url = "http://10.125.14.125/capture" #ip wifi chính
        self.source_type = None  # webcam | video | esp32
    
        # (Các biến quản lý Session giữ nguyên)
        self.current_session_id = None
        self.session_start_time = None      # Dùng time.time() để tính duration
        self.session_appeared_students = set() # Set chứa các student_id đã CÓ trong focus_record
        
        try:
            self.pil_font = ImageFont.truetype(FONT_PATH, 16) 
        except IOError:
            messagebox.showwarning("Lỗi Font", f"Không tìm thấy file font: {FONT_PATH}\n\nChữ tiếng Việt sẽ hiển thị lỗi.")
            self.pil_font = ImageFont.load_default() 
        db_path_full = os.path.join(BASE_DIR, DB_PATH_DEFAULT)
        if os.path.exists(db_path_full):
            try:
                self.recog.load_db(db_path_full)
                self.set_status(f"Đã tải DB: {DB_PATH_DEFAULT} (N={len(self.recog.names)})")
            except Exception as e:
                messagebox.showerror("Lỗi Tải DB", f"Lỗi khi tải {DB_PATH_DEFAULT}:\n{e}")
                self.set_status(f"Lỗi tải DB. (N={len(self.recog.names)})")
        else:
            self.set_status(f"Sẵn sàng. Không tìm thấy {DB_PATH_DEFAULT}. DB trống.")
        self.last_analysis = None
        self.after_id = None 
        self.gui_loop() # Bắt đầu vòng lặp

    
    def set_status(self, t): 
        try:
            if self.status:
                self.status.configure(text=f"Trạng thái: {t}")
        except tk.TclError:
             pass 

    def load_model(self, path):
        # (Hàm này giữ nguyên)
        if not os.path.exists(path):
            messagebox.showerror("Lỗi", f"Không tìm thấy model: {path}"); self.root.destroy()
            return None
        m = YOLO(path)
        if torch.cuda.is_available():
            m.to("cuda"); 
        else: self.set_status("Model CPU")
        try: m.fuse()
        except: pass
        return m

    def read_esp32_frame(self):
        """
        Đọc 1 frame JPEG từ ESP32-CAM qua HTTP
        Trả về frame BGR (numpy) hoặc None
        """
        try:
            r = requests.get(self.esp32_url, timeout=2)
            if r.status_code != 200:
                return None

            img_array = np.frombuffer(r.content, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame

        except Exception as e:
            print(f"Lỗi ESP32 frame: {e}")
            return None

    def select_video_file(self):
        # (Hàm này giữ nguyên)
        if self.mode != 'idle':
            self.stop() 
        video_file_path = filedialog.askopenfilename(
            title="Chọn file video",
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov"), ("All files", "*.*")]
        )
        if not video_file_path: 
            return 
        self.video_file_path = video_file_path 
        self.start_video_stream() 

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # >>> [SỬA 3] ĐẶT LỚP HỌC MẶC ĐỊNH <<<
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def prompt_and_start_session(self):
        """Hỏi người dùng có muốn bắt đầu session không. Trả về True nếu thành công, False nếu hủy."""
        if messagebox.askyesno("Bắt đầu buổi học?", "Bạn có muốn bắt đầu một buổi học (session) mới không?\n(Kết quả sẽ được lưu vào CSDL)", parent=self.root):
            
            # 1. [SỬA] Đặt tên lớp mặc định
            class_name = "A"
            # (Đã xóa simpledialog.askstring)
            
            # 2. Tạo session trong CSDL
            try:
                start_time = datetime.now()
                new_session_id, msg = database.create_session(class_name, start_time)
                
                if new_session_id is None:
                    messagebox.showerror("Lỗi DB", f"Không thể tạo session: {msg}")
                    return False # Lỗi, hủy
                
                # 3. Lưu trạng thái session
                self.current_session_id = new_session_id
                self.session_start_time = time.time() # Dùng time.time() để tính duration
                self.session_appeared_students = set()
                
                # Reset trình quản lý điểm cho session mới
                self.focus_manager = FocusScoreManager(base_score=0) 
                
                self.set_status(f"Session {self.current_session_id} ({class_name}) ĐÃ BẮT ĐẦU.")
                return True # Bắt đầu thành công

            except Exception as e:
                messagebox.showerror("Lỗi DB", f"Lỗi khi gọi database.create_session: {e}")
                traceback.print_exc()
                return False # Lỗi, hủy
        
        else:
            # 4. Người dùng chọn "Không"
            self.current_session_id = None
            self.session_start_time = None
            self.session_appeared_students = set()
            # Reset điểm khi chạy không ghi
            self.focus_manager = FocusScoreManager(base_score=0)
            self.set_status("Đang chạy (không ghi session).")
            return True # Vẫn tiếp tục (nhưng không ghi CSDL)

    # (Hàm start_video_stream giữ nguyên)
    def start_video_stream(self):
        if not self.video_file_path:
            messagebox.showerror("Lỗi", "Chưa chọn file video.")
            return
        try:
            self.cap = cv2.VideoCapture(self.video_file_path)
            if not self.cap.isOpened():
                messagebox.showerror("Lỗi", f"Không mở được video: {self.video_file_path}"); return
            
            if not self.prompt_and_start_session():
                if self.cap: self.cap.release(); self.cap = None
                return 
            
            self.out_path = os.path.join(
                os.path.dirname(self.video_file_path), 
                os.path.splitext(os.path.basename(self.video_file_path))[0] + "_output.mp4"
            )

            print(f"Áp dụng TARGET_FPS ({TARGET_FPS}) cho video.")
            
            SLOW_FACTOR = 1.5
            self.period = (1.0 / TARGET_FPS) * SLOW_FACTOR
            
            # Vẫn cố gắng lấy fps gốc để GHI VIDEO (out_fps)
            fps_goc = self.cap.get(cv2.CAP_PROP_FPS)
            self.out_fps = fps_goc if (fps_goc and fps_goc > 1e-3) else TARGET_FPS

            
            self.running = True  
            self.paused = False  
            self.mode = 'video' 
            
            # (# === SỬA ĐỔI 2: Kích hoạt cờ phân tích ===)
            self.enable_behavior_analysis = True
            
            self.btn_video.configure(text="Dừng Video", state="normal") 
            self.btn_select_video.configure(text="Đổi video") 
            self.btn_webcam.configure(state="normal") 
            self.capture_thread_handle = threading.Thread(target=self.capture_thread, daemon=True)
            self.capture_thread_handle.start()
            self.infer_thread_handle = threading.Thread(target=self.infer_thread, daemon=True)
            self.infer_thread_handle.start()

            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.after(10, self.gui_loop) # Bắt đầu lại vòng lặp (10ms sau)

        except Exception as e:
            messagebox.showerror("Lỗi Video", f"Lỗi không xác định khi mở video:\n{e}")
            if self.cap: self.cap.release(); self.cap = None

    # (Hàm toggle_play_pause giữ nguyên)
    def toggle_play_pause(self):
        if not self.running or self.mode != 'video':
            return 
        if self.paused:
            is_at_end = False
            if self.cap:
                current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if current_frame >= total_frames - 1:
                    is_at_end = True
            if is_at_end:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                if self.current_session_id is None:
                    self.set_status(f"Phát lại: {os.path.basename(self.video_file_path)}")
            else:
                if self.current_session_id is None:
                    self.set_status(f"Đang phát: {os.path.basename(self.video_file_path)}")
            self.paused = False 
            self.btn_video.configure(text="Dừng Video")
        else:
            self.paused = True
            self.btn_video.configure(text="Phát Video")
            if self.current_session_id is None:
                self.set_status("Đã tạm dừng video")
    
    # (Hàm toggle_webcam giữ nguyên)
    def toggle_webcam(self):
        if self.mode == 'webcam':
            self.stop()
        else:
            if self.mode == 'video':
                self.stop()
            self.start_webcam()

    # (Hàm start_webcam giữ nguyên)
    def start_webcam(self):
        try:
            self.cap = cv2.VideoCapture(0) 
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)
                if not self.cap.isOpened():
                        messagebox.showerror("Lỗi Webcam", "Không mở được webcam (đã thử index 0 và 1).")
                        return
                        
            if not self.prompt_and_start_session():
                if self.cap: self.cap.release(); self.cap = None
                return 
            
            self.period = 1.0 / TARGET_FPS
            self.out_fps = TARGET_FPS
            self.out_path = "webcam_output.mp4"
            self.running = True
            self.mode = 'webcam' 
            self.paused = False 
            
            # (# === SỬA ĐỔI 3: Kích hoạt cờ phân tích ===)
            self.enable_behavior_analysis = True
            
            self.btn_webcam.configure(text="Dừng Webcam") 
            self.btn_video.configure(state="disabled", text="Phát Video")
            self.btn_select_video.configure(state="disabled")
            self.capture_thread_handle = threading.Thread(target=self.capture_thread, daemon=True)
            self.capture_thread_handle.start()
            self.infer_thread_handle = threading.Thread(target=self.infer_thread, daemon=True)
            self.infer_thread_handle.start()

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # >>> [SỬA LỖI] BẮT ĐẦU LẠI VÒNG LẶP GUI <<<
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # Phải gọi lại gui_loop() vì nó đã dừng ở màn hình "Sẵn sàng"
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.after(10, self.gui_loop) # Bắt đầu lại vòng lặp (10ms sau)

        except Exception as e:
            messagebox.showerror("Lỗi Webcam", f"Lỗi không xác định khi mở webcam:\n{e}")
            if self.cap: self.cap.release(); self.cap = None

    def start_esp32(self):
        if self.mode != 'idle':
            self.stop()

        if not self.prompt_and_start_session():
            return

        self.running = True
        self.paused = False
        self.mode = 'esp32'
        self.source_type = 'esp32'
        self.period = 1.0 / TARGET_FPS

        # (# === SỬA ĐỔI 3: Kích hoạt cờ phân tích ===)
        self.enable_behavior_analysis = True

        self.set_status("Đang nhận camera từ ESP32")

        # Disable các nguồn khác
        self.btn_video.configure(state="disabled")
        self.btn_webcam.configure(state="disabled")
        self.btn_select_video.configure(state="disabled")
        self.btn_esp32.configure(text="Dừng ESP32")

        self.capture_thread_handle = threading.Thread(
            target=self.capture_thread,
            daemon=True
        )
        self.capture_thread_handle.start()

        self.infer_thread_handle = threading.Thread(
            target=self.infer_thread,
            daemon=True
        )
        self.infer_thread_handle.start()

        self.after(10, self.gui_loop)

    def toggle_esp32(self):
        if self.mode == 'esp32':
            self.stop()
        else:
            self.start_esp32()

    # (Hàm stop giữ nguyên)
    def stop(self):
        try:
            # GỌI HÀM ĐỒNG BỘ MỚI
            self.finalize_session()
        except Exception as e:
            print(f"Lỗi khi finalize_session: {e}")
            traceback.print_exc()

        self.running = False 
        
        # (# === SỬA ĐỔI 4: Reset cờ phân tích ===)
        self.enable_behavior_analysis = False
        
        try:
            if self.capture_thread_handle is not None and self.capture_thread_handle.is_alive():
                self.capture_thread_handle.join(timeout=1.5) 
        except Exception as e:
            print(f"Lỗi khi join luồng capture: {e}")
        try:
            if self.infer_thread_handle is not None and self.infer_thread_handle.is_alive():
                self.infer_thread_handle.join(timeout=1.0) 
        except Exception as e:
            print(f"Lỗi khi join luồng infer: {e}")
        self.mode = 'idle' 
        self.paused = False 
        self.video_file_path = None 
        self.source_type = None

        try:
            self.btn_video.configure(text="Phát Video", state="normal") 
            self.btn_webcam.configure(text="Mở Webcam", state="normal") 
            self.btn_select_video.configure(text="Chọn video", state="normal") 
            self.btn_esp32.configure(text="ESP32 Camera", state="normal")

            self.set_status("Đã dừng")
        except tk.TclError:
            pass 
        if self.cap: 
            self.cap.release()
            self.cap = None
        self._close_writer()
        self.recording = False
        self.capture_thread_handle = None
        self.infer_thread_handle = None

    # (Hàm capture_thread, infer_thread, gui_loop... giữ nguyên)
    def capture_thread(self):
        print("Capture thread started")

        while self.running:
            try:
                if self.paused:
                    time.sleep(0.05)
                    continue

                frame = None

                # ===== ESP32 =====
                if self.source_type == 'esp32':
                    frame = self.read_esp32_frame()

                # ===== Webcam / Video (giữ nguyên) =====
                else:
                    if not self.cap or not self.cap.isOpened():
                        time.sleep(0.01)
                        continue
                    ok, frame = self.cap.read()
                    if not ok:
                        self.running = False
                        # Sử dụng .after(0, ...) để gọi hàm stop() an toàn từ luồng chính
                        self.root.after(0, self.stop)
                        break

                if frame is None:
                    time.sleep(0.02)
                    continue

                frame = cv2.resize(frame, (VIEW_W, VIEW_H))

                with self.frame_lock:
                    self.latest_frame = frame.copy()
                # === [THÊM] lưu kích thước frame gốc ===
                self.frame_w = VIEW_W
                self.frame_h = VIEW_H


                time.sleep(self.period)

            except Exception as e:
                print(f"Lỗi capture_thread: {e}")
                self.running = False

        print("Capture thread exited")
            
    def _handle_video_end(self):
        try:
            if self.mode == 'video':
                self.paused = True
                self.btn_video.configure(text="Phát Lại")
                if self.current_session_id is None:
                    self.set_status("Video đã kết thúc. Bấm 'Phát Lại' để xem lại.")
        except tk.TclError:
            pass 
            
    def infer_thread(self):
        print("Infer thread đã bắt đầu.") 
        while self.running:
            frame = None 
            if self.paused:
                time.sleep(0.05)
                continue
            try:
                with self.frame_lock:
                    if self.latest_frame is not None:
                            frame = self.latest_frame.copy()
                if frame is None:
                    time.sleep(0.005)
                    continue
                if self.model is None:
                    time.sleep(0.01); continue
                self.frame_count += 1
                res = self.model(frame, conf=CONF_THRES, verbose=False)[0]
                boxes  = res.boxes.xyxy.cpu().numpy().astype(int) if res.boxes else np.zeros((0,4), dtype=int)
                scores = res.boxes.conf.cpu().numpy().tolist()   if res.boxes else []
                names = []
                confs = []
                student_ids = []
                force_now = self.force_recog_frames > 0
                if RECOG_ENABLED and len(boxes)>0 and (force_now or (self.frame_count % RECOG_EVERY_N == 0)):
                    embs, idx = self.recog.embed_batch(frame, boxes)
                    pn, pc = [UNKNOWN_NAME]*len(boxes), [0.0]*len(boxes)
                    if embs is not None:
                        pred_names_or_ids, pred_confs = self.recog.predict_batch(embs)
                        for k,i in enumerate(idx): 
                            pn[i] = pred_names_or_ids[k]
                            pc[i] = pred_confs[k]
                    names = [UNKNOWN_NAME] * len(boxes)
                    confs = pc
                    student_ids = [None] * len(boxes)
                    for i, id_str in enumerate(pn):
                        if id_str != UNKNOWN_NAME:
                            try:
                                student_id = int(id_str) 
                                student_ids[i] = student_id
                                if student_id in self.id_to_name_cache:
                                    names[i] = self.id_to_name_cache[student_id]
                                else:
                                    student_info = database.get_student_by_id(student_id)
                                    if student_info:
                                        name = student_info.get('name', f"ID_{id_str}_NO_NAME")
                                        names[i] = name
                                        self.id_to_name_cache[student_id] = name 
                                    else:
                                        names[i] = f"ID_{id_str}_NOT_FOUND" 
                                        self.id_to_name_cache[student_id] = names[i]
                            except ValueError:
                                names[i] = id_str 
                                student_ids[i] = None 
                else:
                    with self.id_lock:
                        if len(self.last_names) == len(boxes):
                            names = self.last_names[:]
                            confs = self.last_confs[:]
                            student_ids = self.last_student_ids[:]
                        else:
                            names = [UNKNOWN_NAME] * len(boxes)
                            confs = [0.0] * len(boxes)
                            student_ids = [None] * len(boxes)
                if self.force_recog_frames>0: self.force_recog_frames-=1
                if self.sticky is not None and len(boxes)>0 and self.sticky.get('ttl',0)>0:
                    sbox=self.sticky['box']
                    sname=self.sticky['name'] 
                    sid = self.sticky.get('id')  
                    best_i,best_iou=-1,0.0
                    for i,b in enumerate(boxes):
                        iou=iou_xyxy(tuple(b), tuple(sbox))
                        if iou>best_iou: best_i,best_iou=i,iou
                    if best_i>=0 and best_iou>=0.3:
                        names[best_i] = sname 
                        student_ids[best_i] = sid 
                        confs[best_i] = 1.0
                        self.sticky['ttl']-=1
                with self.det_lock:
                    self.last_boxes=boxes; self.last_scores=scores
                with self.id_lock:
                    self.last_names = names
                    self.last_confs = confs
                    self.last_student_ids = student_ids 
                
                # (# === SỬA ĐỔI 5: Chỉ chạy phân tích nếu cờ được bật ===)
                if self.enable_behavior_analysis and len(boxes) > 0:
                    fb = [tuple(map(int, b)) for b in boxes]
                    self.last_analysis = self.analyzer.analyze_frame(frame, face_boxes=fb)
                else:
                    # Nếu không bật, reset phân tích
                    self.last_analysis = None
                # (======================================================)
                    
            except Exception as e:
                if self.running:
                    print(f"Lỗi nghiêm trọng trong infer_thread: {e}")
                self.last_analysis = None
        print("Infer thread đã thoát.")


    def gui_loop(self):
        
        try:
            w = self.left_panel.winfo_width()
            h = self.left_panel.winfo_height()
            is_running = self.running 
            is_paused = self.paused
            
            frame = None
            if is_running: 
                with self.frame_lock:
                    if self.latest_frame is not None:
                        frame = self.latest_frame.copy()
            
            # --- A. KHÔNG CHẠY (Đã bấm Stop) ---
            if not is_running:
                self.left_panel.delete("all")
                self.left_panel.create_text(w//2, h//2, text="Sẵn sàng. Hãy 'Chọn video' hoặc 'Mở Webcam'.", anchor="center", fill="white", font=("Arial", 14))
                try:
                    for item in self.info_tree.get_children():
                        self.info_tree.delete(item)
                except tk.TclError: 
                    pass
                if self.after_id:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
                return 

            # --- B. ĐANG CHẠY, NHƯNG BỊ PAUSE (hoặc chưa có frame) ---
            if frame is None or is_paused:
                self.left_panel.delete("all")
                if is_paused:
                    self.left_panel.create_text(w//2, h//2, text="Đã tạm dừng. Bấm 'Phát Video' để tiếp tục.", anchor="center", fill="white", font=("Arial", 14))
                else: 
                    self.left_panel.create_text(w//2, h//2, text="Đang tải...", anchor="center", fill="white", font=("Arial", 14))
                
                self.after_id = self.root.after(16, self.gui_loop)
                return 

            # --- C. ĐANG CHẠY, KHÔNG PAUSE, CÓ FRAME ---
            
            with self.det_lock, self.id_lock:
                boxes=list(self.last_boxes); scores=list(self.last_scores)
                names=list(self.last_names); confs=list(self.last_confs)
                student_ids = list(self.last_student_ids) 
            
            # (Phần logic vẽ giữ nguyên)
            img_pil = None
            draw = None
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                draw = ImageDraw.Draw(img_pil)
            except Exception as e:
                img_pil = None 
            for i, ((x1,y1,x2,y2), detc) in enumerate(zip(boxes, scores)):
                name = names[i] if i < len(names) else UNKNOWN_NAME
                simc = confs[i] if i < len(confs) else 0.0
                student_id = student_ids[i] if i < len(student_ids) else None
                color=(0,255,0) if name!=UNKNOWN_NAME else (0,0,255)
                display_name = name.split(" ")[-1] if name != UNKNOWN_NAME else UNKNOWN_NAME
                id_str = str(student_id) if student_id else '?'
                text_to_draw = f"ID: {id_str} | {display_name} {simc:.2f}"
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
                if img_pil and draw and self.pil_font:
                    try:
                        frame_rgb_with_rect = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(frame_rgb_with_rect)
                        draw = ImageDraw.Draw(img_pil)
                        draw.text((x1 + 2, max(0, y1 - 20)), text_to_draw, font=self.pil_font, fill=color)
                        frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
                    except Exception as e:
                        cv2.putText(frame, text_to_draw,
                            (x1, max(20,y1-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                else:
                    cv2.putText(frame, text_to_draw,
                            (x1, max(20,y1-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if self.last_analysis is not None:
                frame = self.analyzer.draw_analysis_info(frame, self.last_analysis)

            if self.recording and self.writer is not None:
                try: self.writer.write(frame)
                except Exception as e: self.toggle_record() 

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize img to fit left_panel size
            w = self.left_panel.winfo_width()
            h = self.left_panel.winfo_height()
            if w > 10 and h > 10:
                img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
            # === [THÊM] lưu kích thước ảnh hiển thị ===
            self.display_w = w
            self.display_h = h

            imgtk = ImageTk.PhotoImage(Image.fromarray(img))
            self.left_panel.delete("all")
            self.left_panel.create_image(0, 0, anchor="nw", image=imgtk)
            self.left_panel.imgtk = imgtk  # Keep reference 

            try:
                analysis = self.last_analysis if self.last_analysis is not None else {}
                face_states = analysis.get('face_states', []) if isinstance(analysis, dict) else []
                
                current_time = time.time()
                self.focus_logs.clear() 
                
                for i, student_id_db in enumerate(student_ids): 
                    manager_id = student_id_db
                    if manager_id is None:
                        manager_id = f"temp_face_{i}"
                    
                    if self.current_session_id is not None and student_id_db is not None:
                        if student_id_db not in self.session_appeared_students:
                            try:
                                print(f"Ghi nhận {student_id_db} cho session {self.current_session_id}")
                                database.mark_student_appearance(self.current_session_id, student_id_db)
                                self.session_appeared_students.add(student_id_db)
                            except Exception as e:
                                print(f"Lỗi khi ghi nhận (appear) student {student_id_db}: {e}")
                    
                    
                    try:
                        fs = face_states[i] if i < len(face_states) else {}
                        head_state_list = fs.get('head_orientation', {}).get('states', [])
                        head_state = head_state_list[0] if head_state_list else 'HEAD_STRAIGHT'
                        eye_state = fs.get('eye_state', ("NO_FACE", 0))[0]
                        behaviors_list = []
                        if fs.get('behaviors'):
                            behaviors_list = [b.get('label', 'unknown') for b in fs['behaviors']]
                        
                        new_points, logs = self.focus_manager.update_student_score(
                            manager_id, behaviors_list, head_state, eye_state, current_time
                        )
                        
                        if logs:
                            self.focus_logs[manager_id] = logs 
                    except Exception as e:
                        print(f"Lỗi khi cập nhật điểm cho {manager_id}: {e}")

                # (Phần cập nhật Treeview và ngắt dòng)
                for item in self.info_tree.get_children():
                    self.info_tree.delete(item)

                for i, name in enumerate(names):
                    student_id = student_ids[i] if i < len(student_ids) else None
                    id_str = str(student_id) if student_id else ''
                    manager_id_for_display = student_id if student_id else f"temp_face_{i}"
                    current_score = self.focus_manager.get_student_score(manager_id_for_display)
                    
                    # (Logic hiển thị timer)
                    
                    fs = face_states[i] if i < len(face_states) else {} 
                    detected_behavior_labels = set()
                    detection_display_str = ""
                    if fs and 'behaviors' in fs and fs['behaviors']:
                        beh_list = fs['behaviors']
                        detected_behavior_labels = {b.get('label','unknown') for b in beh_list}
                        detection_display_str = ", ".join(f"{b.get('label','')} {b.get('conf',0.0):.2f}" for b in beh_list)
                    
                    timers = self.focus_manager.get_student_timers(manager_id_for_display)
                    timer_strings = []
                    
                    ALWAYS_SHOW_TIMERS = {
                        'EYES_OPEN', 'EYES_CLOSING', 
                        'HEAD_STRAIGHT', 'HEAD_LEFT', 'HEAD_RIGHT', 
                        'good_focus',
                        'reading', 'writing', 'upright'
                    }

                    eye_open_time = timers.get('EYES_OPEN', 0.0)
                    eye_close_time = timers.get('EYES_CLOSING', 0.0)
                    head_straight_time = timers.get('HEAD_STRAIGHT', 0.0)
                    head_left_time = timers.get('HEAD_LEFT', 0.0)
                    head_right_time = timers.get('HEAD_RIGHT', 0.0)

                    for behavior_name, time_val in sorted(timers.items()):
                        if time_val > 0:
                            if behavior_name == 'EYES_OPEN' and eye_close_time > 0: continue
                            if behavior_name == 'EYES_CLOSING' and eye_open_time > 0: continue
                            if behavior_name == 'HEAD_STRAIGHT' and (head_left_time > 0 or head_right_time > 0): continue
                            if behavior_name == 'HEAD_LEFT' and head_straight_time > 0: continue
                            if behavior_name == 'HEAD_RIGHT' and head_straight_time > 0: continue
                                
                            is_always_show_timer = behavior_name in ALWAYS_SHOW_TIMERS
                            behavior_label_check = behavior_name.split(' ')[0] 
                            is_detected_behavior = behavior_label_check in detected_behavior_labels

                            if is_always_show_timer or is_detected_behavior:
                                timer_strings.append(f"{behavior_name.replace('_', ' ')} ({time_val:.1f}s)")
                    
                    timer_display_str = ", ".join(timer_strings)

                    final_behavior_str = ""
                    if detection_display_str and timer_display_str:
                        final_behavior_str = f"{detection_display_str} | T: [{timer_display_str}]"
                    elif detection_display_str: final_behavior_str = detection_display_str
                    elif timer_display_str: final_behavior_str = f"T: [{timer_display_str}]"
                    
                    eye_txt = "NO_FACE"
                    head_txt = "N/A"
                    alerts_txt = ""
                    if fs: 
                        eye_txt = fs.get('eye_state', ("NO_FACE", 0))[0]
                        head_states = fs.get('head_orientation', {}).get('states', [])
                        head_txt = ",".join(head_states) if head_states else 'HEAD_STRAIGHT'
                        focus_alerts = self.focus_logs.get(manager_id_for_display, [])
                        behavior_alerts = fs.get('alerts', []) if fs.get('alerts') is not None else []
                        alerts_txt = ", ".join(focus_alerts + behavior_alerts)
                    else:
                        eye_txt = "N/A" 
                        head_txt = "N/A"
                        
                    row_tag = 'row_even' if (i % 2) == 0 else 'row_odd'
                    MAX_BEHAVIOR_COL_CHARS = 90
                    behavior_chunks = []
                    if final_behavior_str:
                        try:
                            wrapped = textwrap.wrap(final_behavior_str, width=MAX_BEHAVIOR_COL_CHARS, break_long_words=True)
                            behavior_chunks = wrapped if wrapped else [final_behavior_str]
                        except Exception: behavior_chunks = [final_behavior_str] 
                    else:
                         behavior_chunks = ['']
                    first_behavior = behavior_chunks[0]
                    
                    values = (id_str, str(i+1), name, current_score, eye_txt, head_txt, first_behavior)
                    tags = [row_tag]
                    if alerts_txt: tags.append('has_alert')
                    self.info_tree.insert('', 'end', values=values, tags=tuple(tags))

                    for k in range(1, len(behavior_chunks)):
                        cont_vals = ('', '', '', '', '', '', behavior_chunks[k]) 
                        cont_tags = [row_tag, 'continuation']
                        if alerts_txt: cont_tags.append('has_alert')
                        self.info_tree.insert('', 'end', values=cont_vals, tags=tuple(cont_tags))

            except Exception as e:
                print(f"Lỗi nghiêm trọng trong khi cập nhật Treeview: {e}")
                traceback.print_exc()
            
            self.after_id = self.root.after(16, self.gui_loop)
                
        except tk.TclError as e:
            if "invalid command name" in str(e): print("gui_loop: Đã bắt lỗi TclError (widget đã bị hủy), dừng vòng lặp.")
            else:
                if self.running: print(f"gui_loop: Lỗi TclError không xác định: {e}"); traceback.print_exc()
        except Exception as e:
            if self.running: print(f"gui_loop: Lỗi nghiêm trọng: {e}"); traceback.print_exc()

    def build_note_from_logs(self, logs):
        """
        Format: [HH:MM:SS] điểm_hiện_tại (lý do cộng/trừ)
        - Chỉ ghi log có change != 0
        - điểm_hiện_tại = tổng tích lũy tại thời điểm đó
        """
        if not logs:
            return "Không có cộng / trừ điểm."

        logs_sorted = sorted(logs, key=lambda x: x[0])

        current_score = 0
        lines = []

        for ts, msg, change in logs_sorted:
            if change == 0:
                continue

            current_score += change
            time_log = datetime.fromtimestamp(ts).strftime('%H:%M:%S')

            # 🔥 FIX: dùng msg trực tiếp, KHÔNG bọc +1/-1 lần nữa
            lines.append(
                f"[{time_log}] {current_score} ({msg})"
            )

        if not lines:
            return "Không có cộng / trừ điểm."

        return "\n".join(lines)



    
    # ===================================================================
    # >>> SỬA LỖI: CHẠY ĐỒNG BỘ VÀ KHÔNG DÙNG THREADING CHO DB/AI <<<
    # ===================================================================
    def finalize_session(self):
        """
        Lưu kết quả của session hiện tại vào CSDL MỘT CÁCH ĐỒNG BỘ. 
        Loại bỏ threading để đảm bảo quá trình lưu DB hoàn tất trước khi Pytest kết thúc.
        """
        
        # 1. Kiểm tra session
        if self.current_session_id is None:
            return 
        
        session_to_finalize = self.current_session_id
        start_time_to_finalize = self.session_start_time
        students_to_finalize = self.session_appeared_students.copy()
        
        # RẤT QUAN TRỌNG: Đặt lại ngay lập tức
        self.current_session_id = None 
        self.session_start_time = None
        self.session_appeared_students = set()
        
        print(f"Đang kết thúc session {session_to_finalize} (ĐỒNG BỘ)...")
        
        # 2. Cập nhật thời gian kết thúc session
        end_time = datetime.now()
        database.end_session(session_to_finalize, end_time)
        session_duration_sec = time.time() - start_time_to_finalize if start_time_to_finalize else 0
        
        if not students_to_finalize:
            print("Session kết thúc, không có học sinh.")
            return

        # 3. Thu thập dữ liệu từ FocusManager (trên luồng chính)
        student_data_list = []
        for student_id in students_to_finalize:
            if student_id is None: continue
            manager_id = student_id
            
            try:
                focus_point = self.focus_manager.get_student_score(manager_id)
                rate = self.calculate_rate(focus_point, session_duration_sec)
                logs = self.focus_manager.get_student_full_logs(manager_id)
                
                student_data_list.append({
                    "student_id": student_id,
                    "focus_point": focus_point,
                    "rate": rate,
                    "logs": logs
                })
            except Exception as e:
                print(f"Lỗi khi thu thập dữ liệu cho student {student_id}: {e}")
                traceback.print_exc()
        # ===========================================================
        # BƯỚC MỚI: IN LOG CHI TIẾT RA CONSOLE
        # ===========================================================
        # Lấy tên từ cache hoặc DB
        student_name = self.id_to_name_cache.get(student_id, f"Học sinh ID {student_id}")
        
        # Lấy dữ liệu từ Manager
        focus_point = self.focus_manager.get_student_score(student_id)
        rate = self.calculate_rate(focus_point, session_duration_sec)

        logs = self.focus_manager.get_student_full_logs(student_id)
        print(f"\n[DANH TÍNH]: {student_name} (ID: {student_id})")
        print(f" -> Điểm tập trung: {focus_point} | Xếp loại: {rate}")
        print(f" -> Nhật ký hành vi:")
        
        if not logs:
            print("    (Không có biến động điểm)")
        else:
            for ts, msg, change in logs:
                time_log = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                mark = f"+{change}" if change > 0 else f"{change}"
                print(f"    - [{time_log}] {msg:.<40} {mark} điểm")
        
        student_data_list.append({
            "student_id": student_id,
            "name": student_name,
            "focus_point": focus_point,
            "rate": rate,
            "logs": logs
        })
        print("-" * 50)
        
        # 4. CHẠY AI VÀ DB TRÊN LUỒNG HIỆN TẠI (ĐỒNG BỘ)
        # BỎ THÔNG BÁO message_box để luồng không bị chặn
        print(f"Bắt đầu xử lý AI và lưu CSDL đồng bộ cho {len(student_data_list)} học sinh...")
        
        for data in student_data_list:
            student_id = data["student_id"]
            focus_point = data["focus_point"]
            rate = data["rate"]
            logs = data["logs"]
            note = "Không có ghi nhận chi tiết."
            
            try:
                note = self.build_note_from_logs(logs)

                # 4a. Gọi AI Tóm tắt (Sẽ chặn luồng chính cho đến khi hoàn tất)
                # if logs:
                #    try:
                #        note = ai_summarizer.summarize_focus_logs(logs)
                #    except BaseException as e:
                #        print(f"Lỗi gọi AI: {e}")
                #        note = f"Lỗi AI: {str(e)}" 

                # 4b. Cập nhật CSDL (Đồng bộ)
                database.update_focus_record(
                    session_to_finalize,
                    student_id,
                    focus_point,
                    rate,
                    note
                )
                
            except Exception as e:
                print(f"Lỗi lưu CSDL cho student {student_id}: {e}")
                traceback.print_exc()
        
        print(f"--- LƯU DB/AI HOÀN TẤT ĐỒNG BỘ (Session {session_to_finalize}) ---")

    # (Hàm calculate_rate giữ nguyên)
    def calculate_rate(self, score, duration_sec):
        """Tính toán rate dựa trên điểm và tỉ lệ thời gian chuẩn 45 phút."""
        
        STANDARD_DURATION_SEC = 45 * 60 
        prorated_score = score
        
        if duration_sec > 5: 
            scaling_factor = STANDARD_DURATION_SEC / duration_sec
            prorated_score = score * scaling_factor
        
        if prorated_score >= 12:
            return 'Cao độ'
        elif prorated_score >= 9:
            return 'Tốt'
        elif prorated_score >= 5: 
            return 'Trung bình'
        else:
            return 'Thấp'

    # (Các hàm khác như enroll_one, on_click_face, toggle_record, on_close... giữ nguyên)
    def enroll_one(self):
        with self.det_lock:
            if len(self.last_boxes) == 0:
                messagebox.showwarning("Thông báo", "Chưa thấy khuôn mặt nào.")
                return

        dialog = SelectStudentDialog(self.root)
        if dialog.result is None:
            self.set_status("Hủy đăng ký khuôn mặt.")
            return

        self.selected_student_id = dialog.result[0]
        self.selected_student_name = dialog.result[1]

        self.enrolling = True
        self.set_status(f"CLICK vào khuôn mặt để gán cho: {self.selected_student_name}")


    def on_click_face(self, event):
        if not self.enrolling:
            return
         # === [SỬA] map tọa độ UI -> frame ===
        ui_x, ui_y = int(event.x), int(event.y)

        # an toàn: tránh chia cho 0
        if not hasattr(self, 'display_w') or not hasattr(self, 'frame_w'):
            self.set_status("Chưa sẵn sàng để đăng ký.")
            return

        scale_x = self.frame_w / self.display_w
        scale_y = self.frame_h / self.display_h

        x = int(ui_x * scale_x)
        y = int(ui_y * scale_y)


        with self.det_lock, self.frame_lock:
            boxes = list(self.last_boxes)
            frame = self.latest_frame.copy() if self.latest_frame is not None else None

        if frame is None or not boxes:
            self.set_status("Không có frame hoặc khuôn mặt.")
            self.enrolling = False
            return

        chosen, max_area = -1, -1
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    max_area = area
                    chosen = i

        if chosen < 0:
            self.set_status("Click không trúng khuôn mặt.")
            return

        self.enrolling = False
        box = boxes[chosen]

        # ===== 1. Trích xuất embedding =====
        emb, _ = self.recog.embed_batch(frame, np.array([box]))
        if emb is None:
            messagebox.showerror("Lỗi", "Không trích xuất được embedding.")
            return

        face_embedding = emb[0]
        student_id = self.selected_student_id

        # ===== 2. Lưu ảnh khuôn mặt =====
        (x1, y1, x2, y2) = box
        face_crop = frame[y1:y2, x1:x2]

        face_dir = os.path.join(BASE_DIR, "faces_db_images")
        os.makedirs(face_dir, exist_ok=True)

        face_filename = f"face_{student_id}.jpg"
        face_path_rel = os.path.join("faces_db_images", face_filename)
        face_path_abs = os.path.join(BASE_DIR, face_path_rel)

        cv2.imwrite(face_path_abs, face_crop)

        # ===== 3. Update avatar_url =====
        database.update_student_avatar(student_id, face_path_rel)

        # ===== 4. Ghi embedding vào DB =====
        embedding_name = str(student_id)
        ok, msg = database.link_face_embedding(student_id, embedding_name, face_path_rel)
        if not ok:
            messagebox.showwarning("CSDL", f"Lỗi lưu embedding: {msg}")

        # ===== 5. Add vào RecognitionEngine =====
        self.recog.add_face(embedding_name, face_embedding)

        # ===== 6. Save faces_db.npz =====
        try:
            self.recog.save_db(os.path.join(BASE_DIR, DB_PATH_DEFAULT))
        except Exception as e:
            messagebox.showwarning("Cảnh báo", f"Đã đăng ký nhưng lỗi lưu DB: {e}")

        # ===== 7. Cache + sticky =====
        self.id_to_name_cache[student_id] = self.selected_student_name
        self.sticky = {
            "box": box,
            "name": self.selected_student_name,
            "id": student_id,
            "ttl": 30
        }
        self.force_recog_frames = 20

        self.set_status(f"Đã đăng ký khuôn mặt cho {self.selected_student_name}")


    def _open_writer(self, path, fps):
        # (Hàm này giữ nguyên)
        fourcc=cv2.VideoWriter_fourcc(*'mp4v')
        self.writer=cv2.VideoWriter(path, fourcc, float(fps), (VIEW_W, VIEW_H))
        if not self.writer.isOpened():
            self.writer.release(); self.writer=None
            raise RuntimeError("Không mở được VideoWriter.")

    def _close_writer(self):
        # (Hàm này giữ nguyên)
        if self.writer is not None:
            try: self.writer.release()
            except: pass
            self.writer=None

    def toggle_record(self):
        # (Hàm này giữ nguyên)
        if not self.running:
                   messagebox.showwarning("Thông báo", "Phải bật video hoặc webcam trước khi ghi.")
                   return
        if not self.recording:
            path=filedialog.asksaveasfilename(defaultextension=".mp4", initialfile=self.out_path,
                                                filetypes=[("MP4","*.mp4"),("AVI","*.avi"),("All","*.*")])
            if not path: return
            self.out_path=path 
            try: self._open_writer(self.out_path, self.out_fps)
            except Exception as e: messagebox.showerror("Lỗi", str(e)); return
            self.recording=True; self.set_status(f"ĐANG GHI: {self.out_path}")
        else:
            self._close_writer(); self.recording=False
            self.set_status(f"Đã dừng ghi. Lưu tại: {self.out_path}")

    def on_close_app(self):
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát ứng dụng?"):
            print("Đang đóng ứng dụng (từ nút X)...")
            
            self.on_close(force=True) 
            
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.destroy()
                except Exception as e:
                    print(f"Lỗi khi destroy root: {e}")

    def on_close(self):
        self.stop()

    def on_close(self, force=False): 
        try:
            if force: 
                print("Đang chạy Camera.on_close(force=True)...")
                
            try:
                self.finalize_session()
            except Exception as e:
                print(f"Lỗi khi finalize_session trong on_close: {e}")
                traceback.print_exc()

            self.running = False 
            
            # (# === SỬA ĐỔI 6: Đảm bảo cờ tắt khi đóng ===)
            self.enable_behavior_analysis = False
            
            if hasattr(self, 'after_id') and self.after_id:
                try:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
                    print("- Đã hủy vòng lặp 'after' (gui_loop).")
                except Exception as e:
                    print(f"Lỗi khi hủy 'after': {e}")
            try:
                if hasattr(self, 'capture_thread_handle') and self.capture_thread_handle and self.capture_thread_handle.is_alive():
                    self.capture_thread_handle.join(timeout=1.0) 
                    print("- Đã join Capture Thread.")
            except Exception as e:
                print(f"Lỗi khi join capture_thread: {e}")
            try:
                if hasattr(self, 'infer_thread_handle') and self.infer_thread_handle and self.infer_thread_handle.is_alive():
                    self.infer_thread_handle.join(timeout=1.0) 
                    print("- Đã join Infer Thread.")
            except Exception as e:
                print(f"Lỗi khi join infer_thread: {e}")
            if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
                self.cap.release()
                self.cap = None
                print("- Đã giải phóng VideoCapture.")
            self._close_writer()
            print("- Đã đóng VideoWriter (nếu có).")
            print("Camera.on_close() hoàn tất an toàn.")
        except Exception as e:
            print(f"!!! LỖI NGHIÊM TRỌNG TRONG KHI on_close: {e}")
            traceback.print_exc()