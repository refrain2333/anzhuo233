"""
Auth0认证相关工具函数
"""
import json
import requests
from functools import wraps
from urllib.parse import urlencode
from flask import session, redirect, request, url_for, current_app, flash, jsonify
from jose import jwt
import os
from datetime import datetime

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
    支持两种认证方式：
    1. 会话认证（网页模式）
    2. Bearer令牌认证（API模式）
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 先检查API认证模式
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
            try:
                # 验证JWT令牌
                payload = validate_token(token)
                # 将用户信息保存到request对象中，供后续使用
                request.jwt_payload = payload
                return f(*args, **kwargs)
            except Exception as e:
                # 令牌验证失败，检查是否请求期望返回JSON
                if request.is_json or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": False,
                        "message": f"认证失败: {str(e)}",
                        "error": "invalid_token"
                    }), 401
                # 如果不是API请求，回退到会话认证
        
        # 会话认证模式
        if 'user' not in session:
            # 检查是否请求期望返回JSON
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": "未认证",
                    "error": "not_authenticated"
                }), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def requires_verified_email(f):
    """
    验证用户邮箱是否已验证的装饰器
    支持两种认证方式
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 先检查API认证模式
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
            try:
                # 验证JWT令牌
                payload = validate_token(token)
                # 检查邮箱验证状态
                if not payload.get('email_verified', False):
                    if request.is_json or request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "success": False,
                            "message": "请先验证您的邮箱",
                            "error": "email_not_verified"
                        }), 403
                # 将用户信息保存到request对象中，供后续使用
                request.jwt_payload = payload
                return f(*args, **kwargs)
            except Exception as e:
                # 令牌验证失败
                if request.is_json or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": False,
                        "message": f"认证失败: {str(e)}",
                        "error": "invalid_token"
                    }), 401
                # 如果不是API请求，回退到会话认证
        
        # 会话认证模式
        if 'user' not in session:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": "未认证",
                    "error": "not_authenticated"
                }), 401
            return redirect(url_for('auth.login'))
        
        if not session['user'].get('userinfo', {}).get('email_verified', False):
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": "请先验证您的邮箱",
                    "error": "email_not_verified"
                }), 403
            flash('请先验证您的邮箱', 'warning')
            return redirect(url_for('auth.profile'))
        
        return f(*args, **kwargs)
    return decorated

def requires_admin(f):
    """
    验证用户是否为管理员的装饰器
    支持两种认证方式
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 先检查API认证模式
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
            try:
                # 验证JWT令牌
                payload = validate_token(token)
                # 检查用户是否为管理员
                from app.models.user import User
                auth0_id = payload.get('sub')
                user = User.query.filter_by(auth0_id=auth0_id).first()
                
                if not user or not user.is_admin:
                    if request.is_json or request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "success": False,
                            "message": "您没有管理员权限",
                            "error": "not_admin"
                        }), 403
                
                # 将用户信息保存到request对象中，供后续使用
                request.jwt_payload = payload
                return f(*args, **kwargs)
            except Exception as e:
                # 令牌验证失败
                if request.is_json or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": False,
                        "message": f"认证失败: {str(e)}",
                        "error": "invalid_token"
                    }), 401
                # 如果不是API请求，回退到会话认证
        
        # 会话认证模式
        if 'user' not in session:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": "未认证",
                    "error": "not_authenticated"
                }), 401
            return redirect(url_for('auth.login'))
        
        # 检查用户是否为管理员
        user_info = session['user'].get('userinfo', {})
        # 如果is_admin字段不存在或为False，则不是管理员
        from app.models.user import User
        auth0_id = user_info.get('sub')
        user = User.query.filter_by(auth0_id=auth0_id).first()
        
        if not user or not user.is_admin:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": "您没有管理员权限",
                    "error": "not_admin"
                }), 403
            flash('您没有管理员权限', 'danger')
            return redirect(url_for('auth.profile'))
        
        return f(*args, **kwargs)
    return decorated

def validate_token(token):
    """
    验证JWT令牌
    """
    domain = current_app.config["AUTH0_DOMAIN"]
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
                audience=current_app.config["AUTH0_CLIENT_ID"],
                issuer=f"https://{domain}/"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("令牌已过期")
        except jwt.JWTClaimsError:
            raise Exception("令牌包含无效的声明")
        except Exception:
            raise Exception("无法解析令牌")
    
    raise Exception("无法找到合适的密钥")

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