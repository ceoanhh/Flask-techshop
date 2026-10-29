import os
import time
from flask import render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from app.admin import bp
from app.admin.decorators import admin_required
from app.models import Product, Order, OrderItem, Category
from app.extensions import db

# ==========================================
# MODULE ADMIN QUẢN LÝ - PHỤ TRÁCH: ÁNH
# ==========================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.before_request
def require_admin_access():
    """Tự động kiểm tra quyền Admin cho toàn bộ các endpoint thuộc Blueprint Admin."""
    from flask_login import current_user
    if not current_user.is_authenticated:
        flash('Vui lòng đăng nhập bằng tài khoản Quản trị viên để tiếp tục.', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập vào trang Quản trị hệ thống!', 'danger')
        return redirect(url_for('main.index'))


# ----------------------------------------------------
# 1. DASHBOARD TỔNG QUAN
# ----------------------------------------------------
@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    total_orders = Order.query.count()
    total_products = Product.query.count()
    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        total_products=total_products
    )


# ----------------------------------------------------
# 2. QUẢN LÝ SẢN PHẨM (CRUD)
# ----------------------------------------------------
@bp.route('/products')
def manage_products():
    """Hiển thị danh sách sản phẩm với hỗ trợ tìm kiếm và lọc danh mục."""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('q', '').strip()

    query = Product.query

    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.id.desc()).all()
    categories = Category.query.all()

    return render_template(
        'admin/products_manage.html',
        products=products,
        categories=categories,
        selected_category=category_id,
        search_query=search
    )


@bp.route('/products/add', methods=['POST'])
def add_product():
    """Xử lý thêm sản phẩm mới."""
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id', type=int)
    price = request.form.get('price', type=float)
    stock_quantity = request.form.get('stock_quantity', type=int)
    description = request.form.get('description', '').strip()
    image_url_input = request.form.get('image_url', '').strip()

    # Kiểm tra dữ liệu đầu vào
    if not name:
        flash('Tên sản phẩm không được để trống!', 'danger')
        return redirect(url_for('admin.manage_products'))

    if price is None or price < 0:
        flash('Giá sản phẩm phải lớn hơn hoặc bằng 0!', 'danger')
        return redirect(url_for('admin.manage_products'))

    if stock_quantity is None or stock_quantity < 0:
        flash('Số lượng tồn kho phải là số không âm!', 'danger')
        return redirect(url_for('admin.manage_products'))

    # Xử lý ảnh sản phẩm (Ưu tiên File Upload -> URL -> Default)
    image_url = 'default_product.png'
    file = request.files.get('image_file')

    if file and file.filename and allowed_file(file.filename):
        timestamp = int(time.time())
        filename = secure_filename(f"{timestamp}_{file.filename}")
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(upload_path)
            image_url = f"uploads/{filename}"
        except Exception as e:
            flash(f"Lỗi khi tải ảnh lên: {str(e)}", 'warning')
    elif image_url_input:
        image_url = image_url_input

    try:
        product = Product(
            name=name,
            category_id=category_id,
            price=price,
            stock_quantity=stock_quantity,
            description=description,
            image_url=image_url
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Đã thêm sản phẩm "{product.name}" thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi lưu sản phẩm vào cơ sở dữ liệu: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_products'))


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    """Trang xem và chỉnh sửa thông tin sản phẩm."""
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        description = request.form.get('description', '').strip()
        image_url_input = request.form.get('image_url', '').strip()

        if not name:
            flash('Tên sản phẩm không được để trống!', 'danger')
            return redirect(url_for('admin.edit_product', product_id=product.id))

        if price is None or price < 0:
            flash('Giá sản phẩm phải lớn hơn hoặc bằng 0!', 'danger')
            return redirect(url_for('admin.edit_product', product_id=product.id))

        if stock_quantity is None or stock_quantity < 0:
            flash('Số lượng tồn kho không được âm!', 'danger')
            return redirect(url_for('admin.edit_product', product_id=product.id))

        product.name = name
        product.category_id = category_id
        product.price = price
        product.stock_quantity = stock_quantity
        product.description = description

        # Xử lý cập nhật ảnh nếu có file mới
        file = request.files.get('image_file')
        if file and file.filename and allowed_file(file.filename):
            timestamp = int(time.time())
            filename = secure_filename(f"{timestamp}_{file.filename}")
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(upload_path)
                product.image_url = f"uploads/{filename}"
            except Exception as e:
                flash(f"Lỗi khi cập nhật ảnh: {str(e)}", 'warning')
        elif image_url_input:
            product.image_url = image_url_input

        try:
            db.session.commit()
            flash(f'Đã cập nhật sản phẩm "{product.name}" thành công!', 'success')
            return redirect(url_for('admin.manage_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật sản phẩm: {str(e)}', 'danger')

    return render_template('admin/product_edit.html', product=product, categories=categories)


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Xử lý xóa sản phẩm an toàn với kiểm tra ràng buộc đơn hàng."""
    product = Product.query.get_or_404(product_id)

    # Kiểm tra xem sản phẩm đã có trong đơn hàng nào chưa
    has_orders = OrderItem.query.filter_by(product_id=product_id).first()
    if has_orders:
        flash(
            f'Không thể xóa "{product.name}" vì sản phẩm đã có lịch sử đơn hàng! '
            'Bạn có thể chỉnh sửa tồn kho về 0 để ngừng bán.',
            'warning'
        )
        return redirect(url_for('admin.manage_products'))

    try:
        prod_name = product.name
        db.session.delete(product)
        db.session.commit()
        flash(f'Đã xóa sản phẩm "{prod_name}" thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa sản phẩm: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_products'))


# ----------------------------------------------------
# 3. QUẢN LÝ ĐƠN HÀNG & CẬP NHẬT TRẠNG THÁI
# ----------------------------------------------------
@bp.route('/orders')
def manage_orders():
    """Xem danh sách đơn hàng với bộ lọc trạng thái và tìm kiếm."""
    status_filter = request.args.get('status', 'all')
    search = request.args.get('q', '').strip()

    query = Order.query

    if status_filter in ['pending', 'completed', 'cancelled']:
        query = query.filter_by(status=status_filter)

    if search:
        if search.startswith('#'):
            search = search[1:]
        if search.isdigit():
            query = query.filter((Order.id == int(search)) | (Order.phone.ilike(f'%{search}%')))
        else:
            query = query.filter(
                (Order.recipient_name.ilike(f'%{search}%')) |
                (Order.phone.ilike(f'%{search}%')) |
                (Order.address.ilike(f'%{search}%'))
            )

    orders = query.order_by(Order.created_at.desc()).all()

    # Thống kê nhanh số lượng đơn
    counts = {
        'all': Order.query.count(),
        'pending': Order.query.filter_by(status='pending').count(),
        'completed': Order.query.filter_by(status='completed').count(),
        'cancelled': Order.query.filter_by(status='cancelled').count()
    }

    return render_template(
        'admin/orders_manage.html',
        orders=orders,
        status_filter=status_filter,
        counts=counts,
        search_query=search
    )


@bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    """Xem chi tiết một đơn hàng cụ thể."""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@bp.route('/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """
    Cập nhật trạng thái đơn hàng:
    - Nếu chuyển sang 'cancelled': tự động hoàn lại tồn kho cho các sản phẩm trong đơn.
    - Nếu khôi phục từ 'cancelled' sang trạng thái khác: kiểm tra và trừ lại tồn kho.
    """
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    valid_statuses = ['pending', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        flash('Trạng thái đơn hàng không hợp lệ!', 'danger')
        return redirect(request.referrer or url_for('admin.manage_orders'))

    old_status = order.status

    if old_status == new_status:
        flash(f'Đơn hàng #{order.id} đã ở trạng thái {order.status_label}.', 'info')
        return redirect(request.referrer or url_for('admin.manage_orders'))

    try:
        # Nếu hủy đơn: hoàn lại tồn kho
        if new_status == 'cancelled' and old_status != 'cancelled':
            for item in order.items.all():
                if item.product:
                    item.product.stock_quantity += item.quantity

        # Nếu mở lại đơn từ cancelled: kiểm tra và trừ tồn kho
        elif old_status == 'cancelled' and new_status in ['pending', 'completed']:
            for item in order.items.all():
                if item.product and item.product.stock_quantity < item.quantity:
                    flash(
                        f'Không thể khôi phục đơn: Sản phẩm "{item.product.name}" trong kho '
                        f'chỉ còn {item.product.stock_quantity} (đơn yêu cầu {item.quantity}).',
                        'danger'
                    )
                    return redirect(request.referrer or url_for('admin.manage_orders'))

            for item in order.items.all():
                if item.product:
                    item.product.stock_quantity -= item.quantity

        order.status = new_status
        db.session.commit()
        flash(f'Đã cập nhật trạng thái đơn #{order.id} thành "{order.status_label}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi cập nhật trạng thái đơn: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('admin.manage_orders'))


# ----------------------------------------------------
# 4. QUẢN LÝ DANH MỤC NHANH
# ----------------------------------------------------
@bp.route('/categories/add', methods=['POST'])
def add_category():
    """Thêm danh mục sản phẩm mới."""
    name = request.form.get('name', '').strip()
    slug = request.form.get('slug', '').strip().lower()

    if not name:
        flash('Tên danh mục không được để trống!', 'danger')
        return redirect(url_for('admin.manage_products'))

    if not slug:
        slug = name.lower().replace(' ', '-')

    existing = Category.query.filter((Category.name == name) | (Category.slug == slug)).first()
    if existing:
        flash('Danh mục này đã tồn tại!', 'warning')
        return redirect(url_for('admin.manage_products'))

    try:
        cat = Category(name=name, slug=slug)
        db.session.add(cat)
        db.session.commit()
        flash(f'Đã thêm danh mục "{name}" thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi thêm danh mục: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_products'))
