from flask import render_template, request, redirect, url_for
from app.main import bp
from app.models import Product, Category

@bp.route('/')
@bp.route('/index')
def index():
    # 1. Lấy tham số tìm kiếm (q) và tham số danh mục (category) từ URL
    search_query = request.args.get('q', '').strip()
    category_slug = request.args.get('category')
    
    categories = Category.query.all()
    
    # 2. Bắt đầu từ Query tất cả sản phẩm
    query = Product.query

    # 3. Nếu người dùng nhập từ khóa tìm kiếm -> Lọc theo tên sản phẩm (không phân biệt hoa/thường)
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    # 4. Nếu chọn lọc thêm Danh mục
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter(Product.category_id == cat.id)

    # 5. Lấy danh sách sản phẩm kết quả
    products = query.all()
        
    return render_template(
        'index.html', 
        products=products, 
        categories=categories, 
        current_category=category_slug,
        search_query=search_query
    )

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@bp.route('/profile')
def profile_shortcut():
    """Điều hướng nhanh đến trang hồ sơ cá nhân."""
    return redirect(url_for('auth.profile'))