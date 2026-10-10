from app import create_app
from app.extensions import db
from app.models import User, Category, Product

app = create_app()

def seed_data():
    with app.app_context():
        db.create_all()

        # Tạo tài khoản Admin & Khách hàng mẫu
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@techshop.vn', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        if not User.query.filter_by(username='khachhang').first():
            user = User(username='khachhang', email='user@techshop.vn', role='customer')
            user.set_password('user123')
            db.session.add(user)

        # Tạo Danh mục sản phẩm
        cats = [
            {'name': 'Điện thoại', 'slug': 'dien-thoai'},
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'Tai nghe', 'slug': 'tai-nghe'},
            {'name': 'Phụ kiện', 'slug': 'phu-kien'}
        ]
        created_cats = {}
        for c in cats:
            existing = Category.query.filter_by(slug=c['slug']).first()
            if not existing:
                cat_obj = Category(name=c['name'], slug=c['slug'])
                db.session.add(cat_obj)
                created_cats[c['slug']] = cat_obj
            else:
                created_cats[c['slug']] = existing

        db.session.commit()

        # Tạo Sản phẩm mẫu
        if Product.query.count() == 0:
            sample_products = [
                {
                    'name': 'iPhone 15 Pro Max 256GB',
                    'price': 29990000,
                    'stock_quantity': 25,
                    'description': 'Khung viền titan cao cấp, chip Apple A17 Pro cực mạnh.',
                    'category_id': created_cats['dien-thoai'].id
                },
                {
                    'name': 'MacBook Air M2 13.6 inch',
                    'price': 24490000,
                    'stock_quantity': 15,
                    'description': 'Thiết kế mỏng nhẹ, pin trâu cả ngày, chip Apple M2 mượt mà.',
                    'category_id': created_cats['laptop'].id
                },
                {
                    'name': 'Tai nghe Sony WH-1000XM5',
                    'price': 7990000,
                    'stock_quantity': 40,
                    'description': 'Chống ồn chủ động đỉnh cao, âm thanh chi tiết và pin 30h.',
                    'category_id': created_cats['tai-nghe'].id
                },
                {
                    'name': 'Chuột không dây Logitech MX Master 3S',
                    'price': 2190000,
                    'stock_quantity': 50,
                    'description': 'Chuột công thái học cao cấp dành cho lập trình viên và văn phòng.',
                    'category_id': created_cats['phu-kien'].id
                }
            ]

            for p in sample_products:
                prod_obj = Product(**p)
                db.session.add(prod_obj)

            db.session.commit()
            print("=> Đã tạo dữ liệu mẫu thành công!")
        else:
            print("=> CSDL đã có sản phẩm, bỏ qua seed.")

if __name__ == '__main__':
    seed_data()
