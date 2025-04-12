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
