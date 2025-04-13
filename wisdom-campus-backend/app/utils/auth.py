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
import logging

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
    1. 自定义JWT令牌（API模式，优先）
    2. 会话认证（网页模式，备选）
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # 先检查API认证模式（JWT令牌）
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
                
                # 验证JWT令牌
                verify_jwt_in_request()
                
                # 获取用户ID
                user_id = get_jwt_identity()
                logger.info(f"JWT认证成功，用户ID: {user_id}")
                
                # 获取额外声明
                try:
                    jwt_data = get_jwt()
                    logger.info(f"JWT额外信息: {jwt_data.get('name', 'unknown')}, {jwt_data.get('email', 'unknown')}")
                except Exception as jwt_error:
                    logger.warning(f"获取JWT额外信息失败: {str(jwt_error)}")
                
                # 认证成功，继续执行被装饰的函数
                # 可选：从数据库获取用户信息并放入请求上下文
                try:
                    from app.models.user import User
                    # 确保用户ID是整数
                    if isinstance(user_id, str) and user_id.isdigit():
                        user_id = int(user_id)
                    user = User.query.get(user_id)
                    if user:
                        request.user = user
                except Exception as db_error:
                    logger.warning(f"从数据库获取用户信息失败: {str(db_error)}")
                
                return f(*args, **kwargs)
            except Exception as jwt_error:
                # JWT令牌验证失败
                logger.warning(f"JWT认证失败: {str(jwt_error)}")
                
                # 对API请求返回JSON错误响应
                if request.is_json or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": False,
                        "message": "认证失败，请重新登录",
                        "error": "invalid_token"
                    }), 401
        
        # 会话认证模式（后备方案）
        user_id = session.get('user_id')
        if user_id:
            logger.info(f"会话认证成功，用户ID: {user_id}")
            return f(*args, **kwargs)
        
        # 认证失败，检查是否API请求
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": False,
                "message": "未认证，请先登录",
                "error": "not_authenticated"
            }), 401
        
        # 网页请求重定向到登录页面
        logger.info(f"认证失败，重定向到登录页面")
        return redirect(url_for('login'))
    
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
            return redirect(url_for('login'))
        
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
    支持两种认证方式：
    1. 自定义JWT令牌（API模式，优先）
    2. 会话认证（网页模式，备选）
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # 先检查API认证模式
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                # 使用flask_jwt_extended直接验证
                from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
                
                # 验证JWT令牌
                verify_jwt_in_request()
                
                # 获取用户ID和额外数据
                user_id = get_jwt_identity()
                jwt_data = get_jwt()
                
                logger.info(f"JWT验证成功，用户ID: {user_id}")
                logger.info(f"JWT额外数据: {jwt_data.get('is_admin')}, {jwt_data.get('email')}")
                
                # 先检查JWT本身是否有管理员标记
                if not jwt_data.get('is_admin', False):
                    logger.warning(f"JWT不包含管理员标记")
                    if request.is_json or request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "success": False,
                            "message": "您没有管理员权限",
                            "error": "not_admin"
                        }), 403
                    flash('您没有管理员权限', 'danger')
                    return redirect(url_for('login'))
                
                # 查找用户 - 使用用户ID而不是auth0_id
                from app.models.user import User
                # 确保用户ID是整数
                if isinstance(user_id, str) and user_id.isdigit():
                    user_id = int(user_id)
                
                user = User.query.get(user_id)
                
                if not user:
                    logger.warning(f"找不到用户ID: {user_id}")
                    if request.is_json or request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "success": False,
                            "message": "用户不存在",
                            "error": "user_not_found"
                        }), 404
                    return redirect(url_for('login'))
                
                if not user.is_admin:
                    logger.warning(f"用户 {user.name} 不是管理员")
                    if request.is_json or request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "success": False,
                            "message": "您没有管理员权限",
                            "error": "not_admin"
                        }), 403
                    flash('您没有管理员权限', 'danger')
                    return redirect(url_for('login'))
                
                # 验证通过，将用户信息放入请求上下文中
                request.user = user
                return f(*args, **kwargs)
            except Exception as e:
                # 令牌验证失败
                logger.error(f"JWT验证失败: {str(e)}")
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
            return redirect(url_for('login'))
        
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