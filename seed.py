from app import create_app
from app.extensions import db
from app.models import User, Category, Product, Order, OrderItem
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

app = create_app()

def seed_data():
    with app.app_context():
        print("Đang xóa dữ liệu cũ và khởi tạo bảng CSDL mới...")
        db.drop_all()
        db.create_all()

        print("1. Tạo tài khoản người dùng mẫu...")
        admin = User(
            username='admin',
            email='admin@techshop.vn',
            password_hash=generate_password_hash('admin123', method='scrypt'),
            role='admin'
        )
        user1 = User(
            username='khachhang',
            email='user@techshop.vn',
            password_hash=generate_password_hash('user123', method='scrypt'),
            role='customer'
        )
        user2 = User(
            username='danpham',
            email='dan@gmail.com',
            password_hash=generate_password_hash('123456', method='scrypt'),
            role='customer'
        )
        db.session.add_all([admin, user1, user2])
        db.session.commit()

        print("2. Tạo danh mục sản phẩm...")
        cats_data = [
            {'name': 'Điện thoại', 'slug': 'dien-thoai'},
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'Tai nghe', 'slug': 'tai-nghe'},
            {'name': 'Chuột & Bàn phím', 'slug': 'chuot-ban-phim'},
            {'name': 'Phụ kiện', 'slug': 'phu-kien'}
        ]
        cats_dict = {}
        for c in cats_data:
            cat = Category(name=c['name'], slug=c['slug'])
            db.session.add(cat)
            cats_dict[c['slug']] = cat
        db.session.commit()

        print("3. Tạo 16 Loại mặt hàng khác nhau kèm đường dẫn ảnh trùng khớp 100%...")
        products_data = [
            # 1. Laptop MacBook
            {
                'name': 'MacBook Air M2 13.6 inch 256GB',
                'description': 'Thiết kế mỏng nhẹ đẳng cấp, chip Apple M2 hiệu năng vượt trội, thời lượng pin cả ngày dài.',
                'price': 24490000,
                'stock': 15,
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop',
                'category': cats_dict['laptop']
            },
            # 2. Laptop Dell
            {
                'name': 'Dell XPS 13 9315 Core i7',
                'description': 'Màn hình FHD+ sắc nét, thiết kế nhôm nguyên khối sang trọng, tối ưu cho lập trình viên.',
                'price': 28990000,
                'stock': 10,
                'image_url': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500&auto=format&fit=crop',
                'category': cats_dict['laptop']
            },
            # 3. Laptop Gaming
            {
                'name': 'Laptop Gaming ASUS ROG Strix G16',
                'description': 'Intel Core i7 Gen 13, RTX 4060, màn hình 165Hz siêu mượt chuyên game đồ họa nặng.',
                'price': 34990000,
                'stock': 8,
                'image_url': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&auto=format&fit=crop',
                'category': cats_dict['laptop']
            },
            # 4. Laptop ThinkPad
            {
                'name': 'Lenovo ThinkPad X1 Carbon Gen 11',
                'description': 'Bàn phím trứ danh, độ bền chuẩn quân đội, trọng lượng siêu nhẹ chỉ 1.12kg.',
                'price': 36500000,
                'stock': 6,
                'image_url': 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500&auto=format&fit=crop',
                'category': cats_dict['laptop']
            },

            # 5. iPhone
            {
                'name': 'iPhone 15 Pro Max 256GB Titanium',
                'description': 'Khung vỏ Titan siêu bền nhẹ, chip Apple A17 Pro mạnh nhất, camera zoom quang học 5x.',
                'price': 29990000,
                'stock': 20,
                'image_url': 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500&auto=format&fit=crop',
                'category': cats_dict['dien-thoai']
            },
            # 6. Samsung Galaxy
            {
                'name': 'Samsung Galaxy S24 Ultra 512GB',
                'description': 'Tích hợp Galaxy AI thông minh, viết S-Pen tiện lợi, camera 200MP bắt trọn mọi khoảnh khắc.',
                'price': 31490000,
                'stock': 12,
                'image_url': 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500&auto=format&fit=crop',
                'category': cats_dict['dien-thoai']
            },
            # 7. Xiaomi
            {
                'name': 'Xiaomi 14 Ultra 512GB Leica',
                'description': 'Ống kính quang học Leica đỉnh cao, sạc siêu nhanh 90W, màn hình AMOLED 120Hz rực rỡ.',
                'price': 26990000,
                'stock': 7,
                'image_url': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&auto=format&fit=crop',
                'category': cats_dict['dien-thoai']
            },
            # 8. Google Pixel
            {
                'name': 'Google Pixel 8 Pro 128GB',
                'description': 'Hệ điều hành Android thuần mượt mà, xử lý hình ảnh AI đỉnh cao, màn hình Super Actua sắc nét.',
                'price': 21500000,
                'stock': 9,
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop',
                'category': cats_dict['dien-thoai']
            },

            # 9. Tai nghe chụp tai Sony
            {
                'name': 'Tai nghe chống ồn Sony WH-1000XM5',
                'description': 'Công nghệ chống ồn ANC tốt nhất thế giới, âm thanh Hi-Res chân thực, pin sử dụng 30 giờ.',
                'price': 7990000,
                'stock': 25,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop',
                'category': cats_dict['tai-nghe']
            },
            # 10. Tai nghe AirPods
            {
                'name': 'Tai nghe Apple AirPods Pro 2 MagSafe',
                'description': 'Chíp H2 cải tiến, chống ồn gấp 2 lần, âm thanh không gian cảm nhận theo cử động đầu.',
                'price': 5990000,
                'stock': 30,
                'image_url': 'https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&auto=format&fit=crop',
                'category': cats_dict['tai-nghe']
            },
            # 11. Tai nghe Marshall
            {
                'name': 'Tai nghe Marshall Major IV Wireless',
                'description': 'Thiết kế cổ điển đặc trưng Marshall, âm thanh chất lượng cao, thời lượng pin vượt trội 80 giờ.',
                'price': 3990000,
                'stock': 14,
                'image_url': 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&auto=format&fit=crop',
                'category': cats_dict['tai-nghe']
            },

            # 12. Chuột Logitech
            {
                'name': 'Chuột không dây Logitech MX Master 3S',
                'description': 'Cảm biến 8K DPI lướt trên mọi bề mặt, nút cuộn cuộn MagSpeed siêu nhanh và êm ái.',
                'price': 2190000,
                'stock': 40,
                'image_url': 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop',
                'category': cats_dict['chuot-ban-phim']
            },
            # 13. Bàn phím Keychron
            {
                'name': 'Bàn phím cơ Keychron K2 V2 Wireless',
                'description': 'Bàn phím cơ Bluetooth kết nối 3 thiết bị, Switch Gateron gõ cực êm, đèn LED RGB rực rỡ.',
                'price': 1950000,
                'stock': 18,
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop',
                'category': cats_dict['chuot-ban-phim']
            },
            # 14. Bàn phím Akko
            {
                'name': 'Bàn phím cơ Akko 3087 V2 Silent',
                'description': 'Layout TKL gọn gàng, Keycap PBT Double-Shot bền bỉ, Switch Pink cho cảm giác gõ êm nhẹ.',
                'price': 1450000,
                'stock': 22,
                'image_url': 'https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=500&auto=format&fit=crop',
                'category': cats_dict['chuot-ban-phim']
            },

            # 15. Đồng hồ Apple Watch
            {
                'name': 'Đồng hồ Apple Watch Series 9 GPS 45mm',
                'description': 'Theo dõi sức khỏe toàn diện, màn hình Retina Always-On sáng gấp đôi, thao tác chạm hai lần tiện lợi.',
                'price': 10490000,
                'stock': 16,
                'image_url': 'https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=500&auto=format&fit=crop',
                'category': cats_dict['phu-kien']
            },
            # 16. Sạc dự phòng Anker
            {
                'name': 'Sạc dự phòng Anker Prime 20,000mAh 200W',
                'description': 'Công suất cực lớn sạc nhanh cùng lúc 2 laptop, màn hình kỹ thuật số hiển thị thông số sạc.',
                'price': 2850000,
                'stock': 50,
                'image_url': 'https://images.unsplash.com/photo-1609592424009-54743c3d5269?w=500&auto=format&fit=crop',
                'category': cats_dict['phu-kien']
            }
        ]

        created_products = []
        for p in products_data:
            kwargs = {
                'name': p['name'],
                'description': p['description'],
                'price': p['price'],
                'image_url': p['image_url'],
                'category_id': p['category'].id
            }
            if hasattr(Product, 'stock'):
                kwargs['stock'] = p['stock']
            elif hasattr(Product, 'quantity'):
                kwargs['quantity'] = p['stock']

            prod = Product(**kwargs)
            db.session.add(prod)
            created_products.append(prod)
        db.session.commit()

        print("4. Tạo đơn hàng mẫu...")
        statuses = ['completed', 'pending', 'completed', 'cancelled', 'completed']
        sample_names = ['Phạm Văn Dần', 'Nguyễn Thị Ánh', 'Trần Văn Bảo', 'Lê Hoàng Nam', 'Đỗ Thị Linh']
        sample_phones = ['0987654321', '0912345678', '0905123456', '0934567890', '0978123456']
        sample_addresses = [
            '122 Hoàng Quốc Việt, Cầu Giấy, Hà Nội',
            '45 Nguyễn Trãi, Thanh Xuân, Hà Nội',
            '88 Cầu Giấy, Hà Nội',
            '15 Mộc Bài, Q.10, TP.HCM',
            '102 Điện Biên Phủ, Đà Nẵng'
        ]

        for i in range(1, 6):
            sample_prods = random.sample(created_products, k=2)
            total_val = sum(p.price for p in sample_prods)
            
            # Khởi tạo Order đầy đủ các thông tin giao hàng bắt buộc
            order_kwargs = {
                'user_id': user2.id if i % 2 == 0 else user1.id,
                'recipient_name': sample_names[i-1],
                'phone': sample_phones[i-1],
                'address': sample_addresses[i-1],
                'status': statuses[i-1],
                'created_at': datetime.now() - timedelta(days=i*2)
            }

            # Tự động gán trường tổng tiền thích ứng với Model
            if hasattr(Order, 'total_amount'):
                order_kwargs['total_amount'] = total_val
            elif hasattr(Order, 'total_price'):
                order_kwargs['total_price'] = total_val
            elif hasattr(Order, 'total'):
                order_kwargs['total'] = total_val

            order = Order(**order_kwargs)
            db.session.add(order)
            db.session.commit()

            for p in sample_prods:
                item_kwargs = {
                    'order_id': order.id,
                    'product_id': p.id,
                    'quantity': 1
                }
                
                # Tự động chọn đúng tên cột giá trong OrderItem nếu có
                if hasattr(OrderItem, 'price'):
                    item_kwargs['price'] = p.price
                elif hasattr(OrderItem, 'unit_price'):
                    item_kwargs['unit_price'] = p.price
                elif hasattr(OrderItem, 'price_at_purchase'):
                    item_kwargs['price_at_purchase'] = p.price

                item = OrderItem(**item_kwargs)
                db.session.add(item)
        
        db.session.commit()
        print("=== NẠP THÀNH CÔNG 16 MẶT HÀNG CÔNG NGHỆ & ĐƠN HÀNG MẪU! ===")

if __name__ == '__main__':
    seed_data()