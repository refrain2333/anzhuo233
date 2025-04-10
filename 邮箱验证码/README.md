# Auth0 邮箱验证示例应用

这是一个使用 Auth0 进行用户认证和邮箱验证的 Flask Web 应用程序示例。

## 功能特点

- 使用 Auth0 进行用户身份验证
- 邮箱验证功能展示
- 用户登录/注册/登出
- 用户个人资料页面
- 重新发送验证邮件功能

## 技术栈

- Python 3.x
- Flask 2.x
- Authlib 1.0
- Auth0 身份验证服务

## 安装步骤

1. 克隆本仓库：
   ```
   git clone <仓库地址>
   cd auth0-email-verification
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 配置 Auth0：
   - 在 Auth0 Dashboard 创建一个应用
   - 配置回调 URL: `http://localhost:3000/callback`
   - 配置登出 URL: `http://localhost:3000`
   - 复制 Domain、Client ID 和 Client Secret

4. 配置环境变量：
   - 创建 `.env` 文件
   - 添加以下内容：
     ```
     AUTH0_CLIENT_ID=你的客户端ID
     AUTH0_CLIENT_SECRET=你的客户端密钥
     AUTH0_DOMAIN=你的Auth0域名
     APP_SECRET_KEY=你的应用秘钥（使用 openssl rand -hex 32 生成）
     ```

5. 运行应用：
   ```
   python server.py
   ```

6. 在浏览器中访问 `http://localhost:3000`

## 重要文件说明

- `server.py`: 主应用程序文件
- `templates/`: 包含HTML模板
  - `home.html`: 主页模板
  - `profile.html`: 用户资料页面模板
- `.env`: 环境变量配置文件
- `requirements.txt`: 项目依赖

## Auth0 邮箱验证工作流程

1. 用户注册时，Auth0 默认发送邮箱验证邮件
2. 应用程序检查用户的 `email_verified` 字段来确定验证状态
3. 如果邮箱未验证，用户可以通过 "重新发送验证邮件" 按钮请求新的验证邮件

## Auth0 配置说明

为了使邮箱验证功能正常工作，确保在 Auth0 Dashboard 中：

1. 启用了 "Require Email Verification" 选项
2. 配置了适当的邮件模板
3. 配置了正确的应用程序回调 URL

## 注意事项

- 在生产环境中，应使用 HTTPS 而非 HTTP
- 请保管好 `.env` 文件中的密钥信息
- 此示例应用仅作为学习和参考用途 