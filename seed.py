from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Category, Product, Order, OrderItem

app = create_app()

def seed_data():
    with app.app_context():
        # Xóa dữ liệu cũ và tạo lại bảng
        db.drop_all()
        db.create_all()

        print("=> 1. Đang tạo tài khoản người dùng...")
        admin = User(username='admin', email='admin@techshop.vn', phone='0988888888', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        user1 = User(username='khachhang', email='user@techshop.vn', phone='0912345678', role='customer')
        user1.set_password('user123')
        db.session.add(user1)

        user2 = User(username='hoangnam', email='nam.hoang@gmail.com', phone='0977112233', role='customer')
        user2.set_password('user123')
        db.session.add(user2)

        db.session.commit()

        print("=> 2. Đang tạo danh mục sản phẩm...")
        cats_data = [
            {'name': 'Điện thoại', 'slug': 'dien-thoai'},
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'Tai nghe', 'slug': 'tai-nghe'},
            {'name': 'Phụ kiện', 'slug': 'phu-kien'},
            {'name': 'Đồng hồ thông minh', 'slug': 'dong-ho-thong-minh'}
        ]
        created_cats = {}
        for c in cats_data:
            cat_obj = Category(name=c['name'], slug=c['slug'])
            db.session.add(cat_obj)
            db.session.flush()
            created_cats[c['slug']] = cat_obj

        db.session.commit()

        print("=> 3. Đang tạo 16 sản phẩm công nghệ sắc nét...")
        sample_products = [
            # --- ĐIỆN THOẠI ---
            {
                'name': 'iPhone 15 Pro Max 256GB',
                'price': 29990000,
                'stock_quantity': 25,
                'description': 'Khung viền titan cao cấp, chip Apple A17 Pro cực mạnh mẽ, camera tiềm vọng zoom 5x.',
                'image_url': 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 512GB',
                'price': 28490000,
                'stock_quantity': 18,
                'description': 'Màn hình phẳng chống chói 6.8 inch, camera 200MP, tích hợp bút S-Pen và Galaxy AI đỉnh cao.',
                'image_url': 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=600&auto=format&fit=crop',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'Xiaomi 14 Ultra 512GB',
                'price': 24990000,
                'stock_quantity': 12,
                'description': 'Ống kính Leica thế hệ mới, cảm biến 1 inch, chip Snapdragon 8 Gen 3 đỉnh cao.',
                'image_url': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'iPhone 13 128GB',
                'price': 13990000,
                'stock_quantity': 30,
                'description': 'Màn hình Super Retina XDR nét mượt, chip A15 Bionic bền bỉ, dung lượng pin ấn tượng.',
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop',
                'category_id': created_cats['dien-thoai'].id
            },

            # --- LAPTOP ---
            {
                'name': 'MacBook Air M2 13.6 inch 256GB',
                'price': 24490000,
                'stock_quantity': 15,
                'description': 'Thiết kế siêu mỏng nhẹ thời thượng, thời lượng pin cả ngày, chip Apple M2 mượt mà ấn tượng.',
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Laptop Asus ROG Zephyrus G14',
                'price': 38990000,
                'stock_quantity': 10,
                'description': 'Laptop gaming nhỏ gọn mạnh mẽ hàng đầu với AMD Ryzen 9 và GPU NVIDIA RTX 4060.',
                'image_url': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&auto=format&fit=crop',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Dell XPS 13 Plus 9320',
                'price': 41990000,
                'stock_quantity': 8,
                'description': 'Thiết kế tương lai vô cực, màn hình OLED 3.5K cảm ứng, Core i7 gen 13th mạnh mẽ.',
                'image_url': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Lenovo Legion 5 Pro RTX 4070',
                'price': 35990000,
                'stock_quantity': 14,
                'description': 'Màn hình 16 inch 240Hz chuẩn màu, tản nhiệt Coldfront 5.0 tối ưu công suất gaming.',
                'image_url': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop',
                'category_id': created_cats['laptop'].id
            },

            # --- TAI NGHE ---
            {
                'name': 'Tai nghe Sony WH-1000XM5',
                'price': 7990000,
                'stock_quantity': 35,
                'description': 'Công nghệ chống ồn chủ động hàng đầu ngành, thời lượng pin 30 giờ và âm thanh chuẩn Hi-Res.',
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop',
                'category_id': created_cats['tai-nghe'].id
            },
            {
                'name': 'AirPods Pro 2 USB-C',
                'price': 5790000,
                'stock_quantity': 40,
                'description': 'Chống ồn chủ động gấp đôi, chế độ Xuyên âm thích ứng và hộp sạc MagSafe chuẩn Type-C tiện lợi.',
                'image_url': 'https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&auto=format&fit=crop',
                'category_id': created_cats['tai-nghe'].id
            },
            {
                'name': 'Tai nghe Marshall Major IV',
                'price': 3690000,
                'stock_quantity': 25,
                'description': 'Thiết kế cổ điển đặc trưng, âm thanh bùng nổ, thời lượng pin phát nhạc liên tục hơn 80 giờ.',
                'image_url': 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&auto=format&fit=crop',
                'category_id': created_cats['tai-nghe'].id
            },

            # --- PHỤ KIỆN ---
            {
                'name': 'Chuột không dây Logitech MX Master 3S',
                'price': 2190000,
                'stock_quantity': 50,
                'description': 'Chuột công thái học cao cấp dành cho lập trình viên và sáng tạo nội dung, cuộn siêu tốc MagSpeed.',
                'image_url': 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop',
                'category_id': created_cats['phu-kien'].id
            },
            {
                'name': 'Bàn phím cơ Keychron K3 Pro RGB',
                'price': 2490000,
                'stock_quantity': 30,
                'description': 'Bàn phím cơ layout 75% siêu mỏng, hỗ trợ kết nối Bluetooth 5.1 và cáp rời Type-C, hot-swap tiện lợi.',
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop',
                'category_id': created_cats['phu-kien'].id
            },
            {
                'name': 'Sạc Anker Prime 67W GaN 3 Cổng',
                'price': 1190000,
                'stock_quantity': 60,
                'description': 'Công nghệ GaN nhỏ gọn, sạc nhanh đồng thời 3 thiết bị Laptop, iPhone và iPad an toàn.',
                'image_url': 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop',
                'category_id': created_cats['phu-kien'].id
            },

            # --- ĐỒNG HỒ THÔNG MINH ---
            {
                'name': 'Apple Watch Series 9 GPS 45mm',
                'price': 9890000,
                'stock_quantity': 20,
                'description': 'Màn hình Retina siêu sáng, thao tác chạm hai lần Double Tap độc đáo và theo dõi sức khỏe chuyên sâu.',
                'image_url': 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&auto=format&fit=crop',
                'category_id': created_cats['dong-ho-thong-minh'].id
            },
            {
                'name': 'Samsung Galaxy Watch 6 Classic 47mm',
                'price': 7490000,
                'stock_quantity': 15,
                'description': 'Vòng xoay xoay cơ học sang trọng, phân tích thành phần cơ thể BIA và theo dõi giấc ngủ nâng cao.',
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop',
                'category_id': created_cats['dong-ho-thong-minh'].id
            }
        ]

        created_prods_dict = {}
        for p_data in sample_products:
            # Kiểm tra cả 2 trường tên cột tồn tại trong model Product của Ánh/Bảo
            prod_kwargs = {
                'name': p_data['name'],
                'price': p_data['price'],
                'description': p_data['description'],
                'image_url': p_data['image_url'],
                'category_id': p_data['category_id']
            }
            if hasattr(Product, 'stock_quantity'):
                prod_kwargs['stock_quantity'] = p_data['stock_quantity']
            elif hasattr(Product, 'stock'):
                prod_kwargs['stock'] = p_data['stock_quantity']

            prod_obj = Product(**prod_kwargs)
            db.session.add(prod_obj)
            db.session.flush()
            created_prods_dict[p_data['name']] = prod_obj

        db.session.commit()

        print("=> 4. Đang tạo đơn hàng và chi tiết đơn hàng mẫu...")
        now = datetime.now()

        sample_orders = [
            {
                'user_id': user1.id,
                'recipient_name': 'Nguyễn Văn Khách',
                'phone': '0901234567',
                'address': 'Số 12 Chùa Bộc, Đống Đa, Hà Nội',
                'status': 'completed',
                'created_at': now - timedelta(days=25),
                'items': [('iPhone 15 Pro Max 256GB', 1), ('Tai nghe Sony WH-1000XM5', 1)]
            },
            {
                'user_id': user2.id,
                'recipient_name': 'Hoàng Nam',
                'phone': '0918889999',
                'address': 'Tòa Landmark 81, Bình Thạnh, TP.HCM',
                'status': 'completed',
                'created_at': now - timedelta(days=15),
                'items': [('MacBook Air M2 13.6 inch 256GB', 1), ('Chuột không dây Logitech MX Master 3S', 1)]
            },
            {
                'user_id': user1.id,
                'recipient_name': 'Nguyễn Văn Khách',
                'phone': '0901234567',
                'address': 'Số 88 Cầu Giấy, Hà Nội',
                'status': 'pending',
                'created_at': now - timedelta(hours=3),
                'items': [('Bàn phím cơ Keychron K3 Pro RGB', 1), ('Chuột không dây Logitech MX Master 3S', 1)]
            },
            {
                'user_id': None,
                'recipient_name': 'Trần Thị Thu Trang',
                'phone': '0987654321',
                'address': '45 Lê Duẩn, Quận 1, TP.HCM',
                'status': 'pending',
                'created_at': now - timedelta(hours=1),
                'items': [('AirPods Pro 2 USB-C', 2)]
            },
            {
                'user_id': user2.id,
                'recipient_name': 'Hoàng Nam',
                'phone': '0918889999',
                'address': 'Tòa Landmark 81, Bình Thạnh, TP.HCM',
                'status': 'cancelled',
                'created_at': now - timedelta(days=5),
                'items': [('Laptop Asus ROG Zephyrus G14', 1)]
            }
        ]

        for o_data in sample_orders:
            items_spec = o_data.pop('items')
            total_amount = 0.0

            order_kwargs = {
                'user_id': o_data['user_id'],
                'recipient_name': o_data['recipient_name'],
                'phone': o_data['phone'],
                'address': o_data['address'],
                'status': o_data['status'],
                'created_at': o_data['created_at']
            }

            if hasattr(Order, 'total_amount'):
                order_kwargs['total_amount'] = 0.0
            elif hasattr(Order, 'total_price'):
                order_kwargs['total_price'] = 0.0

            order = Order(**order_kwargs)
            db.session.add(order)
            db.session.flush()

            for prod_name, qty in items_spec:
                if prod_name in created_prods_dict:
                    p = created_prods_dict[prod_name]
                    line_total = p.price * qty
                    total_amount += line_total

                    item_kwargs = {
                        'order_id': order.id,
                        'product_id': p.id,
                        'quantity': qty
                    }
                    if hasattr(OrderItem, 'unit_price'):
                        item_kwargs['unit_price'] = p.price
                    elif hasattr(OrderItem, 'price'):
                        item_kwargs['price'] = p.price

                    order_item = OrderItem(**item_kwargs)
                    db.session.add(order_item)

            if hasattr(order, 'total_amount'):
                order.total_amount = total_amount
            elif hasattr(order, 'total_price'):
                order.total_price = total_amount

        db.session.commit()
        print("=> NẠP THÀNH CÔNG 16 SẢN PHẨM SẮC NÉT VÀ ĐƠN HÀNG MẪU CHO CẢ NHÓM!")

if __name__ == '__main__':
    seed_data()