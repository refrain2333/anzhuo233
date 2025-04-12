"""
用户信息管理API
"""
from flask import Blueprint, jsonify, request, session
from app.utils.auth import requires_auth, requires_verified_email, requires_admin
from app.models.user import User, UserProfile, Major
from app.schemas.user import user_schema, users_schema, user_update_schema, major_schema, majors_schema
from sqlalchemy.exc import SQLAlchemyError
from app import db
import logging

# 创建蓝图
user_bp = Blueprint('user', __name__)

# 从check.py导入函数
from app.api.v1.user.check import check_student_id_exists

# 注册学号检查接口
user_bp.route('/check', methods=['GET'])(check_student_id_exists)

@user_bp.route("/profile", methods=["GET"])
@requires_auth
def get_profile():
    """获取当前用户的个人资料"""
    logger = logging.getLogger(__name__)
    
    # 尝试从JWT令牌中获取用户信息
    try:
        jwt_user_id = get_jwt_identity()
        if jwt_user_id:
            logger.info(f"从JWT令牌中获取到用户ID: {jwt_user_id}")
            user = User.query.get(jwt_user_id)
            if user:
                logger.info(f"通过JWT令牌找到用户: {user.name}")
                result = user_schema.dump(user)
                return jsonify(result)
    except Exception as e:
        logger.info(f"从JWT获取用户失败，尝试会话方式: {str(e)}")
    
    # 如果无法从JWT获取，则尝试从会话获取
    user_info = session.get('user', {}).get('userinfo', {})
    auth0_id = user_info.get('sub')
    
    if not auth0_id:
        logger.warning("无法从JWT或会话中获取用户信息")
        return jsonify({"error": "无法获取用户信息"}), 400
    
    # 查询用户
    user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user:
        logger.warning(f"用户不存在: {auth0_id}")
        return jsonify({"error": "用户不存在"}), 404
    
    # 序列化用户数据
    result = user_schema.dump(user)
    return jsonify(result)

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
    
    query = User.query
    
    # 如果有搜索条件
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%')) | 
            (User.student_id.ilike(f'%{search}%'))
        )
    
    # 执行分页查询
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return jsonify({
        'users': users_schema.dump(users),
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

@user_bp.route("/admin/users/<int:id>", methods=["GET"])
@requires_auth
@requires_admin
def admin_get_user(id):
    """获取指定用户信息（管理员权限）"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify(user_schema.dump(user))

@user_bp.route("/admin/users/<int:id>", methods=["PUT"])
@requires_auth
@requires_admin
def admin_update_user(id):
    """更新指定用户信息（管理员权限）"""
    user = User.query.get(id)
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
        return jsonify({"message": "用户信息更新成功", "user": user_schema.dump(user)})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500

@user_bp.route("/admin/users/<int:id>", methods=["DELETE"])
@requires_auth
@requires_admin
def admin_delete_user(id):
    """删除指定用户（管理员权限）"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "用户删除成功"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500 