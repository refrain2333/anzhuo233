"""
用户注册模块
包含用户注册相关功能
"""
from flask import request, current_app, jsonify, Response
import json
import requests
import re
from datetime import datetime
import logging
from app.models.user import User, Major, db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
from app.api.v1.auth.utils import get_auth0_token, search_auth0_user_by_email, delete_auth0_user

logger = logging.getLogger(__name__)

def api_register():
    """
    用户注册API
    
    请求参数:
        student_id: 学号
        name: 姓名
        email: 邮箱
        password: 密码
        major_id: 专业ID
        grade: 年级
        
    返回:
        API响应，表示操作结果
            - 200: 注册成功
            - 400: 请求错误（参数错误）
            - 409: 冲突（用户已存在）
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
    required_fields = ['student_id', 'email', 'password', 'name']
    for field in required_fields:
        if field not in data or not data[field]:
            return api_error(
                message=f"缺少必要参数: {field}",
                error_code=ErrorCode.INVALID_REQUEST
            )
    
    student_id = data.get('student_id')
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    major_id = data.get('major_id')
    grade = data.get('grade')
    
    # 检查学号是否已存在
    existing_student = User.query.filter_by(student_id=student_id).first()
    if existing_student:
        return api_error(
            message="此学号已经注册",
            error_code=ErrorCode.USER_ALREADY_EXISTS
        )
    
    # 检查邮箱是否已存在
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return api_error(
            message="此邮箱已经注册",
            error_code=ErrorCode.USER_ALREADY_EXISTS
        )
    
    # 校验专业ID（如果提供）
    if major_id:
        major = Major.query.get(major_id)
        if not major:
            return api_error(
                message="指定的专业不存在",
                error_code=ErrorCode.INVALID_REQUEST
            )
    
    # 创建Auth0用户
    token = get_auth0_token()
    if not token:
        return api_error(
            message="无法获取认证令牌",
            error_code=ErrorCode.AUTH0_API_ERROR
        )
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    user_metadata = {
        "student_id": student_id,
        "name": name,
        "major_id": major_id,
        "grade": grade
    }
    
    # 构建Auth0请求数据
    auth0_data = {
        "email": email,
        "password": password,
        "connection": "Username-Password-Authentication",
        "email_verified": False,
        "user_metadata": user_metadata
    }
    
    try:
        audience = current_app.config['AUTH0_API_AUDIENCE']
        domain = current_app.config['AUTH0_DOMAIN']
        url = f"https://{domain}/api/v2/users"
        response = requests.post(url, headers=headers, json=auth0_data)
        
        if response.status_code != 201:
            # 如果用户创建失败，检查是否是因为邮箱已存在
            if response.status_code == 409:
                # 邮箱已存在于Auth0，但不在我们的数据库中
                logger.warning(f"用户邮箱 {email} 已存在于Auth0，但不在本地数据库中")
                
                # 查询Auth0用户信息
                user_info = search_auth0_user_by_email(email, token)
                if not user_info:
                    return api_error(
                        message="邮箱已存在，但无法获取用户信息",
                        error_code=ErrorCode.USER_ALREADY_EXISTS
                    )
                
                # 确认学号是否存在于数据库
                metadata = user_info.get('user_metadata', {})
                existing_metadata_sid = metadata.get('student_id')
                
                if existing_metadata_sid and existing_metadata_sid == student_id:
                    return api_error(
                        message="此学号与邮箱组合已注册",
                        error_code=ErrorCode.USER_ALREADY_EXISTS
                    )
                
                # 更新现有Auth0用户或创建新本地用户
                auth0_id = user_info.get('user_id')
                
                # 如果Auth0用户存在但本地数据库没有，创建本地用户
                new_user = User(
                    student_id=student_id,
                    name=name,
                    email=email,
                    major_id=major_id,
                    grade=grade,
                    auth0_id=auth0_id,
                    created_at=datetime.now(),
                    last_update=datetime.now()
                )
                
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    
                    return api_success(
                        message="用户注册成功（使用现有Auth0账户）",
                        data={
                            "user_id": new_user.id,
                            "auth0_id": auth0_id,
                            "email": email
                        }
                    )
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"数据库错误: {str(e)}")
                    return api_error(
                        message="创建用户时发生数据库错误",
                        error_code=ErrorCode.DB_ERROR
                    )
            else:
                # 其他错误
                logger.error(f"Auth0 API错误: {response.status_code}, {response.text}")
                return api_error(
                    message=f"创建用户失败: {response.text}",
                    error_code=ErrorCode.AUTH0_API_ERROR
                )
        
        # 获取Auth0用户ID
        auth0_user = response.json()
        auth0_id = auth0_user.get('user_id')
        
        # 创建本地用户
        new_user = User(
            student_id=student_id,
            name=name,
            email=email,
            major_id=major_id,
            grade=grade,
            auth0_id=auth0_id,
            created_at=datetime.now(),
            last_update=datetime.now()
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # 注册成功后，不在这里自动发送验证邮件
            # 而是等用户跳转到验证等待页面后再发送
            # 这样可以避免重复发送验证邮件
            
            return api_success(
                message="用户注册成功",
                data={
                    "user_id": new_user.id,
                    "auth0_id": auth0_id,
                    "email": email
                }
            )
        except Exception as e:
            # 回滚数据库
            db.session.rollback()
            
            # 删除Auth0用户，因为本地数据库存储失败
            delete_auth0_user(auth0_id)
            
            logger.error(f"数据库错误: {str(e)}")
            return api_error(
                message="创建用户时发生数据库错误",
                error_code=ErrorCode.DB_ERROR
            )
            
    except Exception as e:
        logger.error(f"创建用户时发生错误: {str(e)}")
        return api_error(
            message=f"创建用户时发生错误: {str(e)}",
            error_code=ErrorCode.SERVER_ERROR
        )

def cancel_registration():
    """
    取消注册，删除用户（仅用于注册过程中发生错误时）
    
    请求参数:
        auth0_id: Auth0用户ID
        或者
        email: 用户邮箱
        
    返回:
        API响应，表示操作结果
    """
    # 获取请求数据
    if not request.is_json:
        return api_error(
            message="请求必须是JSON格式",
            error_code=ErrorCode.INVALID_REQUEST
        )
        
    data = request.get_json()
    auth0_id = data.get('auth0_id')
    email = data.get('email')
    
    # 检查是否至少提供了一个查询参数
    if not auth0_id and not email:
        return api_error(
            message="Auth0 ID或邮箱至少需要提供一个",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    # 查询用户
    user = None
    if auth0_id:
        user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user and email:
        user = User.query.filter_by(email=email).first()
    
    if not user:
        logger.warning(f"取消注册：用户不存在 auth0_id={auth0_id}, email={email}")
        return api_success(
            message="用户不存在，无需取消注册"
        )
    
    # 获取Auth0 ID（如果只提供了email）
    auth0_id = user.auth0_id
    
    # 删除Auth0用户
    if auth0_id:
        try:
            token = get_auth0_token()
            
            if token:
                delete_auth0_user(auth0_id)
                logger.info(f"从Auth0删除用户成功: {auth0_id}")
            else:
                logger.error("获取Auth0令牌失败，无法删除Auth0用户")
        except Exception as e:
            logger.error(f"删除Auth0用户失败: {str(e)}")
    
    # 删除本地用户
    try:
        db.session.delete(user)
        db.session.commit()
        logger.info(f"取消注册：成功删除用户 {user.id}")
        
        return api_success(
            message="取消注册成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户时发生错误: {str(e)}")
        
        return api_error(
            message="取消注册失败，请稍后再试",
            error_code=ErrorCode.DB_ERROR
        )
