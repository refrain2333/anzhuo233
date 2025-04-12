"""
密码重置相关功能模块
"""
from flask import request, current_app
import logging
import requests
from app.models.user import User
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

logger = logging.getLogger(__name__)

def api_forgot_password():
    """
    忘记密码API，发送密码重置邮件
    
    请求参数:
        email: 用户邮箱
        
    返回:
        API响应，表示操作结果
    """
    # 获取请求数据
    data = request.get_json()
    if not data or "email" not in data:
        return api_error(
            message="请求参数错误，缺少email",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    email = data.get("email")
    
    # 检查邮箱是否存在于系统中
    user = User.query.filter_by(email=email).first()
    if not user:
        # 出于安全考虑，不透露邮箱是否存在，但记录日志
        logger.warning(f"尝试为不存在的邮箱 {email} 重置密码")
        return api_success(
            message="如果该邮箱已注册，您将收到密码重置邮件"
        )
    
    # 获取Auth0配置
    domain = current_app.config['AUTH0_DOMAIN']
    client_id = current_app.config['AUTH0_CLIENT_ID']
    
    # 调用Auth0发送密码重置邮件
    try:
        url = f"https://{domain}/dbconnections/change_password"
        headers = {"Content-Type": "application/json"}
        data = {
            "client_id": client_id,
            "email": email,
            "connection": "Username-Password-Authentication"
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            logger.error(f"发送密码重置邮件失败: {response.status_code}, {response.text}")
            return api_error(
                message="发送密码重置邮件失败，请稍后重试",
                error_code=ErrorCode.EXTERNAL_API_ERROR
            )
        
        return api_success(
            message="如果该邮箱已注册，您将收到密码重置邮件"
        )
        
    except Exception as e:
        logger.error(f"发送密码重置邮件过程中发生异常: {str(e)}")
        return api_error(
            message="发送密码重置邮件失败，请稍后重试",
            error_code=ErrorCode.EXTERNAL_API_ERROR
        )

def api_change_password():
    """
    修改密码API
    
    请求参数:
        auth0_id: Auth0用户ID
        old_password: 旧密码
        new_password: 新密码
        
    返回:
        API响应，表示操作结果
    """
    # 获取请求数据
    data = request.get_json()
    if not data or "auth0_id" not in data or "old_password" not in data or "new_password" not in data:
        return api_error(
            message="请求参数错误，缺少必要参数",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    auth0_id = data.get("auth0_id")
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    # 检查新密码是否符合要求（至少8个字符）
    if len(new_password) < 8:
        return api_error(
            message="新密码必须至少包含8个字符",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    # 检查用户是否存在
    user = User.query.filter_by(auth0_id=auth0_id).first()
    if not user:
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    # 获取Auth0配置
    domain = current_app.config['AUTH0_DOMAIN']
    client_id = current_app.config['AUTH0_CLIENT_ID']
    client_secret = current_app.config['AUTH0_CLIENT_SECRET']
    
    # 获取Auth0管理API令牌
    try:
        token_url = f"https://{domain}/oauth/token"
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": f"https://{domain}/api/v2/",
            "grant_type": "client_credentials"
        }
        token_headers = {"content-type": "application/json"}
        
        token_response = requests.post(token_url, json=token_payload, headers=token_headers)
        
        if token_response.status_code != 200:
            logger.error(f"获取Auth0管理API令牌失败: {token_response.status_code}, {token_response.text}")
            return api_error(
                message="修改密码失败: 无法获取Auth0访问令牌",
                error_code=ErrorCode.EXTERNAL_API_ERROR
            )
        
        token = token_response.json()["access_token"]
        
        # 调用Auth0修改密码API
        # 注意：这需要使用Auth0的Password Change API，通常需要先验证旧密码
        
        # 先尝试用旧密码获取令牌来验证密码是否正确
        token_verify_url = f"https://{domain}/oauth/token"
        verify_payload = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": user.email,
            "password": old_password,
            "audience": f"https://{domain}/api/v2/",
            "scope": "openid profile email"
        }
        
        verify_response = requests.post(token_verify_url, json=verify_payload, headers=token_headers)
        
        if verify_response.status_code != 200:
            logger.warning(f"验证旧密码失败: {verify_response.status_code}, {verify_response.text}")
            return api_error(
                message="原密码不正确",
                error_code=ErrorCode.INVALID_CREDENTIALS
            )
        
        # 旧密码验证通过，修改密码
        auth0_id_encoded = auth0_id.replace("|", "%7C")  # URL编码
        change_url = f"https://{domain}/api/v2/users/{auth0_id_encoded}"
        change_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        change_payload = {
            "password": new_password
        }
        
        change_response = requests.patch(change_url, json=change_payload, headers=change_headers)
        
        if change_response.status_code != 200:
            logger.error(f"修改密码失败: {change_response.status_code}, {change_response.text}")
            return api_error(
                message="修改密码失败，请稍后重试",
                error_code=ErrorCode.EXTERNAL_API_ERROR
            )
        
        return api_success(
            message="密码修改成功"
        )
        
    except Exception as e:
        logger.error(f"修改密码过程中发生异常: {str(e)}")
        return api_error(
            message="修改密码失败，请稍后重试",
            error_code=ErrorCode.EXTERNAL_API_ERROR
        ) 