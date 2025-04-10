import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import urllib3
import os
from datetime import datetime
from functools import wraps

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, flash, jsonify
import requests

# 禁用SSL警告（仅用于测试环境）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载环境变量
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# 强制URL方案和服务器名
class ReverseProxied:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['wsgi.url_scheme'] = 'http'
        environ['HTTP_HOST'] = 'localhost:4000'
        return self.app(environ, start_response)

app.wsgi_app = ReverseProxied(app.wsgi_app)

# 配置Auth0
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        "verify": False,  # 禁用SSL验证，仅用于测试
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# 管理员权限检查装饰器
def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('请先登录', 'warning')
            return redirect('/login')
        
        # 测试阶段：允许所有登录用户访问管理页面
        return f(*args, **kwargs)
        
        # 正式环境使用以下代码：
        # admin_emails = ['admin@example.com']  # 在实际应用中从配置或数据库中读取
        # if 'userinfo' in session['user'] and session['user']['userinfo']['email'] in admin_emails:
        #     return f(*args, **kwargs)
        # else:
        #     flash('您没有管理员权限', 'danger')
        #     return redirect('/')
    return decorated

# 获取Auth0 Management API访问令牌
def get_management_api_token():
    domain = env.get("AUTH0_DOMAIN")
    client_id = env.get("AUTH0_CLIENT_ID")
    client_secret = env.get("AUTH0_CLIENT_SECRET")
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": f"https://{domain}/api/v2/",
        "grant_type": "client_credentials"
    }
    
    response = requests.post(
        f"https://{domain}/oauth/token", 
        json=payload,
        verify=False  # 禁用SSL验证，仅用于测试
    )
    
    if response.status_code != 200:
        raise Exception(f"无法获取管理API令牌: {response.text}")
    
    return response.json()['access_token']

# 路由设置
@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri="http://localhost:4000/callback"
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    
    # 检查邮箱验证状态
    if 'userinfo' in token and 'email_verified' in token['userinfo']:
        if not token['userinfo']['email_verified']:
            flash('请验证您的邮箱以完成注册', 'warning')
    
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route("/profile")
def profile():
    if 'user' not in session:
        return redirect('/login')
    return render_template("profile.html", user=session.get('user'))

@app.route("/resend-verification")
def resend_verification():
    if 'user' not in session:
        return redirect('/login')
    
    # 获取用户ID
    user_id = session['user']['userinfo']['sub']
    
    # 1. 获取 Management API 访问令牌
    domain = env.get("AUTH0_DOMAIN")
    client_id = env.get("AUTH0_CLIENT_ID")
    client_secret = env.get("AUTH0_CLIENT_SECRET")
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": f"https://{domain}/api/v2/",
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(
            f"https://{domain}/oauth/token", 
            json=payload,
            verify=False  # 禁用SSL验证，仅用于测试
        )
        
        if response.status_code != 200:
            flash('验证邮件发送失败，请稍后再试', 'danger')
            return redirect('/profile')
        
        token = response.json()['access_token']
        
        # 2. 发送验证邮件
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        verification_data = {
            "user_id": user_id
        }
        
        verification_response = requests.post(
            f"https://{domain}/api/v2/jobs/verification-email",
            headers=headers,
            json=verification_data,
            verify=False  # 禁用SSL验证，仅用于测试
        )
        
        if verification_response.status_code == 201:
            flash('验证邮件已重新发送，请查收', 'success')
        else:
            flash(f'验证邮件发送失败: {verification_response.text}', 'danger')
            
    except Exception as e:
        flash(f'发生错误: {str(e)}', 'danger')
    
    return redirect('/profile')

# 管理员页面路由
@app.route("/admin")
@requires_admin
def admin():
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = 10  # 每页显示的记录数
        search_query = request.args.get('search', '')
        filter_type = request.args.get('filter', 'all')
        
        # 获取Management API令牌
        token = get_management_api_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 构建查询参数 - 修复include_totals类型
        params = {
            "page": page - 1,  # Auth0 API使用0为起始页
            "per_page": per_page,
            "include_totals": "true"  # 使用字符串形式的"true"而不是布尔值True
        }
        
        # 添加搜索条件
        q_parts = []
        if search_query:
            q_parts.append(f'(name:"{search_query}*" OR email:"{search_query}*")')
        
        # 添加过滤条件
        if filter_type == 'verified':
            q_parts.append('email_verified:true')
        elif filter_type == 'unverified':
            q_parts.append('email_verified:false')
        
        if q_parts:
            params['q'] = ' AND '.join(q_parts)
            
        # 获取用户列表
        domain = env.get("AUTH0_DOMAIN")
        response = requests.get(
            f"https://{domain}/api/v2/users",
            headers=headers,
            params=params,
            verify=False  # 禁用SSL验证，仅用于测试
        )
        
        if response.status_code != 200:
            flash(f'获取用户列表失败: {response.text}', 'danger')
            return render_template("admin.html", users=[], page=1, total_pages=1, request=request)
        
        data = response.json()
        users = data['users']
        total = data.get('total', len(users))
        total_pages = (total + per_page - 1) // per_page
        
        # 格式化用户数据以便于在模板中使用
        formatted_users = []
        for user in users:
            formatted_users.append({
                'user_id': user['user_id'],
                'name': user.get('name', '未设置'),
                'email': user.get('email', '未设置'),
                'picture': user.get('picture', None),
                'email_verified': user.get('email_verified', False),
                'created_at': datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M') if 'created_at' in user else '未知'
            })
        
        return render_template("admin.html", 
                              users=formatted_users, 
                              page=page, 
                              total_pages=total_pages, 
                              request=request)
                              
    except Exception as e:
        flash(f'获取用户数据时发生错误: {str(e)}', 'danger')
        return render_template("admin.html", users=[], page=1, total_pages=1, request=request)

# 更新用户信息
@app.route("/admin/update-user", methods=["POST"])
@requires_admin
def update_user():
    try:
        # 获取表单数据
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        email = request.form.get('email')
        email_verified = 'email_verified' in request.form
        
        # 获取Management API令牌
        token = get_management_api_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备更新数据
        update_data = {
            "name": name,
            "email": email,
            "email_verified": email_verified
        }
        
        # 更新用户信息
        domain = env.get("AUTH0_DOMAIN")
        response = requests.patch(
            f"https://{domain}/api/v2/users/{user_id}",
            headers=headers,
            json=update_data,
            verify=False  # 禁用SSL验证，仅用于测试
        )
        
        if response.status_code == 200:
            flash('用户信息更新成功', 'success')
        else:
            flash(f'用户信息更新失败: {response.text}', 'danger')
        
    except Exception as e:
        flash(f'更新用户信息时发生错误: {str(e)}', 'danger')
    
    return redirect('/admin')

# 创建新用户
@app.route("/admin/create-user", methods=["POST"])
@requires_admin
def create_user():
    try:
        # 获取表单数据
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        email_verified = 'email_verified' in request.form
        
        # 获取Management API令牌
        token = get_management_api_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备创建用户数据
        domain = env.get("AUTH0_DOMAIN")
        connection = "Username-Password-Authentication"  # Auth0 数据库连接名称
        
        create_data = {
            "name": name,
            "email": email,
            "password": password,
            "email_verified": email_verified,
            "connection": connection
        }
        
        # 创建用户
        response = requests.post(
            f"https://{domain}/api/v2/users",
            headers=headers,
            json=create_data,
            verify=False  # 禁用SSL验证，仅用于测试
        )
        
        if response.status_code == 201:
            flash('用户创建成功', 'success')
        else:
            flash(f'用户创建失败: {response.text}', 'danger')
        
    except Exception as e:
        flash(f'创建用户时发生错误: {str(e)}', 'danger')
    
    return redirect('/admin')

# 删除用户
@app.route("/admin/delete-user", methods=["POST"])
@requires_admin
def delete_user():
    try:
        # 获取表单数据
        user_id = request.form.get('user_id')
        
        # 获取Management API令牌
        token = get_management_api_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 删除用户
        domain = env.get("AUTH0_DOMAIN")
        response = requests.delete(
            f"https://{domain}/api/v2/users/{user_id}",
            headers=headers,
            verify=False  # 禁用SSL验证，仅用于测试
        )
        
        if response.status_code == 204:
            flash('用户删除成功', 'success')
        else:
            flash(f'用户删除失败: {response.status_code} {response.text}', 'danger')
        
    except Exception as e:
        flash(f'删除用户时发生错误: {str(e)}', 'danger')
    
    return redirect('/admin')

if __name__ == "__main__":
    # 设置环境变量确保URL生成正确
    os.environ["FLASK_RUN_HOST"] = "localhost"
    os.environ["FLASK_RUN_PORT"] = "4000" 
    
    # 打印调试信息
    print(f"回调URL: http://localhost:4000/callback")
    print(f"应用运行在: http://localhost:4000")
    
    app.run(host="localhost", port=env.get("PORT", 4000)) 