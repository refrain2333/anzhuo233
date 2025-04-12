"""
用户认证模块 API 蓝图

包含用户注册、登录、验证、资料管理等功能
"""
import logging
from flask import Blueprint, current_app, render_template, jsonify, request

# 创建认证蓝图
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# 配置日志
logger = logging.getLogger(__name__)

# 导入子模块函数
from app.api.v1.auth.authentication import api_login, api_register
from app.api.v1.auth.sessions import api_refresh_token, api_logout, verify_token
from app.api.v1.auth.profile import api_get_user_profile, api_update_user_profile, api_update_avatar
from app.api.v1.auth.verification import api_send_verification_email, api_check_verification, cleanup_unverified_users
from app.api.v1.auth.email_verification import api_resend_verification, check_email_verification
from app.api.v1.auth.password import api_forgot_password, api_change_password
from app.api.v1.auth.register import cancel_registration
from app.api.v1.auth.setup import setup_auth0

# 注册路由
# 登录注册相关
auth_bp.route("/login", methods=["POST"])(api_login)
auth_bp.route("/register", methods=["POST"])(api_register)
auth_bp.route("/logout", methods=["POST"])(api_logout)
auth_bp.route("/refresh-token", methods=["POST"])(api_refresh_token)
auth_bp.route("/verify-token", methods=["GET"])(verify_token)

# 邮箱验证相关
auth_bp.route("/send-verification", methods=["POST"])(api_send_verification_email)
auth_bp.route("/check-verification", methods=["POST", "GET"])(api_check_verification)
auth_bp.route("/resend-verification", methods=["POST"])(api_resend_verification)

# 用户资料相关
auth_bp.route("/profile", methods=["GET"])(api_get_user_profile)
auth_bp.route("/profile", methods=["PUT", "PATCH"])(api_update_user_profile)
auth_bp.route("/update-avatar", methods=["POST"])(api_update_avatar)

# 密码管理相关
auth_bp.route("/forgot-password", methods=["POST"])(api_forgot_password)
auth_bp.route("/change-password", methods=["POST"])(api_change_password)

# 账号管理相关
auth_bp.route("/cancel-registration", methods=["POST"])(cancel_registration)
auth_bp.route("/cleanup-unverified", methods=["POST"])(cleanup_unverified_users)

# 注册验证等待页面路由
@auth_bp.route("/verify-waiting-status", methods=["GET"])
def verification_waiting_status():
    """验证等待页面API端点，返回验证状态的JSON信息"""
    auth0_id = request.args.get('auth0_id')
    email = request.args.get('email')
    
    if not email or email == 'undefined':
        return jsonify({
            "success": False,
            "message": "缺少必要参数：邮箱地址，请返回注册页重试"
        }), 400
    
    # auth0_id可以为空，只要有email就行
    return jsonify({
        "success": True,
        "message": "请检查您的邮箱完成验证",
        "data": {
            "auth0_id": auth0_id or "",
            "email": email
        }
    })

# 注册验证等待页面路由 - 这个添加了重定向功能
@auth_bp.route("/verification-waiting", methods=["GET"])
def verification_waiting_redirect():
    """当前端错误访问API路径时，重定向到正确的页面路径"""
    auth0_id = request.args.get('auth0_id', '')
    email = request.args.get('email', '')
    
    logger.info(f"捕获到API验证等待页面请求，进行重定向: email={email}, auth0_id={auth0_id}")
    
    # 构建正确的URL参数
    redirect_params = []
    if email:
        redirect_params.append(f"email={email}")
    if auth0_id:
        redirect_params.append(f"auth0_id={auth0_id}")
    
    # 返回重定向响应
    redirect_url = f"/verification-waiting?{'&'.join(redirect_params)}" if redirect_params else "/verification-waiting"
    return jsonify({
        "success": False,
        "message": "请使用正确的页面URL",
        "redirect_url": redirect_url
    }), 302, {"Location": redirect_url}

def init_app(app):
    """初始化认证模块"""
    # 设置Auth0
    oauth = setup_auth0(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    
    logger.info("认证模块初始化完成")
    return oauth 