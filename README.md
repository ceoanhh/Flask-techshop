# 🛒 Flask-TechShop: Website Bán Hàng Điện Tử

Hệ thống website thương mại điện tử chuyên cung cấp thiết bị công nghệ và điện tử được xây dựng bằng **Python Flask**, áp dụng kiến trúc **Application Factory + Blueprints**.

---

## 👥 Nhóm Thực Hiện
- **Ánh:** Backend & Giỏ Hàng (Core Architecture, Models, Cart Session, Order Transaction, Admin Backend)
- **Dần:** Authentication & Frontend (Giao diện người dùng, Bootstrap 5, Đăng ký / Đăng nhập, Session User)
- **Bảo:** Thống kê & Biểu đồ (Analytics, Chart APIs, Biểu đồ Chart.js Dashboard Admin)

---

## 🛠️ Công Nghệ Sử Dụng
- **Backend:** Python 3.9+, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate
- **Frontend:** Jinja2, HTML5, CSS3, Bootstrap 5, Bootstrap Icons, Chart.js
- **Database:** SQLite (Phát triển) / MySQL / PostgreSQL

---

## 📂 Cấu Trúc Dự Án
```text
Flask-techshop/
│
├── app/
│   ├── __init__.py           # Application Factory (create_app)
│   ├── extensions.py         # db, login_manager, migrate
│   ├── models.py             # Database Models (User, Category, Product, Order, OrderItem)
│   ├── auth/                 # Module Đăng nhập / Đăng ký (Dần)
│   ├── main/                 # Module Trang chủ & Chi tiết sản phẩm
│   ├── cart/                 # Module Giỏ hàng & Thanh toán (Ánh)
│   ├── admin/                # Module Quản trị & Thống kê (Ánh + Bảo)
│   ├── static/               # CSS, JS, Images (Dần + Bảo)
│   └── templates/            # Giao diện Jinja2 HTML
│
├── config.py                 # Cấu hình hệ thống
├── run.py                    # Khởi động server
├── seed.py                   # Tạo tài khoản & dữ liệu mẫu
├── requirements.txt          # Thư viện phụ thuộc
├── KE_HOACH_TRIEN_KHAI.md    # Tài liệu đặc tả và phân công chi tiết
└── .gitignore
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Thử

### 1. Clone repository
```bash
git clone https://github.com/ceoanhh/Flask-techshop.git
cd Flask-techshop
```

### 2. Tạo môi trường ảo & Cài đặt thư viện
```bash
# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt môi trường:
# Trên macOS / Linux:
source venv/bin/activate
# Trên Windows:
venv\Scripts\activate

# Cài đặt thư viện:
pip install -r requirements.txt
```

### 3. Tạo dữ liệu mẫu (Seed Data)
Lệnh này sẽ tự động khởi tạo CSDL SQLite và thêm sẵn các danh mục, sản phẩm mẫu và tài khoản test:
```bash
python seed.py
```
> **Tài khoản mẫu được tạo sẵn:**
> - **Admin:** `admin` | Mật khẩu: `admin123`
> - **Khách hàng:** `khachhang` | Mật khẩu: `user123`

### 4. Khởi chạy ứng dụng
```bash
python run.py
```
Mở trình duyệt truy cập: **`http://127.0.0.1:5000`**
- Truy cập trang Admin: **`http://127.0.0.1:5000/admin`**
