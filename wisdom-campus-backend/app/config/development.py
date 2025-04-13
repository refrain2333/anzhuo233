"""开发环境配置"""
import os
from dotenv import load_dotenv
from datetime import timedelta

# 加载.env文件中的环境变量
load_dotenv()

# 基础配置
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')

# 数据库配置
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://FZG1234C:FZG1234C@115.120.215.107:3306/xuesheng233')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False  # 不显示SQL查询，减少日志输出

# Auth0配置
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN', 'dev-4pz5hir1kcywjn8m.us.auth0.com')
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID', 'MzZPMotynlZxW5jelcd2xKZ4ca5pEyzE')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET', 'your-auth0-client-secret')
AUTH0_CALLBACK_URL = os.environ.get('AUTH0_CALLBACK_URL', 'http://localhost:5000/api/v1/auth/callback')
AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE', 'https://dev-4pz5hir1kcywjn8m.us.auth0.com/api/v2/')

# 确保 Auth0 API Audience 正确
# 对于Resource Owner Password模式，audience应该是你的API的标识符，而不是Auth0管理API
AUTH0_API_AUDIENCE = os.environ.get('AUTH0_API_AUDIENCE', "")

# 会话配置
SESSION_COOKIE_SECURE = False  # 本地开发环境关闭
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = None  # 允许跨站请求使用会话
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 会话过期时间

# 模拟模式 - 当Auth0连接失败时使用模拟数据（开发/测试环境使用）
MOCK_AUTH0 = True

# 测试模式 - 启用直接登录，不依赖Auth0（仅用于开发测试）
AUTH0_TEST_MODE = True  # 启用测试模式，允许在Auth0验证失败时直接登录

# JWT配置
JWT_SECRET_KEY = SECRET_KEY  # 使用应用密钥
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # 访问令牌过期时间
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 刷新令牌过期时间
JWT_TOKEN_LOCATION = ['headers']  # 令牌位置 