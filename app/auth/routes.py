from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.models import User
from app.extensions import db

# ==========================================
# MODULE AUTH - PHỤ TRÁCH: DẦN
# ==========================================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        # Dần xử lý logic kiểm tra đăng nhập tại đây
        flash('Chức năng đăng nhập đang được Dần hoàn thiện!', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        # Dần xử lý logic đăng ký tài khoản mới tại đây
        flash('Chức năng đăng ký đang được Dần hoàn thiện!', 'info')
        return redirect(url_for('auth.register'))
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công.', 'success')
    return redirect(url_for('main.index'))
