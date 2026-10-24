import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Category, Product, OrderItem, Order

app = create_app()

def seed_data():
    with app.app_context():
        # Xóa và tạo lại toàn bộ bảng để đảm bảo dữ liệu sạch
        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        Category.query.delete()
        User.query.delete()
        db.session.commit()
        db.create_all()

        # 1. Tạo tài khoản Admin & Khách hàng mẫu
        customers = []
        admin = User(username='admin', email='admin@techshop.vn', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        for i in range(1, 6):
            user = User(username=f'khachhang{i}', email=f'user{i}@techshop.vn', role='customer')
            user.set_password('user123')
            customers.append(user)
            db.session.add(user)

        db.session.commit()

        # 2. Tạo Danh mục sản phẩm
        cats = [
            {'name': 'Điện thoại', 'slug': 'dien-thoai'},
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'Tai nghe', 'slug': 'tai-nghe'},
            {'name': 'Phụ kiện', 'slug': 'phu-kien'}
        ]
        created_cats = {}
        for c in cats:
            cat_obj = Category(name=c['name'], slug=c['slug'])
            db.session.add(cat_obj)
            created_cats[c['slug']] = cat_obj

        db.session.commit()

        # 3. Tạo Sản phẩm mẫu
        sample_products = [
            {
                'name': 'iPhone 15 Pro Max 256GB',
                'price': 29990000,
                'stock_quantity': 50,
                'description': 'Khung viền titan cao cấp, chip Apple A17 Pro cực mạnh.',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'price': 27990000,
                'stock_quantity': 40,
                'description': 'Màn hình tràn viền, camera 200MP, tích hợp bút S-Pen.',
                'category_id': created_cats['dien-thoai'].id
            },
            {
                'name': 'MacBook Air M2 13.6 inch',
                'price': 24490000,
                'stock_quantity': 30,
                'description': 'Thiết kế mỏng nhẹ, pin trâu cả ngày, chip Apple M2 mượt mà.',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Dell XPS 13 9315',
                'price': 26500000,
                'stock_quantity': 20,
                'description': 'Laptop doanh nhân mỏng nhẹ, màn hình Full HD+ siêu nét.',
                'category_id': created_cats['laptop'].id
            },
            {
                'name': 'Tai nghe Sony WH-1000XM5',
                'price': 7990000,
                'stock_quantity': 60,
                'description': 'Chống ồn chủ động đỉnh cao, âm thanh chi tiết và pin 30h.',
                'category_id': created_cats['tai-nghe'].id
            },
            {
                'name': 'AirPods Pro 2 USB-C',
                'price': 5690000,
                'stock_quantity': 80,
                'description': 'Chống ồn chủ động gấp 2 lần, cổng sạc USB-C tiện lợi.',
                'category_id': created_cats['tai-nghe'].id
            },
            {
                'name': 'Chuột không dây Logitech MX Master 3S',
                'price': 2190000,
                'stock_quantity': 100,
                'description': 'Chuột công thái học cao cấp dành cho lập trình viên và văn phòng.',
                'category_id': created_cats['phu-kien'].id
            },
            {
                'name': 'Sạc Anker 65W GaNPrime',
                'price': 890000,
                'stock_quantity': 150,
                'description': 'Củ sạc nhanh công suất cao, kích thước nhỏ gọn 3 cổng sạc.',
                'category_id': created_cats['phu-kien'].id
            }
        ]

        products = []
        for p in sample_products:
            prod_obj = Product(**p)
            products.append(prod_obj)
            db.session.add(prod_obj)

        db.session.commit()

        # 4. Giả lập đơn hàng trong khoảng 6 tháng (180 ngày) gần nhất
        print("=> Đang khởi tạo dữ liệu đơn hàng giả lập...")
        statuses = ['completed', 'completed', 'completed', 'pending', 'cancelled']
        now = datetime.utcnow()

        for _ in range(120):
            # Lấy ngẫu nhiên ngày trong 180 ngày qua
            random_days = random.randint(0, 180)
            random_hours = random.randint(0, 23)
            created_date = now - timedelta(days=random_days, hours=random_hours)

            customer = random.choice(customers)
            status = random.choice(statuses)

            order = Order(
                user_id=customer.id,
                recipient_name=f"Khách hàng {customer.username}",
                phone=f"0901234{customer.id:03d}",
                address="123 Đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh",
                status=status,
                created_at=created_date,
                total_amount=0.0
            )
            db.session.add(order)
            db.session.flush()  # Lấy order.id trước khi add OrderItem

            # Chọn ngẫu nhiên từ 1 đến 3 sản phẩm cho mỗi đơn hàng
            selected_products = random.sample(products, k=random.randint(1, 3))
            total_amount = 0.0

            for prod in selected_products:
                qty = random.randint(1, 2)
                item_price = prod.price
                total_amount += item_price * qty

                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=item_price
                )
                db.session.add(item)

            order.total_amount = total_amount

        db.session.commit()
        print("=> Đã tạo toàn bộ dữ liệu mẫu thành công!")

if __name__ == '__main__':
    seed_data()