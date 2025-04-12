"""
认证模块工具函数
"""
import json
import requests
from flask import current_app
from app import db
from app.models.user import User
from app.utils.response import api_error
from app.utils.error_codes import ErrorCode
from datetime import datetime

def get_auth0_token():
    """
    获取Auth0管理API的access token
    
    返回:
        str: Auth0访问令牌，如果获取失败则返回None
    """
    domain = current_app.config.get("AUTH0_DOMAIN")
    client_id = current_app.config.get("AUTH0_CLIENT_ID")
    client_secret = current_app.config.get("AUTH0_CLIENT_SECRET")
    audience = f"https://{domain}/api/v2/"
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials"
    }
    
    response = requests.post(
        f"https://{domain}/oauth/token",
        json=payload,
        headers={"content-type": "application/json"}
    )
    
    if response.status_code != 200:
        current_app.logger.error(f"获取Auth0令牌失败: HTTP {response.status_code}, 响应: {response.text}")
        return None
    
    return response.json().get("access_token")

def delete_auth0_user(auth0_id):
    """
    删除Auth0中的用户
    
    参数:
        auth0_id (str): Auth0用户ID
        
    返回:
        tuple: (成功标志, 错误消息)
    """
    token = get_auth0_token()
    if not token:
        return False, "获取Auth0管理Token失败"
    
    domain = current_app.config["AUTH0_DOMAIN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(
            f"https://{domain}/api/v2/users/{auth0_id}",
            headers=headers
        )
        
        if response.status_code == 204:
            # 成功删除
            return True, None
        else:
            response_data = response.text
            try:
                response_data = response.json()
            except:
                pass
            
            current_app.logger.error(f"删除Auth0用户失败: HTTP {response.status_code}, 响应: {response_data}")
            return False, f"删除Auth0用户失败: HTTP {response.status_code}"
            
    except Exception as e:
        current_app.logger.error(f"删除Auth0用户异常: {str(e)}")
        return False, f"删除Auth0用户时发生异常: {str(e)}"

def search_auth0_user_by_email(email):
    """
    通过邮箱在Auth0中搜索用户
    
    参数:
        email (str): 用户邮箱
        
    返回:
        dict: 用户信息，如果未找到则返回None
    """
    token = get_auth0_token()
    if not token:
        return None
    
    domain = current_app.config["AUTH0_DOMAIN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 注意: 需要URL编码query参数
    # 这里我们直接使用简单的替换，在实际应用中应使用urllib.parse.quote
    query = f"email:\"{email}\""
    
    try:
        response = requests.get(
            f"https://{domain}/api/v2/users?q={query}&search_engine=v3",
            headers=headers
        )
        
        if response.status_code != 200:
            current_app.logger.error(f"通过邮箱搜索Auth0用户失败: HTTP {response.status_code}, 响应: {response.text}")
            return None
        
        users = response.json()
        
        # 如果找到了用户
        if users and len(users) > 0:
            return users[0]
        
        return None
            
    except Exception as e:
        current_app.logger.error(f"查询Auth0用户异常: {str(e)}")
        return None

def update_user_from_auth0(user, user_info):
    """
    根据Auth0返回的用户信息更新数据库中的用户信息
    
    参数:
        user (User): 要更新的用户对象
        user_info (dict): Auth0用户信息
        
    返回:
        bool: 更新是否成功
    """
    try:
        user.email_verified = user_info.get('email_verified', False)
        user.avatar_url = user_info.get('picture')
        user.auth0_sid = user_info.get('sid')
        user.auth0_aud = user_info.get('aud')
        user.auth0_iss = user_info.get('iss')
        user.auth0_updated_at = datetime.utcnow()
        
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"更新用户信息失败: {str(e)}")
        db.session.rollback()
        return False
