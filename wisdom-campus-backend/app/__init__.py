from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask import render_template

# 初始化扩展，但不传入应用实例
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()

def create_app(config_class='app.config.development'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 确保 SECRET_KEY 已设置（用于会话加密）
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev_secret_key_for_session'

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    CORS(app)

    # 初始化Auth0
    from app.api.v1.auth import auth_bp, setup_auth0
    setup_auth0(app)
    
    # 注册蓝图
    from app.api.v1.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    from app.api.v1.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/v1/user')
    
    # 创建一个简单的路由用于测试
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app 