

# 智慧校园学习助手系统 - 项目计划过程说明书

## 欢迎使用智慧校园学习助手系统开发说明书！

本项目旨在为高校学生提供一个全面的学习辅助平台，涵盖个性化学习管理、笔记系统、成绩分析、社区交流等功能。本说明书将指导开发人员（包括使用 Cursor 等工具）从零开始完成项目的后端 API 开发，确保开发过程有条不紊，任务模块化，便于分阶段实现。特别地，用户认证模块将采用 Auth0 技术实现，以增强安全性和开发效率。

---

## 文档目录

以下是构建和了解系统的关键内容：

1. **项目概述与目标** - 项目背景和功能目标概述
2. **技术栈与架构** - 技术选型和系统架构说明
3. **开发环境准备** - 开发环境搭建步骤
4. **项目结构搭建** - 后端项目结构和初始化指南
5. **开发计划与时间安排** - 详细的开发阶段和时间规划
6. **模块化开发任务** - 按模块划分的开发步骤和任务清单
7. **数据库配置与初始化** - 数据库连接和初始化指南
8. **测试与部署** - 测试方法和部署步骤
9. **常见问题与解决方案** - 常见问题解答
10. **贡献与联系方式** - 如何贡献和获取支持

---

## 1. 项目概述与目标

### 1.1 项目背景
智慧校园学习助手系统是一个为高校学生设计的综合性学习平台，旨在通过个性化管理、智能化辅助和社区交流，提升学生的学习效率和体验。系统采用前后端分离架构，后端使用 Flask 框架开发 RESTful API，前端基于 Flutter/Dart 开发跨平台移动应用。用户认证模块特别采用 Auth0 技术，以实现安全、便捷的身份管理和认证。

### 1.2 功能目标
系统主要分为以下模块，每个模块均需在后端提供相应的 API 支持：
- **用户模块**：基于 Auth0 的认证、信息管理、设置
- **学习模块**：课程、成绩、任务、专注记录、打卡
- **笔记模块**：笔记创建、编辑、分类、标签
- **社区模块**：帖子、评论、点赞、收藏、私信
- **成就模块**：经验值、等级、徽章
- **学习计划模块**：计划管理、进度跟踪
- **知识图谱模块**：知识点管理、关联和掌握度评估
- **学习资源模块**：资源管理和推荐
- **学习分析模块**：学习行为记录和分析
- **AI 辅助模块**：智能问答和学习辅助
- **通知模块**：系统通知、任务提醒
- **搜索历史模块**：用户搜索记录
- **管理员模块**：举报管理和操作日志

### 1.3 开发目标
- 完成所有模块的 RESTful API 开发，确保功能完整。
- 实现数据库模型与 API 的无缝集成，特别关注 Auth0 认证的集成。
- 确保代码规范、文档清晰，便于维护和扩展。
- 支持模块化开发，逐步完成每个功能模块。

---

## 2. 技术栈与架构

### 2.1 技术栈
- **核心框架**：Flask 2.0.1
- **ORM 框架**：Flask-SQLAlchemy 2.5.1
- **跨域处理**：Flask-CORS 3.0.10
- **数据库**：MySQL
- **数据库驱动**：PyMySQL 1.0.2
- **身份验证**：Auth0（通过 Auth0 SDK 和 API 实现）
- **数据序列化**：Flask-Marshmallow 0.14.0
- **邮件服务**：Flask-Mail 0.9.1
- **数据库迁移**：Flask-Migrate 3.1.0

### 2.2 系统架构
- **前端**：Flutter/Dart 开发跨平台移动应用
- **后端**：Flask 开发的 RESTful API
- **数据库**：MySQL 存储结构化数据
- **身份认证**：Auth0 提供认证服务
- **部署**：Gunicorn + Nginx

---

## 3. 开发环境准备

### 3.1 开发工具与环境
- **Python 版本**：Python 3.8 或以上
- **IDE**：推荐使用 PyCharm 或 VSCode
- **版本控制**：Git
- **虚拟环境**：venv 或 virtualenv
- **Auth0 账户**：需要注册 Auth0 账户并创建应用以获取认证相关配置

### 3.2 环境搭建步骤
1. **安装 Python**：
   - 下载并安装 Python 3.8+（从 [Python 官网](https://www.python.org/downloads/) 获取）。
   - 验证安装：`python --version`
2. **创建虚拟环境**：
   - 打开终端，导航到项目目录：`cd project_directory`
   - 创建虚拟环境：`python -m venv venv`
   - 激活虚拟环境：
     - Windows：`venv\Scripts\activate`
     - Linux/Mac：`source venv/bin/activate`
3. **安装依赖**：
   - 使用 `requirements.txt`（后续提供）安装依赖：`pip install -r requirements.txt`
   - 核心依赖示例：
     ```bash
     flask==2.0.1
     flask-sqlalchemy==2.5.1
     flask-cors==3.0.10
     pymysql==1.0.2
     auth0-python==3.24.1  # 用于 Auth0 认证
     flask-marshmallow==0.14.0
     flask-mail==0.9.1
     flask-migrate==3.1.0
     ```
4. **配置 MySQL**：
   - 安装 MySQL（如果未安装）：从 [MySQL 官网](https://dev.mysql.com/downloads/) 下载。
   - 创建数据库：登录 MySQL，执行 `CREATE DATABASE xuesheng233;`
   - 记录数据库配置信息（后续使用）：
     - 数据库名称：`xuesheng233`
     - 用户名：`FZG1234C`
     - 密码：`FZG1234C`
     - 主机地址：`115.120.215.107`
     - 端口：`3306`
5. **配置 Auth0**：
   - 注册 Auth0 账户（[Auth0 官网](https://auth0.com/)）。
   - 创建一个新应用，选择“Regular Web Applications”。
   - 获取以下配置信息：
     - Domain（例如：`your-tenant.auth0.com`）
     - Client ID
     - Client Secret
   - 配置回调 URL（例如：`http://localhost:5000/api/v1/auth/callback`）。
   - 将这些配置保存到环境变量或配置文件中。

### 3.3 注意事项
- 确保网络环境可以连接到数据库主机地址和 Auth0 服务。
- 如果使用本地开发，可将数据库配置改为本地 MySQL 实例。

---

## 4. 项目结构搭建

### 4.1 完整项目结构
以下是推荐的项目目录结构，确保代码组织清晰：

```
/wisdom-campus-backend
|-- /app
|   |-- /api
|   |   |-- /v1
|   |   |   |-- /auth               # 用户认证API（基于Auth0）
|   |   |   |-- /user               # 用户信息管理API
|   |   |   |-- /learning           # 学习模块API
|   |   |   |-- /note               # 笔记模块API
|   |   |   |-- /community          # 社区模块API
|   |   |   |-- /achievement        # 成就模块API
|   |   |   |-- /plan               # 学习计划模块API
|   |   |   |-- /knowledge          # 知识图谱模块API
|   |   |   |-- /resource           # 学习资源模块API
|   |   |   |-- /analysis           # 学习分析模块API
|   |   |   |-- /ai                 # AI辅助模块API
|   |   |   |-- /notification       # 通知模块API
|   |   |   |-- /search             # 搜索历史模块API
|   |   |   |-- /admin              # 管理员模块API
|   |   |   |-- __init__.py
|   |-- /models                     # 数据库模型
|   |-- /schemas                    # 数据序列化 schemas
|   |-- /utils                      # 工具函数
|   |-- /config                     # 配置管理
|   |-- __init__.py                 # 应用工厂函数
|-- /migrations                     # 数据库迁移文件
|-- /tests                          # 测试文件
|-- /docs                           # 文档
|-- requirements.txt                # 项目依赖
|-- run.py                          # 项目启动文件
|-- .env                            # 环境变量配置文件
|-- README.md                       # 项目说明
```

### 4.2 从零搭建项目
1. **创建项目目录**：
   - 创建项目根目录：`mkdir wisdom-campus-backend && cd wisdom-campus-backend`
2. **初始化虚拟环境**：
   - 参考“3.2 环境搭建步骤”。
3. **创建基本文件和目录**：
   - 使用终端或 IDE 创建上述目录结构。
4. **初始化 Flask 应用**：
   - 在 `app/__init__.py` 中编写应用工厂函数：
     ```python
     from flask import Flask
     from flask_sqlalchemy import SQLAlchemy
     from flask_migrate import Migrate
     from flask_cors import CORS

     db = SQLAlchemy()
     migrate = Migrate()

     def create_app(config_class='config.DevelopmentConfig'):
         app = Flask(__name__)
         app.config.from_object(config_class)

         db.init_app(app)
         migrate.init_app(app, db)
         CORS(app)

         # 注册蓝图（后续添加）
         from app.api.v1.auth import auth_bp
         app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

         return app
     ```
5. **配置环境变量**：
   - 安装 `python-dotenv`：`pip install python-dotenv`
   - 在根目录创建 `.env` 文件，添加数据库和 Auth0 配置：
     ```
     FLASK_ENV=development
     DATABASE_URL=mysql+pymysql://FZG1234C:FZG1234C@115.120.215.107:3306/xuesheng233
     AUTH0_DOMAIN=your-tenant.auth0.com
     AUTH0_CLIENT_ID=your-client-id
     AUTH0_CLIENT_SECRET=your-client-secret
     AUTH0_CALLBACK_URL=http://localhost:5000/api/v1/auth/callback
     ```
6. **创建启动文件**：
   - 在根目录创建 `run.py`：
     ```python
     from app import create_app

     app = create_app()

     if __name__ == '__main__':
         app.run(debug=True)
     ```

---

## 5. 开发计划与时间安排

### 5.1 开发阶段
项目开发分为以下阶段，每个阶段对应一个或多个模块，预计总耗时 8-10 周（可根据实际情况调整）。

| 阶段 | 模块 | 预计时间 | 备注 |
|------|------|----------|------|
| **第一阶段** | 用户认证与信息管理（基于 Auth0） | 1.5 周 | 核心模块，优先实现，Auth0 集成可能耗时 |
| **第二阶段** | 学习模块（课程、成绩、任务等） | 1.5 周 | 学习相关核心功能 |
| **第三阶段** | 笔记模块 | 1 周 | 学生常用功能 |
| **第四阶段** | 社区模块 | 1 周 | 交流互动功能 |
| **第五阶段** | 成就模块与学习计划模块 | 1 周 | 激励与规划功能 |
| **第六阶段** | 知识图谱与学习资源模块 | 1 周 | 辅助学习功能 |
| **第七阶段** | 学习分析与 AI 辅助模块 | 1 周 | 智能化功能 |
| **第八阶段** | 通知与搜索历史模块 | 0.5 周 | 辅助功能 |
| **第九阶段** | 管理员模块 | 0.5 周 | 管理功能 |
| **第十阶段** | 测试与优化 | 1 周 | 确保系统稳定 |
| **第十一阶段** | 部署上线 | 0.5 周 | 正式上线 |

### 5.2 时间安排注意事项
- 每个阶段完成后，进行单元测试，确保功能无误后再进入下一阶段。
- 如使用 Cursor 开发工具，可将任务进一步拆分为每日小目标。
- 第一阶段的用户认证模块因涉及 Auth0 集成，可能需要额外时间学习和调试。

---

## 6. 模块化开发任务

以下是按模块划分的详细开发任务清单，每个模块包含具体步骤和注意事项，方便分批次完成。

### 6.1 第一阶段 - 用户认证与信息管理模块（基于 Auth0）
#### 任务目标
实现基于 Auth0 的用户认证，包括登录、注册、令牌验证，以及用户个人信息管理和设置功能。

#### 任务清单
1. **定义用户模型**：
   - 在 `app/models/user.py` 中创建 `User` 和 `UserProfile` 模型，字段参考数据库设计。
   - 注意：由于使用 Auth0，`password_hash` 字段可能不直接使用，认证信息存储在 Auth0 中，`auth0_id` 字段用于关联 Auth0 用户。
   - 示例代码：
     ```python
     from app import db

     class User(db.Model):
         __tablename__ = 'user'
         id = db.Column(db.Integer, primary_key=True)
         student_id = db.Column(db.String(20), unique=True)
         auth0_id = db.Column(db.String(50), unique=True)  # 关联 Auth0 用户ID
         name = db.Column(db.String(50))
         email = db.Column(db.String(100), unique=True)
         email_verified = db.Column(db.Boolean, default=False)
         avatar_url = db.Column(db.String(255))
         bio = db.Column(db.Text)
         major_id = db.Column(db.Integer, db.ForeignKey('major.id'))
         total_study_time = db.Column(db.Integer, default=0)
         gpa = db.Column(db.Numeric(3,2), default=0.0)
         exp_points = db.Column(db.Integer, default=0)
         level = db.Column(db.Integer, default=1)
         is_admin = db.Column(db.Boolean, default=False)
         created_at = db.Column(db.DateTime)
         updated_at = db.Column(db.DateTime)
         status = db.Column(db.Enum('active', 'inactive', 'banned'), default='active')

     class UserProfile(db.Model):
         __tablename__ = 'user_profile'
         id = db.Column(db.Integer, primary_key=True)
         user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
         learning_style = db.Column(db.Enum('visual', 'auditory', 'kinesthetic', 'mixed'))
         preferred_time = db.Column(db.Enum('morning', 'afternoon', 'evening', 'night'))
         avg_focus_duration = db.Column(db.Integer)
         strengths = db.Column(db.Text)
         weaknesses = db.Column(db.Text)
         study_habits = db.Column(db.Text)
         notification_email_enabled = db.Column(db.Boolean, default=True)
         notification_app_enabled = db.Column(db.Boolean, default=True)
         notification_types = db.Column(db.Text)
         last_updated = db.Column(db.DateTime)
     ```
2. **创建数据序列化 Schema**：
   - 在 `app/schemas/user.py` 中创建 Marshmallow 序列化类。
   - 示例代码：
     ```python
     from flask_marshmallow import Marshmallow
     ma = Marshmallow()

     class UserSchema(ma.Schema):
         class Meta:
             fields = ('id', 'student_id', 'name', 'email', 'avatar_url', 'bio', 'total_study_time', 'gpa', 'exp_points', 'level', 'is_admin', 'status')
     ```
3. **实现 Auth0 认证工具函数**：
   - 在 `app/utils/auth.py` 中实现与 Auth0 相关的认证功能，包括获取访问令牌、验证用户、同步用户数据等。
   - 示例代码：
     ```python
     import requests
     from flask import current_app

     def get_auth0_user_info(access_token):
         auth0_domain = current_app.config['AUTH0_DOMAIN']
         url = f"https://{auth0_domain}/userinfo"
         headers = {"Authorization": f"Bearer {access_token}"}
         response = requests.get(url, headers=headers)
         if response.status_code == 200:
             return response.json()
         return None

     def sync_user_with_auth0(auth0_user_info):
         user = User.query.filter_by(auth0_id=auth0_user_info.get('sub')).first()
         if not user:
             user = User(
                 auth0_id=auth0_user_info.get('sub'),
                 email=auth0_user_info.get('email'),
                 name=auth0_user_info.get('name'),
                 email_verified=auth0_user_info.get('email_verified', False),
                 avatar_url=auth0_user_info.get('picture', '')
             )
             db.session.add(user)
             db.session.commit()
         return user
     ```
4. **实现认证 API**：
   - 在 `app/api/v1/auth/__init__.py` 中创建蓝图。
   - 实现登录回调、获取用户信息的 API，由于注册和登录流程由 Auth0 前端 SDK 处理，后端主要处理回调和令牌验证。
   - 示例 API：`/api/v1/auth/callback`（处理 Auth0 回调，获取令牌和用户信息）
   - 示例代码：
     ```python
     from flask import Blueprint, request, jsonify
     from app.utils.auth import get_auth0_user_info, sync_user_with_auth0

     auth_bp = Blueprint('auth', __name__)

     @auth_bp.route('/callback', methods=['GET'])
     def callback():
         code = request.args.get('code')
         if not code:
             return jsonify({"error": "Authorization code not found"}), 400

         # 交换授权码获取访问令牌
         auth0_domain = current_app.config['AUTH0_DOMAIN']
         client_id = current_app.config['AUTH0_CLIENT_ID']
         client_secret = current_app.config['AUTH0_CLIENT_SECRET']
         callback_url = current_app.config['AUTH0_CALLBACK_URL']
         token_url = f"https://{auth0_domain}/oauth/token"
         payload = {
             'grant_type': 'authorization_code',
             'client_id': client_id,
             'client_secret': client_secret,
             'code': code,
             'redirect_uri': callback_url
         }
         response = requests.post(token_url, json=payload)
         if response.status_code != 200:
             return jsonify({"error": "Failed to get token"}), 400

         token_data = response.json()
         access_token = token_data.get('access_token')
         user_info = get_auth0_user_info(access_token)
         if not user_info:
             return jsonify({"error": "Failed to get user info"}), 400

         user = sync_user_with_auth0(user_info)
         return jsonify({
             "access_token": access_token,
             "user": {"id": user.id, "email": user.email, "name": user.name}
         })
     ```
5. **实现用户信息管理 API**：
   - 在 `app/api/v1/user/__init__.py` 中创建蓝图。
   - 实现获取/更新个人信息、设置通知偏好 API。
   - 示例 API：`/api/v1/user/profile`
   - 注意：API 需要验证 Auth0 提供的访问令牌，确保用户已认证。
6. **测试 API 接口**：
   - 使用 Postman 或 pytest 进行单元测试，确保 Auth0 回调、用户信息同步和获取正常。
   - 确保前端可以通过 Auth0 SDK 跳转到登录页面，并成功回调到后端 API。

#### 注意事项
- **Auth0 集成**：需要熟悉 Auth0 的 OAuth 2.0 流程，前端通过 Auth0 SDK 发起登录，后端处理回调和令牌验证。
- **用户数据同步**：从 Auth0 获取用户信息后，需同步到本地数据库（通过 `auth0_id` 字段关联）。
- **安全配置**：确保 `.env` 文件中的 Auth0 配置信息不泄露，生产环境需使用更安全的存储方式。

---

### 6.2 第二阶段 - 学习模块
#### 任务目标
实现课程、成绩、任务、专注记录和打卡功能。

#### 任务清单
1. **定义学习模块模型**：
   - 在 `app/models/learning.py` 中定义 `Course`, `CourseSchedule`, `Grade`, `MajorCourse`, `Task`, `FocusRecord`, `CheckIn` 模型，字段参考数据库设计。
2. **创建数据序列化 Schema**：
   - 在 `app/schemas/learning.py` 中创建相应 Schema。
3. **实现学习模块 API**：
   - 在 `app/api/v1/learning/__init__.py` 中创建蓝图。
   - 实现课程管理、成绩查询、任务管理、专注记录和打卡 API。
   - 示例 API：`/api/v1/learning/courses`, `/api/v1/learning/tasks`
   - 注意：API 需要通过 Auth0 令牌验证用户身份。
4. **测试 API 接口**：
   - 编写测试用例，确保功能完整。

#### 注意事项
- 任务管理需支持截止日期提醒（结合后续通知模块）。
- 课程表功能需支持个性化时间安排。

---

### 6.3 第三阶段 - 笔记模块
#### 任务目标
实现笔记的创建、编辑、分类、标签和文件上传功能。

#### 任务清单
1. **定义笔记模块模型**：
   - 在 `app/models/note.py` 中定义 `Note`, `NoteFile`, `NoteTag` 模型，字段参考数据库设计。
2. **创建数据序列化 Schema**：
   - 在 `app/schemas/note.py` 中创建相应 Schema。
3. **实现笔记模块 API**：
   - 在 `app/api/v1/note/__init__.py` 中创建蓝图。
   - 实现笔记 CRUD、分类、标签管理和文件上传 API。
   - 示例 API：`/api/v1/note/create`, `/api/v1/note/list`
4. **测试 API 接口**：
   - 测试笔记创建、文件上传和标签功能。

#### 注意事项
- 文件上传需限制文件大小和类型，确保安全性。
- 笔记支持总结生成（后续结合 AI 模块）。

---

### 6.4 第四阶段 - 社区模块
#### 任务目标
实现帖子、评论、点赞、收藏和私信功能。

#### 任务清单
1. **定义社区模块模型**：
   - 在 `app/models/community.py` 中定义 `Post`, `Comment`, `Like`, `Favorite`, `Message` 模型，字段参考数据库设计。
2. **创建数据序列化 Schema**：
   - 在 `app/schemas/community.py` 中创建相应 Schema。
3. **实现社区模块 API**：
   - 在 `app/api/v1/community/__init__.py` 中创建蓝图。
   - 实现帖子发布、评论、点赞、收藏和私信 API。
   - 示例 API：`/api/v1/community/posts`, `/api/v1/community/messages`
4. **测试 API 接口**：
   - 测试帖子发布、评论回复和私信功能。

#### 注意事项
- 帖子和评论需支持匿名发布。
- 私信内容需加密存储或严格权限控制。

---

### 6.5 第五阶段 - 成就模块与学习计划模块
#### 任务目标
实现经验值、等级、徽章和学习计划管理功能。

#### 任务清单
1. **定义模型**：
   - 在 `app/models/achievement.py` 定义 `Badge`, `UserBadge` 模型。
   - 在 `app/models/plan.py` 定义 `StudyPlan` 模型。
2. **创建数据序列化 Schema**：
   - 在 `app/schemas/` 中创建相应 Schema。
3. **实现 API**：
   - 在 `app/api/v1/achievement/__init__.py` 和 `app/api/v1/plan/__init__.py` 中创建蓝图并实现 API。
4. **测试 API 接口**：
   - 确保成就和学习计划功能正常。

---

### 6.6 第六阶段 - 知识图谱与学习资源模块
#### 任务目标
实现知识点管理、关联、掌握度评估和资源管理和推荐功能。

#### 任务清单
1. **定义模型**：
   - 在 `app/models/knowledge.py` 定义 `KnowledgePoint`, `KnowledgeRelation`, `UserKnowledgeMastery` 模型。
   - 在 `app/models/resource.py` 定义 `LearningResource`, `ResourceRecommendation`, `ResourceComment` 模型。
2. **创建 Schema 和 API**：
   - 实现知识点和资源相关 API。
3. **测试 API 接口**：
   - 确保功能正常。

---

### 6.7 第七阶段 - 学习分析与 AI 辅助模块
#### 任务目标
实现学习行为记录、分析和 AI 问答、学习辅助功能。

#### 任务清单
1. **定义模型**：
   - 在 `app/models/analysis.py` 定义 `LearningBehavior`, `LearningAnalysis` 模型。
   - 在 `app/models/ai.py` 定义 `AIQuestion`, `AILearningAssistant` 模型。
2. **创建 Schema 和 API**：
   - 实现分析和 AI 相关 API。
3. **测试 API 接口**：
   - 确保功能正常。

---

### 6.8 第八阶段 - 通知与搜索历史模块
#### 任务目标
实现系统通知、任务提醒和搜索历史记录功能。

#### 任务清单
1. **定义模型**：
   - 在 `app/models/notification.py` 定义 `Notification` 模型。
   - 在 `app/models/search.py` 定义 `SearchHistory` 模型。
2. **创建 Schema 和 API**：
   - 实现通知和搜索历史相关 API。
3. **测试 API 接口**：
   - 确保功能正常。

---

### 6.9 第九阶段 - 管理员模块
#### 任务目标
实现举报管理和管理员操作日志功能。

#### 任务清单
1. **定义模型**：
   - 在 `app/models/admin.py` 定义 `Report`, `AdminLog` 模型。
2. **创建 Schema 和 API**：
   - 实现管理员相关 API。
3. **测试 API 接口**：
   - 确保功能正常。

---

### 6.10 第十阶段 - 测试与优化
#### 任务目标
确保系统功能完整、性能优化。

#### 任务清单
1. **单元测试**：为每个模块编写测试用例。
2. **集成测试**：测试 API 之间的协作。
3. **性能优化**：优化数据库查询，添加缓存。

---

### 6.11 第十一阶段 - 部署上线
#### 任务目标
将系统部署到生产环境。

#### 任务清单
1. **配置生产环境**：使用 Gunicorn 和 Nginx。
2. **部署 API**：将代码部署到服务器。
3. **监控与维护**：设置日志监控。

---

## 7. 数据库配置与初始化

### 7.1 配置数据库连接
- 在 `app/config.py` 中配置数据库：
  ```python
  class DevelopmentConfig:
      SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://FZG1234C:FZG1234C@115.120.215.107:3306/xuesheng233'
      SQLALCHEMY_TRACK_MODIFICATIONS = False
      AUTH0_DOMAIN = 'your-tenant.auth0.com'
      AUTH0_CLIENT_ID = 'your-client-id'
      AUTH0_CLIENT_SECRET = 'your-client-secret'
      AUTH0_CALLBACK_URL = 'http://localhost:5000/api/v1/auth/callback'
  ```

### 7.2 初始化数据库
1. 初始化迁移：`flask db init`
2. 生成迁移脚本：`flask db migrate`
3. 应用迁移：`flask db upgrade`

---

## 8. 测试与部署

### 8.1 测试
- **单元测试**：使用 pytest 编写单元测试，确保每个模块功能正常。
- **集成测试**：测试 Auth0 认证与 API 集成，确保用户数据同步无误。

### 8.2 部署
- **配置生产环境**：参考 Flask 官方文档，使用 Gunicorn 和 Nginx 部署。
- **Auth0 生产配置**：确保 Auth0 应用的回调 URL 更新为生产环境 URL。

---

## 9. 常见问题与解决方案

- **数据库连接失败**：检查 `.env` 文件中的配置是否正确。
- **Auth0 认证问题**：确保 Auth0 配置信息正确，回调 URL 与应用设置一致。
- **令牌验证失败**：检查访问令牌是否过期，是否正确传递到 API。

---

## 10. 贡献与联系方式

- **贡献方式**：Fork 仓库，提交 Pull Request。
- **联系方式**：项目负责人、技术支持（待补充）。

---

这份说明书提供了详细的项目计划和模块化任务清单，特别调整了用户认证模块以适应 Auth0 技术，方便使用 Cursor 等工具分批次完成开发。如果有进一步需求或调整，请随时告知，我可以提供更具体的代码示例或进一步拆分任务！