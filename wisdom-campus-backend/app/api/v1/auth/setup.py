"""
Auth0设置和初始化模块
"""
from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import JWTManager

# 初始化OAuth
oauth = OAuth()

# 初始化JWT管理器
jwt = JWTManager()

# Auth0配置函数
def setup_auth0(app):
    """
    初始化Auth0配置
    
    参数:
        app: Flask应用实例
    """
    oauth.init_app(app)
    
    # 初始化JWT管理器
    jwt.init_app(app)
    
    # 添加JWT标识转换回调函数，确保用户ID始终是字符串
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        # 确保用户ID始终是字符串类型
        if user is not None:
            return str(user)
        return user
        
    # 添加JWT标识加载回调函数
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        # 获取用户ID
        identity = jwt_data["sub"]
        # 从数据库中获取用户
        from app.models.user import User
        # 如果ID是字符串但可以转换为数字，就转换
        if isinstance(identity, str) and identity.isdigit():
            user_id = int(identity)
        else:
            user_id = identity
        # 返回用户对象
        return User.query.get(user_id)
    
    # 配置基本的 Auth0 参数
    oauth.register(
        "auth0",
        client_id=app.config["AUTH0_CLIENT_ID"],
        client_secret=app.config["AUTH0_CLIENT_SECRET"],
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration',
        # 临时解决方案：关闭 state 验证
        enforce_state=False
    )
    
    return oauth
