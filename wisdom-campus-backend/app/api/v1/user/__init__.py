"""
用户信息管理API
"""
from flask import Blueprint, jsonify, request, session, current_app
from app.utils.auth import requires_auth, requires_verified_email, requires_admin
from app.models.user import User, UserProfile, Major
from app.schemas.user import user_schema, users_schema, user_update_schema, major_schema, majors_schema
from sqlalchemy.exc import SQLAlchemyError
from app import db
import logging
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, get_jwt
import requests
from datetime import datetime
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

# 创建蓝图
user_bp = Blueprint('user', __name__)

# 初始化日志
logger = logging.getLogger(__name__)

# 从check.py导入函数
from app.api.v1.user.check import check_student_id_exists

# 注册学号检查接口
user_bp.route('/check', methods=['GET'])(check_student_id_exists)

@user_bp.route("/profile", methods=["GET"])
@requires_auth
def get_profile():
    """获取当前用户的个人资料"""
    logger.info("请求用户资料API")
    
    # 首先尝试获取JWT令牌中的用户ID
    try:
        # 尝试验证JWT（如果令牌失效会引发异常）
        verify_jwt_in_request(optional=True)
        
        # 获取令牌中的用户ID（可能是字符串形式）
        user_id = get_jwt_identity()
        logger.info(f"从JWT获取到用户ID: {user_id} (类型: {type(user_id).__name__})")
        
        # 将字符串ID转换为整数（如果是字符串）
        if isinstance(user_id, str):
            # 如果是数字字符串，则转换为整数
            if user_id.isdigit():
                user_id = int(user_id)
                logger.info(f"将字符串用户ID转换为整数: {user_id}")
            else:
                # 非数字字符串，可能是auth0_id
                logger.info(f"使用非数字字符串用户ID: {user_id}")
                user = User.query.filter_by(auth0_id=user_id).first()
                if user:
                    logger.info(f"通过auth0_id找到用户: {user.name}")
                    user_id = user.id  # 获取数据库中的用户ID
        
        # 查询用户（如果上面没有通过auth0_id找到）
        if 'user' not in locals() or user is None:
            user = User.query.get(user_id)
        
        if user:
            logger.info(f"通过JWT找到用户: {user.name}")
            # 返回用户信息，放在data属性中以保持一致的API格式
            return jsonify({
                "success": True,
                "message": "成功获取用户资料",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "student_id": user.student_id,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio,
                    "gpa": float(user.gpa) if user.gpa else None,
                    "level": user.level,
                    "exp_points": user.exp_points,
                    "total_study_time": user.total_study_time,
                    "email_verified": user.email_verified,
                    "status": user.status
                }
            })
        else:
            logger.warning(f"找不到用户，ID: {user_id}")
    except Exception as e:
        logger.warning(f"获取JWT信息失败: {str(e)}")
    
    # 备选方案：尝试从会话中获取
    try:
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                logger.info(f"从会话中找到用户: {user.name}")
                # 返回用户信息，放在data属性中以保持一致的API格式
                return jsonify({
                    "success": True,
                    "message": "成功获取用户资料",
                    "data": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "student_id": user.student_id,
                        "avatar_url": user.avatar_url,
                        "bio": user.bio,
                        "gpa": float(user.gpa) if user.gpa else None,
                        "level": user.level,
                        "exp_points": user.exp_points,
                        "total_study_time": user.total_study_time,
                        "email_verified": user.email_verified,
                        "status": user.status
                    }
                })
            else:
                logger.warning(f"从会话中找不到用户，ID: {user_id}")
    except Exception as e:
        logger.error(f"从会话获取用户信息失败: {str(e)}")
    
    # 如果都失败了，返回错误
    return jsonify({
        "success": False,
        "message": "未授权，无法获取用户资料，请重新登录"
    }), 401

@user_bp.route("/profile", methods=["PUT"])
@requires_auth
def update_profile():
    """更新当前用户的个人资料"""
    user_info = session.get('user', {}).get('userinfo', {})
    auth0_id = user_info.get('sub')
    
    if not auth0_id:
        return jsonify({"error": "无法获取用户信息"}), 400
    
    # 查询用户
    user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    # 验证和解析请求数据
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "未提供有效的JSON数据"}), 400
    
    try:
        data = user_update_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    # 更新用户信息
    if 'name' in data:
        user.name = data['name']
    if 'bio' in data:
        user.bio = data['bio']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    if 'major_id' in data:
        user.major_id = data['major_id']
    
    # 更新用户画像
    if not user.profile:
        user.profile = UserProfile(user=user)
    
    profile = user.profile
    if 'learning_style' in data:
        profile.learning_style = data['learning_style']
    if 'preferred_time' in data:
        profile.preferred_time = data['preferred_time']
    if 'avg_focus_duration' in data:
        profile.avg_focus_duration = data['avg_focus_duration']
    if 'strengths' in data:
        profile.strengths = data['strengths']
    if 'weaknesses' in data:
        profile.weaknesses = data['weaknesses']
    if 'study_habits' in data:
        profile.study_habits = data['study_habits']
    if 'notification_email_enabled' in data:
        profile.notification_email_enabled = data['notification_email_enabled']
    if 'notification_app_enabled' in data:
        profile.notification_app_enabled = data['notification_app_enabled']
    if 'notification_types' in data:
        profile.notification_types = data['notification_types']
    
    try:
        db.session.commit()
        return jsonify({"message": "个人资料更新成功", "user": user_schema.dump(user)})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500

@user_bp.route("/majors", methods=["GET"])
def get_majors():
    """获取所有专业列表"""
    majors = Major.query.all()
    return jsonify(majors_schema.dump(majors))

@user_bp.route("/majors/<int:id>", methods=["GET"])
def get_major(id):
    """获取指定专业信息"""
    major = Major.query.get(id)
    if not major:
        return jsonify({"error": "专业不存在"}), 404
    return jsonify(major_schema.dump(major))

@user_bp.route("/check-student-id", methods=["POST"])
@requires_auth
def check_student_id():
    """检查学号是否可用"""
    data = request.get_json()
    if not data or 'student_id' not in data:
        return jsonify({"error": "未提供学号"}), 400
    
    student_id = data['student_id']
    
    # 检查学号格式
    if not student_id.isdigit():
        return jsonify({"valid": False, "message": "学号必须全部是数字"})
    
    # 检查学号是否已被使用
    user_info = session.get('user', {}).get('userinfo', {})
    auth0_id = user_info.get('sub')
    
    # 查询除了当前用户以外是否有其他用户使用了这个学号
    user = User.query.filter(User.student_id == student_id, User.auth0_id != auth0_id).first()
    
    if user:
        return jsonify({"valid": False, "message": "学号已被使用"})
    
    return jsonify({"valid": True, "message": "学号可用"})

# 管理员API
@user_bp.route("/admin/users", methods=["GET"])
@requires_auth
@requires_admin
def admin_get_users():
    """获取所有用户列表（管理员权限）"""
    # 支持分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 支持搜索
    search = request.args.get('search', '')
    keyword = request.args.get('keyword', search)  # 兼容前端使用keyword参数
    
    query = User.query
    
    # 如果有搜索条件
    if keyword:
        query = query.filter(
            (User.name.ilike(f'%{keyword}%')) | 
            (User.email.ilike(f'%{keyword}%')) | 
            (User.student_id.ilike(f'%{keyword}%'))
        )
    
    # 执行分页查询
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    # 对用户数据进行处理，添加专业名称等信息
    user_data = []
    for user in users:
        user_info = user_schema.dump(user)
        # 添加专业名称
        if user.major_id:
            major = Major.query.get(user.major_id)
            user_info['major_name'] = major.name if major else None
        else:
            user_info['major_name'] = None
        user_data.append(user_info)
    
    return api_success(data={
        'users': user_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

@user_bp.route("/admin/users", methods=["POST"])
@requires_auth
@requires_admin
def admin_create_user():
    """创建新用户（管理员权限）"""
    # 验证请求数据
    if not request.is_json:
        return api_error(
            message="请求必须是JSON格式",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    json_data = request.get_json()
    
    # 验证必要参数
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if field not in json_data or not json_data[field]:
            return api_error(
                message=f"缺少必要参数: {field}",
                error_code=ErrorCode.INVALID_REQUEST
            )
    
    name = json_data.get('name')
    email = json_data.get('email')
    password = json_data.get('password')
    student_id = json_data.get('student_id')
    major_id = json_data.get('major_id')
    
    # 检查邮箱是否已存在
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return api_error(
            message="此邮箱已被使用",
            error_code=ErrorCode.USER_ALREADY_EXISTS
        )
    
    # 如果提供了学号，检查学号是否已存在
    if student_id:
        existing_student = User.query.filter_by(student_id=student_id).first()
        if existing_student:
            return api_error(
                message="此学号已被使用",
                error_code=ErrorCode.USER_ALREADY_EXISTS
            )
    
    # 通过Auth0创建用户
    try:
        from app.api.v1.auth.utils import get_auth0_token
        
        token = get_auth0_token()
        if not token:
            return api_error(
                message="无法获取认证令牌",
                error_code=ErrorCode.AUTH0_API_ERROR
            )
        
        domain = current_app.config.get('AUTH0_DOMAIN')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        user_metadata = {
            "name": name,
            "student_id": student_id,
            "major_id": major_id
        }
        
        # 构建Auth0请求数据
        auth0_data = {
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication",
            "email_verified": True,  # 管理员创建的用户自动验证邮箱
            "user_metadata": user_metadata
        }
        
        # 创建Auth0用户
        url = f"https://{domain}/api/v2/users"
        response = requests.post(url, headers=headers, json=auth0_data)
        
        if response.status_code != 201:
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
            auth0_id=auth0_id,
            email_verified=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 管理员创建的用户如果指定为管理员，则设置is_admin为True
        if json_data.get('is_admin'):
            new_user.is_admin = True
        
        db.session.add(new_user)
        db.session.commit()
        
        # 获取专业名称
        major_name = None
        if major_id:
            major = Major.query.get(major_id)
            major_name = major.name if major else None
        
        user_data = user_schema.dump(new_user)
        user_data['major_name'] = major_name
        
        return api_success(
            message="用户创建成功",
            data={
                'user': user_data
            }
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建用户时发生错误: {str(e)}")
        return api_error(
            message=f"创建用户时发生错误: {str(e)}",
            error_code=ErrorCode.SERVER_ERROR
        )

@user_bp.route("/admin/users/<int:id>", methods=["GET"])
@requires_auth
@requires_admin
def admin_get_user(id):
    """获取指定用户信息（管理员权限）"""
    user = User.query.get(id)
    if not user:
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    user_data = user_schema.dump(user)
    # 添加专业名称
    if user.major_id:
        major = Major.query.get(user.major_id)
        user_data['major_name'] = major.name if major else None
    else:
        user_data['major_name'] = None
    
    return api_success(data={
        'user': user_data
    })

@user_bp.route("/admin/users/<int:id>", methods=["PUT"])
@requires_auth
@requires_admin
def admin_update_user(id):
    """更新指定用户信息（管理员权限）"""
    user = User.query.get(id)
    if not user:
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    # 验证和解析请求数据
    if not request.is_json:
        return api_error(
            message="请求必须是JSON格式",
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    json_data = request.get_json()
    
    # 更新用户信息
    if 'name' in json_data:
        user.name = json_data['name']
    if 'student_id' in json_data:
        # 检查学号是否已存在
        if json_data['student_id'] != user.student_id:
            existing_student = User.query.filter_by(student_id=json_data['student_id']).first()
            if existing_student:
                return api_error(
                    message="此学号已被使用",
                    error_code=ErrorCode.USER_ALREADY_EXISTS
                )
        user.student_id = json_data['student_id']
    if 'email' in json_data:
        # 检查邮箱是否已存在
        if json_data['email'] != user.email:
            existing_email = User.query.filter_by(email=json_data['email']).first()
            if existing_email:
                return api_error(
                    message="此邮箱已被使用",
                    error_code=ErrorCode.USER_ALREADY_EXISTS
                )
        user.email = json_data['email']
    if 'major_id' in json_data:
        user.major_id = json_data['major_id']
    if 'bio' in json_data:
        user.bio = json_data['bio']
    if 'avatar_url' in json_data:
        user.avatar_url = json_data['avatar_url']
    if 'is_admin' in json_data:
        user.is_admin = json_data['is_admin']
    
    # 更新用户画像
    if 'profile' in json_data:
        profile_data = json_data['profile']
        if not user.profile:
            user.profile = UserProfile(user=user)
        
        profile = user.profile
        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
    
    # 如果提供了密码，更新Auth0密码
    if 'password' in json_data and json_data['password']:
        try:
            from app.api.v1.auth.utils import get_auth0_token
            
            token = get_auth0_token()
            if token:
                domain = current_app.config.get('AUTH0_DOMAIN')
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # 更新Auth0密码
                password_data = {
                    "password": json_data['password'],
                    "connection": "Username-Password-Authentication"
                }
                
                url = f"https://{domain}/api/v2/users/{user.auth0_id}"
                response = requests.patch(url, headers=headers, json=password_data)
                
                if response.status_code != 200:
                    logger.error(f"更新用户密码失败: {response.text}")
                    # 不返回错误，继续更新其他字段
        except Exception as e:
            logger.error(f"更新用户密码时发生错误: {str(e)}")
            # 不返回错误，继续更新其他字段
    
    try:
        user.updated_at = datetime.now()
        db.session.commit()
        
        # 获取专业名称
        major_name = None
        if user.major_id:
            major = Major.query.get(user.major_id)
            major_name = major.name if major else None
        
        user_data = user_schema.dump(user)
        user_data['major_name'] = major_name
        
        return api_success(
            message="用户信息更新成功",
            data={
                'user': user_data
            }
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"更新用户信息时发生数据库错误: {str(e)}")
        return api_error(
            message=f"数据库错误: {str(e)}",
            error_code=ErrorCode.DB_ERROR
        )

@user_bp.route("/admin/users/<int:id>", methods=["DELETE"])
@requires_auth
@requires_admin
def admin_delete_user(id):
    """删除指定用户（管理员权限）"""
    user = User.query.get(id)
    if not user:
        return api_error(
            message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    try:
        # 删除Auth0用户
        try:
            from app.api.v1.auth.utils import get_auth0_token, delete_auth0_user
            
            if user.auth0_id:
                token = get_auth0_token()
                if token:
                    delete_auth0_user(user.auth0_id)
        except Exception as e:
            logger.error(f"删除Auth0用户时发生错误: {str(e)}")
            # 继续删除本地用户
        
        # 删除本地用户
        db.session.delete(user)
        db.session.commit()
        
        return api_success(
            message="用户删除成功"
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"删除用户时发生数据库错误: {str(e)}")
        return api_error(
            message=f"数据库错误: {str(e)}",
            error_code=ErrorCode.DB_ERROR
        ) 