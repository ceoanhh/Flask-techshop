from flask import render_template, request
from app.main import bp
from app.models import Product, Category

@bp.route('/')
@bp.route('/index')
def index():
    # 1. Lấy tham số category từ URL (Ví dụ: /index?category=dien-thoai)
    category_slug = request.args.get('category')
    categories = Category.query.all()
    
    # 2. Xử lý lọc danh mục (Hiển thị đầy đủ 16 sản phẩm thay vì limit 8)
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            products = Product.query.filter_by(category_id=cat.id).all()
        else:
            products = Product.query.all()
    else:
        products = Product.query.all()
        
    return render_template(
        'index.html', 
        products=products, 
        categories=categories, 
        current_category=category_slug
    )

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)