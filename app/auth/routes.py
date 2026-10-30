import time
import random
import re
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp  
from app.models import User, Order
from app.extensions import db

VIETNAM_PHONE_REGEX = r'^(0|\+84)(3[2-9]|5[2689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7}$'

def clean_identifier(val):
    """Chuẩn hóa Email hoặc Số điện thoại (Email giữ nguyên dấu chấm, SĐT loại bỏ ký tự lạ)."""
    if not val:
        return ''
    val = val.strip()
    if '@' in val:
        return val.lower()
    return val.replace(' ', '').replace('.', '').replace('-', '')


# ====================================================
# 1. ĐĂNG KÝ TÀI KHOẢN (2 BƯỚC: NHẬP TIN ➔ XÁC NHẬN OTP)
# ====================================================

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Bước 1: Điền thông tin đăng ký. Khi bấm Đăng ký, hệ thống tự động sinh và gửi OTP."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    next_page = request.args.get('next')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = clean_identifier(request.form.get('phone', ''))
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Kiểm tra tính hợp lệ của dữ liệu
        if len(password) < 6:
            flash('Mật khẩu phải chứa ít nhất 6 ký tự!', 'warning')
            return render_template('auth/register.html', next=next_page)

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'danger')
            return render_template('auth/register.html', next=next_page)

        if not re.match(VIETNAM_PHONE_REGEX, phone):
            flash('Số điện thoại không đúng chuẩn 10 chữ số của các nhà mạng Việt Nam (đầu 03, 05, 07, 08, 09)!', 'danger')
            return render_template('auth/register.html', next=next_page)

        # Kiểm tra xem tên, email hoặc SĐT đã tồn tại chưa
        if User.query.filter(User.username == username).first():
            flash('Tên người dùng (Username) này đã được sử dụng!', 'danger')
            return render_template('auth/register.html', next=next_page)

        if User.query.filter(User.email == email).first():
            flash('Địa chỉ Email này đã được đăng ký tài khoản khác!', 'danger')
            return render_template('auth/register.html', next=next_page)

        if User.query.filter(User.phone == phone).first():
            flash('Số điện thoại này đã được sử dụng cho một tài khoản khác!', 'danger')
            return render_template('auth/register.html', next=next_page)

        # TỰ ĐỘNG SINH MÃ OTP VÀ LƯU VÀO SESSION CHỜ XÁC THỰC
        otp_code = str(random.randint(100000, 999999))
        session['pending_register'] = {
            'username': username,
            'email': email,
            'phone': phone,
            'password': password,
            'next': next_page
        }
        session['register_otp'] = otp_code
        session['register_expiry'] = time.time() + 180  # Hạn 3 phút
        session.pop('otp_demo', None)

        # GỬI MÃ OTP VÀO TERMINAL MÁY CHỦ THAY VÌ HIỂN THỊ TRÊN WEB
        print("\n" + "=" * 60)
        print("🔒 [TECHSHOP SECURITY] MÃ XÁC THỰC OTP ĐĂNG KÝ TÀI KHOẢN")
        print(f"👉 Người dùng   : {username}")
        print(f"📞 Số điện thoại: {phone}")
        print(f"📧 Email         : {email}")
        print(f"🔑 MÃ OTP       : >>> {otp_code} <<<")
        print("⏰ Hiệu lực     : 3 phút (180 giây)")
        print("=" * 60 + "\n", flush=True)

        flash(f'Mã xác thực OTP đã được gửi đến số điện thoại {phone}. Vui lòng nhập mã để hoàn tất đăng ký!', 'info')
        return redirect(url_for('auth.verify_register'))

    return render_template('auth/register.html', next=next_page)


@bp.route('/verify-register', methods=['GET', 'POST'])
def verify_register():
    """Bước 2: Xác nhận mã OTP để kích hoạt tài khoản."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    pending = session.get('pending_register')
    stored_otp = session.get('register_otp')
    stored_expiry = session.get('register_expiry', 0)

    if not pending or not stored_otp:
        flash('Vui lòng điền thông tin đăng ký tài khoản trước!', 'warning')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()

        if otp != stored_otp or time.time() > stored_expiry:
            flash('Mã OTP không chính xác hoặc đã hết hạn (3 phút)! Vui lòng bấm gửi lại mã OTP.', 'danger')
            return render_template('auth/verify_register.html', phone=pending['phone'])

        # Khởi tạo User mới sau khi đã xác thực SĐT thành công 100%
        new_user = User(
            username=pending['username'],
            email=pending['email'],
            phone=pending['phone'],
            role='customer'
        )
        new_user.set_password(pending['password'])

        db.session.add(new_user)
        db.session.flush()

        # Tự động gom các đơn hàng cũ của số điện thoại này vào tài khoản mới
        Order.query.filter_by(phone=pending['phone'], user_id=None).update({'user_id': new_user.id})
        db.session.commit()

        next_page = pending.get('next')

        # Dọn dẹp session
        session.pop('pending_register', None)
        session.pop('register_otp', None)
        session.pop('register_expiry', None)
        session.pop('otp_demo', None)

        login_user(new_user)
        flash(f'Chúc mừng {new_user.username}! Tài khoản và số điện thoại {new_user.phone} đã được xác thực thành công.', 'success')

        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.index'))

    return render_template('auth/verify_register.html', phone=pending['phone'])


@bp.route('/api/resend-register-otp', methods=['POST'])
def resend_register_otp():
    """API gửi lại mã OTP cho trang xác nhận đăng ký."""
    pending = session.get('pending_register')
    if not pending:
        return jsonify({'success': False, 'message': 'Không tìm thấy phiên đăng ký!'}), 400

    new_otp = str(random.randint(100000, 999999))
    session['register_otp'] = new_otp
    session['register_expiry'] = time.time() + 180
    session.pop('otp_demo', None)

    # GỬI MÃ OTP MỚI VÀO TERMINAL MÁY CHỦ
    print("\n" + "=" * 60)
    print("🔒 [TECHSHOP SECURITY] GỬI LẠI MÃ OTP ĐĂNG KÝ TÀI KHOẢN")
    print(f"👉 Người dùng   : {pending['username']}")
    print(f"📞 Số điện thoại: {pending['phone']}")
    print(f"🔑 MÃ OTP MỚI   : >>> {new_otp} <<<")
    print("⏰ Hiệu lực     : 3 phút (180 giây)")
    print("=" * 60 + "\n", flush=True)

    return jsonify({
        'success': True,
        'message': f'Đã gửi lại mã OTP đến {pending["phone"]}!',
        'target': pending['phone']
    })


# ====================================================
# 2. ĐĂNG NHẬP / ĐĂNG XUẤT
# ====================================================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    next_page = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        login_id = clean_identifier(request.form.get('login_id', ''))
        password = request.form.get('password')

        # Cho phép đăng nhập linh hoạt bằng Email HOẶC Số điện thoại HOẶC Username
        user = User.query.filter(
            (User.email == login_id) | (User.phone == login_id) | (User.username == login_id)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Chào mừng {user.username} đã đăng nhập!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Thông tin tài khoản hoặc mật khẩu không chính xác!', 'danger')

    return render_template('auth/login.html', next=next_page)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất tài khoản.', 'info')
    return redirect(url_for('main.index'))


# ====================================================
# 3. QUÊN MẬT KHẨU (2 BƯỚC: NHẬP SĐT/EMAIL ➔ NHẬP OTP & ĐẶT LẠI)
# ====================================================

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Bước 1: Nhập Email hoặc SĐT và bấm Gửi mã OTP."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        identifier = clean_identifier(request.form.get('identifier', ''))

        if not identifier:
            flash('Vui lòng nhập Email hoặc Số điện thoại của bạn!', 'warning')
            return render_template('auth/forgot_password.html')

        # Tìm kiếm tài khoản chính xác theo Email hoặc SĐT
        user = User.query.filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()

        if not user:
            flash('Không tìm thấy tài khoản nào gắn với Số điện thoại hoặc Email này!', 'danger')
            return render_template('auth/forgot_password.html')

        now = time.time()
        current_target = session.get('reset_target')
        sent_at = session.get('reset_otp_sent_at', 0)
        stored_otp = session.get('reset_otp')
        stored_expiry = session.get('reset_expiry', 0)

        # KIỂM TRA COOLDOWN 60 GIÂY:
        # Nếu cùng tài khoản và mã cũ vẫn còn hạn (3 phút) & chưa quá 60s kể từ lần gửi trước,
        # hệ thống giữ nguyên mã OTP cũ, không gửi thêm mã mới ra Terminal.
        is_same_target = (current_target == identifier)
        if is_same_target and stored_otp and (now < stored_expiry) and ((now - sent_at) < 60):
            return redirect(url_for('auth.reset_password'))

        # Sinh mã OTP mới khi đã qua 60s hoặc đổi tài khoản hoặc chưa có mã
        otp_code = str(random.randint(100000, 999999))
        session['reset_target'] = identifier
        session['reset_user_id'] = user.id
        session['reset_otp'] = otp_code
        session['reset_expiry'] = now + 180   # Hạn 3 phút
        session['reset_otp_sent_at'] = now    # Thời điểm gửi để tính cooldown 60s
        session['reset_otp_fails'] = 0        # Đặt lại số lần nhập sai
        session.pop('otp_demo', None)

        # GỬI MÃ OTP VÀO TERMINAL MÁY CHỦ THAY VÌ HIỂN THỊ TRÊN WEB ĐẢM BẢO AN TOÀN
        print("\n" + "=" * 60)
        print("🔒 [TECHSHOP SECURITY] MÃ XÁC THỰC OTP KHÔI PHỤC MẬT KHẨU")
        print(f"👉 Tài khoản  : {user.username}")
        print(f"📧 Người nhận : {identifier}")
        print(f"🔑 MÃ OTP     : >>> {otp_code} <<<")
        print("⏰ Hiệu lực   : 3 phút (180 giây)")
        print("=" * 60 + "\n", flush=True)

        return redirect(url_for('auth.reset_password'))

    return render_template('auth/forgot_password.html')


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Bước 2: Nhập mã OTP và mật khẩu mới."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    target = session.get('reset_target')
    stored_otp = session.get('reset_otp')
    stored_expiry = session.get('reset_expiry', 0)
    user_id = session.get('reset_user_id')
    sent_at = session.get('reset_otp_sent_at', 0)
    now = time.time()
    cooldown_seconds = max(0, int(60 - (now - sent_at)))

    if not target or not user_id:
        flash('Vui lòng nhập Email hoặc Số điện thoại để nhận mã xác thực trước!', 'warning')
        return redirect(url_for('auth.forgot_password'))

    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.is_json
        or request.accept_mimetypes.best == 'application/json'
    )

    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 6:
            err_msg = 'Mật khẩu mới phải chứa ít nhất 6 ký tự!'
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg}), 400
            flash(err_msg, 'warning')
            return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)

        if new_password != confirm_password:
            err_msg = 'Mật khẩu xác nhận không trùng khớp!'
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg}), 400
            flash(err_msg, 'danger')
            return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)

        # Kiểm tra nếu mã OTP đã bị hủy (do nhập sai đủ 5 lần)
        if not stored_otp:
            err_msg = 'Mã OTP này đã bị hủy. Vui lòng bấm "Gửi lại mã OTP" để nhận mã mới!'
            if is_ajax:
                return jsonify({'success': False, 'otp_invalidated': True, 'message': err_msg}), 400
            flash(err_msg, 'danger')
            return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)

        # Kiểm tra hết hạn (3 phút)
        if now > stored_expiry:
            err_msg = 'Mã OTP đã hết hạn (3 phút)! Vui lòng bấm gửi lại mã OTP.'
            if is_ajax:
                return jsonify({'success': False, 'otp_invalidated': True, 'message': err_msg}), 400
            flash(err_msg, 'danger')
            return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)

        # Kiểm tra mã OTP nhập vào
        if otp != stored_otp:
            # Tăng số lần nhập sai ngầm trong session
            fails = session.get('reset_otp_fails', 0) + 1
            session['reset_otp_fails'] = fails
            session.modified = True

            # NẾU NHẬP SAI ĐỦ 5 LẦN: HỦY MÃ OTP VÀ THÔNG BÁO GỬI LẠI MÃ MỚI
            if fails >= 5:
                session.pop('reset_otp', None)
                session.pop('reset_expiry', None)
                session.pop('reset_otp_fails', None)
                session.modified = True
                err_msg = 'Bạn đã nhập sai mã OTP quá nhiều lần. Mã xác thực này đã bị hủy, vui lòng gửi lại mã OTP mới!'
                if is_ajax:
                    return jsonify({'success': False, 'otp_invalidated': True, 'message': err_msg}), 400
                flash(err_msg, 'danger')
                return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)

            # NẾU DƯỚI 5 LẦN: CHỈ THÔNG BÁO SAI, TUYỆT ĐỐI KHÔNG HIỂN THỊ SỐ LẦN ĐÃ SAI
            err_msg = 'Mã OTP không chính xác. Vui lòng kiểm tra và nhập lại!'
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg}), 400
            flash(err_msg, 'danger')
            return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)

        # NẾU MÃ OTP HỢP LỆ: TIẾN HÀNH ĐẶT LẠI MẬT KHẨU
        user = db.session.get(User, user_id)
        if not user:
            err_msg = 'Tài khoản người dùng không còn tồn tại!'
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg}), 400
            flash(err_msg, 'danger')
            return redirect(url_for('auth.forgot_password'))

        # Cập nhật mật khẩu mới
        user.set_password(new_password)
        db.session.commit()

        # Dọn dẹp session
        session.pop('reset_target', None)
        session.pop('reset_user_id', None)
        session.pop('reset_otp', None)
        session.pop('reset_expiry', None)
        session.pop('reset_otp_sent_at', None)
        session.pop('reset_otp_fails', None)
        session.pop('otp_demo', None)

        flash('Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay bằng mật khẩu mới.', 'success')
        if is_ajax:
            return jsonify({'success': True, 'redirect_url': url_for('auth.login')})
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', target=target, cooldown_seconds=cooldown_seconds)


@bp.route('/api/resend-reset-otp', methods=['POST'])
def resend_reset_otp():
    """API gửi lại mã OTP cho trang đặt lại mật khẩu với giới hạn chờ 60 giây."""
    target = session.get('reset_target')
    if not target:
        return jsonify({'success': False, 'message': 'Không tìm thấy phiên khôi phục mật khẩu!'}), 400

    now = time.time()
    sent_at = session.get('reset_otp_sent_at', 0)
    remaining = int(60 - (now - sent_at))
    if remaining > 0:
        return jsonify({
            'success': False,
            'message': f'Vui lòng đợi thêm {remaining} giây trước khi gửi lại mã OTP mới!',
            'remaining_seconds': remaining
        }), 429

    new_otp = str(random.randint(100000, 999999))
    session['reset_otp'] = new_otp
    session['reset_expiry'] = now + 180
    session['reset_otp_sent_at'] = now
    session['reset_otp_fails'] = 0  # Đặt lại số lần nhập sai
    session.pop('otp_demo', None)
    session.modified = True

    # GỬI MÃ OTP MỚI VÀO TERMINAL MÁY CHỦ
    print("\n" + "=" * 60)
    print("🔒 [TECHSHOP SECURITY] GỬI LẠI MÃ OTP KHÔI PHỤC MẬT KHẨU")
    print(f"👉 Người nhận : {target}")
    print(f"🔑 MÃ OTP MỚI : >>> {new_otp} <<<")
    print("⏰ Hiệu lực   : 3 phút (180 giây)")
    print("=" * 60 + "\n", flush=True)

    return jsonify({
        'success': True,
        'message': 'Đã gửi lại mã OTP thành công!',
        'target': target,
        'cooldown_seconds': 60
    })
