"""
用户登录相关功能模块
"""
from flask import request, current_app, jsonify, session
import json
import requests
from datetime import datetime, timedelta
import logging
from app.models.user import User
from app import db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

logger = logging.getLogger(__name__)

def api_login():
    """
    用户登录API
    
    请求参数:
        email: 邮箱
        password: 密码
        
    返回:
        API响应，表示操作结果
            - 200: 登录成功，返回用户信息
            - 400: 请求错误（参数错误）
            - 401: 认证失败（用户名或密码错误）
            - 500: 服务器错误
    """
    # 获取请求数据
    if not request.is_json:
        return api_error(
            message="请求必须是JSON格式",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    data = request.get_json()
    
    # 验证必要参数
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return api_error(
                message=f"缺少必要参数: {field}",
                error_code=ErrorCode.INVALID_REQUEST
            )
    
    email = data.get('email')
    password = data.get('password')
    
    # 查找用户
    user = User.query.filter_by(email=email).first()
    if not user:
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    # 获取Auth0凭证
    domain = current_app.config['AUTH0_DOMAIN']
    client_id = current_app.config['AUTH0_CLIENT_ID']
    client_secret = current_app.config['AUTH0_CLIENT_SECRET']
    audience = current_app.config['AUTH0_API_AUDIENCE']
    
    # 进行Auth0认证
    auth0_url = f"https://{domain}/oauth/token"
    headers = {'content-type': 'application/json'}
    auth0_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "username": email,
        "password": password,
        "grant_type": "password",
        "scope": "openid profile email",
        "audience": audience
    }
    
    try:
        # 调用Auth0 API
        auth_response = requests.post(auth0_url, json=auth0_payload, headers=headers)
        
        # 检查认证结果
        if auth_response.status_code != 200:
            logger.error(f"Auth0登录失败: {auth_response.status_code}, {auth_response.text}")
            return api_error(
                message="邮箱或密码错误",
                error_code=ErrorCode.AUTHENTICATION_FAILED
            )
        
        # 解析Auth0响应
        auth_data = auth_response.json()
        access_token = auth_data.get('access_token')
        id_token = auth_data.get('id_token')
        expires_in = auth_data.get('expires_in', 86400)  # 默认24小时
        
        # 获取用户信息
        user_info_url = f"https://{domain}/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        
        if user_info_response.status_code != 200:
            logger.error(f"获取用户信息失败: {user_info_response.status_code}, {user_info_response.text}")
            return api_error(
                message="无法获取用户信息",
                error_code=ErrorCode.AUTH0_API_ERROR
            )
        
        user_info = user_info_response.json()
        sub = user_info.get('sub')  # Auth0用户ID
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        db.session.commit()
        
        # 存储会话信息
        session['user_id'] = user.id
        session['auth0_id'] = sub
        session['email'] = email
        session['expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).timestamp()
        
        # 返回成功响应
        return api_success(
            message="登录成功",
            data={
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "student_id": user.student_id,
                "major_id": user.major_id,
                "grade": user.grade,
                "access_token": access_token,
                "id_token": id_token,
                "expires_in": expires_in
            }
        )
        
    except Exception as e:
        logger.error(f"登录过程中发生错误: {str(e)}")
        return api_error(
            message="登录过程中发生服务器错误",
            error_code=ErrorCode.SERVER_ERROR
        )

def api_logout():
    """
    用户登出API
    
    返回:
        API响应，表示操作结果
    """
    # 清除会话
    session.clear()
    
    return api_success(
        message="已成功登出",
    )

def check_session():
    """
    检查会话状态API
    
    返回:
        API响应，表示操作结果
            - 200: 会话有效，返回用户信息
            - 401: 会话无效或已过期
    """
    # 检查会话是否存在
    if 'user_id' not in session:
        return api_error(
            message="未登录",
            error_code=ErrorCode.SESSION_INVALID
        )
    
    # 检查会话是否过期
    expires_at = session.get('expires_at', 0)
    if datetime.now().timestamp() > expires_at:
        session.clear()
        return api_error(
            message="会话已过期，请重新登录",
            error_code=ErrorCode.SESSION_EXPIRED
        )
    
    # 获取用户信息
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    # 返回成功响应
    return api_success(
        message="会话有效",
        data={
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "student_id": user.student_id,
            "major_id": user.major_id,
            "grade": user.grade
        }
    )
