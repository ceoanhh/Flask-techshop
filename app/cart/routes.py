import re
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user, login_user
from app.cart import bp
from app.cart.cart_service import CartService
from app.models import Order, User
from app.extensions import db

# ==========================================
# MODULE CART & CHECKOUT - PHỤ TRÁCH: ÁNH
# ==========================================

def _is_ajax():
    """Kiểm tra request có phải gửi qua AJAX/Fetch hay không."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.is_json
        or request.accept_mimetypes.best == 'application/json'
    )

@bp.route('/')
def view_cart():
    """Trang xem chi tiết giỏ hàng và danh sách sản phẩm đã chọn."""
    cart_items_all, all_total_price, all_total_quantity = CartService.get_cart_items()
    
    current_pids = [item['product'].id for item in cart_items_all]
    selected_pids = session.get('selected_cart_pids')

    if selected_pids is None:
        # Lần đầu vào giỏ: mặc định chọn tất cả sản phẩm
        selected_pids = current_pids
    else:
        # Giữ nguyên các sản phẩm đã chọn trước đó mà vẫn còn tồn tại trong giỏ
        selected_pids = [pid for pid in selected_pids if pid in current_pids]

    session['selected_cart_pids'] = selected_pids
    session.modified = True

    # Tính tổng tiền và tổng số lượng theo đúng các sản phẩm đang được chọn
    _, selected_total_price, selected_total_quantity = CartService.get_cart_items(selected_ids=selected_pids)

    return render_template(
        'cart.html',
        cart_items=cart_items_all,
        selected_pids=selected_pids,
        total_price=selected_total_price,
        total_quantity=selected_total_quantity,
        cart_total_quantity=all_total_quantity
    )

@bp.route('/save-selection', methods=['POST'])
def save_selection():
    """Lưu danh sách ID sản phẩm được tích chọn vào session để giữ nguyên khi thoát ra xem hàng."""
    if request.is_json:
        data = request.get_json() or {}
        selected = data.get('selected', [])
    else:
        raw = request.form.get('selected', '')
        selected = [x.strip() for x in raw.split(',') if x.strip().isdigit()]

    selected_ids = []
    for x in selected:
        try:
            selected_ids.append(int(x))
        except (ValueError, TypeError):
            continue

    session['selected_cart_pids'] = selected_ids
    session.modified = True
    return jsonify({'success': True, 'selected_ids': selected_ids})

@bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Thêm sản phẩm vào giỏ hàng."""
    if request.is_json:
        data = request.get_json() or {}
        quantity = data.get('quantity', 1)
    else:
        quantity = request.form.get('quantity', 1)

    success, message = CartService.add_to_cart(product_id, quantity)

    if success:
        # Khi thêm sản phẩm mới vào giỏ, nếu session đã lưu danh sách chọn trước đó,
        # tự động thêm sản phẩm mới này vào danh sách chọn mà vẫn bảo toàn các lựa chọn cũ
        selected_pids = session.get('selected_cart_pids')
        if selected_pids is not None and product_id not in selected_pids:
            selected_pids.append(product_id)
            session['selected_cart_pids'] = selected_pids
            session.modified = True

    if _is_ajax():
        cart_items, total_price, total_quantity = CartService.get_cart_items()
        return jsonify({
            'success': success,
            'message': message,
            'cart_count': len(CartService.get_raw_cart()),
            'total_quantity': total_quantity,
            'total_price': total_price
        }), (200 if success else 400)

    flash(message, 'success' if success else 'danger')
    return redirect(request.referrer or url_for('cart.view_cart'))

@bp.route('/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Cập nhật số lượng của sản phẩm trong giỏ hàng."""
    if request.is_json:
        data = request.get_json() or {}
        quantity = data.get('quantity', 1)
    else:
        quantity = request.form.get('quantity', 1)

    success, message = CartService.update_cart(product_id, quantity)

    if _is_ajax():
        cart_items, total_price, total_quantity = CartService.get_cart_items()
        item_total = 0
        item_quantity = 0
        for item in cart_items:
            if item['product'].id == product_id:
                item_total = item['item_total']
                item_quantity = item['quantity']
                break

        return jsonify({
            'success': success,
            'message': message,
            'cart_count': len(CartService.get_raw_cart()),
            'total_quantity': total_quantity,
            'total_price': total_price,
            'product_id': product_id,
            'item_quantity': item_quantity,
            'item_total': item_total
        }), (200 if success else 400)

    flash(message, 'success' if success else 'warning')
    return redirect(url_for('cart.view_cart'))

@bp.route('/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Xóa một sản phẩm khỏi giỏ hàng."""
    success, message = CartService.remove_from_cart(product_id)

    if success and 'selected_cart_pids' in session:
        selected_pids = session.get('selected_cart_pids', [])
        if product_id in selected_pids:
            selected_pids.remove(product_id)
            session['selected_cart_pids'] = selected_pids
            session.modified = True

    if _is_ajax():
        cart_items, total_price, total_quantity = CartService.get_cart_items()
        return jsonify({
            'success': success,
            'message': message,
            'cart_count': len(CartService.get_raw_cart()),
            'total_quantity': total_quantity,
            'total_price': total_price,
            'product_id': product_id
        }), (200 if success else 400)

    flash(message, 'info' if success else 'warning')
    return redirect(url_for('cart.view_cart'))

@bp.route('/clear', methods=['POST'])
def clear_cart():
    """Làm trống toàn bộ giỏ hàng."""
    CartService.clear_cart()
    session.pop('selected_cart_pids', None)

    if _is_ajax():
        return jsonify({
            'success': True,
            'message': 'Đã làm trống toàn bộ giỏ hàng.',
            'cart_count': 0,
            'total_quantity': 0,
            'total_price': 0
        }), 200

    flash('Đã làm trống toàn bộ giỏ hàng.', 'info')
    return redirect(url_for('cart.view_cart'))

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Xử lý quá trình đặt hàng và trừ tồn kho (Bắt buộc đăng nhập, chỉ mua các sản phẩm được chọn)."""
    selected_raw = request.args.get('selected') or request.form.get('selected')
    if not current_user.is_authenticated:
        flash('Vui lòng đăng nhập tài khoản để tiến hành đặt hàng!', 'info')
        next_url = url_for('cart.checkout', selected=selected_raw) if selected_raw else url_for('cart.checkout')
        return redirect(url_for('auth.login', next=next_url))

    selected_ids = None
    if selected_raw:
        try:
            selected_ids = [int(x.strip()) for x in selected_raw.split(',') if x.strip().isdigit()]
        except (ValueError, TypeError):
            selected_ids = None
    elif 'selected_cart_pids' in session:
        selected_ids = session.get('selected_cart_pids')

    cart_items, total_price, total_quantity = CartService.get_cart_items(selected_ids=selected_ids)

    if not cart_items:
        flash('Không có sản phẩm nào được chọn để thanh toán! Vui lòng chọn sản phẩm trong giỏ hàng.', 'warning')
        return redirect(url_for('cart.view_cart'))

    if request.method == 'POST':
        recipient_name = request.form.get('recipient_name', '').strip()
        phone = request.form.get('phone', '').strip().replace(' ', '').replace('.', '').replace('-', '')
        address = request.form.get('address', '').strip()

        # Kiểm tra tính hợp lệ của dữ liệu đầu vào
        if not recipient_name or not phone or not address:
            flash('Vui lòng điền đầy đủ Họ tên, Số điện thoại và Địa chỉ giao hàng!', 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                total_price=total_price,
                total_quantity=total_quantity,
                selected_raw=selected_raw
            )

        VIETNAM_PHONE_REGEX = r'^(0|\+84)(3[2-9]|5[2689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7}$'
        if not re.match(VIETNAM_PHONE_REGEX, phone):
            flash('Số điện thoại không đúng chuẩn 10 chữ số nhà mạng Việt Nam (đầu 03, 05, 07, 08, 09)!', 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                total_price=total_price,
                total_quantity=total_quantity,
                selected_raw=selected_raw
            )

        user_id = current_user.id if current_user.is_authenticated else None
        payment_method = request.form.get('payment_method', 'cod')
        if payment_method not in ['cod', 'qr_code']:
            payment_method = 'cod'

        order, error = CartService.checkout(
            recipient_name=recipient_name,
            phone=phone,
            address=address,
            user_id=user_id,
            selected_ids=selected_ids,
            payment_method=payment_method
        )

        if error:
            flash(error, 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                total_price=total_price,
                total_quantity=total_quantity,
                selected_raw=selected_raw
            )

        flash(f'Đặt hàng thành công! Mã đơn hàng của bạn là #{order.id}.', 'success')
        # Dọn dẹp các sản phẩm đã mua khỏi danh sách chọn trong session
        if 'selected_cart_pids' in session:
            current_selected = session.get('selected_cart_pids', [])
            purchased_pids = [item['product'].id for item in cart_items]
            session['selected_cart_pids'] = [pid for pid in current_selected if pid not in purchased_pids]
            session.modified = True
        return redirect(url_for('cart.order_success', order_id=order.id))

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        total_price=total_price,
        total_quantity=total_quantity,
        selected_raw=selected_raw
    )

@bp.route('/success/<int:order_id>')
def order_success(order_id):
    """Trang thông báo đặt hàng thành công và chi tiết đơn hàng."""
    order = Order.query.get_or_404(order_id)
    return render_template('order_success.html', order=order)

@bp.route('/order/<int:order_id>/confirm-payment', methods=['POST'])
def confirm_order_payment(order_id):
    """Khách hàng bấm xác nhận đã chuyển khoản thành công qua mã QR."""
    order = Order.query.get_or_404(order_id)
    
    if order.payment_status == 'paid':
        flash('Đơn hàng này đã được xác nhận thanh toán thành công!', 'info')
    else:
        order.payment_status = 'awaiting_confirmation'
        db.session.commit()
        flash(f'Đã gửi thông báo xác nhận chuyển khoản cho đơn #{order.id}! Quản trị viên TechShop sẽ đối soát và xử lý trong ít phút.', 'success')

    if _is_ajax():
        return jsonify({
            'success': True,
            'payment_status': order.payment_status,
            'payment_status_label': order.payment_status_label,
            'message': f'Đã gửi thông báo xác nhận chuyển khoản cho đơn #{order.id}!'
        })

    return redirect(request.referrer or url_for('cart.order_success', order_id=order.id))

@bp.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Khách hàng hủy đơn hàng khi chưa thanh toán / đang chờ xử lý."""
    order = Order.query.get_or_404(order_id)

    if order.status == 'cancelled':
        flash(f'Đơn hàng #{order.id} đã ở trạng thái đã hủy trước đó.', 'info')
        return redirect(request.referrer or url_for('cart.order_success', order_id=order.id))

    if order.status == 'completed':
        flash('Không thể hủy đơn hàng đã hoàn thành!', 'danger')
        return redirect(request.referrer or url_for('cart.order_success', order_id=order.id))

    if order.payment_status == 'paid':
        flash('Đơn hàng đã được thanh toán thành công. Vui lòng liên hệ hotline TechShop để được hỗ trợ hủy đơn và hoàn tiền!', 'warning')
        return redirect(request.referrer or url_for('cart.order_success', order_id=order.id))

    if order.payment_status == 'awaiting_confirmation':
        flash('Đơn hàng đã được gửi xác nhận chuyển khoản và đang chờ Admin kiểm tra tài khoản. Bạn không thể tự hủy đơn lúc này! Vui lòng liên hệ TechShop nếu cần hỗ trợ.', 'warning')
        if _is_ajax():
            return jsonify({
                'success': False,
                'message': 'Đơn hàng đang chờ Admin đối soát thanh toán, bạn không thể tự hủy đơn.'
            }), 400
        return redirect(request.referrer or url_for('cart.order_success', order_id=order.id))

    try:
        # Cập nhật trạng thái đã hủy
        order.status = 'cancelled'

        # Hoàn trả lại số lượng tồn kho sản phẩm
        for item in order.items.all():
            if item.product:
                item.product.stock_quantity += item.quantity

        db.session.commit()
        flash(f'Đã hủy đơn hàng #{order.id} thành công! Toàn bộ sản phẩm đã được hoàn trả lại kho.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi hủy đơn hàng: {str(e)}', 'danger')

    if _is_ajax():
        return jsonify({
            'success': True,
            'message': f'Đã hủy đơn hàng #{order.id} thành công!',
            'status': order.status,
            'status_label': order.status_label
        })

    return redirect(request.referrer or url_for('cart.order_success', order_id=order.id))

@bp.route('/order/<int:order_id>/reorder', methods=['GET', 'POST'])
def reorder(order_id):
    """Đặt lại đơn hàng: nạp lại các sản phẩm của đơn hàng cũ vào giỏ hàng."""
    order = Order.query.get_or_404(order_id)
    added_count = 0
    for item in order.items.all():
        if item.product and item.product.stock_quantity > 0:
            qty = min(item.quantity, item.product.stock_quantity)
            CartService.add_to_cart(item.product_id, qty)
            added_count += 1

    if added_count > 0:
        flash(f'Đã nạp lại các sản phẩm từ đơn #{order.id} vào giỏ hàng của bạn.', 'success')
    else:
        flash('Các sản phẩm trong đơn hàng này hiện đã hết hàng trong kho!', 'warning')

    return redirect(url_for('cart.view_cart'))

@bp.route('/tracking')
def order_tracking():
    """Tra cứu đơn hàng và xem lịch sử mua hàng qua Số điện thoại hoặc Mã đơn hàng."""
    search_query = request.args.get('q', '').strip()
    orders = []
    searched = bool(search_query)

    if search_query:
        clean_q = search_query.replace(' ', '').replace('.', '').replace('-', '')
        found = []

        # 1. Tìm chính xác theo mã đơn nếu là số ngắn
        if clean_q.isdigit() and len(clean_q) <= 6:
            single_order = db.session.get(Order, int(clean_q))
            if single_order:
                found.append(single_order)

        # 2. Tìm theo số điện thoại (chứa hoặc bằng số điện thoại nhập vào)
        phone_matches = Order.query.filter(Order.phone.ilike(f'%{clean_q}%')).order_by(Order.created_at.desc()).all()
        for o in phone_matches:
            if o not in found:
                found.append(o)

        orders = found
    elif current_user.is_authenticated:
        # Nếu đã đăng nhập và chưa tìm kiếm gì -> Tự động hiển thị toàn bộ lịch sử đơn hàng của tài khoản
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()

    return render_template(
        'order_tracking.html',
        orders=orders,
        search_query=search_query,
        searched=searched
    )

@bp.route('/claim-account/<int:order_id>', methods=['POST'])
def claim_account(order_id):
    """Cơ chế liên kết tài khoản sau khi mua hàng (Claim Account)."""
    if current_user.is_authenticated:
        flash('Bạn hiện đã đăng nhập tài khoản rồi.', 'info')
        return redirect(url_for('cart.order_tracking'))

    order = Order.query.get_or_404(order_id)
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not username or not email or not password:
        flash('Vui lòng điền đầy đủ Tên tài khoản, Email và Mật khẩu!', 'danger')
        return redirect(url_for('cart.order_success', order_id=order.id))

    if len(password) < 6:
        flash('Mật khẩu bảo mật phải có ít nhất 6 ký tự!', 'warning')
        return redirect(url_for('cart.order_success', order_id=order.id))

    if password != confirm_password:
        flash('Mật khẩu xác nhận không trùng khớp!', 'danger')
        return redirect(url_for('cart.order_success', order_id=order.id))

    # Kiểm tra xem username hoặc email đã tồn tại chưa
    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash('Tên người dùng hoặc Email này đã tồn tại, vui lòng chọn tên/email khác!', 'danger')
        return redirect(url_for('cart.order_success', order_id=order.id))

    # Tạo User mới
    new_user = User(username=username, email=email, role='customer')
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.flush()

    # Tự động liên kết TẤT CẢ các đơn hàng của số điện thoại này vào tài khoản mới
    linked_orders = Order.query.filter_by(phone=order.phone, user_id=None).all()
    for o in linked_orders:
        o.user_id = new_user.id

    db.session.commit()

    # Đăng nhập luôn cho khách hàng
    login_user(new_user)
    flash(f'Tạo tài khoản thành công! Đã tự động lưu trữ và liên kết {len(linked_orders)} đơn hàng thuộc số điện thoại {order.phone} vào tài khoản của bạn.', 'success')
    return redirect(url_for('cart.order_tracking'))
