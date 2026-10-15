from flask import render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp  
from app.models import User
from app.extensions import db

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if len(password) < 6:
            flash('Mật khẩu phải chứa ít nhất 6 ký tự!', 'warning')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash('Email hoặc Tên tài khoản đã tồn tại!', 'danger')
            return redirect(url_for('auth.register'))

        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            role='customer'
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Chào mừng {user.username} đã đăng nhập!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.index'))
        else:
            flash('Email hoặc mật khẩu không chính xác!', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất tài khoản.', 'info')
    return redirect(url_for('main.index'))