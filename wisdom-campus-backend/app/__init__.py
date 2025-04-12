from flask import Flask, session, redirect, url_for
from flask_cors import CORS
from flask import render_template, request, jsonify
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
from app.extensions import db, migrate, ma
from flask_jwt_extended import jwt_required, get_jwt_identity

# 不再在这里初始化扩展
# db = SQLAlchemy()
# migrate = Migrate()
# ma = Marshmallow()

def create_app(config_class='app.config.development'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 确保使用UTF-8编码处理响应
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
    
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
    
    # 初始化Swagger
    from app.utils.swagger import setup_swagger
    setup_swagger(app)
    
    # 注册蓝图
    from app.api.v1.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    from app.api.v1.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/v1/user')
    
    # 注册Auth0诊断工具蓝图，便于排查问题
    try:
        from app.api.v1.auth.auth0_diag import auth0_diag_bp
        app.register_blueprint(auth0_diag_bp, url_prefix='/api/v1/diag/auth0')
        app.logger.info("已注册Auth0诊断工具路由: /api/v1/diag/auth0/check")
    except ImportError:
        app.logger.warning("Auth0诊断工具未找到，跳过注册")
    
    # 注册学习模块蓝图 (如果存在)
    try:
        from app.api.v1.learning import learning_bp
        app.register_blueprint(learning_bp, url_prefix='/api/v1/learning')
    except ImportError:
        pass
    
    # 创建一个简单的路由用于测试
    @app.route('/')
    def index():
        # 检查用户是否已登录（通过session或JWT）
        user_id = session.get('user_id')
        if user_id:
            # 已登录用户，重定向到学生仪表盘
            return redirect(url_for('student_dashboard'))
        # 未登录用户，显示首页
        return render_template('index.html')

    @app.route('/login')
    def login():
        """登录页面"""
        # 如果已登录，直接重定向到学生仪表盘
        if 'user_id' in session:
            return redirect(url_for('student_dashboard'))
        return render_template('auth/login.html')
        
    @app.route('/register')
    def register():
        """注册页面"""
        # 如果已登录，直接重定向到学生仪表盘
        if 'user_id' in session:
            return redirect(url_for('student_dashboard'))
        return render_template('auth/register.html')

    @app.route('/verification-waiting')
    def verification_waiting_page():
        """邮箱验证等待页面"""
        # 获取URL参数
        email = request.args.get('email', '')
        auth0_id = request.args.get('auth0_id', '')
        
        # 记录日志
        app.logger.info(f"访问验证等待页面: email={email}, auth0_id={auth0_id}")
        
        # 将参数传递给模板
        return render_template('auth/verification_waiting.html', email=email, auth0_id=auth0_id)

    @app.route('/api_docs')
    def api_docs():
        """API文档页面"""
        return render_template('api_docs.html')

    @app.route('/health')
    def health():
        """健康检查接口"""
        return api_success(data={'status': 'ok'})

    @app.route('/admin')
    @app.route('/admin/')
    def admin_dashboard():
        """管理员控制台"""
        from app.utils.auth import requires_auth, requires_admin
        # 使用装饰器验证是否登录并且是管理员
        @requires_auth
        @requires_admin
        def protected_admin():
            return render_template('admin/dashboard.html')
        return protected_admin()
    
    @app.route('/student/dashboard')
    def student_dashboard():
        """学生仪表盘页面"""
        # 导入User模型
        from app.models.user import User

        # 首先检查session中是否有user_id
        user_id = session.get('user_id')
        user = None

        # 如果session中没有user_id，尝试从JWT令牌获取
        if not user_id:
            # 尝试从请求头获取JWT令牌
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    from flask_jwt_extended import decode_token
                    token = auth_header.split(' ')[1]
                    token_data = decode_token(token)
                    user_id = token_data.get('sub')  # JWT中的subject是用户ID
                    app.logger.info(f"从JWT令牌获取用户ID: {user_id}")
                except Exception as e:
                    app.logger.error(f"解析JWT令牌失败: {str(e)}")
            
            # 如果localStorage中有auth_token，尝试从中获取用户信息
            # 这部分逻辑需要在前端JavaScript中实现

        # 如果通过任何方式找到了user_id
        if user_id:
            try:
                # 查询用户
                user = User.query.get(user_id)
                if user:
                    app.logger.info(f"用户已登录: ID={user_id}, 名称={user.name}")
                else:
                    app.logger.warning(f"用户ID有效但未找到用户记录: {user_id}")
            except Exception as e:
                app.logger.error(f"查询用户时发生错误: {str(e)}")
        
        # 即使未登录也允许访问仪表盘页面，但页面内容会根据是否登录而不同
        # 这样可以避免重定向循环，前端可以处理未登录状态
        return render_template('student/dashboard.html', user=user)
    
    # 注册错误处理程序
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    return app 