"""
用户会话管理模块
包含JWT令牌刷新、用户注销等功能
"""
from flask import request, current_app, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token,
    get_jwt, verify_jwt_in_request
)
import logging
from datetime import datetime, timedelta
import requests
from app.models.user import User, db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

logger = logging.getLogger(__name__)

@jwt_required(refresh=True)
def api_refresh_token():
    """
    刷新访问令牌API端点
    
    请求头需包含:
        Authorization: Bearer <refresh_token>
        
    返回:
        成功: 返回新的访问令牌
        失败: 返回错误信息
    """
    try:
        # 获取当前用户身份
        current_user_id = get_jwt_identity()
        
        # 查询用户
        user = User.query.get(current_user_id)
        if not user:
            logger.warning(f"刷新令牌失败: 用户不存在 ID={current_user_id}")
            return api_error(ErrorCode.NOT_FOUND, "用户不存在")
            
        # 创建用户声明
        user_claims = {
            "user_id": user.id,
            "auth0_id": user.auth0_id,
            "email": user.email,
            "email_verified": user.email_verified
        }
        
        # 创建新的访问令牌
        access_token = create_access_token(identity=user.id, additional_claims=user_claims)
        
        # 更新用户最后活跃时间
        user.last_active = datetime.now()
        
        try:
            db.session.commit()
            logger.info(f"刷新令牌成功: 用户ID={user.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新用户活跃时间失败: {str(e)}")
            
        # 返回新令牌
        return api_success({
            "token": access_token,
            "expires_in": current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(minutes=60)).total_seconds()
        })
        
    except Exception as e:
        logger.error(f"刷新令牌时发生错误: {str(e)}")
        return api_error(ErrorCode.SERVER_ERROR, "处理刷新令牌请求时发生错误")

@jwt_required()
def api_logout():
    """
    用户注销API端点
    
    请求头需包含:
        Authorization: Bearer <access_token>
        
    返回:
        成功: 返回成功消息
        失败: 返回错误信息
    """
    try:
        # 获取当前用户身份
        current_user_id = get_jwt_identity()
        jwt = get_jwt()
        
        # 查询用户
        user = User.query.get(current_user_id)
        if not user:
            logger.warning(f"注销失败: 用户不存在 ID={current_user_id}")
            return api_error(ErrorCode.NOT_FOUND, "用户不存在")
            
        # 我们可以在此处实现令牌加入黑名单的逻辑
        # 例如，将令牌存入Redis并设置过期时间
        # 或者，更新用户的登录状态
        
        logger.info(f"用户注销成功: ID={user.id}, 邮箱={user.email}")
        
        return api_success({"message": "注销成功"})
        
    except Exception as e:
        logger.error(f"处理注销请求时发生错误: {str(e)}")
        return api_error(ErrorCode.SERVER_ERROR, "处理注销请求时发生错误")

def verify_token():
    """
    验证令牌有效性
    
    请求头需包含:
        Authorization: Bearer <access_token>
        
    返回:
        成功: 返回用户信息
        失败: 返回错误信息
    """
    try:
        # 验证JWT令牌
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # 查询用户
        user = User.query.get(current_user_id)
        if not user:
            logger.warning(f"验证令牌失败: 用户不存在 ID={current_user_id}")
            return api_error(ErrorCode.NOT_FOUND, "用户不存在")
            
        # 更新最后活跃时间
        user.last_active = datetime.now()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新用户活跃时间失败: {str(e)}")
            
        # 返回用户信息
        return api_success({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "student_id": user.student_id,
                "email_verified": user.email_verified,
                "major": user.major.name if user.major else None,
                "grade": user.grade
            }
        })
        
    except Exception as e:
        logger.error(f"验证令牌时发生错误: {str(e)}")
        return api_error(ErrorCode.UNAUTHORIZED, "无效的令牌或令牌已过期") 