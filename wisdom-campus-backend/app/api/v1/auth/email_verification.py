"""
邮箱验证相关接口模块
包含发送验证邮件和验证邮箱功能
"""
from flask import request, current_app, url_for
import requests
import logging
import json
from datetime import datetime, timedelta
from app.models.user import User, db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
from functools import wraps

logger = logging.getLogger(__name__)

# 简单的令牌缓存，避免频繁请求Auth0 API
_token_cache = {
    'token': None,
    'expires_at': None
}

# 邮件发送记录缓存 (使用内存缓存代替数据库字段)
# 格式: {email: timestamp}
_verification_sent_cache = {}

def get_cached_auth0_token():
    """
    获取Auth0管理API令牌，带缓存功能
    
    返回:
        str: Auth0管理API令牌
    """
    now = datetime.now()
    
    # 检查缓存中是否有有效令牌
    if _token_cache['token'] and _token_cache['expires_at'] and _token_cache['expires_at'] > now:
        return _token_cache['token']
    
    # 获取Auth0配置
    domain = current_app.config.get('AUTH0_DOMAIN')
    client_id = current_app.config.get('AUTH0_CLIENT_ID')
    client_secret = current_app.config.get('AUTH0_CLIENT_SECRET')
    
    # 获取Auth0管理API令牌
    token_url = f"https://{domain}/oauth/token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": f"https://{domain}/api/v2/",
        "grant_type": "client_credentials"
    }
    token_headers = {"content-type": "application/json"}
    
    try:
        token_response = requests.post(token_url, json=token_payload, headers=token_headers, timeout=10)
        
        if token_response.status_code != 200:
            logger.error(f"获取Auth0管理令牌失败: {token_response.text}")
            return None
            
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 86400)  # 默认24小时
        
        # 缓存令牌
        _token_cache['token'] = access_token
        _token_cache['expires_at'] = now + timedelta(seconds=expires_in - 300)  # 提前5分钟过期
        
        return access_token
    except Exception as e:
        logger.error(f"获取Auth0令牌时发生错误: {str(e)}")
        return None

def auth0_api_error_handler(f):
    """
    Auth0 API错误处理装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth0 API请求异常: {str(e)}")
            return api_error(ErrorCode.SYSTEM_ERROR, "连接认证服务失败，请稍后重试")
        except Exception as e:
            logger.error(f"Auth0 API处理异常: {str(e)}")
            return api_error(ErrorCode.SYSTEM_ERROR, "处理请求时发生错误")
    return decorated_function

def send_verification_email(email):
    """
    发送验证邮件
    
    参数:
        email: 用户邮箱
        
    返回:
        成功: 返回True
        失败: 抛出异常
    """
    # 获取管理API令牌
    management_api_token = get_cached_auth0_token()
    if not management_api_token:
        raise Exception("无法获取Auth0令牌")
    
    # 查找用户
    user = User.query.filter_by(email=email).first()
    
    if not user:
        logger.error(f"用户不存在: {email}")
        raise Exception("用户不存在")
    
    # 获取Auth0配置
    domain = current_app.config.get('AUTH0_DOMAIN')
    client_id = current_app.config.get('AUTH0_CLIENT_ID')
        
    # 发送验证邮件
    job_url = f"https://{domain}/api/v2/jobs/verification-email"
    job_headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {management_api_token}"
    }
    job_payload = {
        "user_id": user.auth0_id,
        "client_id": client_id
    }
    
    job_response = requests.post(job_url, json=job_payload, headers=job_headers, timeout=10)
    
    if job_response.status_code != 201:
        logger.error(f"发送验证邮件失败: {job_response.text}")
        raise Exception("发送验证邮件失败")
        
    # 记录发送时间（内存缓存）
    _verification_sent_cache[email] = datetime.now()
        
    return True

@auth0_api_error_handler
def api_resend_verification():
    """
    重新发送验证邮件API端点
    
    请求参数:
        email: 用户邮箱
        或者
        auth0_id: Auth0用户ID
        
    返回:
        成功: 返回成功消息
        失败: 返回错误信息
    """
    # 获取请求数据
    data = request.get_json()
    
    if not data:
        return api_error(ErrorCode.INVALID_INPUT, "缺少请求参数")
        
    email = data.get('email')
    auth0_id = data.get('auth0_id')
    
    # 检查是否至少提供了一个查询参数
    if not email and not auth0_id:
        return api_error(ErrorCode.INVALID_INPUT, "邮箱或Auth0 ID至少需要提供一个")
        
    # 根据提供的参数查询用户
    user = None
    if auth0_id:
        user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user and email:
        user = User.query.filter_by(email=email).first()
    
    if not user:
        logger.warning(f"重发验证邮件失败: 用户不存在 email={email}, auth0_id={auth0_id}")
        return api_error(ErrorCode.NOT_FOUND, "用户不存在")
        
    # 获取用户邮箱（如果只提供了auth0_id）
    email = user.email
    
    # 检查邮箱是否已验证
    if user.email_verified:
        logger.info(f"邮箱已验证，无需重发: {email}")
        return api_success({"message": "邮箱已验证，无需重发验证邮件"})
    
    # 检查是否频繁发送（使用内存缓存）
    now = datetime.now()
    if email in _verification_sent_cache:
        time_diff = now - _verification_sent_cache[email]
        if time_diff.total_seconds() < 60:  # 限制60秒内只能发送一次
            seconds_to_wait = 60 - int(time_diff.total_seconds())
            return api_error(
                ErrorCode.RATE_LIMIT_EXCEEDED, 
                f"发送过于频繁，请{seconds_to_wait}秒后再试",
                http_status=429
            )
        
    # 发送验证邮件
    try:
        send_verification_email(email)
        logger.info(f"重新发送验证邮件成功: {email}")
        return api_success({"message": "验证邮件已发送，请查收"})
    except Exception as e:
        logger.error(f"重发验证邮件失败: {str(e)}")
        return api_error(ErrorCode.SERVER_ERROR, "发送验证邮件失败，请稍后重试")

@auth0_api_error_handler
def check_email_verification(auth0_id=None, email=None):
    """
    检查用户邮箱验证状态
    
    参数:
        auth0_id: Auth0用户ID
        或者
        email: 用户邮箱
        
    返回:
        成功: 返回用户验证状态
        失败: 返回错误信息
    """
    # 如果是API请求，从请求中获取参数
    if request.is_json:
        data = request.get_json()
        auth0_id = auth0_id or data.get('auth0_id')
        email = email or data.get('email')
    
    # 检查是否至少提供了一个查询参数
    if not auth0_id and not email:
        return api_error(ErrorCode.INVALID_INPUT, "Auth0 ID或邮箱至少需要提供一个")
    
    # 查找用户
    user = None
    if auth0_id:
        user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user and email:
        user = User.query.filter_by(email=email).first()
    
    if not user:
        logger.error(f"检查验证状态失败: 用户不存在 auth0_id={auth0_id}, email={email}")
        return api_error(ErrorCode.NOT_FOUND, "用户不存在")
        
    # 如果已验证，直接返回
    if user.email_verified:
        return api_success({
            "email_verified": True,
            "is_verified": True
        })
    
    # 获取管理API令牌
    management_api_token = get_cached_auth0_token()
    if not management_api_token:
        return api_error(ErrorCode.SERVER_ERROR, "验证服务暂时不可用")
    
    # 获取Auth0配置
    domain = current_app.config.get('AUTH0_DOMAIN')
    
    # 查询用户在Auth0中的状态
    user_url = f"https://{domain}/api/v2/users/{user.auth0_id}"
    user_headers = {
        "Authorization": f"Bearer {management_api_token}"
    }
    
    user_response = requests.get(user_url, headers=user_headers, timeout=10)
    
    if user_response.status_code != 200:
        logger.error(f"获取Auth0用户信息失败: {user_response.text}")
        return api_error(ErrorCode.SERVER_ERROR, "获取用户信息失败")
        
    auth0_user = user_response.json()
    email_verified = auth0_user.get('email_verified', False)
    
    # 更新数据库中的验证状态
    if email_verified != user.email_verified:
        user.email_verified = email_verified
        
        try:
            db.session.commit()
            logger.info(f"更新用户验证状态成功: {user.email}, verified: {email_verified}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新用户验证状态失败: {str(e)}")
            return api_error(ErrorCode.DB_ERROR, "更新验证状态失败")
    
    # 统一返回字段名，同时返回email_verified和is_verified
    logger.info(f"检查用户验证状态: email={user.email}, verified={email_verified}")
    return api_success({
        "email_verified": email_verified,
        "is_verified": email_verified
    }) 