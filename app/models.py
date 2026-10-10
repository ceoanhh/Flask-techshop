from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer')  # 'customer' hoặc 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order #{self.id} - {self.status}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<OrderItem Prod:{self.product_id} x {self.quantity}>'
