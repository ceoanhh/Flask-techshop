from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user

def admin_required(f):
    """
    Decorator kiểm tra quyền truy cập của Quản trị viên:
    - Nếu chưa đăng nhập: chuyển hướng tới trang Đăng nhập
    - Nếu không phải admin: báo lỗi và chuyển hướng về Trang chủ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vui lòng đăng nhập bằng tài khoản Quản trị viên để truy cập.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            flash('Bạn không có quyền truy cập vào khu vực Quản trị!', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
