from flask import render_template, request
from app.main import bp
from app.models import Product, Category

@bp.route('/')
@bp.route('/index')
def index():
    products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', products=products, categories=categories)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)
