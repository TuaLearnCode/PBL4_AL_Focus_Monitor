import mysql.connector
import bcrypt
from datetime import datetime
import getpass

def create_terminal_account():
    try:
        # 1. Kết nối cơ sở dữ liệu giamsatatt
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="", # Thay đổi theo máy bạn
            database="giamsatatt"
        )
        cursor = db.cursor()

        # 2. Nhập thông tin từ Terminal
        print("--- TẠO TÀI KHOẢN HỆ THỐNG ---")
        username = input("Nhập tên đăng nhập: ").strip()
        email = input("Nhập email: ").strip()
        # getpass sẽ ẩn mật khẩu khi bạn gõ
        password = getpass.getpass("Nhập mật khẩu: ").strip()

        if not username or not password:
            print("Lỗi: Tên đăng nhập và mật khẩu không được để trống!")
            return

        # 3. Mã hóa mật khẩu bằng bcrypt (Tự động tạo Salt)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        # 4. Lưu vào bảng account
        sql = "INSERT INTO account (username, email, password, created_at) VALUES (%s, %s, %s, %s)"
        val = (username, email if email else None, hashed, datetime.now())

        cursor.execute(sql, val)
        db.commit()
        
        print(f"\n[Thành công] Đã tạo tài khoản '{username}'!")
        print(f"Mã hash đã lưu: {hashed}") # Chuỗi này sẽ dài đúng 60 ký tự

    except mysql.connector.Error as err:
        print(f"Lỗi Database: {err}")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

if __name__ == "__main__":
    create_terminal_account()