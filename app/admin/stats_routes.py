from datetime import datetime, timedelta
from app.admin import bp
from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract
from app.extensions import db
from app.models import Order, OrderItem, Product  # Import models của bạn

from datetime import datetime
from flask import jsonify
from sqlalchemy import extract, func


@bp.route('/api/stats/monthly-revenue')
def monthly_revenue():
    """Doanh thu, Số lượng đơn & AOV 6 tháng gần nhất (chỉ tính đơn 'completed')"""
    now = datetime.utcnow()

    # 1. Tạo khung 6 tháng gần nhất (từ cũ đến mới)
    months_list = []
    current_year = now.year
    current_month = now.month

    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1

        months_list.append({
            'year': y,
            'month': m,
            'label': f"T{m:02d}/{y}"
        })

    first_month = months_list[0]
    start_date = datetime(first_month['year'], first_month['month'], 1)

    # 2. Truy vấn tính Tổng Doanh thu VÀ Số lượng đơn thành công
    results = db.session.query(
        extract('year', Order.created_at).label('year'),
        extract('month', Order.created_at).label('month'),
        func.sum(Order.total_amount).label('total_revenue'),
        func.count(Order.id).label('order_count')
    ).filter(
        Order.status == 'completed',
        Order.created_at >= start_date
    ).group_by(
        extract('year', Order.created_at),
        extract('month', Order.created_at)
    ).all()

    # 3. Tạo Map tra cứu {(year, month): (revenue, count)}
    data_map = {
        (int(row.year), int(row.month)): (
            float(row.total_revenue or 0.0),
            int(row.order_count or 0)
        )
        for row in results
    }

    # 4. Tách dữ liệu thành các mảng tương ứng
    labels = []
    revenues = []
    order_counts = []
    aov_list = []

    for m in months_list:
        labels.append(m['label'])
        rev, count = data_map.get((m['year'], m['month']), (0.0, 0))

        revenues.append(rev)
        order_counts.append(count)
        # Tính AOV = Tổng doanh thu / Số đơn hàng (tránh chia cho 0)
        aov_list.append(round(rev / count) if count > 0 else 0)

    return jsonify({
        "labels": labels,
        "revenues": revenues,
        "order_counts": order_counts,
        "aov": aov_list
    })

@bp.route('/api/stats/order-status')
def order_status():
    """Thống kê số lượng đơn theo từng trạng thái"""
    # Ánh xạ từ status mã (pending, completed, cancelled) sang tên hiển thị Tiếng Việt
    status_map = {
        'completed': 'Hoàn thành',
        'pending': 'Chờ xử lý',
        'cancelled': 'Đã hủy'
    }

    results = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()

    labels = []
    counts = []
    for row in results:
        labels.append(status_map.get(row.status, row.status))
        counts.append(row.count)

    return jsonify({
        "labels": labels,
        "counts": counts
    })


@bp.route('/api/stats/top-products')
def top_products():
    """Top 5 sản phẩm bán chạy nhất (tính theo số lượng đã bán của đơn 'completed')"""
    results = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.status == 'completed'
    ).group_by(
        Product.id, Product.name
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(5).all()

    labels = [row.name for row in results]
    quantities = [int(row.total_quantity or 0) for row in results]

    return jsonify({
        "labels": labels,
        "quantities": quantities
    })