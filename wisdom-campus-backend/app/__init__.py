from flask import Flask, session, redirect, url_for, make_response
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
    
    # 配置自定义JSON编码器，处理Decimal等特殊类型
    from app.utils.response import CustomJSONEncoder
    app.json_encoder = CustomJSONEncoder
    
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
        from app.models.user import User
        from flask_jwt_extended import decode_token
        
        # 首先尝试从请求中获取JWT令牌
        user = None
        auth_header = request.headers.get('Authorization', '')
        token_param = request.args.get('token', '')
        cookie_token = request.cookies.get('admin_token')
        
        # 检查URL中是否有login_success参数，这表示是从登录页面重定向而来
        is_login_success = request.args.get('login_success') == 'true'
        
        app.logger.info(f"访问管理员仪表盘: headers={bool(auth_header)}, token_param={bool(token_param)}, cookie_token={bool(cookie_token)}, is_login_success={is_login_success}")
        
        # 如果有防止重定向循环的cookie标记并且不是login_success=true，直接进入页面不做认证
        prevent_redirect = request.cookies.get('prevent_redirect_loop') == 'true'
        if prevent_redirect and not is_login_success:
            app.logger.info("检测到防重定向cookie，跳过认证检查直接渲染页面")
            response = make_response(render_template('admin/dashboard.html', user={'name': 'Admin'}))
            # 延长防重定向cookie的有效期
            response.set_cookie('prevent_redirect_loop', 'true', max_age=60)  # 60秒有效期
            return response
        
        # 首先从请求头获取token
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            app.logger.info(f"从请求头获取到JWT令牌")
        # 如果请求头没有，从URL参数获取
        elif token_param:
            token = token_param
            app.logger.info(f"从URL参数获取到JWT令牌")
        # 如果URL参数没有，从cookie获取
        elif cookie_token:
            token = cookie_token
            app.logger.info(f"从cookie获取到JWT令牌: {cookie_token[:10]}...")
        
        # 尝试解析JWT令牌
        if token:
            try:
                app.logger.info(f"尝试解析JWT令牌: {token[:10]}...")
                payload = decode_token(token)
                app.logger.info(f"JWT解析结果: user_id={payload.get('sub')}, is_admin={payload.get('is_admin')}")
                
                # 从JWT中获取用户ID
                user_id = payload.get('sub')
                app.logger.info(f"从JWT中获取用户ID: {user_id}")
                
                # 如果用户ID是字符串且可以转换为整数，则转换
                if isinstance(user_id, str) and user_id.isdigit():
                    user_id = int(user_id)
                
                # 根据用户ID查询用户
                user = User.query.get(user_id)
                
                if user:
                    app.logger.info(f"通过JWT找到用户: {user.name}, 是否管理员: {user.is_admin}")
                else:
                    app.logger.warning(f"通过JWT找不到用户, ID: {user_id}")
            except Exception as e:
                app.logger.error(f"解析JWT令牌出错: {str(e)}")
        
        # 如果没有登录或者不是管理员，重定向到管理员登录页面
        if not user:
            app.logger.warning("用户未找到，重定向到管理员登录页面")
            return redirect(url_for('admin_login'))
            
        if not user.is_admin:
            app.logger.warning(f"用户不是管理员: {user.name}, 重定向到管理员登录页面")
            return redirect(url_for('admin_login'))
        
        # 用户已登录且是管理员，渲染管理员控制台页面
        app.logger.info(f"管理员{user.name}成功访问管理员仪表盘")
        
        # 检查是否来自登录页面的重定向
        is_redirect = request.args.get('login_success') == 'true'
        app.logger.info(f"是否来自登录成功的重定向: {is_redirect}")
        
        # 创建响应对象，以便设置cookie
        response = make_response(render_template('admin/dashboard.html', user=user))
        
        # 在cookie中设置一个管理员token（备份）
        if token:
            response.set_cookie('admin_token', token, max_age=3600, httponly=False)  # 1小时有效期，允许JS访问
        
        # 在cookie中设置一个最近登录的标记
        response.set_cookie('admin_login_verified', 'true', max_age=300)  # 5分钟有效期
        
        # 如果是重定向过来的，设置一个特殊标记以防止循环
        if is_redirect:
            response.set_cookie('prevent_redirect_loop', 'true', max_age=60)  # 60秒有效期
            app.logger.info("设置防重定向循环cookie标记")
            
        return response
    
    @app.route('/admin/login')
    def admin_login():
        """管理员登录页面"""
        # 检查是否有防重定向循环标记
        prevent_redirect = request.cookies.get('prevent_redirect_loop') == 'true'
        
        if prevent_redirect:
            app.logger.warning("检测到潜在的重定向循环，显示错误信息而不是重定向")
            return render_template('error.html', 
                                  title="重定向循环检测", 
                                  message="系统检测到潜在的重定向循环。请尝试清除浏览器缓存和Cookie，然后重新登录。如果问题持续出现，请联系系统管理员。",
                                  error_code=400), 400
        
        # 检查是否已登录
        user_id = session.get('user_id')
        if user_id:
            # 检查是否是管理员
            from app.models.user import User
            user = User.query.get(user_id)
            if user and user.is_admin:
                # 已登录且是管理员，直接重定向到管理员控制台
                app.logger.info(f"管理员{user.name}已通过session登录，重定向到管理员控制台")
                return redirect(url_for('admin_dashboard'))
        
        # 同时检查token
        auth_header = request.headers.get('Authorization', '')
        cookie_token = request.cookies.get('admin_token')
        
        # 记录状态
        app.logger.info(f"访问管理员登录页面: auth_header存在={bool(auth_header)}, cookie_token存在={bool(cookie_token)}")
        
        # 如果有token，检查是否有效
        if (auth_header.startswith('Bearer ') or cookie_token):
            try:
                from flask_jwt_extended import decode_token
                from app.models.user import User
                
                token = None
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    app.logger.info("从Authorization头获取token")
                elif cookie_token:
                    token = cookie_token
                    app.logger.info(f"从cookie获取token: {cookie_token[:10]}...")
                
                if token:
                    # 解析JWT令牌
                    app.logger.info(f"尝试解析JWT令牌: {token[:10]}...")
                    payload = decode_token(token)
                    user_id = payload.get('sub')
                    is_admin = payload.get('is_admin', False)
                    
                    app.logger.info(f"JWT解析结果: user_id={user_id}, is_admin={is_admin}")
                    
                    if user_id and isinstance(user_id, str) and user_id.isdigit():
                        user_id_int = int(user_id)
                        user = User.query.get(user_id_int)
                        
                        if user and user.is_admin:
                            # 令牌有效且用户是管理员，重定向到仪表盘
                            app.logger.info(f"管理员{user.name}已通过JWT登录，重定向到管理员控制台")
                            # 清除防重定向标记，允许正常访问仪表盘
                            response = make_response(redirect(url_for('admin_dashboard')))
                            response.delete_cookie('prevent_redirect_loop')
                            return response
                        elif user:
                            app.logger.warning(f"用户{user.name}通过JWT登录但不是管理员")
                        else:
                            app.logger.warning(f"通过JWT无法找到用户: {user_id}")
            except Exception as e:
                app.logger.error(f"验证管理员token失败: {str(e)}", exc_info=True)
        
        # 未登录或不是管理员，显示管理员登录页面
        response = make_response(render_template('admin/login.html'))
        
        # 清除可能导致问题的cookie
        response.delete_cookie('prevent_redirect_loop')
        
        return response
    
    @app.route('/student/dashboard')
    def student_dashboard():
        """学生仪表盘页面"""
        # 导入User模型
        from app.models.user import User
        from flask_jwt_extended import decode_token, verify_jwt_in_request, get_jwt_identity, current_user
        
        # 首先尝试从请求中获取JWT令牌（前端传递）
        user = None
        auth_header = request.headers.get('Authorization', '')
        
        # 检查是否是验证请求
        auth_verify = request.args.get('auth_verify', '0') == '1'
        token_param = request.args.get('token', '')
        
        # 是否只是验证不渲染页面（用于iframe验证）
        verify_only = request.args.get('verify_only', '0') == '1'
        
        # 如果有令牌参数，则使用参数中的令牌
        if token_param:
            app.logger.info(f"从URL参数获取到JWT令牌")
            auth_header = f"Bearer {token_param}"
        
        # 记录请求头信息，帮助调试
        app.logger.info(f"仪表盘请求头: {dict(request.headers)}")
        
        if auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                app.logger.info(f"从{'URL参数' if token_param else '请求头'}获取到JWT令牌")
                
                # 解析JWT令牌
                payload = decode_token(token)
                user_id = payload.get('sub')  # JWT中的subject是用户ID
                
                app.logger.info(f"JWT令牌解析结果: user_id={user_id}, 类型={type(user_id).__name__}, payload={payload}")
                
                if user_id:
                    # 确保user_id是整数类型（因为数据库ID字段是整数）
                    if isinstance(user_id, str):
                        # 如果是数字字符串，转换为整数
                        if user_id.isdigit():
                            user_id_int = int(user_id)
                            app.logger.info(f"将字符串用户ID转换为整数: {user_id} -> {user_id_int}")
                            user = User.query.get(user_id_int)
                        else:
                            # 非数字字符串，可能是其他格式
                            app.logger.info(f"使用非数字字符串用户ID查询: {user_id}")
                            user = User.query.filter_by(auth0_id=user_id).first()
                    else:
                        # 直接使用用户ID查询
                        app.logger.info(f"使用非字符串用户ID查询: {user_id}")
                        user = User.query.get(user_id)
                    
                    if user:
                        app.logger.info(f"成功获取用户信息: {user.name}")
                        
                        # 只有当明确请求验证且不渲染页面时才返回JSON
                        if auth_verify and verify_only:
                            from app.utils.response import api_success
                            return api_success(data={
                                'verified': True,
                                'user_id': str(user.id),
                                'name': user.name
                            })
                        # 否则继续执行，渲染HTML页面
                    else:
                        app.logger.warning(f"未找到用户记录，用户ID: {user_id}")
            except Exception as e:
                app.logger.error(f"解析JWT令牌失败: {str(e)}")
                
                # 只有当明确请求验证且不渲染页面时才返回错误信息
                if auth_verify and verify_only:
                    from app.utils.response import api_error
                    return api_error(message=f"令牌验证失败: {str(e)}")

        # 如果未通过JWT找到用户，则尝试从session中获取
        if not user:
            user_id = session.get('user_id')
            if user_id:
                try:
                    user = User.query.get(user_id)
                    app.logger.info(f"从会话中识别用户: ID={user_id}, 名称={user.name if user else 'Unknown'}")
                except Exception as e:
                    app.logger.error(f"从会话中获取用户信息失败: {str(e)}")
        
        # 只有当明确请求验证且不渲染页面时才返回未认证信息
        if auth_verify and verify_only:
            from app.utils.response import api_error
            return api_error(message="用户未认证")
            
        # 即使未登录也允许访问仪表盘页面，但页面内容会根据是否登录而不同
        # 这样可以避免重定向循环，前端可以处理未登录状态
        app.logger.info(f"渲染仪表盘页面，用户状态: {'已登录' if user else '未登录'}")
        return render_template('student/dashboard.html', user=user)
    
    @app.route('/student/profile')
    def student_profile():
        """学生个人主页"""
        # 导入User模型
        from app.models.user import User
        from flask_jwt_extended import decode_token, verify_jwt_in_request, get_jwt_identity

        # 首先尝试从请求中获取JWT令牌
        user = None
        auth_header = request.headers.get('Authorization', '')
        
        # 检查是否是验证请求
        auth_verify = request.args.get('auth_verify', '0') == '1'
        token_param = request.args.get('token', '')
        
        # 是否只是验证不渲染页面（用于iframe验证）
        verify_only = request.args.get('verify_only', '0') == '1'
        
        # 如果有令牌参数，则使用参数中的令牌
        if token_param:
            app.logger.info(f"从URL参数获取到JWT令牌")
            auth_header = f"Bearer {token_param}"
        
        # 记录请求头信息，帮助调试
        app.logger.info(f"个人主页请求头: {dict(request.headers)}")
        
        if auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                app.logger.info(f"从{'URL参数' if token_param else '请求头'}获取到JWT令牌")
                
                # 解析JWT令牌
                payload = decode_token(token)
                user_id = payload.get('sub')  # JWT中的subject是用户ID
                
                app.logger.info(f"JWT令牌解析结果: user_id={user_id}, 类型={type(user_id).__name__}, payload={payload}")
                
                if user_id:
                    # 确保user_id是整数类型（因为数据库ID字段是整数）
                    if isinstance(user_id, str):
                        # 如果是数字字符串，转换为整数
                        if user_id.isdigit():
                            user_id_int = int(user_id)
                            app.logger.info(f"将字符串用户ID转换为整数: {user_id} -> {user_id_int}")
                            user = User.query.get(user_id_int)
                        else:
                            # 非数字字符串，可能是其他格式
                            app.logger.info(f"使用非数字字符串用户ID查询: {user_id}")
                            user = User.query.filter_by(auth0_id=user_id).first()
                    else:
                        # 直接使用用户ID查询
                        app.logger.info(f"使用非字符串用户ID查询: {user_id}")
                        user = User.query.get(user_id)
                    
                    if user:
                        app.logger.info(f"成功获取用户信息: {user.name}")
                        
                        # 只有当明确请求验证且不渲染页面时才返回JSON
                        if auth_verify and verify_only:
                            from app.utils.response import api_success
                            return api_success(data={
                                'verified': True,
                                'user_id': str(user.id),
                                'name': user.name
                            })
                        # 否则继续执行，渲染HTML页面
                    else:
                        app.logger.warning(f"未找到用户记录，用户ID: {user_id}")
            
            except Exception as e:
                app.logger.error(f"解析JWT令牌失败: {str(e)}")
            
            # 注意：如果令牌验证成功但没有返回，会继续执行，渲染页面

        # 如果未通过JWT找到用户，则尝试从session中获取
        if not user:
            user_id = session.get('user_id')
            if user_id:
                try:
                    user = User.query.get(user_id)
                    app.logger.info(f"从会话中识别用户: ID={user_id}, 名称={user.name if user else 'Unknown'}")
                    # 同时获取用户画像数据
                    if user and not user.profile:
                        app.logger.info(f"用户没有画像数据，创建默认画像")
                        from app.models.user import UserProfile
                        user.profile = UserProfile(user_id=user.id)
                        db.session.commit()
                except Exception as e:
                    app.logger.error(f"从会话中获取用户信息失败: {str(e)}")
        
        # 如果明确只是验证请求且不渲染页面，但未找到用户，返回未认证信息
        if auth_verify and verify_only:
            from app.utils.response import api_error
            return api_error(message="用户未认证")
            
        # 如果用户未登录，重定向到登录页面
        if not user:
            app.logger.warning("用户未登录，重定向到登录页面")
            return redirect(url_for('login'))
        
        # 渲染个人主页模板，传入用户对象
        return render_template('student/profile.html', user=user)
    
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