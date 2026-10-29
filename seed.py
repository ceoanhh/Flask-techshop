from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Category, Product, Order, OrderItem

app = create_app()

def seed_data():
    with app.app_context():
        db.create_all()

        print("=> Đang tạo tài khoản người dùng...")
        # 1. Tạo tài khoản Admin & Khách hàng mẫu
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@techshop.vn', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        user1 = User.query.filter_by(username='khachhang').first()
        if not user1:
            user1 = User(username='khachhang', email='user@techshop.vn', role='customer')
            user1.set_password('user123')
            db.session.add(user1)

        user2 = User.query.filter_by(username='hoangnam').first()
        if not user2:
            user2 = User(username='hoangnam', email='nam.hoang@gmail.com', role='customer')
            user2.set_password('user123')
            db.session.add(user2)

        db.session.commit()

        # 2. Tạo Danh mục sản phẩm
        print("=> Đang tạo danh mục sản phẩm...")
        cats_data = [
            {'name': 'Điện thoại', 'slug': 'dien-thoai'},
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'Tai nghe', 'slug': 'tai-nghe'},
            {'name': 'Phụ kiện', 'slug': 'phu-kien'},
            {'name': 'Đồng hồ thông minh', 'slug': 'dong-ho-thong-minh'}
        ]
        created_cats = {}
        for c in cats_data:
            cat_obj = Category.query.filter_by(slug=c['slug']).first()
            if not cat_obj:
                cat_obj = Category(name=c['name'], slug=c['slug'])
                db.session.add(cat_obj)
                db.session.flush()
            created_cats[c['slug']] = cat_obj

        db.session.commit()

        # 3. Tạo Sản phẩm mẫu
        print("=> Đang kiểm tra và tạo sản phẩm mẫu...")
        sample_products = [
            {
                'name': 'iPhone 15 Pro Max 256GB',
                'price': 29990000,
                'stock_quantity': 25,
                'description': 'Khung viền titan cao cấp, chip Apple A17 Pro cực mạnh mẽ, camera tiềm vọng zoom 5x.',
                'image_url': 'default_product.png',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 512GB',
                'price': 28490000,
                'stock_quantity': 18,
                'description': 'Màn hình phẳng chống chói 6.8 inch, camera 200MP, tích hợp bút S-Pen và Galaxy AI đỉnh cao.',
                'image_url': 'default_product.png',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'MacBook Air M2 13.6 inch 256GB',
                'price': 24490000,
                'stock_quantity': 15,
                'description': 'Thiết kế siêu mỏng nhẹ thời thượng, thời lượng pin cả ngày, chip Apple M2 mượt mà ấn tượng.',
                'image_url': 'default_product.png',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Laptop Asus ROG Zephyrus G14',
                'price': 38990000,
                'stock_quantity': 10,
                'description': 'Laptop gaming nhỏ gọn mạnh mẽ hàng đầu với AMD Ryzen 9 và GPU NVIDIA RTX 4060.',
                'image_url': 'default_product.png',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Tai nghe Sony WH-1000XM5',
                'price': 7990000,
                'stock_quantity': 35,
                'description': 'Công nghệ chống ồn chủ động hàng đầu ngành, thời lượng pin 30 giờ và âm thanh chuẩn Hi-Res.',
                'image_url': 'default_product.png',
                'category_id': created_cats['tai-nghe'].id
            },
            {
                'name': 'AirPods Pro 2 USB-C',
                'price': 5790000,
                'stock_quantity': 40,
                'description': 'Chống ồn chủ động gấp đôi, chế độ Xuyên âm thích ứng và hộp sạc MagSafe chuẩn Type-C tiện lợi.',
                'image_url': 'default_product.png',
                'category_id': created_cats['tai-nghe'].id
            },
            {
                'name': 'Chuột không dây Logitech MX Master 3S',
                'price': 2190000,
                'stock_quantity': 50,
                'description': 'Chuột công thái học cao cấp dành cho lập trình viên và sáng tạo nội dung, cuộn siêu tốc MagSpeed.',
                'image_url': 'default_product.png',
                'category_id': created_cats['phu-kien'].id
            },
            {
                'name': 'Bàn phím cơ Keychron K3 Pro RGB',
                'price': 2490000,
                'stock_quantity': 30,
                'description': 'Bàn phím cơ layout 75% siêu mỏng, hỗ trợ kết nối Bluetooth 5.1 và cáp rời Type-C, hot-swap tiện lợi.',
                'image_url': 'default_product.png',
                'category_id': created_cats['phu-kien'].id
            },
            {
                'name': 'Apple Watch Series 9 GPS 45mm',
                'price': 9890000,
                'stock_quantity': 20,
                'description': 'Màn hình luôn bật Retina siêu sáng, thao tác chạm hai lần Double Tap độc đáo và theo dõi sức khỏe chuyên sâu.',
                'image_url': 'default_product.png',
                'category_id': created_cats['dong-ho-thong-minh'].id
            }
        ]

        for p_data in sample_products:
            existing_prod = Product.query.filter_by(name=p_data['name']).first()
            if not existing_prod:
                prod_obj = Product(**p_data)
                db.session.add(prod_obj)

        db.session.commit()

        # 4. Tạo Đơn hàng mẫu (Giúp cả nhóm và Bảo test Dashboard, Thống kê, Quản lý đơn)
        if Order.query.count() == 0:
            print("=> Đang tạo đơn hàng và chi tiết đơn hàng mẫu...")
            prods = Product.query.all()
            prod_dict = {p.name: p for p in prods}

            now = datetime.utcnow()

            sample_orders = [
                {
                    'user_id': user1.id,
                    'recipient_name': 'Nguyễn Văn Khách',
                    'phone': '0901234567',
                    'address': 'Số 12 Chùa Bộc, Đống Đa, Hà Nội',
                    'status': 'completed',
                    'created_at': now - timedelta(days=25),
                    'items': [
                        ('iPhone 15 Pro Max 256GB', 1),
                        ('Tai nghe Sony WH-1000XM5', 1)
                    ]
                },
                {
                    'user_id': user2.id,
                    'recipient_name': 'Hoàng Nam',
                    'phone': '0918889999',
                    'address': 'Tòa Landmark 81, Bình Thạnh, TP.HCM',
                    'status': 'completed',
                    'created_at': now - timedelta(days=15),
                    'items': [
                        ('MacBook Air M2 13.6 inch 256GB', 1),
                        ('Chuột không dây Logitech MX Master 3S', 1)
                    ]
                },
                {
                    'user_id': user1.id,
                    'recipient_name': 'Nguyễn Văn Khách',
                    'phone': '0901234567',
                    'address': 'Số 88 Cầu Giấy, Hà Nội',
                    'status': 'pending',
                    'created_at': now - timedelta(hours=3),
                    'items': [
                        ('Bàn phím cơ Keychron K3 Pro RGB', 1),
                        ('Chuột không dây Logitech MX Master 3S', 1)
                    ]
                },
                {
                    'user_id': None,
                    'recipient_name': 'Trần Thị Thu Trang',
                    'phone': '0987654321',
                    'address': '45 Lê Duẩn, Quận 1, TP.HCM',
                    'status': 'pending',
                    'created_at': now - timedelta(hours=1),
                    'items': [
                        ('AirPods Pro 2 USB-C', 2)
                    ]
                },
                {
                    'user_id': user2.id,
                    'recipient_name': 'Hoàng Nam',
                    'phone': '0918889999',
                    'address': 'Tòa Landmark 81, Bình Thạnh, TP.HCM',
                    'status': 'cancelled',
                    'created_at': now - timedelta(days=5),
                    'items': [
                        ('Laptop Asus ROG Zephyrus G14', 1)
                    ]
                }
            ]

            for o_data in sample_orders:
                items_spec = o_data.pop('items')
                total_amount = 0.0

                order = Order(**o_data, total_amount=0.0)
                db.session.add(order)
                db.session.flush()

                for prod_name, qty in items_spec:
                    if prod_name in prod_dict:
                        p = prod_dict[prod_name]
                        line_total = p.price * qty
                        total_amount += line_total
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=p.id,
                            quantity=qty,
                            unit_price=p.price
                        )
                        db.session.add(order_item)

                order.total_amount = total_amount

            db.session.commit()
            print("=> Đã tạo đơn hàng mẫu thành công!")

        print("=> Toàn bộ dữ liệu mẫu (Seed Data) đã sẵn sàng để cả nhóm kiểm thử!")

if __name__ == '__main__':
    seed_data()
