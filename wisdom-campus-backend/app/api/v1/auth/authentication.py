"""
用户认证相关接口模块
包含用户登录和注册功能
"""
from flask import request, current_app, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import requests
import logging
import json
from datetime import datetime, timedelta
import re
from app.models.user import User, Major, db, UserProfile
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
from app.api.v1.auth.email_verification import send_verification_email, check_email_verification
from app.schemas.user import UserCreateSchema, UserSchema
from sqlalchemy.exc import SQLAlchemyError
import traceback
import time

logger = logging.getLogger(__name__)

# 添加一个映射存储最后发送验证邮件的时间
_last_verification_sent = {}  # 格式: {email: timestamp}

def api_login():
    """
    用户登录API端点
    
    请求参数:
        email: 用户邮箱 或 student_id: 学号 (二选一)
        password: 用户密码
        
    返回:
        成功: 返回用户信息和JWT令牌
        失败: 返回错误信息
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return api_error(ErrorCode.get_message(ErrorCode.INVALID_INPUT), ErrorCode.INVALID_INPUT)
            
        email = data.get('email')
        student_id = data.get('student_id')
        password = data.get('password')
        
        # 验证必填字段
        if not password:
            return api_error("密码不能为空", ErrorCode.INVALID_INPUT)
            
        # 如果提供的是学号而不是邮箱，则通过学号查询对应的邮箱
        if not email and student_id:
            logger.info(f"使用学号 {student_id} 登录，查询对应邮箱")
            user = User.query.filter_by(student_id=student_id).first()
            if not user:
                logger.warning(f"登录失败: 学号不存在 {student_id}")
                return api_error("该学号不存在，请先注册", ErrorCode.USER_NOT_FOUND)
            email = user.email
            logger.info(f"学号 {student_id} 对应的邮箱为 {email}")
        
        # 如果没有提供邮箱也没有提供学号，或者查询不到对应的邮箱，则返回错误
        if not email:
            return api_error("邮箱和学号不能同时为空", ErrorCode.INVALID_INPUT)
            
        # 获取Auth0配置
        domain = current_app.config.get('AUTH0_DOMAIN')
        client_id = current_app.config.get('AUTH0_CLIENT_ID')
        client_secret = current_app.config.get('AUTH0_CLIENT_SECRET')
        audience = current_app.config.get('AUTH0_API_AUDIENCE')
        
        # 记录Auth0配置信息(不包含敏感信息)
        logger.info(f"Auth0配置: domain={domain}, 使用邮箱={email}, audience={audience}")
        
        # 尝试使用/oauth/token端点进行认证
        try:
            # 方法1：尝试使用不同的连接名称
            auth_url = f"https://{domain}/oauth/token"
            auth_payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "http://auth0.com/oauth/grant-type/password-realm",  # 使用realm方式
                "username": email,
                "password": password,
                "realm": "Username-Password-Authentication",  # 修改为Auth0实际的连接名称
                "scope": "openid profile email",
                "audience": audience
            }
            
            auth_headers = {
                "content-type": "application/json"
            }
            
            # 打印请求信息(不包含密码)
            debug_payload = auth_payload.copy()
            debug_payload["password"] = "******"
            logger.info(f"方法1 - Auth0请求(使用Username-Password-Authentication连接): {auth_url}, 请求体={json.dumps(debug_payload)}")
            
            auth_response = requests.post(auth_url, json=auth_payload, headers=auth_headers)
            
            # 如果方法1失败，尝试方法2
            if auth_response.status_code != 200:
                error_data = auth_response.json()
                error_description = error_data.get('error_description', '登录失败')
                logger.error(f"方法1 - Auth0认证失败: {error_description}")
                
                # 尝试方法2: 使用Auth0 Management API进行登录
                logger.info("尝试使用方法2：获取管理API令牌进行登录")
                
                # 获取管理API令牌
                token_url = f"https://{domain}/oauth/token"
                token_payload = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": f"https://{domain}/api/v2/",
                    "grant_type": "client_credentials"
                }
                
                token_headers = {"content-type": "application/json"}
                logger.info(f"尝试获取管理令牌: URL={token_url}")
                token_response = requests.post(token_url, json=token_payload, headers=token_headers)
                
                if token_response.status_code != 200:
                    logger.error(f"获取管理API令牌失败: 状态码={token_response.status_code}, 响应={token_response.text}")
                    return api_error("身份验证服务暂时不可用", ErrorCode.AUTH0_ERROR)
                else:
                    logger.info(f"获取管理API令牌成功: 响应长度={len(token_response.text)}")
                
                management_token = token_response.json().get('access_token')
                
                # 使用管理API查询用户
                # 1. 首先检查用户是否存在于Auth0
                search_url = f"https://{domain}/api/v2/users-by-email"
                search_headers = {
                    "Authorization": f"Bearer {management_token}",
                    "Content-Type": "application/json"
                }
                search_params = {"email": email}
                
                search_response = requests.get(search_url, headers=search_headers, params=search_params)
                
                if search_response.status_code != 200:
                    logger.error(f"查询Auth0用户失败: {search_response.text}")
                    return api_error("无法验证用户信息", ErrorCode.AUTH0_ERROR)
                
                auth0_users = search_response.json()
                
                if not auth0_users or len(auth0_users) == 0:
                    logger.warning(f"用户邮箱在Auth0中不存在: {email}")
                    return api_error("用户不存在，请先注册", ErrorCode.USER_NOT_FOUND)
                
                # 用户存在，获取Auth0用户信息
                auth0_user = auth0_users[0]
                auth0_id = auth0_user.get('user_id')
                
                # 2. 然后尝试使用接收到的密码在Auth0中验证用户
                # 注意：这部分仍然需要Resource Owner Password Flow，
                # 但我们已经确认了用户确实存在，所以提供更明确的错误信息
                
                # 查询本地用户信息
                user = User.query.filter_by(email=email).first()
                if not user:
                    # 如果Auth0有用户但本地没有，创建本地用户记录
                    logger.warning(f"用户在Auth0中存在但本地不存在: {email}, auth0_id={auth0_id}")
                    user = User(
                        email=email,
                        auth0_id=auth0_id,
                        name=auth0_user.get('name', ''),
                        email_verified=auth0_user.get('email_verified', False)
                    )
                    
                    # 如果是学号登录，设置学号
                    if student_id:
                        user.student_id = student_id
                    
                    try:
                        db.session.add(user)
                        db.session.commit()
                        logger.info(f"为Auth0用户创建本地记录: {email}")
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"创建本地用户记录失败: {str(e)}")
                        return api_error("系统错误，请稍后重试", ErrorCode.DB_ERROR)
                
                # 3. 最后，如果用户验证通过，创建JWT令牌
                # 如果之前用方法1验证失败，可能是密码错误
                # 这里不能自动验证成功，应返回错误信息让用户重试
                
                # 根据初始方法1的错误，返回相应错误信息
                if "Wrong email or password" in error_description:
                    return api_error("密码错误，请重试", ErrorCode.AUTH_INVALID_PASSWORD)
                elif "Please verify your email" in error_description:
                    return api_error("邮箱未验证，请先验证邮箱", ErrorCode.AUTH_EMAIL_NOT_VERIFIED)
                elif "unauthorized_client" in error_description:
                    return api_error("认证方式未启用，请联系系统管理员配置Auth0", ErrorCode.AUTH0_ERROR)
                else:
                    # 对于其他错误，返回具体错误信息
                    return api_error(f"认证失败: {error_description}", ErrorCode.UNAUTHORIZED)
            
            # 处理成功的身份验证
            auth0_data = auth_response.json()
            access_token = auth0_data.get('access_token')
            id_token = auth0_data.get('id_token')
            
            user_url = f"https://{domain}/userinfo"
            user_headers = {"Authorization": f"Bearer {access_token}"}
            
            user_response = requests.get(user_url, headers=user_headers)
            
            if user_response.status_code != 200:
                logger.error(f"获取用户信息失败: {user_response.text}")
                return api_error("无法获取用户信息", ErrorCode.SYSTEM_ERROR)
                
            user_info = user_response.json()
            auth0_id = user_info.get('sub')
            
            # 检查用户是否存在于系统中
            user = User.query.filter_by(auth0_id=auth0_id).first()
            
            # 如果用户不存在，创建新用户
            if not user:
                user = User(
                    auth0_id=auth0_id,
                    email=user_info.get('email'),
                    name=user_info.get('name', ''),
                    email_verified=user_info.get('email_verified', False),
                    auth0_sid=None,
                    auth0_aud=None,
                    auth0_iss=None
                )
                
                try:
                    db.session.add(user)
                    db.session.commit()
                    logger.info(f"新用户登录成功，已创建用户记录: {user.email}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"创建用户记录失败: {str(e)}")
                    return api_error("用户登录异常，请稍后重试", ErrorCode.SYSTEM_ERROR)
            else:
                # 更新用户登录信息 - 只更新email_verified状态，不更新不存在的字段
                user.email_verified = user_info.get('email_verified', user.email_verified)
                
                try:
                    db.session.commit()
                    logger.info(f"用户登录成功: {user.email}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"更新用户信息失败: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接Auth0服务失败: {str(e)}")
            return api_error("无法连接到身份验证服务", ErrorCode.AUTH0_ERROR)
        except Exception as e:
            logger.error(f"Auth0认证请求发生异常: {str(e)}")
            return api_error("认证服务连接失败", ErrorCode.AUTH0_ERROR)
        
        # 创建JWT令牌
        user_claims = {
            "user_id": user.id,
            "auth0_id": user.auth0_id,
            "email": user.email,
            "email_verified": user.email_verified
        }
        
        access_token = create_access_token(identity=user.id, additional_claims=user_claims)
        refresh_token = create_refresh_token(identity=user.id)
        
        # 准备返回数据
        return api_success({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "student_id": user.student_id,
                "email_verified": user.email_verified,
                "major": user.major.name if user.major else None,
                "level": user.level
            },
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(minutes=60)).total_seconds()
        })
        
    except Exception as e:
        logger.error(f"处理登录请求时发生错误: {str(e)}")
        return api_error("处理登录请求时发生错误", ErrorCode.SYSTEM_ERROR)

def _check_verification_cooldown(email):
    """检查验证邮件冷却期
    
    返回:
        tuple: (是否可以发送, 剩余冷却时间秒数)
    """
    now = time.time()
    if email in _last_verification_sent:
        last_sent = _last_verification_sent[email]
        elapsed = now - last_sent
        cooldown = 60  # 1分钟冷却期
        
        if elapsed < cooldown:
            return False, int(cooldown - elapsed)
    
    # 可以发送，更新时间戳
    _last_verification_sent[email] = now
    return True, 0

def api_register():
    """
    用户注册API端点
    
    请求参数:
        email: 用户邮箱(必填)
        password: 用户密码(必填)
        name: 用户姓名(必填)
        student_id: 学号(选填)
        major_id: 专业ID(选填)
        grade: 年级(选填) - 存储在user_metadata中，不在User模型中
        
    返回:
        成功: 返回成功消息
        失败: 返回错误信息
    """
    try:
        logger.info("=== 开始处理注册请求 ===")
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            logger.error("注册失败: 缺少请求参数，请求体为空")
            return api_error(ErrorCode.get_message(ErrorCode.INVALID_INPUT), ErrorCode.INVALID_INPUT)
            
        # 获取和验证必填字段
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        # 记录请求字段（不记录密码）
        logger.info(f"注册请求参数: email={email}, name={name}, 包含student_id={'是' if data.get('student_id') else '否'}, 包含major_id={'是' if data.get('major_id') else '否'}")
        
        if not email or not password or not name:
            logger.error(f"注册失败: 必填字段缺失, email={bool(email)}, password={bool(password)}, name={bool(name)}")
            return api_error(ErrorCode.get_message(ErrorCode.INVALID_INPUT), ErrorCode.INVALID_INPUT)
            
        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            logger.error(f"注册失败: 邮箱格式不正确 {email}")
            return api_error("邮箱格式不正确", ErrorCode.INVALID_INPUT)
            
        # 验证密码强度
        if len(password) < 8:
            logger.error("注册失败: 密码长度不足8位")
            return api_error("密码长度不能少于8位", ErrorCode.INVALID_INPUT)
            
        # 获取选填字段
        student_id = data.get('student_id')
        major_id = data.get('major_id')
        grade = data.get('grade')  # 年级信息只存储在Auth0的user_metadata中，不存储在User模型
                
        # 获取Auth0配置
        domain = current_app.config.get('AUTH0_DOMAIN')
        client_id = current_app.config.get('AUTH0_CLIENT_ID')
        client_secret = current_app.config.get('AUTH0_CLIENT_SECRET')
        audience = current_app.config.get('AUTH0_API_AUDIENCE')
        
        logger.info(f"Auth0配置: domain={domain}, client_id={'已设置' if client_id else '未设置'}")
        
        # 获取Auth0管理API令牌
        token_url = f"https://{domain}/oauth/token"
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": f"https://{domain}/api/v2/",
            "grant_type": "client_credentials"
        }
        token_headers = {"content-type": "application/json"}
        
        logger.info(f"准备获取Auth0管理令牌, URL: {token_url}")
        
        try:
            token_response = requests.post(token_url, json=token_payload, headers=token_headers)
            logger.info(f"Auth0令牌请求响应状态码: {token_response.status_code}")
            
            if token_response.status_code != 200:
                logger.error(f"获取Auth0管理令牌失败: 状态码={token_response.status_code}, 响应={token_response.text[:200]}")
                return api_error(ErrorCode.AUTH0_ERROR, "连接认证服务失败，请稍后重试")
            
            management_api_token = token_response.json().get('access_token')
            logger.info(f"成功获取Auth0管理令牌, 令牌长度: {len(management_api_token) if management_api_token else 0}")
        except Exception as e:
            logger.error(f"请求Auth0令牌时发生异常: {str(e)}")
            return api_error(ErrorCode.AUTH0_ERROR, "连接认证服务失败，请稍后重试")
            
        # 1. 先检查邮箱是否已在Auth0中存在，即使不在本地数据库中
        search_url = f"https://{domain}/api/v2/users-by-email"
        search_headers = {
            "Authorization": f"Bearer {management_api_token}",
            "Content-Type": "application/json"
        }
        search_params = {"email": email}
        
        try:
            search_response = requests.get(search_url, headers=search_headers, params=search_params)
            logger.info(f"搜索Auth0用户响应状态码: {search_response.status_code}")
            
            if search_response.status_code == 200:
                users = search_response.json()
                logger.info(f"Auth0搜索结果: 找到{len(users)}个用户")
                
                if users:
                    # 邮箱已存在于Auth0
                    auth0_user = users[0]
                    auth0_id = auth0_user.get('user_id')
                    email_verified = auth0_user.get('email_verified', False)
                    logger.info(f"邮箱在Auth0中已存在: auth0_id={auth0_id}, 邮箱已验证={email_verified}")
                    
                    # 先检查学号是否已经被其他账号使用
                    existing_student = db.session.query(User).filter_by(student_id=student_id).first()
                    if existing_student:
                        # 如果学号已存在但对应不同邮箱，返回错误
                        if existing_student.email != email:
                            logger.warning(f"学号已被其他邮箱使用: student_id={student_id}, 已存在邮箱={existing_student.email}, 当前邮箱={email}")
                            return api_error(
                                f"学号 {student_id} 已被其他账号使用",
                                ErrorCode.AUTH_STUDENT_ID_EXISTS
                            )
                    
                    # 再检查邮箱是否已存在于本地数据库
                    existing_user = db.session.query(User).filter_by(email=email).first()
                    if existing_user:
                        # 如果用户存在且超过1分钟未验证，则删除重建
                        if not existing_user.email_verified:
                            time_diff = datetime.utcnow() - existing_user.created_at
                            if time_diff.total_seconds() > 60:
                                logger.info(f"删除超时未验证的用户记录: id={existing_user.id}, email={email}, 创建时间={existing_user.created_at}")
                                db.session.delete(existing_user)
                                db.session.commit()
                                # 继续创建新用户的流程
                            else:
                                # 未超时，重新发送验证邮件
                                try:
                                    # 更新学号
                                    if existing_user.student_id != student_id:
                                        existing_user.student_id = student_id
                                        db.session.commit()
                                        logger.info(f"更新用户学号: id={existing_user.id}, 新学号={student_id}")
                                    
                                    # 添加冷却期检查
                                    can_send, cooldown_remaining = _check_verification_cooldown(email)
                                    if not can_send:
                                        logger.info(f"验证邮件发送太频繁: email={email}, 剩余冷却时间={cooldown_remaining}秒")
                                        return api_error(
                                            f"验证邮件发送过于频繁，请{cooldown_remaining}秒后再试",
                                            ErrorCode.RATE_LIMIT_EXCEEDED
                                        )
                                    
                                    send_verification_email(email)
                                    logger.info(f"重新发送验证邮件: email={email}")
                                    return api_success({
                                        "message": "验证邮件已发送，请查收邮箱完成注册",
                                        "auth0_id": auth0_id,
                                        "email": email
                                    })
                                except Exception as e:
                                    logger.error(f"重新发送验证邮件失败: {str(e)}")
                                    return api_error(
                                        "您的账号已注册但尚未验证邮箱，发送验证邮件失败，请稍后在登录页面请求重新发送",
                                        ErrorCode.AUTH_EMAIL_NOT_VERIFIED
                                    )
                        else:
                            # 邮箱已验证，返回已注册信息
                            logger.info(f"邮箱已验证，用户尝试重复注册: email={email}")
                            return api_error(
                                ErrorCode.get_message(ErrorCode.AUTH_USER_ALREADY_EXISTS),
                                ErrorCode.AUTH_USER_ALREADY_EXISTS
                            )
                    
                    # 用户存在于Auth0但不在本地数据库
                    if email_verified:
                        # 邮箱已验证，创建本地用户并关联
                        try:
                            logger.info(f"创建本地用户并关联已验证Auth0账号: email={email}, auth0_id={auth0_id}")
                            user = User(
                                auth0_id=auth0_id,
                                email=email,
                                name=name,
                                student_id=student_id,
                                email_verified=True,
                                auth0_sid=None,
                                auth0_aud=None,
                                auth0_iss=None,
                                created_at=datetime.utcnow(),
                                status='active'
                            )
                            db.session.add(user)
                            db.session.commit()
                            
                            # 创建用户画像
                            user_profile = UserProfile(user_id=user.id)
                            db.session.add(user_profile)
                            db.session.commit()
                            
                            logger.info(f"关联已验证Auth0账号成功: id={user.id}, email={email}")
                            return api_success(
                                message="您的账号已成功关联学号，请使用邮箱和密码登录",
                                data={
                                    "user_id": user.id,
                                    "auth0_id": auth0_id,
                                    "email": email
                                }
                            )
                        except SQLAlchemyError as e:
                            db.session.rollback()
                            logger.error(f"数据库错误(创建用户)：{str(e)}")
                            logger.error(f"错误类型：{type(e).__name__}")
                            if hasattr(e, 'orig') and e.orig:
                                logger.error(f"原始错误：{str(e.orig)}")
                            return api_error(
                                "注册失败，数据库操作错误", 
                                ErrorCode.DB_ERROR,
                                data={"error": "database_error"}
                            )
                    else:
                        # 邮箱在Auth0中但未验证，创建本地用户并发送验证邮件
                        try:
                            logger.info(f"创建本地用户并关联未验证Auth0账号: email={email}, auth0_id={auth0_id}")
                            new_user = User(
                                auth0_id=auth0_id,
                                email=email,
                                name=name,
                                student_id=student_id,
                                email_verified=False,
                                auth0_sid=None,
                                auth0_aud=None,
                                auth0_iss=None,
                                created_at=datetime.utcnow(),
                                status='active'
                            )
                            db.session.add(new_user)
                            db.session.commit()
                            
                            # 创建用户画像
                            user_profile = UserProfile(user_id=new_user.id)
                            db.session.add(user_profile)
                            db.session.commit()
                            
                            logger.info(f"关联未验证Auth0账号并创建本地用户成功: id={new_user.id}, email={email}")
                            
                            # 发送验证邮件
                            try:
                                # 添加冷却期检查
                                can_send, cooldown_remaining = _check_verification_cooldown(email)
                                if not can_send:
                                    logger.info(f"验证邮件发送太频繁: email={email}, 剩余冷却时间={cooldown_remaining}秒")
                                    return api_success({
                                        "user_id": new_user.id,
                                        "auth0_id": auth0_id,
                                        "email": email,
                                        "message": f"注册成功，但验证邮件发送过于频繁，请{cooldown_remaining}秒后在登录页面请求重新发送"
                                    })
                                
                                send_verification_email(email)
                                logger.info(f"发送验证邮件成功: {email}")
                                return api_success(
                                    message="验证邮件已发送，请查收邮箱完成注册",
                                    data={
                                        "auth0_id": auth0_id,
                                        "email": email
                                    }
                                )
                            except Exception as e:
                                logger.warning(f"发送验证邮件失败: {str(e)}")
                                return api_success({
                                    "user_id": new_user.id,
                                    "auth0_id": auth0_id,
                                    "email": email,
                                    "message": "注册成功，但发送验证邮件失败，请稍后在登录页面请求重新发送"
                                })
                        except SQLAlchemyError as e:
                            db.session.rollback()
                            logger.error(f"数据库错误(创建用户)：{str(e)}")
                            logger.error(f"错误类型：{type(e).__name__}")
                            if hasattr(e, 'orig') and e.orig:
                                logger.error(f"原始错误：{str(e.orig)}")
                            return api_error(
                                "注册失败，数据库操作错误", 
                                ErrorCode.DB_ERROR,
                                data={"error": "database_error"}
                            )
        except Exception as e:
            logger.error(f"检查Auth0用户时发生异常: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return api_error(ErrorCode.AUTH0_ERROR, "连接认证服务失败，请稍后重试")
        
        # 检查学号是否已存在(如果提供了学号)
        if student_id:
            try:
                existing_student = User.query.filter_by(student_id=student_id).first()
                if existing_student:
                    logger.warning(f"注册失败: 学号已存在 {student_id}")
                    return api_error(ErrorCode.AUTH_STUDENT_ID_EXISTS, "该学号已被其他账号使用，请确认您的学号")
            except Exception as db_error:
                logger.error(f"查询学号时发生错误: {str(db_error)}")
                if hasattr(db_error, 'orig'):
                    logger.error(f"数据库原始错误: {str(db_error.orig)}")
                return api_error(ErrorCode.DB_ERROR, "数据库查询失败，请稍后重试")
                
        # 检查邮箱是否已存在于本地数据库
        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                logger.warning(f"注册失败: 邮箱已存在于本地数据库 {email}")
                # 如果用户邮箱验证状态为False，主动发送验证邮件
                if not existing_user.email_verified:
                    try:
                        send_verification_email(email)
                        logger.info(f"重新发送验证邮件成功: {email}")
                        return api_error(ErrorCode.AUTH_EMAIL_EXISTS, "该邮箱已注册但未验证，已重新发送验证邮件，请查收")
                    except Exception as e:
                        logger.error(f"重新发送验证邮件失败: {str(e)}")
                return api_error(ErrorCode.AUTH_EMAIL_EXISTS, "该邮箱已注册，请直接登录")
        except Exception as db_error:
            logger.error(f"查询邮箱时发生错误: {str(db_error)}")
            if hasattr(db_error, 'orig'):
                logger.error(f"数据库原始错误: {str(db_error.orig)}")
            return api_error(ErrorCode.DB_ERROR, "数据库查询失败，请稍后重试")
                
        # 检查专业是否存在(如果提供了专业ID)
        if major_id:
            try:
                major = Major.query.get(major_id)
                if not major:
                    logger.warning(f"注册失败: 专业不存在 {major_id}")
                    return api_error(ErrorCode.NOT_FOUND, "指定的专业不存在")
            except Exception as db_error:
                logger.error(f"查询专业时发生错误: {str(db_error)}")
                if hasattr(db_error, 'orig'):
                    logger.error(f"数据库原始错误: {str(db_error.orig)}")
                return api_error(ErrorCode.DB_ERROR, "数据库查询失败，请稍后重试")
        
        # 在Auth0中创建用户
        user_url = f"https://{domain}/api/v2/users"
        user_headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {management_api_token}"
        }
        user_payload = {
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication",
            "email_verified": False,
            "name": name,
            "user_metadata": {
                "student_id": student_id,
                "major_id": major_id,
                "grade": grade
            }
        }
        
        logger.info(f"准备在Auth0中创建用户: email={email}, name={name}")
        
        try:
            user_response = requests.post(user_url, json=user_payload, headers=user_headers)
            logger.info(f"Auth0创建用户响应状态码: {user_response.status_code}")
            
            # 处理Auth0创建用户响应
            if user_response.status_code != 201:
                error_data = user_response.json()
                error_message = error_data.get('message', '注册失败')
                logger.error(f"在Auth0中创建用户失败: 状态码={user_response.status_code}, 响应={user_response.text[:200]}")
                
                # 处理特定错误
                if "PasswordStrengthError" in error_message:
                    logger.warning(f"注册失败: 密码强度不足 {email}")
                    return api_error(ErrorCode.INVALID_INPUT, "密码强度不足，请包含大小写字母、数字和特殊字符")
                elif "already exists" in error_message:
                    return api_error(ErrorCode.get_message(ErrorCode.AUTH_EMAIL_EXISTS), ErrorCode.AUTH_EMAIL_EXISTS)
                else:
                    return api_error(ErrorCode.AUTH0_ERROR, f"创建账号失败: {error_message}")
        except Exception as e:
            logger.error(f"请求Auth0创建用户API时发生异常: {str(e)}")
            return api_error(ErrorCode.AUTH0_ERROR, "连接认证服务失败，请稍后重试")
        
        # 获取Auth0用户信息
        auth0_user = user_response.json()
        auth0_id = auth0_user.get('user_id')
        logger.info(f"Auth0创建用户成功: auth0_id={auth0_id}")
        
        # 创建本地用户记录
        try:
            logger.info(f"准备创建本地用户记录：email={email}, auth0_id={auth0_id}")
            new_user = User(
                auth0_id=auth0_id,
                email=email,
                name=name,
                student_id=student_id,
                email_verified=False,
                # 显式设置这些字段为None，避免SQLAlchemy尝试自动处理
                auth0_sid=None,
                auth0_aud=None,
                auth0_iss=None,
                created_at=datetime.utcnow(),
                status='active'
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"本地用户记录创建成功：ID={new_user.id}")
            
            # 创建用户画像记录
            logger.info(f"准备创建用户画像记录")
            user_profile = UserProfile(user_id=new_user.id)
            db.session.add(user_profile)
            db.session.commit()
            logger.info(f"用户画像记录创建成功")
            
            # 注册成功后发送验证邮件
            try:
                # 添加冷却期检查
                can_send, cooldown_remaining = _check_verification_cooldown(email)
                if not can_send:
                    logger.info(f"验证邮件发送太频繁: email={email}, 剩余冷却时间={cooldown_remaining}秒")
                    return api_success({
                        "user_id": new_user.id,
                        "auth0_id": auth0_id,
                        "email": email,
                        "message": f"注册成功，但验证邮件发送过于频繁，请{cooldown_remaining}秒后在登录页面请求重新发送"
                    })
                
                send_verification_email(email)
                logger.info(f"发送验证邮件成功: {email}")
                return api_success(
                    message="验证邮件已发送，请查收邮箱完成注册",
                    data={
                        "auth0_id": auth0_id,
                        "email": email
                    }
                )
            except Exception as e:
                logger.warning(f"发送验证邮件失败: {str(e)}")
                return api_success({
                    "user_id": new_user.id,
                    "auth0_id": auth0_id,
                    "email": email,
                    "message": "注册成功，但发送验证邮件失败，请稍后在登录页面请求重新发送"
                })
        except SQLAlchemyError as e:
            db.session.rollback()
            # 添加详细错误日志
            logger.error(f"数据库错误(创建用户)：{str(e)}")
            logger.error(f"错误类型：{type(e).__name__}")
            if hasattr(e, 'orig') and e.orig:
                logger.error(f"原始错误：{str(e.orig)}")
            
            # 删除Auth0用户，因为本地数据库创建失败
            try:
                # 这里添加删除Auth0用户的代码
                logger.info(f"尝试删除Auth0用户: {auth0_id}")
                # delete_auth0_user(auth0_id)
            except Exception as del_err:
                logger.error(f"删除Auth0用户失败: {str(del_err)}")
            
            return api_error(
                "注册失败，数据库操作错误", 
                ErrorCode.DB_ERROR,
                data={"error": "database_error"}
            )
            
        # 返回成功信息
        logger.info(f"注册流程完成: {email}")
        return api_success({
            "user_id": new_user.id,
            "auth0_id": auth0_id,
            "email": email,
            "message": "注册成功，请查收验证邮件完成注册"
        })
        
    except Exception as e:
        logger.error(f"处理注册请求时发生错误: {str(e)}")
        # 如果是操作错误，记录详细信息
        if hasattr(e, 'orig'):
            logger.error(f"数据库原始错误: {str(e.orig)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return api_error("处理注册请求时发生错误", ErrorCode.SYSTEM_ERROR)

    except SQLAlchemyError as e:
        db.session.rollback()
        # 添加详细错误日志
        logger.error(f"数据库错误：{str(e)}")
        logger.error(f"错误类型：{type(e).__name__}")
        # 对于某些特定错误类型，提供更多信息
        if hasattr(e, 'orig') and e.orig:
            logger.error(f"原始错误：{str(e.orig)}")
        if hasattr(e, 'params') and e.params:
            logger.error(f"参数：{str(e.params)}")
            
        return api_error(
            "注册失败，数据库操作错误",
            ErrorCode.DB_ERROR,
            data={"error": "database_error"}
        ) 