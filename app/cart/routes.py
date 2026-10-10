from flask import render_template, redirect, url_for, flash, request, session
from app.cart import bp
from app.models import Product, Order, OrderItem
from app.extensions import db

# ==========================================
# MODULE CART & CHECKOUT - PHỤ TRÁCH: ÁNH
# ==========================================

@bp.route('/')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = product.price * quantity
            total_price += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    str_id = str(product_id)
    cart[str_id] = cart.get(str_id, 0) + quantity
    session.modified = True

    flash(f'Đã thêm {product.name} vào giỏ hàng!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Ánh sẽ hoàn thiện logic checkout tại đây
    return render_template('checkout.html')
