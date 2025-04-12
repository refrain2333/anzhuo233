"""
用户资料管理相关接口模块
包含获取用户资料、更新资料、更新头像等功能
"""
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
from app.models.user import User, Major, db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

logger = logging.getLogger(__name__)

@jwt_required()
def api_get_user_profile():
    """
    获取用户个人资料API端点
    
    返回:
        成功: 返回用户信息
        失败: 返回错误信息
    """
    try:
        # 获取当前用户ID
        user_id = get_jwt_identity()
        
        # 从数据库获取用户
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"获取用户资料失败: 用户不存在, id: {user_id}")
            return api_error(ErrorCode.NOT_FOUND, "用户不存在")
            
        # 组装用户资料
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "student_id": user.student_id,
            "major": user.major.name if user.major else None,
            "major_id": user.major_id,
            "grade": user.grade,
            "email_verified": user.email_verified,
            "avatar": user.avatar if user.avatar else None,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
            "last_login": user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else None
        }
        
        return api_success(user_data)
        
    except Exception as e:
        logger.error(f"获取用户资料过程中发生错误: {str(e)}")
        return api_error(ErrorCode.SERVER_ERROR, "获取用户资料过程中发生错误")

@jwt_required()
def api_update_user_profile():
    """
    更新用户个人资料API端点
    
    请求参数:
        name: 用户姓名 (可选)
        student_id: 学号 (可选)
        major_id: 专业ID (可选)
        grade: 年级 (可选)
        
    返回:
        成功: 返回更新后的用户信息
        失败: 返回错误信息
    """
    try:
        # 获取当前用户ID
        user_id = get_jwt_identity()
        
        # 从数据库获取用户
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"更新用户资料失败: 用户不存在, id: {user_id}")
            return api_error(ErrorCode.NOT_FOUND, "用户不存在")
            
        # 获取更新信息
        data = request.get_json()
        
        if not data:
            return api_error(ErrorCode.INVALID_INPUT, "缺少请求参数")
            
        # 更新用户信息
        has_update = False
        
        # 更新姓名
        if 'name' in data and data['name']:
            user.name = data['name']
            has_update = True
            
        # 更新学号
        if 'student_id' in data:
            # 检查学号是否已存在
            if data['student_id'] and user.student_id != data['student_id']:
                existing_user = User.query.filter_by(student_id=data['student_id']).first()
                if existing_user and existing_user.id != user.id:
                    logger.warning(f"学号已存在: {data['student_id']}, 用户: {user.email}")
                    return api_error(ErrorCode.CONFLICT, "该学号已被其他用户使用")
            
            user.student_id = data['student_id']
            has_update = True
            
        # 更新专业
        if 'major_id' in data:
            # 检查专业是否存在
            if data['major_id']:
                major = Major.query.get(data['major_id'])
                if not major:
                    return api_error(ErrorCode.INVALID_INPUT, "指定的专业不存在")
                    
            user.major_id = data['major_id']
            has_update = True
            
        # 更新年级
        if 'grade' in data:
            user.grade = data['grade']
            has_update = True
            
        # 保存更新
        if has_update:
            try:
                db.session.commit()
                logger.info(f"用户资料更新成功: id: {user.id}, email: {user.email}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"保存用户资料更新失败: {str(e)}")
                return api_error(ErrorCode.SERVER_ERROR, "保存资料失败")
        else:
            logger.info(f"用户资料没有变化: id: {user.id}, email: {user.email}")
            
        # 返回更新后的用户资料
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "student_id": user.student_id,
            "major": user.major.name if user.major else None,
            "major_id": user.major_id,
            "grade": user.grade,
            "email_verified": user.email_verified,
            "avatar": user.avatar if user.avatar else None
        }
        
        return api_success(user_data)
        
    except Exception as e:
        logger.error(f"更新用户资料过程中发生错误: {str(e)}")
        return api_error(ErrorCode.SERVER_ERROR, "更新用户资料过程中发生错误")

@jwt_required()
def api_update_avatar():
    """
    更新用户头像API端点
    
    请求参数:
        avatar: 头像数据（Base64编码）
        
    返回:
        成功: 返回头像URL
        失败: 返回错误信息
    """
    try:
        # 获取当前用户ID
        user_id = get_jwt_identity()
        
        # 从数据库获取用户
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"更新头像失败: 用户不存在, id: {user_id}")
            return api_error(ErrorCode.NOT_FOUND, "用户不存在")
            
        # 获取头像数据
        data = request.get_json()
        
        if not data or 'avatar' not in data:
            return api_error(ErrorCode.INVALID_INPUT, "缺少头像数据")
            
        avatar_data = data.get('avatar', '')
        
        # 处理Base64编码的头像
        try:
            # 去除Base64前缀（如果有）
            if ',' in avatar_data:
                avatar_data = avatar_data.split(',', 1)[1]
                
            # 解码Base64数据
            avatar_binary = base64.b64decode(avatar_data)
            
            # 检查文件大小
            max_size = 5 * 1024 * 1024  # 5MB
            if len(avatar_binary) > max_size:
                return api_error(ErrorCode.INVALID_INPUT, "头像文件过大，请上传小于5MB的图片")
                
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"avatar_{user_id}_{timestamp}.jpg"
            safe_filename = secure_filename(filename)
            
            # 确保上传目录存在
            avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 保存文件
            filepath = os.path.join(avatar_dir, safe_filename)
            with open(filepath, 'wb') as f:
                f.write(avatar_binary)
                
            # 更新用户头像URL
            avatar_url = f"/uploads/avatars/{safe_filename}"
            user.avatar = avatar_url
            
            db.session.commit()
            logger.info(f"用户头像更新成功: id: {user.id}, email: {user.email}")
            
            return api_success({"avatar": avatar_url})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"处理头像数据失败: {str(e)}")
            return api_error(ErrorCode.SERVER_ERROR, "处理头像数据失败")
            
    except Exception as e:
        logger.error(f"更新头像过程中发生错误: {str(e)}")
        return api_error(ErrorCode.SERVER_ERROR, "更新头像过程中发生错误")
