import os
from flask import Flask
from config import Config
from app.extensions import db, login_manager, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Đảm bảo thư mục lưu trữ dữ liệu và upload tồn tại
    instance_path = os.path.join(app.root_path, '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Khởi tạo extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Đăng ký Blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.cart import bp as cart_bp
    app.register_blueprint(cart_bp, url_prefix='/cart')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
