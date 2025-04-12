"""
用户邮箱验证相关功能模块
"""
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import logging
from app.models.user import User, db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
import time
from datetime import datetime, timedelta
from app.api.v1.auth.utils import get_auth0_token

logger = logging.getLogger(__name__)

@jwt_required()
def api_send_verification_email():
    """
    发送邮箱验证邮件API
    
    请求参数:
        无，从JWT获取用户ID
        
    返回:
        API响应，表示操作结果
    """
    # 从JWT获取用户ID
    user_id = get_jwt_identity()
    
    # 查询用户
    user = User.query.get(user_id)
    if not user:
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    # 如果用户邮箱已验证，无需重新发送
    if user.email_verified:
        return api_success(
            message="邮箱已验证，无需重新发送"
        )
    
    # 获取Auth0配置
    domain = current_app.config['AUTH0_DOMAIN']
    client_id = current_app.config['AUTH0_CLIENT_ID']
    client_secret = current_app.config['AUTH0_CLIENT_SECRET']
    audience = f"https://{domain}/api/v2/"
    
    # 获取管理API访问令牌
    token_url = f"https://{domain}/oauth/token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials"
    }
    
    token_headers = {"content-type": "application/json"}
    
    try:
        token_response = requests.post(token_url, json=token_payload, headers=token_headers)
        token_data = token_response.json()
        
        if 'access_token' not in token_data:
            logger.error(f"获取Auth0令牌失败: {token_data}")
            return api_error(
                message="发送验证邮件失败：服务错误",
                error_code=ErrorCode.AUTH0_ERROR
            )
        
        access_token = token_data['access_token']
        
        # 检查用户的Auth0 ID是否存在
        if not user.auth0_id:
            return api_error(
                message="用户未关联Auth0账号，无法发送验证邮件",
                error_code=ErrorCode.USER_NOT_FOUND
            )
        
        # 模拟模式处理
        if user.auth0_id.startswith('mock|'):
            logger.info(f"模拟用户 {user_id} 发送验证邮件")
            # 更新用户的验证邮件发送时间
            user.verification_sent_at = int(time.time())
            db.session.commit()
            return api_success(
                message="模拟模式：验证邮件发送成功"
            )
            
        # 发送验证邮件
        auth0_id = user.auth0_id.replace("|", "%7C")  # URL编码
        user_url = f"https://{domain}/api/v2/jobs/verification-email"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "content-type": "application/json"
        }
        
        payload = {
            "user_id": user.auth0_id,
            "client_id": client_id
        }
        
        response = requests.post(user_url, json=payload, headers=headers)
        
        if response.status_code == 201:
            # 更新用户的验证邮件发送时间
            user.verification_sent_at = int(time.time())
            db.session.commit()
            
            return api_success(
                message="验证邮件发送成功，请查收邮箱"
            )
        else:
            logger.error(f"发送验证邮件失败: {response.status_code}, {response.text}")
            return api_error(
                message="发送验证邮件失败",
                error_code=ErrorCode.AUTH0_ERROR
            )
            
    except Exception as e:
        logger.error(f"发送验证邮件过程中发生错误: {str(e)}")
        return api_error(
            message="发送验证邮件失败：服务错误",
            error_code=ErrorCode.SERVER_ERROR
        )

def check_verification(user, force_update=False):
    """
    检查用户的邮箱验证状态
    
    参数:
        user: User实例
        force_update: 是否强制从Auth0获取最新状态
        
    返回:
        API响应，表示操作结果
    """
    # 检查用户是否已验证邮箱
    if user.email_verified and not force_update:
        return api_success(
            message="邮箱已验证",
            data={"is_verified": True, "email_verified": True}
        )
    
    # 检查用户的Auth0 ID是否存在
    if not user.auth0_id:
        return api_error(
            message="用户未关联Auth0账号，无法验证邮箱",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    # 模拟模式处理
    if user.auth0_id.startswith('mock|'):
        # 检查是否已发送验证邮件且已经过了60秒
        if user.verification_sent_at and (int(time.time()) - user.verification_sent_at) > 60:
            # 自动将用户标记为已验证
            user.email_verified = True
            try:
                db.session.commit()
                logger.info(f"模拟模式：用户 {user.id} 邮箱自动标记为已验证")
            except Exception as e:
                db.session.rollback()
                logger.error(f"更新用户验证状态失败: {str(e)}")
                return api_error(
                    message="验证邮箱失败：数据库更新错误",
                    error_code=ErrorCode.DATABASE_ERROR
                )
            
            return api_success(
                message="模拟模式：邮箱已验证",
                data={"is_verified": True}
            )
        else:
            return api_success(
                message="模拟模式：邮箱尚未验证",
                data={"is_verified": False}
            )
    
    # 获取Auth0配置
    domain = current_app.config['AUTH0_DOMAIN']
    client_id = current_app.config['AUTH0_CLIENT_ID']
    client_secret = current_app.config['AUTH0_CLIENT_SECRET']
    audience = f"https://{domain}/api/v2/"
    
    # 获取管理API访问令牌
    token_url = f"https://{domain}/oauth/token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials"
    }
    
    token_headers = {"content-type": "application/json"}
    
    try:
        token_response = requests.post(token_url, json=token_payload, headers=token_headers)
        token_data = token_response.json()
        
        if 'access_token' not in token_data:
            logger.error(f"获取Auth0令牌失败: {token_data}")
            return api_error(
                message="验证邮箱失败：服务错误",
                error_code=ErrorCode.AUTH0_ERROR
            )
        
        access_token = token_data['access_token']
        
        # 获取用户信息
        auth0_id = user.auth0_id.replace("|", "%7C")  # URL编码
        user_url = f"https://{domain}/api/v2/users/{auth0_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "content-type": "application/json"
        }
        
        response = requests.get(user_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            is_verified = user_data.get('email_verified', False)
            
            # 更新用户验证状态
            if is_verified != user.email_verified:
                user.email_verified = is_verified
                try:
                    db.session.commit()
                    logger.info(f"用户 {user.id} 邮箱验证状态更新为: {is_verified}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"更新用户验证状态失败: {str(e)}")
                    return api_error(
                        message="验证邮箱失败：数据库更新错误",
                        error_code=ErrorCode.DATABASE_ERROR
                    )
            
            # 统一返回字段名为email_verified和is_verified，保证向后兼容
            return api_success(
                message="邮箱已验证" if is_verified else "邮箱尚未验证",
                data={
                    "is_verified": is_verified,
                    "email_verified": is_verified
                }
            )
        else:
            logger.error(f"获取用户验证状态失败: {response.status_code}, {response.text}")
            return api_error(
                message="验证邮箱失败：无法获取验证状态",
                error_code=ErrorCode.AUTH0_ERROR
            )
            
    except Exception as e:
        logger.error(f"验证邮箱过程中发生错误: {str(e)}")
        return api_error(
            message="验证邮箱失败：服务错误",
            error_code=ErrorCode.SERVER_ERROR
        )

# @jwt_required()  # 移除JWT认证限制，以便验证等待页面可以直接检查
def api_check_verification():
    """
    检查用户邮箱验证状态API
    
    请求参数:
        如果已登录: 从JWT获取用户ID
        否则: 需要提供auth0_id或email
        
    返回:
        API响应，表示操作结果
    """
    # 检查是否提供了auth0_id或email参数
    auth0_id = None
    email = None
    
    # 处理GET请求的URL参数
    if request.method == 'GET':
        auth0_id = request.args.get('auth0_id')
        email = request.args.get('email')
    
    # 处理POST请求的JSON数据
    elif request.is_json:
        data = request.get_json()
        auth0_id = data.get('auth0_id')
        email = data.get('email')
    
    # 尝试从JWT中获取用户ID
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        if user_id:
            # 查询用户
            user = User.query.get(user_id)
            if user:
                return check_verification(user)
    except Exception as e:
        logger.debug(f"无法从JWT获取用户信息: {str(e)}")
    
    # 如果没有从JWT获取到用户，则根据提供的auth0_id或email查询
    if auth0_id or email:
        user = None
        if auth0_id:
            user = User.query.filter_by(auth0_id=auth0_id).first()
        if not user and email:
            user = User.query.filter_by(email=email).first()
        
        if user:
            return check_verification(user)
        else:
            logger.warning(f"用户不存在: auth0_id={auth0_id}, email={email}")
            return api_error(
                message="用户不存在",
                error_code=ErrorCode.USER_NOT_FOUND
            )
    
    # 没有提供有效的用户标识
    return api_error(
        message="无法识别用户，请提供auth0_id或email",
        error_code=ErrorCode.INVALID_REQUEST
    )

def cleanup_unverified_users():
    """
    清理未验证的用户账号
    
    请求参数:
        minutes: 清理多少分钟前注册的未验证用户，默认60分钟
        
    返回:
        API响应，表示操作结果
    """
    try:
        data = request.get_json()
        minutes = data.get('minutes', 60) if data else 60
        
        # 计算截止时间
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # 查询符合条件的用户：未验证邮箱且注册时间早于截止时间
        users = User.query.filter(
            User.email_verified == False,
            User.created_at <= cutoff_time
        ).all()
        
        if not users:
            logger.info(f"没有找到需要清理的未验证用户账号")
            return api_success({
                "message": "没有找到需要清理的未验证用户账号",
                "count": 0
            })
        
        # 记录要删除的用户ID
        user_ids = [user.id for user in users]
        auth0_ids = [user.auth0_id for user in users if user.auth0_id]
        
        deleted_count = 0
        # 删除Auth0用户
        for auth0_id in auth0_ids:
            try:
                token = get_auth0_token()
                if token:
                    from app.api.v1.auth.utils import delete_auth0_user
                    delete_auth0_user(auth0_id)
                    logger.info(f"从Auth0删除未验证用户: {auth0_id}")
                    deleted_count += 1
            except Exception as e:
                logger.error(f"删除Auth0用户失败: {str(e)}")
        
        # 删除本地用户记录
        try:
            for user in users:
                db.session.delete(user)
            db.session.commit()
            logger.info(f"成功清理 {len(users)} 个未验证用户账号")
            
            return api_success({
                "message": f"成功清理 {len(users)} 个未验证用户账号",
                "count": len(users),
                "user_ids": user_ids
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"清理未验证用户失败: {str(e)}")
            return api_error(
                message=f"清理未验证用户失败: {str(e)}",
                error_code=ErrorCode.DB_ERROR
            )
            
    except Exception as e:
        logger.error(f"清理未验证用户过程中发生错误: {str(e)}")
        return api_error(
            message="清理未验证用户失败",
            error_code=ErrorCode.SERVER_ERROR
        )
