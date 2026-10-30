from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer')  # 'customer' hoặc 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)

    products = db.relationship('Product', backref='category_rel', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, default='')
    image_url = db.Column(db.String(256), default='default_product.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recipient_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'cancelled'
    payment_method = db.Column(db.String(30), default='cod')  # 'cod', 'qr_code'
    payment_status = db.Column(db.String(30), default='unpaid')  # 'unpaid', 'awaiting_confirmation', 'paid'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def status_label(self):
        labels = {
            'pending': 'Chờ xử lý',
            'completed': 'Hoàn thành',
            'cancelled': 'Đã hủy'
        }
        return labels.get(self.status, self.status)

    @property
    def status_badge_class(self):
        classes = {
            'pending': 'warning',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return classes.get(self.status, 'secondary')

    @property
    def payment_method_label(self):
        if self.payment_method == 'qr_code':
            return 'Chuyển khoản QR'
        return 'Thanh toán khi nhận hàng (COD)'

    @property
    def payment_status_label(self):
        labels = {
            'unpaid': 'Chưa thanh toán',
            'awaiting_confirmation': 'Chờ xác nhận CK',
            'paid': 'Đã thanh toán'
        }
        return labels.get(self.payment_status, self.payment_status)

    @property
    def payment_status_badge_class(self):
        classes = {
            'unpaid': 'secondary',
            'awaiting_confirmation': 'warning text-dark',
            'paid': 'success'
        }
        return classes.get(self.payment_status, 'secondary')

    @property
    def qr_code_url(self):
        """Tạo đường dẫn mã VietQR tự động qua Napas / VietQR API."""
        bank_id = "MB"
        account_no = "0366760056"
        account_name = "TECHSHOP STORE"
        amount = int(self.total_amount)
        memo = f"TECHSHOP {self.id}"
        from urllib.parse import quote
        return f"https://img.vietqr.io/image/{bank_id}-{account_no}-compact2.jpg?amount={amount}&addInfo={quote(memo)}&accountName={quote(account_name)}"

    @property
    def qr_expiry_seconds(self):
        """Tính số giây còn lại của hiệu lực 15 phút (900 giây) kể từ khi tạo đơn."""
        if not self.created_at:
            return 0
        diff = (datetime.utcnow() - self.created_at).total_seconds()
        remaining = 900 - int(diff)
        return max(0, remaining)

    @property
    def is_qr_expired(self):
        return self.qr_expiry_seconds <= 0

    def __repr__(self):
        return f'<Order #{self.id} - {self.status}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __repr__(self):
        return f'<OrderItem Prod:{self.product_id} x {self.quantity}>'
