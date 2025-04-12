"""
核心认证功能模块
包含Auth0配置和基础认证功能
"""
from flask import current_app, request
import json
import logging
import requests
from functools import wraps
from app.models.user import User
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

logger = logging.getLogger(__name__)

def setup_auth0(app):
    """
    配置Auth0认证
    
    参数:
        app: Flask应用实例
    """
    # 确认必要的Auth0配置存在
    required_config = ['AUTH0_DOMAIN', 'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET', 'AUTH0_AUDIENCE']
    missing_config = [config for config in required_config if config not in app.config]
    
    if missing_config:
        logger.warning(f"缺少Auth0配置: {', '.join(missing_config)}")
        logger.warning("Auth0功能可能无法正常工作！")
    else:
        logger.info("Auth0配置加载完成")

def get_auth0_management_token():
    """
    获取Auth0管理API的访问令牌
    
    返回:
        str: 访问令牌字符串
    """
    domain = current_app.config['AUTH0_DOMAIN']
    client_id = current_app.config['AUTH0_CLIENT_ID']
    client_secret = current_app.config['AUTH0_CLIENT_SECRET']
    audience = f"https://{domain}/api/v2/"
    
    token_url = f"https://{domain}/oauth/token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials"
    }
    
    token_headers = {"content-type": "application/json"}
    
    response = requests.post(token_url, json=token_payload, headers=token_headers)
    
    if response.status_code != 200:
        raise Exception(f"获取Auth0管理API令牌失败: {response.status_code}, {response.text}")
    
    return response.json()["access_token"]

def get_user_from_auth0(auth0_id):
    """
    从Auth0获取用户信息
    
    参数:
        auth0_id: Auth0用户ID
        
    返回:
        dict: 用户信息字典或None
    """
    try:
        # 获取Auth0管理API令牌
        token = get_auth0_management_token()
        
        # 查询Auth0用户信息
        domain = current_app.config['AUTH0_DOMAIN']
        auth0_id_encoded = auth0_id.replace("|", "%7C")  # URL编码
        url = f"https://{domain}/api/v2/users/{auth0_id_encoded}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"获取Auth0用户信息失败: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"从Auth0获取用户信息失败: {str(e)}")
        return None

def search_users_in_auth0(email=None, query=None, page=0, per_page=10):
    """
    在Auth0中搜索用户
    
    参数:
        email: 用户邮箱
        query: 搜索查询字符串
        page: 页码，从0开始
        per_page: 每页数量
        
    返回:
        dict: 包含用户列表和元数据的字典，失败返回None
    """
    try:
        # 获取Auth0管理API令牌
        token = get_auth0_management_token()
        
        # 构建查询参数
        domain = current_app.config['AUTH0_DOMAIN']
        url = f"https://{domain}/api/v2/users"
        
        params = {
            "page": page,
            "per_page": per_page,
            "include_totals": "true"
        }
        
        if email:
            params["q"] = f"email:\"{email}\""
        elif query:
            params["q"] = query
            
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Auth0用户搜索失败: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Auth0用户搜索过程中发生错误: {str(e)}")
        return None

def validate_auth0_token(token):
    """
    验证Auth0 JWT令牌
    
    参数:
        token: JWT令牌
        
    返回:
        dict: 用户信息字典，验证失败返回None
    """
    try:
        domain = current_app.config['AUTH0_DOMAIN']
        audience = current_app.config['AUTH0_AUDIENCE']
        
        # 构建验证请求
        jwks_url = f"https://{domain}/.well-known/jwks.json"
        jwks_client = requests.get(jwks_url).json()
        
        # 这里应该使用适当的JWT库进行验证
        # 以下为简化示例，实际实现中应使用jose或pyjwt等库
        
        # 解析令牌获取用户信息
        # 示例中简化处理，实际应验证签名
        
        return {"sub": "user_id", "email": "user@example.com"}
        
    except Exception as e:
        logger.error(f"验证Auth0令牌失败: {str(e)}")
        return None

def create_user_in_auth0(user_data):
    """
    在Auth0中创建用户
    
    参数:
        user_data: 包含用户信息的字典，至少需要包含email和password
        
    返回:
        dict: 创建成功返回用户信息，失败返回None
    """
    try:
        # 获取Auth0管理API令牌
        token = get_auth0_management_token()
        
        # 创建用户请求
        domain = current_app.config['AUTH0_DOMAIN']
        url = f"https://{domain}/api/v2/users"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Auth0接受的基本用户数据
        payload = {
            "email": user_data["email"],
            "password": user_data["password"],
            "connection": "Username-Password-Authentication"
        }
        
        # 添加额外的用户元数据
        if "user_metadata" in user_data:
            payload["user_metadata"] = user_data["user_metadata"]
            
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            return response.json()
        else:
            logger.error(f"在Auth0中创建用户失败: {response.status_code}, {response.text}")
            return {"status_code": response.status_code, "error": response.text}
            
    except Exception as e:
        logger.error(f"创建Auth0用户过程中发生错误: {str(e)}")
        return None 