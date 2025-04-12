"""
基于Auth0的认证API
"""
from flask import Blueprint, redirect, render_template, session, url_for, request, jsonify, current_app, flash
from app.utils.auth import requires_auth, resend_verification_email, generate_auth0_logout_url
from urllib.parse import urlencode
from authlib.integrations.flask_client import OAuth
from app import db
from app.models.user import User, UserProfile
import json

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 初始化OAuth
oauth = OAuth()

# Auth0配置函数
def setup_auth0(app):
    oauth.init_app(app)
    
    # 配置基本的 Auth0 参数
    oauth.register(
        "auth0",
        client_id=app.config["AUTH0_CLIENT_ID"],
        client_secret=app.config["AUTH0_CLIENT_SECRET"],
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration',
        # 临时解决方案：关闭 state 验证
        enforce_state=False
    )

@auth_bp.route("/")
def index():
    """首页"""
    return render_template(
        "auth/home.html", 
        session=session.get('user'), 
        pretty=json.dumps(session.get('user'), indent=4)
    )

@auth_bp.route("/login")
def login():
    """登录页面"""
    # 为了确保Auth0回调正常工作，让我们简化这个流程
    # 清除旧会话数据
    session.clear()
    
    # 重定向到Auth0登录页面
    return oauth.auth0.authorize_redirect(
        redirect_uri=current_app.config["AUTH0_CALLBACK_URL"]
    )

@auth_bp.route("/callback", methods=["GET", "POST"])
def callback():
    """Auth0回调处理"""
    try:
        # 尝试获取访问令牌
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        
        # 获取用户信息
        user_info = token.get('userinfo', {})
        
        # 检查用户是否存在于数据库
        auth0_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        if not auth0_id:
            flash('无法获取用户ID，请重新登录', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(auth0_id=auth0_id).first()
        
        if not user:
            # 创建新用户
            user = User(
                auth0_id=auth0_id,
                email=email,
                email_verified=user_info.get('email_verified', False),
                name=name,
                student_id=f"temp_{auth0_id[-8:]}",  # 临时学号，用户需要后续设置
                avatar_url=user_info.get('picture')
            )
            
            # 创建用户画像
            profile = UserProfile(user=user)
            
            try:
                db.session.add(user)
                db.session.add(profile)
                db.session.commit()
                flash('账号创建成功，请完善个人信息', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'创建用户失败: {str(e)}', 'danger')
                return redirect(url_for('auth.index'))
            
            # 提示用户完善信息
            flash('请完善您的个人信息，特别是学号', 'warning')
            return redirect(url_for('auth.profile_edit'))
        
        # 检查邮箱验证状态
        if 'email_verified' in user_info and not user_info['email_verified']:
            flash('请验证您的邮箱以完成注册', 'warning')
        
        return redirect(url_for('auth.index'))
    
    except Exception as e:
        # 处理各种可能的异常
        flash(f'登录过程中出现错误: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route("/logout")
def logout():
    """退出登录"""
    session.clear()
    return redirect(generate_auth0_logout_url())

@auth_bp.route("/profile")
@requires_auth
def profile():
    """用户个人资料页面"""
    return render_template("auth/profile.html", user=session.get('user'))

@auth_bp.route("/profile/edit")
@requires_auth
def profile_edit():
    """编辑个人资料页面"""
    user_info = session.get('user', {}).get('userinfo', {})
    auth0_id = user_info.get('sub')
    
    if not auth0_id:
        flash('无法获取用户信息', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 从数据库获取用户信息
    user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('auth.profile'))
    
    return render_template("auth/profile_edit.html", user=user)

@auth_bp.route("/profile/update", methods=["POST"])
@requires_auth
def profile_update():
    """更新个人资料"""
    user_info = session.get('user', {}).get('userinfo', {})
    auth0_id = user_info.get('sub')
    
    if not auth0_id:
        flash('无法获取用户信息', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 从数据库获取用户信息
    user = User.query.filter_by(auth0_id=auth0_id).first()
    
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 更新用户信息
    user.student_id = request.form.get('student_id', user.student_id)
    user.name = request.form.get('name', user.name)
    user.bio = request.form.get('bio', user.bio)
    
    # 处理major_id字段，空字符串转为None
    major_id = request.form.get('major_id', '')
    if major_id == '':
        user.major_id = None
    else:
        user.major_id = int(major_id)
    
    # 更新用户画像
    if user.profile:
        # 处理学习风格字段，空字符串转为None
        learning_style = request.form.get('learning_style', '')
        if learning_style == '':
            user.profile.learning_style = None
        else:
            user.profile.learning_style = learning_style
        
        # 处理偏好学习时间字段，空字符串转为None
        preferred_time = request.form.get('preferred_time', '')
        if preferred_time == '':
            user.profile.preferred_time = None
        else:
            user.profile.preferred_time = preferred_time
            
        user.profile.strengths = request.form.get('strengths', user.profile.strengths)
        user.profile.weaknesses = request.form.get('weaknesses', user.profile.weaknesses)
        user.profile.study_habits = request.form.get('study_habits', user.profile.study_habits)
        
        # 布尔值处理
        user.profile.notification_email_enabled = 'notification_email_enabled' in request.form
        user.profile.notification_app_enabled = 'notification_app_enabled' in request.form
    
    try:
        db.session.commit()
        flash('个人资料更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'保存个人资料失败: {str(e)}', 'danger')
        
    return redirect(url_for('auth.profile'))

@auth_bp.route("/resend-verification")
@requires_auth
def resend_verification():
    """重新发送验证邮件"""
    user_info = session.get('user', {}).get('userinfo', {})
    auth0_id = user_info.get('sub')
    
    if not auth0_id:
        flash('无法获取用户信息', 'danger')
        return redirect(url_for('auth.profile'))
    
    try:
        result = resend_verification_email(auth0_id)
        flash('验证邮件已重新发送，请查收', 'success')
    except Exception as e:
        flash(f'验证邮件发送失败: {str(e)}', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route("/api/v1/auth/status")
def auth_status():
    """获取认证状态API"""
    if 'user' in session:
        return jsonify({
            'authenticated': True,
            'user': session['user'].get('userinfo', {})
        })
    else:
        return jsonify({
            'authenticated': False
        }) 