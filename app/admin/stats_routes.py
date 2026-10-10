from flask import jsonify
from app.admin import bp
from app.models import Order, Product, OrderItem
from app.extensions import db

# ==========================================
# MODULE THỐNG KÊ & BIỂU ĐỒ - PHỤ TRÁCH: BẢO
# ==========================================

@bp.route('/api/stats/monthly-revenue')
def monthly_revenue():
    """Bảo viết query tính doanh thu theo các tháng gần đây"""
    mock_data = {
        "labels": ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6"],
        "revenues": [15000000, 22000000, 18500000, 31000000, 25000000, 42000000]
    }
    return jsonify(mock_data)

@bp.route('/api/stats/order-status')
def order_status():
    """Bảo viết query thống kê số lượng đơn theo từng trạng thái"""
    mock_data = {
        "labels": ["Hoàn thành", "Chờ xử lý", "Đã hủy"],
        "counts": [65, 20, 15]
    }
    return jsonify(mock_data)

@bp.route('/api/stats/top-products')
def top_products():
    """Bảo viết query top sản phẩm bán chạy nhất"""
    mock_data = {
        "labels": ["iPhone 15 Pro", "MacBook Air M2", "Sony WH-1000XM5", "Bàn phím cơ", "Chuột MX Master 3"],
        "quantities": [120, 85, 70, 64, 52]
    }
    return jsonify(mock_data)
