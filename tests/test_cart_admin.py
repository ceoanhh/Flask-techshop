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

    def test_selective_checkout_retains_unselected_items(self):
        """Kiểm tra tính năng mua sản phẩm được tích chọn: chỉ thanh toán món được chọn, món còn lại giữ nguyên trong giỏ."""
        # Tạo thêm sản phẩm thứ 2
        prod2 = Product(
            name='MacBook Pro M3',
            category_id=self.category.id,
            price=45000000,
            stock_quantity=5,
            description='Test laptop',
            image_url='laptop.png'
        )
        db.session.add(prod2)
        db.session.commit()

        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                # Thêm cả 2 sản phẩm vào giỏ
                CartService.add_to_cart(self.product.id, quantity=2)
                CartService.add_to_cart(prod2.id, quantity=1)

                # Giỏ hàng hiện có 2 món
                items, total_price, total_qty = CartService.get_cart_items()
                self.assertEqual(len(items), 2)
                self.assertEqual(total_qty, 3)

                # Khách chỉ chọn mua sản phẩm 1 (self.product.id)
                selected_items, sel_price, sel_qty = CartService.get_cart_items(selected_ids=[self.product.id])
                self.assertEqual(len(selected_items), 1)
                self.assertEqual(selected_items[0]['product'].id, self.product.id)
                self.assertEqual(sel_qty, 2)
                self.assertEqual(sel_price, 60000000)

                # Thực hiện checkout chỉ với sản phẩm 1
                order, err = CartService.checkout(
                    recipient_name='Ánh Tester',
                    phone='0987654321',
                    address='Hà Nội',
                    user_id=self.customer.id,
                    selected_ids=[self.product.id]
                )
                self.assertIsNotNone(order)
                self.assertIsNone(err)
                self.assertEqual(order.total_amount, 60000000)

                # Sản phẩm 1 bị trừ tồn kho: 10 - 2 = 8
                p1 = db.session.get(Product, self.product.id)
                self.assertEqual(p1.stock_quantity, 8)

                # Sản phẩm 2 KHÔNG bị trừ tồn kho: vẫn còn 5
                p2 = db.session.get(Product, prod2.id)
                self.assertEqual(p2.stock_quantity, 5)

                # Giỏ hàng VẪN CÒN sản phẩm 2 với số lượng 1
                raw_cart = CartService.get_raw_cart()
                self.assertNotIn(str(self.product.id), raw_cart)
                self.assertIn(str(prod2.id), raw_cart)
                self.assertEqual(raw_cart[str(prod2.id)], 1)

                # Kiểm tra get_cart_items trả về đúng sản phẩm 2
                remaining_items, remaining_price, remaining_qty = CartService.get_cart_items()
                self.assertEqual(len(remaining_items), 1)
                self.assertEqual(remaining_items[0]['product'].id, prod2.id)
                self.assertEqual(remaining_qty, 1)
                self.assertEqual(remaining_price, 45000000)

    def test_cart_selection_persisted_when_browsing_and_adding_more(self):
        """
        Kiểm tra kịch bản người dùng:
        - Có 3 sản phẩm, user chọn SP 1 và 2 (bỏ chọn SP 3).
        - Thoát ra xem hàng và thêm SP 4 vào giỏ.
        - Quay lại giỏ hàng: SP 1 và 2 VẪN GIỮ ĐƯỢC CHỌN, SP 3 vẫn bị bỏ chọn.
        """
        # Tạo thêm SP 2, SP 3, SP 4
        p2 = Product(name='MacBook Pro M3', category_id=self.category.id, price=40000000, stock_quantity=5, description='laptop', image_url='p2.png')
        p3 = Product(name='AirPods Pro 2', category_id=self.category.id, price=5000000, stock_quantity=10, description='audio', image_url='p3.png')
        p4 = Product(name='Apple Watch Ultra', category_id=self.category.id, price=20000000, stock_quantity=8, description='watch', image_url='p4.png')
        db.session.add_all([p2, p3, p4])
        db.session.commit()

        # Thêm 3 sản phẩm đầu vào giỏ: SP 1, SP 2, SP 3
        self.client.post(f'/cart/add/{self.product.id}', data={'quantity': 1})
        self.client.post(f'/cart/add/{p2.id}', data={'quantity': 1})
        self.client.post(f'/cart/add/{p3.id}', data={'quantity': 1})

        # Vào giỏ hàng lần đầu: cả 3 sản phẩm được chọn
        res = self.client.get('/cart/')
        self.assertEqual(res.status_code, 200)

        # Người dùng bỏ chọn SP 3, chỉ giữ lại SP 1 và SP 2
        res_save = self.client.post('/cart/save-selection', json={'selected': [self.product.id, p2.id]})
        self.assertEqual(res_save.status_code, 200)
        self.assertEqual(res_save.get_json()['selected_ids'], [self.product.id, p2.id])

        # Người dùng thoát ra xem hàng và thêm SP 4 vào giỏ hàng
        res_add4 = self.client.post(f'/cart/add/{p4.id}', data={'quantity': 1})
        self.assertEqual(res_add4.status_code, 302)

        # Người dùng quay lại giỏ hàng
        res_cart = self.client.get('/cart/')
        self.assertEqual(res_cart.status_code, 200)
        html = res_cart.data.decode('utf-8')

        # Kiểm tra URL nút checkout truyền đúng danh sách ID đã chọn: 1, 2, 4
        self.assertIn(f'selected={self.product.id},{p2.id},{p4.id}', html)
        self.assertIn('90,000,000 VNĐ', html)

        # Kiểm tra SP 1 và SP 2 VẪN ĐƯỢC CHỌN (có checked trong row)
        row_p1 = html.split(f'id="cart-row-{self.product.id}"')[1].split('</tr>')[0]
        self.assertIn('checked', row_p1)

        row_p2 = html.split(f'id="cart-row-{p2.id}"')[1].split('</tr>')[0]
        self.assertIn('checked', row_p2)

        # Kiểm tra SP 3 KHÔNG ĐƯỢC CHỌN (không có checked trong row)
        row_p3 = html.split(f'id="cart-row-{p3.id}"')[1].split('</tr>')[0]
        self.assertNotIn('checked', row_p3)

        # Kiểm tra SP 4 mới thêm vào CŨNG ĐƯỢC CHỌN (có checked trong row)
        row_p4 = html.split(f'id="cart-row-{p4.id}"')[1].split('</tr>')[0]
        self.assertIn('checked', row_p4)

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

        # 3. Đăng nhập tài khoản trước khi Checkout
        self.client.post('/auth/login', data={
            'login_id': 'user@test.vn',
            'password': 'user123'
        })

        # 4. Đặt hàng qua route POST
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

    def test_order_tracking(self):
        """Kiểm tra chức năng tra cứu đơn hàng bằng Số điện thoại hoặc Mã đơn hàng."""
        # Tạo đơn hàng mẫu
        order = Order(
            recipient_name='Lê Văn Test',
            phone='0988776655',
            address='Đà Nẵng',
            total_amount=30000000,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        # 1. Tra cứu bằng số điện thoại
        res = self.client.get('/cart/tracking?q=0988776655')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'0988776655', res.data)
        self.assertIn(f'#Đơn {order.id}'.encode('utf-8'), res.data)

        # 2. Tra cứu bằng mã đơn hàng
        res = self.client.get(f'/cart/tracking?q={order.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'0988776655', res.data)

        # 3. Tra cứu không tìm thấy
        res = self.client.get('/cart/tracking?q=0000000000')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Không tìm thấy đơn hàng'.encode('utf-8'), res.data)

    def test_claim_account_and_link_guest_orders(self):
        """Kiểm tra cơ chế liên kết tài khoản sau khi mua (Claim Account)."""
        # Tạo 2 đơn hàng vãng lai cùng số điện thoại 0977112233
        order1 = Order(recipient_name='Khách 1', phone='0977112233', address='HN', total_amount=1000, user_id=None)
        order2 = Order(recipient_name='Khách 1', phone='0977112233', address='HN', total_amount=2000, user_id=None)
        db.session.add_all([order1, order2])
        db.session.commit()

        self.assertIsNone(order1.user_id)
        self.assertIsNone(order2.user_id)

        # Thực hiện Claim Account
        res = self.client.post(f'/cart/claim-account/{order1.id}', data={
            'username': 'claimuser',
            'email': 'claim@techshop.vn',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)

        # Kiểm tra user mới đã được tạo
        new_user = User.query.filter_by(username='claimuser').first()
        self.assertIsNotNone(new_user)

        # Kiểm tra cả 2 đơn hàng cũ đã được tự động liên kết vào new_user.id
        reloaded_o1 = db.session.get(Order, order1.id)
        reloaded_o2 = db.session.get(Order, order2.id)
        self.assertEqual(reloaded_o1.user_id, new_user.id)
        self.assertEqual(reloaded_o2.user_id, new_user.id)

    def test_register_and_forgot_password_flow(self):
        """Kiểm tra toàn bộ luồng đăng ký 2 bước (OTP SĐT) và quên mật khẩu 2 bước (bằng Email có dấu chấm)."""
        # --- LUỒNG 1: ĐĂNG KÝ 2 BƯỚC ---
        # Bước 1.1: Gửi form đăng ký -> Tự động sinh OTP và redirect sang verify-register
        res = self.client.post('/auth/register', data={
            'username': 'otpuser',
            'email': 'otpuser@test.vn',
            'phone': '0981234567',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/verify-register', res.headers['Location'])

        # Lấy OTP sinh tự động từ session
        with self.client.session_transaction() as sess:
            register_otp = sess['register_otp']

        # Bước 1.2: Nhập mã OTP để xác nhận và kích hoạt tài khoản
        res = self.client.post('/auth/verify-register', data={'otp': register_otp}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        created_user = User.query.filter_by(username='otpuser').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.phone, '0981234567')

        # --- LUỒNG 2: QUÊN MẬT KHẨU 2 BƯỚC (BẰNG EMAIL CÓ DẤU CHẤM) ---
        # Bước 2.1: Đăng xuất tài khoản
        self.client.get('/auth/logout')

        # Bước 2.2: Trang 1 - Nhập Email và yêu cầu gửi OTP
        res = self.client.post('/auth/forgot-password', data={'identifier': 'otpuser@test.vn'}, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/reset-password', res.headers['Location'])

        with self.client.session_transaction() as sess:
            reset_otp = sess['reset_otp']

        # Bước 2.3: Trang 2 - Nhập OTP và đặt lại mật khẩu mới
        res = self.client.post('/auth/reset-password', data={
            'otp': reset_otp,
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Bước 2.4: Đăng nhập lại với mật khẩu mới bằng SĐT
        res = self.client.post('/auth/login', data={
            'login_id': '0981234567',
            'password': 'newpassword123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Chào mừng'.encode('utf-8'), res.data)

    def test_forgot_password_cooldown_and_max_5_fails(self):
        """
        Kiểm tra:
        1. Cooldown 60s: Trong 60s thoát ra nhập lại email, mã OTP giữ nguyên không đổi.
        2. Nhập sai OTP không làm lộ số lần đã sai.
        3. Nhập sai đủ 5 lần: mã OTP bị hủy và yêu cầu gửi lại mã mới.
        """
        # Bước 1: Yêu cầu OTP lần 1
        self.client.post('/auth/forgot-password', data={'identifier': self.customer.email})
        with self.client.session_transaction() as sess:
            otp1 = sess['reset_otp']
            self.assertIsNotNone(otp1)

        # Bước 2: Thoát ra ngoài và bấm gửi lại ngay trong 60s -> mã giữ nguyên
        self.client.post('/auth/forgot-password', data={'identifier': self.customer.email})
        with self.client.session_transaction() as sess:
            otp2 = sess['reset_otp']
            self.assertEqual(otp1, otp2)  # Không sinh mã mới, vẫn dùng mã cũ

        # Bước 3: Thử bấm resend API trong 60s -> Bị chặn 429
        res_resend_blocked = self.client.post('/auth/api/resend-reset-otp')
        self.assertEqual(res_resend_blocked.status_code, 429)

        # Bước 4: Nhập sai 4 lần đầu qua AJAX
        ajax_headers = {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
        for i in range(1, 5):
            res_wrong = self.client.post('/auth/reset-password', data={
                'otp': '999999',
                'new_password': 'password678',
                'confirm_password': 'password678'
            }, headers=ajax_headers)
            self.assertEqual(res_wrong.status_code, 400)
            data = res_wrong.get_json()
            self.assertFalse(data['success'])
            self.assertIn('Mã OTP không chính xác', data['message'])
            # Không hiển thị số lần sai
            self.assertNotIn(str(i), data['message'])

        # Bước 5: Nhập sai lần thứ 5 -> Mã OTP bị hủy
        res_wrong_5 = self.client.post('/auth/reset-password', data={
            'otp': '999999',
            'new_password': 'password678',
            'confirm_password': 'password678'
        }, headers=ajax_headers)
        self.assertEqual(res_wrong_5.status_code, 400)
        data5 = res_wrong_5.get_json()
        self.assertTrue(data5.get('otp_invalidated'))
        self.assertIn('đã bị hủy', data5['message'])

        # Kiểm tra session không còn reset_otp
        with self.client.session_transaction() as sess:
            self.assertNotIn('reset_otp', sess)

        # Bước 6: Thử nhập lại bằng OTP cũ (otp1) -> Vẫn bị từ chối vì đã hủy
        res_try_old = self.client.post('/auth/reset-password', data={
            'otp': otp1,
            'new_password': 'password678',
            'confirm_password': 'password678'
        }, headers=ajax_headers)
        self.assertEqual(res_try_old.status_code, 400)
        self.assertIn('đã bị hủy', res_try_old.get_json()['message'])

    def test_qr_payment_and_manual_confirmation(self):
        """Kiểm tra luồng thanh toán QR VietQR và xác nhận thủ công (khách báo CK & admin duyệt)."""
        # 1. Thêm sản phẩm vào giỏ
        self.client.post(f'/cart/add/{self.product.id}', data={'quantity': 1})

        # 2. Đăng nhập customer
        self.client.post('/auth/login', data={'login_id': 'user@test.vn', 'password': 'user123'})

        # 3. Đặt hàng chọn payment_method = 'qr_code'
        res_checkout = self.client.post('/cart/checkout', data={
            'recipient_name': 'Khách Test QR',
            'phone': '0912345678',
            'address': 'Hà Nội',
            'payment_method': 'qr_code'
        }, follow_redirects=True)
        self.assertEqual(res_checkout.status_code, 200)

        # Kiểm tra Order trong DB
        order = Order.query.filter_by(phone='0912345678').order_by(Order.id.desc()).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_method, 'qr_code')
        self.assertEqual(order.payment_status, 'unpaid')
        self.assertIn('vietqr.io', order.qr_code_url)
        self.assertGreater(order.qr_expiry_seconds, 850)
        self.assertFalse(order.is_qr_expired)

        # Kiểm tra trang order_success có thông tin VietQR
        html = res_checkout.data.decode('utf-8')
        self.assertIn('MBBank', html)
        self.assertIn('0366760056', html)
        self.assertIn(f'TECHSHOP {order.id}', html)

        # 4. Khách hàng bấm "Tôi đã chuyển khoản thành công"
        res_confirm = self.client.post(f'/cart/order/{order.id}/confirm-payment', follow_redirects=True)
        self.assertEqual(res_confirm.status_code, 200)
        reloaded_order = db.session.get(Order, order.id)
        self.assertEqual(reloaded_order.payment_status, 'awaiting_confirmation')

        # 5. Admin đăng nhập và duyệt thanh toán
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={'login_id': 'admin@test.vn', 'password': 'admin123'})

        res_admin_confirm = self.client.post(f'/admin/orders/{order.id}/confirm-payment', follow_redirects=True)
        self.assertEqual(res_admin_confirm.status_code, 200)
        reloaded_order2 = db.session.get(Order, order.id)
        self.assertEqual(reloaded_order2.payment_status, 'paid')

    def test_cancel_unpaid_order_and_reorder(self):
        """Kiểm tra người mua hủy đơn hàng khi chưa thanh toán và đặt lại đơn."""
        # 1. Ban đầu tồn kho là 10. Mua 3 cái -> tồn kho còn 7
        self.client.post(f'/cart/add/{self.product.id}', data={'quantity': 3})
        self.client.post('/auth/login', data={'login_id': 'user@test.vn', 'password': 'user123'})
        res_checkout = self.client.post('/cart/checkout', data={
            'recipient_name': 'Khách Hủy Đơn',
            'phone': '0912345678',
            'address': 'Hà Nội',
            'payment_method': 'qr_code'
        }, follow_redirects=True)
        self.assertEqual(res_checkout.status_code, 200)

        p = db.session.get(Product, self.product.id)
        self.assertEqual(p.stock_quantity, 7)

        order = Order.query.filter_by(recipient_name='Khách Hủy Đơn').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'pending')

        # 2. Khách hàng thực hiện hủy đơn hàng
        res_cancel = self.client.post(f'/cart/order/{order.id}/cancel', follow_redirects=True)
        self.assertEqual(res_cancel.status_code, 200)
        self.assertIn('Đơn Hàng Đã Bị Hủy'.encode('utf-8'), res_cancel.data)

        # Kiểm tra trạng thái đơn đã chuyển sang cancelled
        reloaded_order = db.session.get(Order, order.id)
        self.assertEqual(reloaded_order.status, 'cancelled')

        # Kiểm tra tồn kho đã được hoàn lại: 7 + 3 = 10
        p_reloaded = db.session.get(Product, self.product.id)
        self.assertEqual(p_reloaded.stock_quantity, 10)

        # 3. Khách bấm đặt lại đơn hàng này (reorder)
        res_reorder = self.client.get(f'/cart/order/{order.id}/reorder', follow_redirects=True)
        self.assertEqual(res_reorder.status_code, 200)

        # Giỏ hàng phải có lại 3 sản phẩm
        with self.client.session_transaction() as sess:
            cart = sess.get('cart', {})
            self.assertEqual(cart.get(str(self.product.id)), 3)

    def test_cannot_cancel_after_clicking_paid_and_admin_cancel_unpaid(self):
        """Kiểm tra: khách bấm đã chuyển khoản thì không thể tự hủy đơn, admin có quyền hủy đơn khi chưa nhận được tiền."""
        # 1. Khách mua 2 sản phẩm (tồn kho 10 -> còn 8)
        self.client.post(f'/cart/add/{self.product.id}', data={'quantity': 2})
        self.client.post('/auth/login', data={'login_id': 'user@test.vn', 'password': 'user123'})
        res_checkout = self.client.post('/cart/checkout', data={
            'recipient_name': 'Khách Xác Nhận Giả',
            'phone': '0912345678',
            'address': 'TP.HCM',
            'payment_method': 'qr_code'
        }, follow_redirects=True)
        self.assertEqual(res_checkout.status_code, 200)

        order = Order.query.filter_by(recipient_name='Khách Xác Nhận Giả').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, 'unpaid')

        # 2. Khách bấm "Tôi đã chuyển khoản thành công"
        res_confirm = self.client.post(f'/cart/order/{order.id}/confirm-payment', follow_redirects=True)
        self.assertEqual(res_confirm.status_code, 200)

        reloaded_order = db.session.get(Order, order.id)
        self.assertEqual(reloaded_order.payment_status, 'awaiting_confirmation')

        # 3. Khách cố tình bấm hủy đơn hàng -> Bị chặn, không thể tự hủy
        res_cancel = self.client.post(f'/cart/order/{order.id}/cancel', follow_redirects=True)
        self.assertEqual(res_cancel.status_code, 200)
        self.assertIn('không thể tự hủy'.encode('utf-8'), res_cancel.data)

        # Trạng thái đơn vẫn là pending, tồn kho vẫn là 8
        reloaded_order = db.session.get(Order, order.id)
        self.assertEqual(reloaded_order.status, 'pending')
        p = db.session.get(Product, self.product.id)
        self.assertEqual(p.stock_quantity, 8)

        # 4. Admin đăng nhập và kiểm tra thấy chưa nhận được tiền -> Admin bấm Hủy đơn
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={'login_id': 'admin@test.vn', 'password': 'admin123'})

        res_admin_cancel = self.client.post(
            f'/admin/orders/{order.id}/cancel-unpaid',
            data={'reason': 'Kiểm tra tài khoản không có giao dịch'},
            follow_redirects=True
        )
        self.assertEqual(res_admin_cancel.status_code, 200)
        self.assertIn('Đã hủy đơn hàng'.encode('utf-8'), res_admin_cancel.data)

        # 5. Kiểm tra đơn hàng đã bị hủy, payment_status là unpaid, và tồn kho được hoàn lại 8 + 2 = 10
        order_final = db.session.get(Order, order.id)
        self.assertEqual(order_final.status, 'cancelled')
        self.assertEqual(order_final.payment_status, 'unpaid')

        p_final = db.session.get(Product, self.product.id)
        self.assertEqual(p_final.stock_quantity, 10)

    def test_profile_requires_login(self):
        """Khách vãng lai chưa đăng nhập truy cập /auth/profile phải bị chuyển hướng đến trang đăng nhập."""
        res = self.client.get('/auth/profile')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers.get('Location', ''))

    def test_view_and_update_profile_info(self):
        """Đăng nhập xem hồ sơ và chỉnh sửa thông tin (số điện thoại, email, tên người dùng)."""
        # Đăng nhập
        self.client.post('/auth/login', data={'login_id': 'user@test.vn', 'password': 'user123'})

        # Xem trang hồ sơ
        res = self.client.get('/auth/profile')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Hồ Sơ Cá Nhân'.encode('utf-8'), res.data)
        self.assertIn(self.customer.username.encode('utf-8'), res.data)

        # Cập nhật số điện thoại và thông tin
        res_update = self.client.post('/auth/profile', data={
            'action': 'update_info',
            'username': 'customer_updated',
            'email': 'customer_updated@test.vn',
            'phone': '0934567890'
        }, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)
        self.assertIn('Cập nhật thông tin hồ sơ thành công'.encode('utf-8'), res_update.data)

        # Kiểm tra database
        updated_user = db.session.get(User, self.customer.id)
        self.assertEqual(updated_user.username, 'customer_updated')
        self.assertEqual(updated_user.email, 'customer_updated@test.vn')
        self.assertEqual(updated_user.phone, '0934567890')

    def test_update_profile_validation_conflicts(self):
        """Kiểm tra validation khi cập nhật hồ sơ: sai định dạng SĐT, trùng lặp với người dùng khác."""
        self.client.post('/auth/login', data={'login_id': 'user@test.vn', 'password': 'user123'})

        # 1. Số điện thoại sai định dạng
        res_invalid_phone = self.client.post('/auth/profile', data={
            'action': 'update_info',
            'username': 'user_test',
            'email': 'user@test.vn',
            'phone': '012345'
        }, follow_redirects=True)
        self.assertIn('Số điện thoại không đúng chuẩn 10 chữ số'.encode('utf-8'), res_invalid_phone.data)

        # 2. Trùng lặp email với Admin
        res_conflict_email = self.client.post('/auth/profile', data={
            'action': 'update_info',
            'username': 'user_test',
            'email': 'admin@test.vn',
            'phone': '0912345678'
        }, follow_redirects=True)
        self.assertIn('đã được đăng ký cho một tài khoản khác'.encode('utf-8'), res_conflict_email.data)

    def test_change_password_in_profile(self):
        """Kiểm tra chức năng đổi mật khẩu trong hồ sơ cá nhân."""
        self.client.post('/auth/login', data={'login_id': 'user@test.vn', 'password': 'user123'})

        # 1. Nhập sai mật khẩu hiện tại
        res_wrong = self.client.post('/auth/profile', data={
            'action': 'change_password',
            'current_password': 'sai_mat_khau',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        self.assertIn('Mật khẩu hiện tại không chính xác'.encode('utf-8'), res_wrong.data)

        # 2. Đổi mật khẩu thành công
        res_success = self.client.post('/auth/profile', data={
            'action': 'change_password',
            'current_password': 'user123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        self.assertIn('Đổi mật khẩu thành công'.encode('utf-8'), res_success.data)

        # 3. Đăng xuất và đăng nhập lại bằng mật khẩu mới
        self.client.get('/auth/logout')
        res_login_new = self.client.post('/auth/login', data={
            'login_id': 'user@test.vn',
            'password': 'newpassword123'
        }, follow_redirects=True)
        self.assertEqual(res_login_new.status_code, 200)
        self.assertIn('đã đăng nhập'.encode('utf-8'), res_login_new.data)

if __name__ == '__main__':
    unittest.main()
