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

# Auth0配置
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN', 'your-tenant.auth0.com')
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID', 'your-client-id')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET', 'your-client-secret')
AUTH0_CALLBACK_URL = os.environ.get('AUTH0_CALLBACK_URL', 'http://localhost:5000/api/v1/auth/callback') 

# 会话配置
SESSION_COOKIE_SECURE = False  # 本地开发环境关闭
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = None  # 允许跨站请求使用会话
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 会话过期时间 