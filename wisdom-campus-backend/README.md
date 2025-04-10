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
|   |-- __init__.py                 # 应用工厂函数
|-- /migrations                     # 数据库迁移文件
|-- /tests                          # 测试文件
|-- /docs                           # 文档
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

6. 初始化数据库
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

7. 运行应用
   ```
   python run.py
   ```

应用将在 http://localhost:5000 运行

## API文档

API文档将在完成开发后提供，或者可以通过访问 `/api/docs` 端点查看。

## 开发团队

- [开发者姓名] - [联系方式]

## 许可证

本项目采用 [许可证类型] 许可证 - 详情见 LICENSE 文件 