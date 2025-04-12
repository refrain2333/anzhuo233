"""
Auth0认证相关工具函数
"""
import json
import requests
from functools import wraps
from urllib.parse import urlencode
from flask import session, redirect, request, url_for, current_app, flash
from jose import jwt

def get_auth0_token():
    """
    获取Auth0 Management API的访问令牌
    """
    domain = current_app.config["AUTH0_DOMAIN"]
    client_id = current_app.config["AUTH0_CLIENT_ID"]
    client_secret = current_app.config["AUTH0_CLIENT_SECRET"]
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": f"https://{domain}/api/v2/",
        "grant_type": "client_credentials"
    }
    
    response = requests.post(
        f"https://{domain}/oauth/token", 
        json=payload
    )
    
    if response.status_code != 200:
        raise Exception(f"无法获取管理API令牌: {response.text}")
    
    return response.json()['access_token']

def requires_auth(f):
    """
    验证用户是否已登录的装饰器
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def requires_verified_email(f):
    """
    验证用户邮箱是否已验证的装饰器
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        
        if not session['user'].get('userinfo', {}).get('email_verified', False):
            flash('请先验证您的邮箱', 'warning')
            return redirect(url_for('auth.profile'))
        
        return f(*args, **kwargs)
    return decorated

def requires_admin(f):
    """
    验证用户是否为管理员的装饰器
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        
        # 检查用户是否为管理员
        user_info = session['user'].get('userinfo', {})
        # 如果is_admin字段不存在或为False，则不是管理员
        if not user_info.get('is_admin', False):
            flash('您没有管理员权限', 'danger')
            return redirect(url_for('auth.profile'))
        
        return f(*args, **kwargs)
    return decorated

def get_user_info(user_id):
    """
    通过用户ID获取用户详细信息
    """
    token = get_auth0_token()
    domain = current_app.config["AUTH0_DOMAIN"]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"https://{domain}/api/v2/users/{user_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"获取用户信息失败: {response.text}")
    
    return response.json()

def update_user_metadata(user_id, metadata):
    """
    更新用户元数据
    """
    token = get_auth0_token()
    domain = current_app.config["AUTH0_DOMAIN"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "user_metadata": metadata
    }
    
    response = requests.patch(
        f"https://{domain}/api/v2/users/{user_id}",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"更新用户元数据失败: {response.text}")
    
    return response.json()

def resend_verification_email(user_id):
    """
    重新发送验证邮件
    """
    token = get_auth0_token()
    domain = current_app.config["AUTH0_DOMAIN"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "user_id": user_id
    }
    
    response = requests.post(
        f"https://{domain}/api/v2/jobs/verification-email",
        headers=headers,
        json=data
    )
    
    if response.status_code != 201:
        raise Exception(f"发送验证邮件失败: {response.text}")
    
    return response.json()

def generate_auth0_logout_url():
    """
    生成Auth0登出URL
    """
    domain = current_app.config["AUTH0_DOMAIN"]
    client_id = current_app.config["AUTH0_CLIENT_ID"]
    return_to = url_for('auth.index', _external=True)
    
    params = {
        'returnTo': return_to,
        'client_id': client_id
    }
    
    return f"https://{domain}/v2/logout?{urlencode(params)}"

def validate_id_token(token):
    """
    验证ID Token
    """
    domain = current_app.config["AUTH0_DOMAIN"]
    client_id = current_app.config["AUTH0_CLIENT_ID"]
    jwks_url = f"https://{domain}/.well-known/jwks.json"
    
    # 获取jwks
    jwks_response = requests.get(jwks_url)
    jwks = jwks_response.json()
    
    # 解析token
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=f"https://{domain}/"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token已过期")
        except jwt.JWTClaimsError:
            raise Exception("无效的Token声明")
        except Exception as e:
            raise Exception(f"无法解析Token: {str(e)}")
    
    raise Exception("无法找到合适的密钥验证Token") 