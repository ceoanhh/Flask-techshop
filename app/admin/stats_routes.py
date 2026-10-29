from datetime import datetime, timedelta
from app.admin import bp
from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract, or_, case
from app.extensions import db
from app.models import Order, OrderItem, Product, Category, User  # Import models của bạn

from datetime import datetime
from flask import jsonify
from sqlalchemy import extract, func

@bp.route('/api/stats/category-revenue')
def category_revenue():
    """Doanh thu, Số đơn thành công & AOV phân theo từng Danh mục trong 6 tháng gần nhất"""
    now = datetime.utcnow()

    # 1. Khung 6 tháng gần nhất
    months_list = []
    current_year = now.year
    current_month = now.month

    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        months_list.append({'year': y, 'month': m, 'label': f"T{m:02d}/{y}"})

    first_month = months_list[0]
    start_date = datetime(first_month['year'], first_month['month'], 1)

    # 2. Truy vấn Doanh thu VÀ Số đơn hàng distinct theo Tháng + Category
    results = db.session.query(
        extract('year', Order.created_at).label('year'),
        extract('month', Order.created_at).label('month'),
        Category.name.label('category_name'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('category_revenue'),
        func.count(func.distinct(Order.id)).label('category_order_count')
    ).join(OrderItem, Order.id == OrderItem.order_id) \
        .join(Product, OrderItem.product_id == Product.id) \
        .join(Category, Product.category_id == Category.id) \
        .filter(
        Order.status == 'completed',
        Order.created_at >= start_date
    ).group_by(
        extract('year', Order.created_at),
        extract('month', Order.created_at),
        Category.name
    ).all()

    # 3. Gom nhóm dữ liệu theo Category
    cat_data = {}
    categories = set()

    for row in results:
        cat_name = row.category_name or "Khác"
        categories.add(cat_name)
        if cat_name not in cat_data:
            cat_data[cat_name] = {}

        cat_data[cat_name][(int(row.year), int(row.month))] = {
            'revenue': float(row.category_revenue or 0.0),
            'order_count': int(row.category_order_count or 0)
        }

    labels = [m['label'] for m in months_list]
    datasets_revenue = []
    datasets_orders = []
    datasets_aov = []

    # Bảng màu cố định cho các cột Category
    colors = [
        {'bg': 'rgba(255, 99, 132, 0.7)', 'border': 'rgba(255, 99, 132, 1)'},
        {'bg': 'rgba(75, 192, 192, 0.7)', 'border': 'rgba(75, 192, 192, 1)'},
        {'bg': 'rgba(153, 102, 255, 0.7)', 'border': 'rgba(153, 102, 255, 1)'},
        {'bg': 'rgba(255, 159, 64, 0.7)', 'border': 'rgba(255, 159, 64, 1)'},
        {'bg': 'rgba(54, 162, 235, 0.7)', 'border': 'rgba(54, 162, 235, 1)'}
    ]

    for idx, cat_name in enumerate(sorted(list(categories))):
        color = colors[idx % len(colors)]

        rev_series = []
        orders_series = []
        aov_series = []

        for m in months_list:
            data = cat_data[cat_name].get((m['year'], m['month']), {'revenue': 0.0, 'order_count': 0})
            rev = data['revenue']
            cnt = data['order_count']

            # Tính AOV theo category = Doanh thu danh mục / Số đơn chứa danh mục đó
            aov = round(rev / cnt) if cnt > 0 else 0

            rev_series.append(rev)
            orders_series.append(cnt)
            aov_series.append(aov)

        # Dataset Doanh thu
        datasets_revenue.append({
            'label': cat_name,
            'data': rev_series,
            'backgroundColor': color['bg'],
            'borderColor': color['border'],
            'borderWidth': 1,
            'borderRadius': 4
        })

        # Dataset Số đơn thành công
        datasets_orders.append({
            'label': cat_name,
            'data': orders_series,
            'backgroundColor': color['bg'],
            'borderColor': color['border'],
            'borderWidth': 1,
            'borderRadius': 4
        })

        # Dataset AOV
        datasets_aov.append({
            'label': cat_name,
            'data': aov_series,
            'backgroundColor': color['bg'],
            'borderColor': color['border'],
            'borderWidth': 1,
            'borderRadius': 4
        })

    return jsonify({
        "labels": labels,
        "category_revenues": datasets_revenue,
        "category_orders": datasets_orders,
        "category_aov": datasets_aov
    })

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

@bp.route('/api/stats/low-stock') # Hoặc /admin/api/stats/low-stock tùy theo blueprint
def low_stock_products():
    # 1. Lấy tham số threshold và ép kiểu int (mặc định 5)
    threshold = request.args.get('threshold', default=10, type=int)

    # 2. Truy vấn dùng outerjoin và bao hàm cả trường hợp stock_quantity bị NULL
    results = db.session.query(
        Product.id,
        Product.name,
        Product.stock_quantity,
        Product.price,
        Category.name.label('category_name')
    ).outerjoin(
        Category, Product.category_id == Category.id
    ).filter(
        or_(
            Product.stock_quantity <= threshold,
            Product.stock_quantity.is_(None) # Bắt cả trường hợp chưa nhập số lượng
        )
    ).order_by(
        Product.stock_quantity.asc()
    ).all()

    # 3. Tạo danh sách kết quả
    data = [
        {
            "id": row.id,
            "name": row.name,
            "stock_quantity": 0 if row.stock_quantity is None else int(row.stock_quantity),
            "price": float(row.price or 0.0),
            "category": row.category_name or "Chưa phân loại"
        }
        for row in results
    ]

    return jsonify(data)

@bp.route('/api/stats/advanced-analytics')
def advanced_analytics():
    """Tích hợp: Tỷ lệ hủy đơn, Khách hàng mới vs Quay lại, Top Khách hàng & Hàng tồn lâu"""
    now = datetime.utcnow()
    ninety_days_ago = now - timedelta(days=90)

    # --- 1. TỶ LỆ HỦY ĐƠN (Cancellation Rate) ---
    total_orders_count = db.session.query(func.count(Order.id)).scalar() or 0
    cancelled_orders_count = db.session.query(func.count(Order.id)).filter(Order.status == 'cancelled').scalar() or 0
    cancellation_rate = round((cancelled_orders_count / total_orders_count * 100), 2) if total_orders_count > 0 else 0.0

    # --- 2. KHÁCH HÀNG MỚI VS KHÁCH HÀNG QUAY LẠI ---
    # Đếm số đơn của từng user
    user_order_counts = db.session.query(
        Order.user_id,
        func.count(Order.id).label('order_cnt')
    ).filter(Order.user_id.isnot(None))\
     .group_by(Order.user_id).subquery()

    # Phân loại đơn hàng
    customer_types = db.session.query(
        func.count(case((user_order_counts.c.order_cnt == 1, 1))).label('new_customers'),
        func.count(case((user_order_counts.c.order_cnt > 1, 1))).label('returning_customers')
    ).first()

    new_cust = customer_types.new_customers or 0
    ret_cust = customer_types.returning_customers or 0

    # --- 3. TOP KHÁCH HÀNG THÂN THIẾT (Top 5) ---
    top_customers_query = db.session.query(
        User.username,
        User.email,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_spent')
    ).join(Order, User.id == Order.user_id)\
     .filter(Order.status == 'completed')\
     .group_by(User.id, User.username, User.email)\
     .order_by(func.sum(Order.total_amount).desc())\
     .limit(5).all()

    top_customers = [
        {
            "username": row.username,
            "email": row.email,
            "total_orders": int(row.total_orders or 0),
            "total_spent": float(row.total_spent or 0.0)
        }
        for row in top_customers_query
    ]

    # --- 4. SẢN PHẨM TỒN KHÔ LAU / HÀNG CHẾT (Không bán được trong 90 ngày) ---
    # Subquery: Lấy danh sách ID các sản phẩm có đơn hàng completed trong 90 ngày qua
    recent_sold_product_ids = db.session.query(OrderItem.product_id)\
        .join(Order, OrderItem.order_id == Order.id)\
        .filter(Order.status == 'completed', Order.created_at >= ninety_days_ago)\
        .distinct().subquery()

    # Query sản phẩm không nằm trong danh sách bán gần đây
    dead_stock_query = db.session.query(
        Product.id,
        Product.name,
        Product.stock_quantity,
        Product.price
    ).filter(~Product.id.in_(recent_sold_product_ids))\
     .order_by(Product.stock_quantity.desc())\
     .limit(5).all()

    dead_stock = [
        {
            "id": row.id,
            "name": row.name,
            "stock_quantity": int(row.stock_quantity or 0),
            "price": float(row.price or 0.0)
        }
        for row in dead_stock_query
    ]

    return jsonify({
        "cancellation_rate": cancellation_rate,
        "total_orders": total_orders_count,
        "cancelled_orders": cancelled_orders_count,
        "customer_segments": {
            "new_customers": new_cust,
            "returning_customers": ret_cust
        },
        "top_customers": top_customers,
        "dead_stock": dead_stock
    })


@bp.route('/api/stats/peak-hours')
def peak_hours():
    """5. Thống kê đơn hàng theo Khung giờ trong ngày (0-23h)"""
    results = db.session.query(
        extract('hour', Order.created_at).label('hour'),
        func.count(Order.id).label('order_count')
    ).group_by(extract('hour', Order.created_at))\
     .order_by(extract('hour', Order.created_at)).all()

    # Khởi tạo mảng 24 giờ
    hours_data = {int(h): 0 for h in range(24)}
    for row in results:
        hours_data[int(row.hour)] = int(row.order_count or 0)

    labels = [f"{h:02d}:00" for h in range(24)]
    counts = [hours_data[h] for h in range(24)]

    return jsonify({
        "labels": labels,
        "counts": counts
    })