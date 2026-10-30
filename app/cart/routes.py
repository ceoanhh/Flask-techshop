from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from app.cart import bp
from app.cart.cart_service import CartService
from app.models import Order

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
    cart_items, total_price, total_quantity = CartService.get_cart_items()
    return render_template(
        'cart.html',
        cart_items=cart_items,
        total_price=total_price,
        total_quantity=total_quantity
    )

@bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Thêm sản phẩm vào giỏ hàng."""
    if request.is_json:
        data = request.get_json() or {}
        quantity = data.get('quantity', 1)
    else:
        quantity = request.form.get('quantity', 1)

    success, message = CartService.add_to_cart(product_id, quantity)

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
    """Xử lý quá trình đặt hàng và trừ tồn kho."""
    cart_items, total_price, total_quantity = CartService.get_cart_items()

    if not cart_items:
        flash('Giỏ hàng của bạn đang trống! Vui lòng chọn sản phẩm trước khi thanh toán.', 'warning')
        return redirect(url_for('cart.view_cart'))

    if request.method == 'POST':
        recipient_name = request.form.get('recipient_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        # Kiểm tra tính hợp lệ của dữ liệu đầu vào
        if not recipient_name or not phone or not address:
            flash('Vui lòng điền đầy đủ Họ tên, Số điện thoại và Địa chỉ giao hàng!', 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                total_price=total_price,
                total_quantity=total_quantity
            )

        if len(phone) < 9 or not phone.replace('+', '').replace(' ', '').isdigit():
            flash('Số điện thoại không hợp lệ, vui lòng kiểm tra lại!', 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                total_price=total_price,
                total_quantity=total_quantity
            )

        user_id = current_user.id if current_user.is_authenticated else None
        order, error = CartService.checkout(
            recipient_name=recipient_name,
            phone=phone,
            address=address,
            user_id=user_id
        )

        if error:
            flash(error, 'danger')
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                total_price=total_price,
                total_quantity=total_quantity
            )

        flash(f'Đặt hàng thành công! Mã đơn hàng của bạn là #{order.id}.', 'success')
        return redirect(url_for('cart.order_success', order_id=order.id))

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        total_price=total_price,
        total_quantity=total_quantity
    )

@bp.route('/success/<int:order_id>')
def order_success(order_id):
    """Trang thông báo đặt hàng thành công và chi tiết đơn hàng."""
    order = Order.query.get_or_404(order_id)
    return render_template('order_success.html', order=order)
