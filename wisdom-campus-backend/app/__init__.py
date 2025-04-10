from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_marshmallow import Marshmallow

# 初始化扩展，但不传入应用实例
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()

def create_app(config_class='app.config.development'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    CORS(app)

    # 在此处注册蓝图
    # from app.api.v1.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    # 创建一个简单的路由用于测试
    @app.route('/')
    def index():
        return {'message': '欢迎使用智慧校园学习助手系统API!'}

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app 