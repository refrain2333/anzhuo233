"""
用户登录相关功能模块
"""
from flask import request, current_app, jsonify, session, redirect
import json
import requests
from datetime import datetime, timedelta
import logging
from app.models.user import User
from app import db
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
from flask_jwt_extended import create_access_token

logger = logging.getLogger(__name__)

def api_login():
    """
    用户登录API
    
    请求参数:
        email: 邮箱
        或
        student_id: 学号
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
    
    # 验证是否提供了学号或邮箱
    if not (data.get('email') or data.get('student_id')):
        return api_error(
            message="缺少必要参数: 请提供学号或邮箱",
            error_code=ErrorCode.INVALID_REQUEST
        )
        
    # 验证是否提供了密码
    if not data.get('password'):
        return api_error(
            message="缺少必要参数: 密码",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    password = data.get('password')
    email = data.get('email')
    student_id = data.get('student_id')
    
    # 如果提供的是学号，查找对应的邮箱
    user = None
    if student_id and not email:
        logger.info(f"使用学号 {student_id} 登录")
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return api_error(
                message="该学号不存在",
                error_code=ErrorCode.USER_NOT_FOUND
            )
        email = user.email
    else:
        # 直接使用邮箱查找用户
        user = User.query.filter_by(email=email).first()
        if not user:
            return api_error(
                message="该邮箱不存在",
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
        "username": email,  # 始终使用邮箱进行Auth0验证
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
                message="学号/邮箱或密码错误",
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
        
        # 为用户生成JWT令牌
        try:
            # 如果用户存在，为其创建JWT令牌
            from flask_jwt_extended import create_access_token
            
            # 确保用户ID作为身份标识符（转为字符串）
            user_id_str = str(user.id)
            
            # 创建额外的声明
            additional_claims = {
                "username": user.name,
                "email": user.email,
                "student_id": user.student_id,
                "auth_source": "application"  # 标记这是应用内认证
            }
            
            # 创建JWT令牌（明确使用字符串类型的用户ID）
            access_token = create_access_token(
                identity=user_id_str,
                additional_claims=additional_claims
            )
            
            # 记录JWT令牌创建信息
            logger.info(f"为用户 {user.student_id} 创建JWT令牌, 用户ID: {user_id_str} (类型: {type(user_id_str).__name__})")
            
            # 返回成功响应
            return api_success(
                message="登录成功",
                data={
                    "token": access_token,
                    "user": {
                        "id": user_id_str,  # 确保返回字符串ID
                        "name": user.name,
                        "email": user.email,
                        "student_id": user.student_id
                    }
                }
            )
        except Exception as e:
            logger.error(f"JWT令牌生成失败: {str(e)}")
            return api_error(
                message="登录过程中发生服务器错误",
                error_code=ErrorCode.SERVER_ERROR
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
    # 记录日志
    logger.info(f"用户请求登出，会话ID: {session.get('user_id', '未知')}")
    
    # 清除所有会话数据
    try:
        # 记录当前会话中的关键信息用于日志
        user_id = session.get('user_id')
        email = session.get('email')
        
        session.clear()
        
        logger.info(f"会话已清除，用户ID: {user_id}, 邮箱: {email}")
    except Exception as e:
        logger.error(f"清除会话时发生错误: {str(e)}")
    
    return api_success(
        message="已成功登出，请重新登录",
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

def api_admin_login():
    """
    管理员登录API
    
    请求参数:
        username: 用户名（可以是邮箱或学号）
        password: 密码
        
    返回:
        API响应，表示操作结果
            - 200: 登录成功，返回管理员令牌
            - 400: 请求错误（参数错误）
            - 401: 认证失败（用户名或密码错误）
            - 403: 权限不足（非管理员）
            - 500: 服务器错误
    """
    # 获取请求数据（同时支持JSON和表单数据）
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    # 记录请求信息（不包含密码）
    logger.info(f"管理员登录请求: 请求方式={request.method}, 内容类型={request.content_type}, 用户名={data.get('username', '')}")
    
    # 验证是否提供了用户名和密码
    if not data.get('username'):
        logger.warning("管理员登录缺少用户名参数")
        
        # 如果是传统表单提交，重定向回登录页面
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            return redirect('/admin/login?error=请提供用户名')
            
        return api_error(
            message="缺少必要参数: 用户名",
            error_code=ErrorCode.INVALID_REQUEST
        )
        
    if not data.get('password'):
        logger.warning("管理员登录缺少密码参数")
        
        # 如果是传统表单提交，重定向回登录页面
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            return redirect('/admin/login?error=请提供密码')
            
        return api_error(
            message="缺少必要参数: 密码",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    username = data.get('username')
    password = data.get('password')
    
    # 判断用户名是邮箱还是学号
    user = None
    if '@' in username:
        # 视为邮箱
        user = User.query.filter_by(email=username).first()
    else:
        # 视为学号
        user = User.query.filter_by(student_id=username).first()
    
    # 检查用户是否存在
    if not user:
        logger.warning(f"管理员登录失败: 用户名不存在 {username}")
        
        # 如果是传统表单提交，重定向回登录页面
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            return redirect('/admin/login?error=用户名或密码不正确')
            
        return api_error(
            message="用户名或密码不正确",
            error_code=ErrorCode.AUTH_VERIFICATION_FAILED
        )
    
    # 检查用户是否为管理员
    if not user.is_admin:
        logger.warning(f"管理员登录失败: 用户不是管理员 {username}")
        
        # 如果是传统表单提交，重定向回登录页面
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            return redirect('/admin/login?error=您没有管理员权限')
            
        return api_error(
            message="您没有管理员权限",
            error_code=ErrorCode.PERMISSION_DENIED
        )
    
    # 验证密码（使用Auth0）
    domain = current_app.config.get('AUTH0_DOMAIN')
    client_id = current_app.config.get('AUTH0_CLIENT_ID')
    client_secret = current_app.config.get('AUTH0_CLIENT_SECRET')
    audience = current_app.config.get('AUTH0_API_AUDIENCE')
    
    # 如果是邮箱登录，直接使用邮箱；如果是学号登录，使用用户的邮箱
    email = user.email
    
    # 请求Auth0获取令牌
    try:
        # 尝试不同的audience组合，解决不同Auth0租户的配置差异
        # 方法1-1：尝试使用API audience
        auth_url = f"https://{domain}/oauth/token"
        auth_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",  # 使用realm方式
            "username": email,
            "password": password,
            "realm": "Username-Password-Authentication",  # Auth0默认连接名称
            "scope": "openid profile email",
            "audience": audience  # 使用API audience
        }
        
        auth_headers = {
            "content-type": "application/json"
        }
        
        # 记录请求信息（不包含密码和密钥）
        debug_payload = auth_payload.copy()
        debug_payload["password"] = "******"
        debug_payload["client_secret"] = "******"
        logger.info(f"方法1-1 - Auth0管理员认证请求: {auth_url}, 使用连接={auth_payload['realm']}, audience={audience}")
        logger.info(f"方法1-1 - 完整请求参数: {json.dumps(debug_payload)}")
        
        auth_response = requests.post(auth_url, json=auth_payload, headers=auth_headers)
        
        # 如果方法1-1失败，尝试方法1-2：不使用audience
        if auth_response.status_code != 200:
            error_data = auth_response.json()
            error_description = error_data.get('error_description', '登录失败')
            logger.warning(f"方法1-1 - Auth0管理员认证失败: {error_description}")
            
            # 方法1-2：尝试不使用audience
            auth_payload_no_audience = auth_payload.copy()
            auth_payload_no_audience.pop('audience', None)
            
            logger.info(f"方法1-2 - 尝试不使用audience进行管理员认证")
            auth_response = requests.post(auth_url, json=auth_payload_no_audience, headers=auth_headers)
            
            # 如果方法1-2失败，尝试方法1-3
            if auth_response.status_code != 200:
                error_data = auth_response.json()
                error_description = error_data.get('error_description', '登录失败')
                logger.warning(f"方法1-2 - Auth0管理员认证失败: {error_description}")
                
                # 方法1-3：尝试使用Auth0管理API作为audience
                auth_payload_mgmt = auth_payload.copy()
                auth_payload_mgmt['audience'] = f"https://{domain}/api/v2/"
                
                logger.info(f"方法1-3 - 尝试使用管理API作为audience: {auth_payload_mgmt['audience']}")
                auth_response = requests.post(auth_url, json=auth_payload_mgmt, headers=auth_headers)
                
                # 如果方法1-3失败，尝试方法2
                if auth_response.status_code != 200:
                    error_data = auth_response.json()
                    error_description = error_data.get('error_description', '登录失败')
                    logger.warning(f"方法1-3 - Auth0管理员认证失败: {error_description}")
                    
                    # 方法2：使用标准password方式
                    password_payload = {
                        'grant_type': 'password',
                        'username': email,
                        'password': password,
                        'audience': audience,
                        'scope': 'openid profile email',
                        'client_id': client_id,
                        'client_secret': client_secret
                    }
                    
                    logger.info(f"方法2 - 尝试使用标准password方式进行管理员认证")
                    password_response = requests.post(auth_url, json=password_payload, headers=auth_headers)
                    
                    if password_response.status_code != 200:
                        # 如果方法2也失败，返回错误信息
                        error_detail = password_response.json().get('error_description', 'Unknown error')
                        logger.warning(f"方法2 - Auth0管理员认证失败: {error_detail}")
                        
                        # 记录详细的错误信息便于调试
                        logger.error(f"管理员登录失败 - Auth0认证错误: 方法1错误={error_description}, 方法2错误={error_detail}")
                        
                        # 如果是传统表单提交，重定向回登录页面
                        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
                            return redirect('/admin/login?error=用户名或密码不正确')
                        
                        return api_error(
                            message="用户名或密码不正确",
                            error_code=ErrorCode.AUTH_VERIFICATION_FAILED
                        )
                    else:
                        # 方法2成功
                        auth0_data = password_response.json()
                        id_token = auth0_data.get('id_token')
                else:
                    # 方法1-3成功
                    auth0_data = auth_response.json()
                    id_token = auth0_data.get('id_token')
            else:
                # 方法1-2成功
                auth0_data = auth_response.json()
                id_token = auth0_data.get('id_token')
        else:
            # 方法1-1成功
            auth0_data = auth_response.json()
            id_token = auth0_data.get('id_token')
        
        # 创建JWT令牌
        # 为管理员令牌使用更长的过期时间
        expires = timedelta(hours=12)
        additional_claims = {
            'is_admin': True,
            'name': user.name,
            'email': user.email
        }
        
        admin_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=expires
        )
        
        # 记录登录成功
        logger.info(f"管理员登录成功: {username}")
        
        # 如果是传统表单提交，设置cookie并重定向到管理员仪表板
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            response = redirect('/admin/dashboard')
            response.set_cookie('admin_token', admin_token, httponly=False, max_age=43200) # 12小时
            return response
            
        # 返回成功响应和令牌
        return api_success(data={
            'token': admin_token,
            'admin': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        })
        
    except Exception as e:
        logger.error(f"管理员登录时发生错误: {str(e)}", exc_info=True)
        
        # 如果是传统表单提交，重定向回登录页面
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            return redirect('/admin/login?error=服务器错误，请稍后再试')
            
        return api_error(
            message="服务器内部错误",
            error_code=ErrorCode.SYSTEM_ERROR
        )

def api_check_admin():
    """
    验证管理员令牌有效性
    
    请求参数:
        Authorization 头部: Bearer token
        
    返回:
        API响应，表示操作结果
            - 200: 令牌有效，返回管理员信息
            - 401: 令牌无效或已过期
            - 403: 用户不是管理员
    """
    from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
    
    @jwt_required()
    def check_admin_token():
        try:
            jwt_data = get_jwt()
            user_id = get_jwt_identity()
            
            # 详细记录JWT内容，辅助调试
            logger.info(f"JWT认证成功，用户ID: {user_id}")
            # 记录JWT中的关键信息（不包含敏感数据）
            log_data = {k: v for k, v in jwt_data.items() if k in ['exp', 'iat', 'is_admin', 'name', 'email']}
            logger.info(f"JWT额外信息: {log_data.get('name', 'unknown')}, {log_data.get('email', 'unknown')}")
            
            # 验证是否是管理员令牌
            if not jwt_data.get('is_admin', False):
                logger.warning(f"验证管理员令牌失败: 令牌不是管理员令牌")
                return api_error(
                    message="您没有管理员权限",
                    error_code=ErrorCode.PERMISSION_DENIED
                )
            
            # 获取用户信息
            user = User.query.get(int(user_id))
            if not user:
                logger.warning(f"验证管理员令牌失败: 用户不存在 ID={user_id}")
                return api_error(
                    message="用户不存在",
                    error_code=ErrorCode.USER_NOT_FOUND
                )
            
            # 检查用户是否为管理员
            if not user.is_admin:
                logger.warning(f"验证管理员令牌失败: 用户不是管理员 ID={user_id}")
                return api_error(
                    message="您没有管理员权限",
                    error_code=ErrorCode.PERMISSION_DENIED
                )
            
            # 返回成功响应和管理员信息
            return api_success(data={
                'success': True,
                'admin': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'student_id': user.student_id,
                    'avatar_url': user.avatar_url,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'is_admin': user.is_admin
                }
            })
            
        except Exception as e:
            logger.error(f"验证管理员令牌时发生错误: {str(e)}", exc_info=True)
            return api_error(
                message="令牌无效或已过期",
                error_code=ErrorCode.TOKEN_INVALID
            )
    
    return check_admin_token()
