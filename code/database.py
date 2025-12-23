import mysql.connector
from mysql.connector import Error, IntegrityError
import os
from datetime import datetime
import bcrypt
import time
import random

# import sqlite3 # <- ĐÃ XÓA

# ===================================================================
# 1. CẤU HÌNH KẾT NỐI MYSQL
# !! QUAN TRỌNG: Hãy thay đổi các giá trị này !!
# ===================================================================
DB_CONFIG = {
    'host': '127.0.0.1',      # Hoặc IP của server MySQL
    'user': 'root', # Tên user MySQL của bạn
    'password': '', # Mật khẩu của user  
    'database': 'giamsatatt' # Tên database bạn đã tạo
}
# ===================================================================

def get_db_connection(): 
    """Tạo kết nối CSDL MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
        return None

def init_db():
    """
    Hàm này tạo tất cả các bảng CSDL (nếu chúng chưa tồn tại)
    dựa trên Django models của bạn.
    """
    print(f"Kiểm tra/Khởi tạo CSDL MySQL: {DB_CONFIG['database']}...")
    conn = get_db_connection()
    if conn is None:
        print("Không thể kết nối CSDL. Dừng khởi tạo.")
        return
        
    cursor = conn.cursor()

    try:
        # === 1. Bảng Student (từ model Student) ===
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            student_id  INT PRIMARY KEY AUTO_INCREMENT,
            name        VARCHAR(100) NOT NULL,
            class_name  VARCHAR(100) NOT NULL,
            gender      ENUM('Nam', 'Nữ', 'Khác') NOT NULL,
            birthday    DATE NOT NULL, -- Dùng kiểu DATE
            avatar_url VARCHAR(255),
            profile_avatar_url VARCHAR(255), 
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_student_class (class_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # === 2. Bảng Account (từ model Account) ===
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id          INT PRIMARY KEY AUTO_INCREMENT,
            username    VARCHAR(100) UNIQUE NOT NULL,
            password    VARCHAR(255) NOT NULL, -- Nhớ hash mật khẩu
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # === 3. Bảng Seasion (từ model Seasion) ===
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seasion (
            seasion_id  INT PRIMARY KEY AUTO_INCREMENT,
            class_name  VARCHAR(100) NOT NULL,
            start_time  DATETIME NOT NULL,
            end_time    DATETIME DEFAULT NULL, -- [SỬA] Phải là NULL (vì lúc tạo chưa kết thúc)
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_seasion_class (class_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # === 4. Bảng FaceEmbedding (từ model FaceEmbedding) ===
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_embedding (
            face_id         INT PRIMARY KEY AUTO_INCREMENT,
            student_id      INT UNIQUE NOT NULL, -- Liên kết 1-1
            embedding_name  VARCHAR(255) NOT NULL,
            face_image      VARCHAR(255), -- Lưu đường dẫn file ảnh
            registered_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (student_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # === 5. Bảng FocusRecord (từ model FocusRecord) ===
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_record (
            record_id   BIGINT PRIMARY KEY AUTO_INCREMENT,
            seasion_id  INT NOT NULL,
            student_id  INT NOT NULL,
            appear      BOOLEAN NOT NULL DEFAULT TRUE, -- 1 (True) 0 (False)
            focus_point INT NOT NULL DEFAULT 0,
            rate        ENUM('Cao độ', 'Tốt', 'Trung bình', 'Thấp') DEFAULT NULL, -- [SỬA] Phải là NULL (vì lúc tạo chưa có rate)
            note        TEXT,
            ts_created  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seasion_id) REFERENCES seasion (seasion_id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES student (student_id) ON DELETE CASCADE,
            UNIQUE INDEX idx_focus_seasion_student (seasion_id, student_id), -- [SỬA] Phải là UNIQUE
            INDEX idx_focus_rate (rate)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        conn.commit()
        print("Kiểm tra/Khởi tạo CSDL hoàn tất.")
        
    except Error as e:
        print(f"Lỗi khi khởi tạo bảng: {e}")
        conn.rollback() # Hoàn tác nếu có lỗi
    finally:
        cursor.close()
        conn.close()

# ===================================================================
# PASSWORD SECURITY (bcrypt)
# ===================================================================

# ================= PASSWORD =================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
# ===================================================================
# CÁC HÀM CRUD (TKINTER SẼ GỌI CÁC HÀM NÀY)
# (Đã cập nhật để dùng MySQL Connector)
# ===================================================================

# --- Các hàm CRUD cho Student ---

def get_all_students():
    """Lấy tất cả học sinh (thay thế Student.objects.all())."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return []
        # dictionary=True để trả về kết quả dạng dict
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM student ORDER BY class_name, name")
        students = cursor.fetchall()
        return students
    except Error as e:
        print(f"Lỗi khi lấy danh sách học sinh: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_student_by_id(student_db_id):
    """Lấy một học sinh bằng ID (thay thế Student.objects.get(pk=...))."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return None
        cursor = conn.cursor(dictionary=True)
        # Dùng %s làm placeholder
        cursor.execute("SELECT * FROM student WHERE student_id = %s", (student_db_id,))
        student = cursor.fetchone()
        return student # Trả về dict hoặc None
    except Error as e:
        print(f"Lỗi khi lấy học sinh (ID: {student_db_id}): {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def add_student(name, class_name, gender, birthday, avatar_url=None, profile_avatar_url=None):
    """
    Thêm học sinh mới và TRẢ VỀ ID MỚI ĐƯỢC TẠO.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return None, "Lỗi kết nối CSDL"
        
        # Kiểm tra định dạng ngày sinh
        try:
            # Chuyển đổi chuỗi YYYY-MM-DD sang đối tượng date
            datetime.strptime(birthday, '%Y-%m-%d').date()
        except ValueError:
            return None, "Định dạng ngày sinh không hợp lệ. Phải là YYYY-MM-DD."

        cursor = conn.cursor()
        sql = """INSERT INTO student (name, class_name, gender, birthday, avatar_url, profile_avatar_url) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        params = (name, class_name, gender, birthday, avatar_url, profile_avatar_url)
        cursor.execute(sql, params)
        
        conn.commit()
        new_id = cursor.lastrowid # Lấy ID tự tăng vừa được tạo
        
        # Trả về ID và thông báo thành công
        return new_id, f"Thêm thành công (ID: {new_id})" 
        
    except IntegrityError as e:
        if conn: conn.rollback()
        return None, f"Lỗi trùng lặp dữ liệu: {e}"
    except Error as e:
        if conn: conn.rollback()
        return None, f"Lỗi MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_student_avatar(student_db_id, avatar_url):
    """Cập nhật đường dẫn ảnh đại diện cho một học sinh đã có."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        sql = """UPDATE student SET avatar_url = %s
                 WHERE student_id = %s"""
        params = (avatar_url, student_db_id)
        cursor.execute(sql, params)
        
        conn.commit()
        return True, "Cập nhật avatar thành công"
    except Error as e:
        if conn: conn.rollback()
        return False, f"Lỗi MySQL khi cập nhật avatar: {e}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_student_profile_avatar(student_db_id, profile_avatar_url):
    """Cập nhật đường dẫn ảnh hồ sơ cho học sinh."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        sql = """UPDATE student SET profile_avatar_url = %s WHERE student_id = %s"""
        params = (profile_avatar_url, student_db_id)
        cursor.execute(sql, params)
        conn.commit()
        return True, "Cập nhật ảnh hồ sơ thành công"
    except Error as e:
        if conn: conn.rollback()
        return False, f"Lỗi MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
def delete_student(student_db_id):
    """Xóa hoàn toàn học sinh khỏi cơ sở dữ liệu.
    - XÓA: face_embedding, student, focus_record (do CASCADE)
    - XÓA: dữ liệu trong faces_db.npz và ảnh trong faces_db_images/
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        
        # 1. Xóa dữ liệu trong bảng face_embedding (nếu có)
        cursor.execute("DELETE FROM face_embedding WHERE student_id = %s", (student_db_id,))
        
        # 2. Xóa dữ liệu trong bảng focus_record (tự động do CASCADE, nhưng xóa rõ ràng)
        cursor.execute("DELETE FROM focus_record WHERE student_id = %s", (student_db_id,))
        
        # 3. Xóa học sinh khỏi bảng student
        cursor.execute("DELETE FROM student WHERE student_id = %s", (student_db_id,))
        
        if cursor.rowcount == 0:
            return False, "Không tìm thấy học sinh để xóa"
        
        conn.commit()
        
        # 4. Xóa face embedding trong file faces_db.npz
        import numpy as np
        import os
        npz_path = os.path.join(os.path.dirname(__file__), 'faces_db.npz')
        if os.path.exists(npz_path):
            try:
                data = np.load(npz_path, allow_pickle=True)
                embeddings = data.get('embeddings', np.array([]))
                labels = data.get('labels', np.array([]))
                names = data.get('names', np.array([]))
                
                if len(labels) > 0:
                    labels_list = labels.tolist()
                    student_id_str = str(student_db_id)
                    indices_to_keep = [i for i, label in enumerate(labels_list) if str(label) != student_id_str]
                    
                    if len(indices_to_keep) < len(labels_list):
                        new_embeddings = embeddings[indices_to_keep]
                        new_labels = labels[indices_to_keep]
                        new_names = names[indices_to_keep]
                        
                        np.savez(npz_path, 
                                 embeddings=new_embeddings, 
                                 labels=new_labels, 
                                 names=new_names)
                        print(f"Đã xóa {len(labels_list) - len(indices_to_keep)} face embedding(s) của {student_db_id} khỏi faces_db.npz")
                        
            except Exception as e:
                print(f"Lỗi khi xóa face embedding trong npz: {e}")
        
        # 5. Xóa ảnh khuôn mặt trong thư mục faces_db_images/
        images_dir = os.path.join(os.path.dirname(__file__), 'faces_db_images')
        if os.path.exists(images_dir):
            try:
                for filename in os.listdir(images_dir):
                    if filename.startswith(f"{student_db_id}_"):
                        file_path = os.path.join(images_dir, filename)
                        os.remove(file_path)
                        print(f"Đã xóa ảnh: {filename}")
            except Exception as e:
                print(f"Lỗi khi xóa ảnh: {e}")
        
        return True, "Đã xóa hoàn toàn học sinh khỏi hệ thống"
        
    except Error as e:
        if conn: conn.rollback()
        return False, f"Lỗi MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_student(
    student_db_id,
    name=None,
    class_name=None,
    gender=None,
    birthday_str=None,
    profile_avatar_url=None
):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Lỗi kết nối CSDL"

        # Validate ngày sinh
        if birthday_str:
            try:
                datetime.strptime(birthday_str, "%Y-%m-%d")
            except ValueError:
                return False, "Ngày sinh phải theo định dạng YYYY-MM-DD"

        cursor = conn.cursor()

        update_fields = []
        params = []

        if name is not None:
            update_fields.append("name = %s")
            params.append(name)

        if class_name is not None:
            update_fields.append("class_name = %s")
            params.append(class_name)

        if gender is not None:
            update_fields.append("gender = %s")
            params.append(gender)

        if birthday_str is not None:
            update_fields.append("birthday = %s")
            params.append(birthday_str)

        if profile_avatar_url is not None:
            update_fields.append("profile_avatar_url = %s")
            params.append(profile_avatar_url)

        if not update_fields:
            return True, "Không có dữ liệu thay đổi"

        params.append(student_db_id)

        sql = f"""
            UPDATE student
            SET {', '.join(update_fields)}
            WHERE student_id = %s
        """

        cursor.execute(sql, params)
        conn.commit()

        return True, "Cập nhật học sinh thành công"

    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Lỗi MySQL: {e}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# --- Các hàm CRUD cho Account ---

# ================= LOGIN =================
def verify_account(username, plain_password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM account WHERE username = %s",
        (username,)
    )
    acc = cursor.fetchone()

    if not acc or not acc["password"]:
        cursor.close()
        conn.close()
        return False, "Tài khoản không tồn tại"

    try:
        if bcrypt.checkpw(
            plain_password.encode(),
            acc["password"].encode()
        ):
            cursor.close()
            conn.close()
            return True, acc
        else:
            cursor.close()
            conn.close()
            return False, "Sai mật khẩu"
    except Exception:
        cursor.close()
        conn.close()
        return False, "Mật khẩu không hợp lệ"

# ================= RESET PASSWORD =================
def create_reset_code(email):
    otp = str(random.randint(100000, 999999))
    expire = int(time.time()) + 300

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO password_reset (email, otp_code, expire_at)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            otp_code = VALUES(otp_code),
            expire_at = VALUES(expire_at)
    """, (email, otp, expire))

    conn.commit()
    cursor.close()
    conn.close()
    return otp

def verify_reset_code(email, otp):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM password_reset WHERE email = %s",
        (email,)
    )
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return False
    if row["otp_code"] != otp:
        return False
    if row["expire_at"] < time.time():
        return False

    return True

def reset_password(email, new_password):
    hashed = hash_password(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE account SET password = %s WHERE email = %s",
        (hashed, email)
    )

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        raise Exception("Email không tồn tại")

    cursor.execute(
        "DELETE FROM password_reset WHERE email = %s",
        (email,)
    )

    conn.commit()
    cursor.close()
    conn.close()

# --- Các hàm CRUD cho FaceEmbedding ---

def link_face_embedding(student_db_id, embedding_name, face_image_path):
    """Đăng ký khuôn mặt (thay thế logic trong register_face)."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        
        # Lấy thời gian hiện tại để gửi vào CSDL
        now = datetime.now() 
        
        # --- SỬA CÂU SQL VÀ PARAMS ---
        # Thêm 'updated_at' vào cả phần INSERT
        sql = """INSERT INTO face_embedding (student_id, embedding_name, face_image, registered_at, updated_at) 
                 VALUES (%s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE 
                 embedding_name = VALUES(embedding_name), 
                 face_image = VALUES(face_image),
                 updated_at = %s;""" # Cập nhật 'updated_at' khi 'ON DUPLICATE'
        
        # Sửa 'params' để có 6 giá trị (5 cho INSERT, 1 cho UPDATE)
        params = (student_db_id, embedding_name, face_image_path, now, now, now) 
        cursor.execute(sql, params)
        
        conn.commit()
        return True, "Liên kết khuôn mặt thành công"
        
    except IntegrityError as e:
        conn.rollback()
        return False, f"Lỗi khóa ngoại: Student ID {student_db_id} không tồn tại. {e}"
    except Error as e:
        if conn: conn.rollback()
        return False, f"Lỗi MySQL: {e}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
# ===================================================================
# [SỬA] CÁC HÀM MỚI CHO SESSION (Đã đổi sang MySQL)
# ===================================================================

def create_session(class_name, start_time):
    """Tạo một session mới và trả về session_id."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return None, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO seasion (class_name, start_time) 
        VALUES (%s, %s)
        """
        # start_time nên là đối tượng datetime
        cursor.execute(sql, (class_name, start_time))
        conn.commit()
        
        new_session_id = cursor.lastrowid
        return new_session_id, "Tạo session thành công"
        
    except Error as e: # [SỬA] Đổi từ sqlite3.Error
        if conn:
            conn.rollback()
        print(f"Lỗi CSDL khi tạo session: {e}")
        return None, str(e)
    finally:
        if cursor: cursor.close() # [SỬA] Thêm
        if conn:
            conn.close()

def end_session(session_id, end_time):
    """Cập nhật end_time cho một session."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        
        sql = "UPDATE seasion SET end_time = %s WHERE seasion_id = %s" # [SỬA] Đổi ?
        cursor.execute(sql, (end_time, session_id))
        conn.commit()
        return True, "Cập nhật end_time thành công"
        
    except Error as e: # [SỬA] Đổi từ sqlite3.Error
        if conn:
            conn.rollback()
        print(f"Lỗi CSDL khi kết thúc session: {e}")
        return False, str(e)
    finally:
        if cursor: cursor.close() # [SỬA] Thêm
        if conn:
            conn.close()

def mark_student_appearance(session_id, student_id):
    """Tạo bản ghi focus_record khi học sinh xuất hiện lần đầu."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        
        # [SỬA] Đổi sang cú pháp MySQL 'INSERT IGNORE' và %s
        # (Bảng phải có UNIQUE INDEX(seasion_id, student_id)
        # (Bảng phải cho phép 'rate' là NULL)
        sql = """
        INSERT IGNORE INTO focus_record (seasion_id, student_id, appear, ts_created) 
        VALUES (%s, %s, 1, %s)
        """
        
        cursor.execute(sql, (session_id, student_id, datetime.now()))
        conn.commit()
        return True, "Đã ghi nhận"
        
    except Error as e: # [SỬA] Đổi từ sqlite3.Error
        if conn:
            conn.rollback()
        print(f"Lỗi CSDL khi ghi nhận (appear): {e}")
        return False, str(e)
    finally:
        if cursor: cursor.close() # [SỬA] Thêm
        if conn:
            conn.close()

def update_focus_record(session_id, student_id, focus_point, rate, note):
    """Cập nhật kết quả cuối cùng cho học sinh vào focus_record."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: return False, "Lỗi kết nối CSDL"
        cursor = conn.cursor()
        
        # [SỬA] Đổi ? sang %s
        sql = """
        UPDATE focus_record 
        SET focus_point = %s, rate = %s, note = %s
        WHERE seasion_id = %s AND student_id = %s
        """
        cursor.execute(sql, (focus_point, rate, note, session_id, student_id))
        conn.commit()
        
        if cursor.rowcount == 0:
             print(f"Không tìm thấy focus_record để update cho student {student_id} session {session_id}")
             return False, "Không tìm thấy bản ghi"
             
        return True, "Cập nhật thành công"
        
    except Error as e: # [SỬA] Đổi từ sqlite3.Error
        if conn:
            conn.rollback()
        print(f"Lỗi CSDL khi cập nhật focus_record: {e}")
        return False, str(e)
    finally:
        if cursor: cursor.close() # [SỬA] Thêm
        if conn:
            conn.close()