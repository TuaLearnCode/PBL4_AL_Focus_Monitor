 📊 Hệ thống Điểm danh & Giám sát Sự tập trung bằng AI

Đây là dự án Python sử dụng **Computer Vision và AI** để:
- Điểm danh học sinh tự động bằng nhận diện khuôn mặt
- Theo dõi sự tập trung trong buổi học
- Lưu lịch sử, thống kê và báo cáo kết quả

---

## 🚀 Chức năng chính

- 📷 Nhận diện khuôn mặt realtime qua camera
- 👥 Quản lý học sinh (thêm / sửa / xóa)
- 📝 Tạo buổi học, điểm danh tự động và tính điểm tập trung
- 📚 Lịch sử các buổi học
- 📊 Thống kê mức độ tập trung
- 🧠 Phân tích hành vi học sinh (AI)

---

## 🛠 Công nghệ sử dụng

- Python 3.11
- OpenCV
- CustomTkinter / Tkinter
- MySQL
- YOLO (phát hiện khuôn mặt)
- Face Recognition (embedding)
- NumPy, Pillow

---

## 📁 Cấu trúc thư mục (rút gọn)

detection
    │──code
        │── app_main.py
        │── ai_summarizer.py
        │── behavior_analyer.py
        │── focus_manager.py
        │── recognition_engine.py
        │── login.py
        │── hash-password.py
        │── email_service.py
        │── home.py
        │── camera.py
        │── hocsinh.py
        │── lichsu.py
        │── chitiet.py
        │── thongke.py
        │── database.py
        │── data_loader.py
        │── faces_db.npz
        │── faces_db_images/
        │── image/
        │── student_avatars/
        │── image/
        │── remember.txt
    │── data.yml
    │── README.md
    │── .gitignore
    │── requirement.txt
    │── venv/ (tự tạo)
    │── weights/
        │──best.pt
        │──last.pt


## ⚙️ Cài đặt & Chạy chương trình

---

## ⚙️ Cài đặt & Chạy chương trình

### 1️⃣ Clone repository
```bash
git clone https://github.com/TuaLearnCode/PBL4_AL_Focus_Monitor.git
cd Detection

### 2️⃣ Cài đặt python
    - Cài python 3.11 (thích hợp nhất với dự án của chúng tôi)

### 3️⃣ Chạy các lệnh sau
    py -3.11 -m venv venv
    venv\Scripts\activate     
    pip install -r requirements.txt                         
    python.exe -m pip install --upgrade pip 

### 3️⃣ Thay đổi các điểm sau: 
    - Trong email_service.py: 
        EMAIL = "Email của bạn"
        APP_PASSWORD = "Bạn tự tạo"
    - Trong ai_summarizer.py:
        GEMINI_API_KEY = "Bạn tự tạo"
    - Trong database.py: 
        DB_CONFIG = {
            'host': 'localhost',      # Hoặc IP của server MySQL
            'user': 'root', # Tên user MySQL của bạn
            'password': 'root', # Mật khẩu của user  
            'database': 'giamsatatt' # Tên database bạn đã tạo
    

### 4️⃣ Chạy chương trình
    python app_main.py

⚠️ Lưu ý
1. Thư mục venv/ không được push lên GitHub
2. 📦 Model
    - File model YOLO (`best.pt`, `last.pt`, `yolo8n-face-lindevs.pt`, `yolo8s-face-lindevs.pt` ) không được push lên GitHub.
    - Vui lòng huấn luyện hoặc tải model và đặt vào thư mục `weights/`.
3. File faces_db.npz và ảnh khuôn mặt chỉ dùng local
4. Cần cấu hình database MySQL trước khi chạy

