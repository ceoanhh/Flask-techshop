import unittest
from app import create_app
from app.extensions import db
from app.models import User, Product, Category, Order, OrderItem
from app.cart.cart_service import CartService

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = '/tmp/techshop_test_uploads'

class TestCartAndAdminTasks(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Tạo category mẫu
        self.category = Category(name='Điện thoại', slug='dien-thoai')
        db.session.add(self.category)
        db.session.commit()

        # Tạo sản phẩm mẫu
        self.product = Product(
            name='iPhone 15 Pro Max',
            category_id=self.category.id,
            price=30000000,
            stock_quantity=10,
            description='Test phone',
            image_url='default_product.png'
        )
        db.session.add(self.product)

        # Tạo user admin & customer
        self.admin = User(username='admin_test', email='admin@test.vn', role='admin')
        self.admin.set_password('admin123')
        db.session.add(self.admin)

        self.customer = User(username='user_test', email='user@test.vn', role='customer')
        self.customer.set_password('user123')
        db.session.add(self.customer)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # ------------------------------------------------------------------
    # 1. TEST CART SERVICE & LOGIC
    # ------------------------------------------------------------------
    def test_cart_service_add_and_get(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['cart'] = {}

            # Thêm sản phẩm hợp lệ
            with self.app.test_request_context():
                with c.session_transaction() as sess:
                    from flask import session
                    success, msg = CartService.add_to_cart(self.product.id, quantity=2)
                    self.assertTrue(success)
                    items, total_price, total_qty = CartService.get_cart_items()
                    self.assertEqual(len(items), 1)
                    self.assertEqual(total_qty, 2)
                    self.assertEqual(total_price, 60000000)

    def test_cart_service_stock_limit(self):
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                # Thêm vượt quá tồn kho (tồn kho là 10, yêu cầu 15)
                success, msg = CartService.add_to_cart(self.product.id, quantity=15)
                self.assertTrue(success)
                items, total_price, total_qty = CartService.get_cart_items()
                self.assertEqual(total_qty, 10)  # Tự động điều chỉnh về 10

    def test_cart_service_update_and_remove(self):
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                CartService.add_to_cart(self.product.id, quantity=3)
                # Cập nhật số lượng
                success, msg = CartService.update_cart(self.product.id, quantity=5)
                self.assertTrue(success)
                items, total_price, total_qty = CartService.get_cart_items()
                self.assertEqual(total_qty, 5)

                # Cập nhật về 0 -> xóa
                CartService.update_cart(self.product.id, quantity=0)
                items, total_price, total_qty = CartService.get_cart_items()
                self.assertEqual(len(items), 0)

    def test_checkout_success_and_stock_deduction(self):
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                CartService.add_to_cart(self.product.id, quantity=4)
                order, err = CartService.checkout(
                    recipient_name='Ánh Tester',
                    phone='0987654321',
                    address='Hà Nội',
                    user_id=self.customer.id
                )
                self.assertIsNotNone(order)
                self.assertIsNone(err)
                self.assertEqual(order.total_amount, 120000000)
                self.assertEqual(order.status, 'pending')

                # Kiểm tra tồn kho sau khi trừ: 10 - 4 = 6
                updated_prod = db.session.get(Product, self.product.id)
                self.assertEqual(updated_prod.stock_quantity, 6)

                # Kiểm tra OrderItem
                items = order.items.all()
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0].quantity, 4)

                # Giỏ hàng phải rỗng sau khi checkout
                raw_cart = CartService.get_raw_cart()
                self.assertEqual(len(raw_cart), 0)

    # ------------------------------------------------------------------
    # 2. TEST HTTP ROUTES CHO CART & CHECKOUT
    # ------------------------------------------------------------------
    def test_cart_http_flow(self):
        # 1. Thêm sản phẩm vào giỏ qua route POST
        res = self.client.post(f'/cart/add/{self.product.id}', data={'quantity': 2}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'iPhone 15 Pro Max', res.data)

        # 2. Xem giỏ hàng
        res = self.client.get('/cart/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'iPhone 15 Pro Max', res.data)

        # 3. Đặt hàng qua route POST
        res = self.client.post('/cart/checkout', data={
            'recipient_name': 'Nguyễn Văn A',
            'phone': '0912345678',
            'address': '123 Phố Huế, Hà Nội'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Đặt Hàng Thành Công'.encode('utf-8'), res.data)

    # ------------------------------------------------------------------
    # 3. TEST PHÂN QUYỀN ADMIN (ACCESS CONTROL)
    # ------------------------------------------------------------------
    def test_admin_access_unauthorized(self):
        # Chưa đăng nhập -> redirect sang login
        res = self.client.get('/admin/products', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

    def test_admin_access_forbidden_for_customer(self):
        # Đăng nhập bằng tài khoản role=customer
        with self.client:
            self.client.post('/auth/login', data={'email': 'user@test.vn', 'password': 'user123'})
            # Giả lập current_user là customer
            from flask_login import login_user
            with self.app.test_request_context():
                login_user(self.customer)
            res = self.client.get('/admin/products', follow_redirects=True)
            # Phải bị chặn và quay về trang index
            self.assertIn('không có quyền truy cập'.encode('utf-8'), res.data)

    # ------------------------------------------------------------------
    # 4. TEST ADMIN CRUD SẢN PHẨM & ĐƠN HÀNG
    # ------------------------------------------------------------------
    def test_admin_product_crud(self):
        # Giả lập đăng nhập admin
        with self.client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(self.admin.id)
                sess['_fresh'] = True

            # 1. Thêm sản phẩm mới
            res = c.post('/admin/products/add', data={
                'name': 'MacBook Pro M3 Max',
                'category_id': self.category.id,
                'price': '65000000',
                'stock_quantity': '5',
                'description': 'Laptop Apple M3 đỉnh cao',
                'image_url': 'default_product.png'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('MacBook Pro M3 Max'.encode('utf-8'), res.data)

            new_prod = Product.query.filter_by(name='MacBook Pro M3 Max').first()
            self.assertIsNotNone(new_prod)

            # 2. Sửa sản phẩm
            res = c.post(f'/admin/products/{new_prod.id}/edit', data={
                'name': 'MacBook Pro M3 Max (Đã sửa)',
                'category_id': self.category.id,
                'price': '63000000',
                'stock_quantity': '8',
                'description': 'Đã sửa mô tả',
                'image_url': 'default_product.png'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            edited_prod = db.session.get(Product, new_prod.id)
            self.assertEqual(edited_prod.name, 'MacBook Pro M3 Max (Đã sửa)')
            self.assertEqual(edited_prod.stock_quantity, 8)

            # 3. Xóa sản phẩm chưa có đơn hàng
            res = c.post(f'/admin/products/{new_prod.id}/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            deleted_prod = db.session.get(Product, new_prod.id)
            self.assertIsNone(deleted_prod)

    def test_admin_order_status_update_and_inventory_refund(self):
        # Tạo 1 đơn hàng với 3 sản phẩm iPhone
        order = Order(
            recipient_name='Khách Hàng',
            phone='0912345678',
            address='Hà Nội',
            total_amount=90000000,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(order_id=order.id, product_id=self.product.id, quantity=3, unit_price=30000000)
        self.product.stock_quantity -= 3  # Kho còn 7
        db.session.add(item)
        db.session.commit()

        self.assertEqual(self.product.stock_quantity, 7)

        with self.client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(self.admin.id)
                sess['_fresh'] = True

            # 1. Hủy đơn hàng -> Tồn kho phải được hoàn lại (+3 = 10)
            res = c.post(f'/admin/orders/{order.id}/status', data={'status': 'cancelled'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            updated_order = db.session.get(Order, order.id)
            self.assertEqual(updated_order.status, 'cancelled')
            reloaded_prod = db.session.get(Product, self.product.id)
            self.assertEqual(reloaded_prod.stock_quantity, 10)

            # 2. Chuyển lại sang hoàn thành -> Tồn kho phải bị trừ lại (-3 = 7)
            res = c.post(f'/admin/orders/{order.id}/status', data={'status': 'completed'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            reloaded_prod = db.session.get(Product, self.product.id)
            self.assertEqual(reloaded_prod.stock_quantity, 7)

    def test_cart_ajax_operations(self):
        """Kiểm tra phản hồi JSON cho các thao tác giỏ hàng qua AJAX (không tải lại trang)."""
        ajax_headers = {'X-Requested-With': 'XMLHttpRequest'}

        # 1. Thêm vào giỏ qua AJAX
        res = self.client.post(
            f'/cart/add/{self.product.id}',
            data={'quantity': 2},
            headers=ajax_headers
        )
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['cart_count'], 1)
        self.assertEqual(json_data['total_quantity'], 2)
        self.assertEqual(json_data['total_price'], 60000000)

        # 2. Cập nhật số lượng qua AJAX
        res = self.client.post(
            f'/cart/update/{self.product.id}',
            data={'quantity': 3},
            headers=ajax_headers
        )
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['total_quantity'], 3)
        self.assertEqual(json_data['item_total'], 90000000)

        # 3. Xóa sản phẩm qua AJAX
        res = self.client.post(
            f'/cart/remove/{self.product.id}',
            headers=ajax_headers
        )
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['cart_count'], 0)
        self.assertEqual(json_data['total_quantity'], 0)

        # 4. Thêm lại rồi Xóa toàn bộ qua AJAX
        self.client.post(f'/cart/add/{self.product.id}', data={'quantity': 1}, headers=ajax_headers)
        res = self.client.post('/cart/clear', headers=ajax_headers)
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['cart_count'], 0)

if __name__ == '__main__':
    unittest.main()
