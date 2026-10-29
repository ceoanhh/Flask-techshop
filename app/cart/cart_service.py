from flask import session
from app.extensions import db
from app.models import Product, Order, OrderItem

class CartService:
    """Service xử lý nghiệp vụ giỏ hàng và thanh toán đặt hàng."""

    @staticmethod
    def get_raw_cart():
        if 'cart' not in session:
            session['cart'] = {}
        return session['cart']

    @classmethod
    def get_cart_items(cls):
        """
        Lấy danh sách các sản phẩm trong giỏ hàng kèm thông tin chi tiết.
        Sử dụng batch query để tối ưu hiệu năng (tránh N+1 query).
        """
        cart = cls.get_raw_cart()
        if not cart:
            return [], 0.0, 0

        # Trích xuất danh sách ID sản phẩm hợp lệ
        valid_pids = []
        for pid_str in cart.keys():
            try:
                valid_pids.append(int(pid_str))
            except (ValueError, TypeError):
                continue

        if not valid_pids:
            return [], 0.0, 0

        # Lấy tất cả sản phẩm trong 1 query duy nhất
        products = {p.id: p for p in Product.query.filter(Product.id.in_(valid_pids)).all()}

        items = []
        total_price = 0.0
        total_quantity = 0
        cleaned_cart = {}

        for pid_str, qty in cart.items():
            try:
                pid = int(pid_str)
            except (ValueError, TypeError):
                continue

            product = products.get(pid)
            if not product:
                # Sản phẩm đã bị xóa khỏi hệ thống -> tự động lọc bỏ khỏi giỏ
                continue

            try:
                qty = max(1, int(qty))
            except (ValueError, TypeError):
                qty = 1

            item_total = product.price * qty
            total_price += item_total
            total_quantity += qty
            cleaned_cart[str(pid)] = qty

            items.append({
                'product': product,
                'quantity': qty,
                'item_total': item_total,
                'is_in_stock': product.stock_quantity >= qty,
                'max_stock': product.stock_quantity
            })

        # Cập nhật lại session nếu có sản phẩm không còn tồn tại
        if len(cleaned_cart) != len(cart):
            session['cart'] = cleaned_cart
            session.modified = True

        return items, total_price, total_quantity

    @classmethod
    def add_to_cart(cls, product_id, quantity=1):
        """Thêm sản phẩm vào giỏ hàng với kiểm tra tồn kho."""
        product = db.session.get(Product, product_id)
        if not product:
            return False, "Sản phẩm không tồn tại!"

        if product.stock_quantity <= 0:
            return False, f"Sản phẩm '{product.name}' hiện đã hết hàng!"

        try:
            quantity = max(1, int(quantity))
        except (ValueError, TypeError):
            quantity = 1

        cart = cls.get_raw_cart()
        str_id = str(product_id)
        current_qty = cart.get(str_id, 0)
        new_qty = current_qty + quantity

        if new_qty > product.stock_quantity:
            cart[str_id] = product.stock_quantity
            session.modified = True
            return True, f"Đã thêm tối đa {product.stock_quantity} sản phẩm '{product.name}' theo số lượng tồn kho."

        cart[str_id] = new_qty
        session.modified = True
        return True, f"Đã thêm '{product.name}' vào giỏ hàng thành công!"

    @classmethod
    def update_cart(cls, product_id, quantity):
        """Cập nhật số lượng của một sản phẩm trong giỏ hàng."""
        product = db.session.get(Product, product_id)
        if not product:
            return False, "Sản phẩm không tồn tại!"

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 1

        cart = cls.get_raw_cart()
        str_id = str(product_id)

        if quantity <= 0:
            return cls.remove_from_cart(product_id)

        if quantity > product.stock_quantity:
            cart[str_id] = product.stock_quantity
            session.modified = True
            return True, f"Số lượng sản phẩm '{product.name}' đã được điều chỉnh về tồn kho tối đa ({product.stock_quantity})."

        cart[str_id] = quantity
        session.modified = True
        return True, f"Đã cập nhật số lượng cho '{product.name}'."

    @classmethod
    def remove_from_cart(cls, product_id):
        """Xóa sản phẩm khỏi giỏ hàng."""
        cart = cls.get_raw_cart()
        str_id = str(product_id)
        if str_id in cart:
            product = db.session.get(Product, product_id)
            prod_name = product.name if product else "Sản phẩm"
            del cart[str_id]
            session.modified = True
            return True, f"Đã xóa '{prod_name}' khỏi giỏ hàng."
        return False, "Sản phẩm không có trong giỏ hàng."

    @classmethod
    def clear_cart(cls):
        """Làm trống giỏ hàng."""
        session['cart'] = {}
        session.modified = True
        return True, "Đã làm trống giỏ hàng."

    @classmethod
    def checkout(cls, recipient_name, phone, address, user_id=None):
        """
        Thực hiện giao dịch thanh toán đặt hàng:
        - Kiểm tra tính hợp lệ của giỏ hàng
        - Kiểm tra số lượng tồn kho trước khi tạo đơn
        - Trừ tồn kho và lưu Order + OrderItem vào DB bằng transaction
        - Xóa giỏ hàng sau khi thành công
        """
        items, total_price, _ = cls.get_cart_items()

        if not items:
            return None, "Giỏ hàng của bạn đang trống, không thể thanh toán!"

        # Kiểm tra tồn kho toàn bộ giỏ hàng
        for item in items:
            prod = item['product']
            qty = item['quantity']
            if prod.stock_quantity < qty:
                return None, f"Sản phẩm '{prod.name}' chỉ còn {prod.stock_quantity} chiếc trong kho (bạn đặt {qty} chiếc)."

        try:
            order = Order(
                user_id=user_id,
                recipient_name=recipient_name.strip(),
                phone=phone.strip(),
                address=address.strip(),
                total_amount=total_price,
                status='pending'
            )
            db.session.add(order)
            db.session.flush()  # Để lấy order.id

            for item in items:
                prod = item['product']
                qty = item['quantity']
                
                # Trừ tồn kho
                prod.stock_quantity -= qty

                # Tạo OrderItem
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=prod.price
                )
                db.session.add(order_item)

            db.session.commit()

            # Dọn dẹp giỏ hàng
            cls.clear_cart()
            return order, None

        except Exception as e:
            db.session.rollback()
            return None, f"Có lỗi xảy ra khi tạo đơn hàng: {str(e)}"
