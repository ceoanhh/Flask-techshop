from app import create_app
from app.extensions import db
from app.models import User, Product, Category, Order, OrderItem

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Category': Category,
        'Order': Order,
        'OrderItem': OrderItem
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tự động tạo bảng SQLite nếu chưa tồn tại
    app.run(debug=True, port=5000)
