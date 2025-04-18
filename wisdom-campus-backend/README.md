# 智慧校园学习助手系统 - 后端API

## 项目简介

智慧校园学习助手系统是一个为高校学生设计的综合性学习平台，旨在通过个性化管理、智能化辅助和社区交流，提升学生的学习效率和体验。本仓库包含系统的后端API，使用Flask框架开发。

## 技术栈

- **核心框架**：Flask 2.0.1
- **ORM框架**：Flask-SQLAlchemy 2.5.1
- **跨域处理**：Flask-CORS 3.0.10
- **数据库**：MySQL
- **数据库驱动**：PyMySQL 1.0.2
- **身份验证**：Auth0
- **数据序列化**：Flask-Marshmallow 0.14.0
- **邮件服务**：Flask-Mail 0.9.1
- **数据库迁移**：Flask-Migrate 3.1.0

## 项目结构

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
|   |-- /templates                  # HTML模板
|   |-- __init__.py                 # 应用工厂函数
|-- /migrations                     # 数据库迁移文件
|-- /tests                          # 测试文件
|-- /docs                           # 文档
|-- /scripts                        # 实用脚本
|-- requirements.txt                # 项目依赖
|-- run.py                          # 项目启动文件
|-- .env                            # 环境变量配置文件
|-- README.md                       # 项目说明
```

## 安装与运行

### 环境要求

- Python 3.8+
- MySQL

### 安装步骤

1. 克隆仓库
   ```
   git clone <仓库地址>
   cd wisdom-campus-backend
   ```

2. 创建虚拟环境
   ```
   python -m venv venv
   ```

3. 激活虚拟环境
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```

4. 安装依赖
   ```
   pip install -r requirements.txt
   ```

5. 配置环境变量
   - 复制`.env.example`为`.env`
   - 编辑`.env`文件，设置必要的环境变量

6. 运行应用
   ```
   python run.py
   ```

应用将在 http://localhost:5000 运行

## 数据库管理

### 数据库初始化

```bash
# 检查数据库连接
python scripts/check_db_connection.py

# 创建数据库表
python scripts/execute_sql.py
```

### 重置数据库

```bash
# 清空现有数据库并使用新的SQL文件重建结构
python scripts/reset_database.py
```

### 数据迁移

```bash
# 迁移Auth0用户数据到新结构
python scripts/migrate_auth0_data.py
```

## API文档

API文档将在完成开发后提供，或者可以通过访问 `/api/docs` 端点查看。

## 更新日志

- [2023-05-28] 完成任务1：数据库配置与初始化
  - 配置MySQL数据库连接
  - 创建数据库表结构
  - 验证数据库连接成功

- [2023-05-30] 完成任务2：用户认证与信息管理模块（基于Auth0）
  - 实现基于Auth0的用户认证系统
  - 添加邮箱验证功能
  - 实现用户个人资料管理
  - 添加用户画像维护功能
  - 新增依赖：auth0-python, authlib, python-jose
  - 支持用户信息管理API
  - 添加前端页面模板

- [2023-06-05] 数据库结构优化
  - 优化用户表结构，更好地适配Auth0用户信息
  - 增加用户表的新字段：nickname, auth0_sid, auth0_aud, auth0_iss等
  - 增加相关索引提高查询性能
  - 添加数据库重置和数据迁移脚本
  - 更新Auth0回调处理函数

## 开发团队

- [开发者姓名] - [联系方式]

## 许可证

本项目采用 [许可证类型] 许可证 - 详情见 LICENSE 文件 