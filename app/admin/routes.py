from flask import render_template, request, flash, redirect, url_for
from app.admin import bp
from app.models import Product, Order
from app.extensions import db

# ==========================================
# MODULE ADMIN QUẢN LÝ - PHỤ TRÁCH: ÁNH
# ==========================================

@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    total_orders = Order.query.count()
    total_products = Product.query.count()
    return render_template('admin/dashboard.html', total_orders=total_orders, total_products=total_products)

@bp.route('/products')
def manage_products():
    products = Product.query.all()
    return render_template('admin/products_manage.html', products=products)

@bp.route('/orders')
def manage_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders_manage.html', orders=orders)
