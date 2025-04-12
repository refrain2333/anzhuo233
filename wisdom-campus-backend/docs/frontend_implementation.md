# 智慧校园学习助手系统 - 前端实现文档

## 前端架构概述

本项目主要侧重于后端API实现，前端部分主要用于验证API是否正常工作，因此采用了简洁的架构设计：

- 使用 **Flask** 内置的 **Jinja2** 模板引擎
- 基于 **HTML5 + CSS3 + JavaScript** 的前端技术栈
- 不引入额外的前端框架，保持轻量化
- 遵循响应式设计原则，适配不同屏幕尺寸

## 目录结构

```
app/
├── templates/           # Jinja2模板目录
│   ├── base.html        # 基础模板（页面布局）
│   ├── index.html       # 首页模板
│   ├── api_docs.html    # API文档页面
│   ├── auth/            # 认证相关页面
│   │   ├── login.html   # 登录页面
│   │   └── register.html # 注册页面
│   ├── errors/          # 错误页面
│   │   ├── 403.html     # 无权限页面
│   │   ├── 404.html     # 页面未找到
│   │   └── 500.html     # 服务器错误
│   └── admin/           # 管理员相关页面
│       └── dashboard.html # 管理控制台
├── static/              # 静态资源目录
│   ├── css/             # CSS样式文件
│   │   └── style.css    # 主样式文件
│   └── js/              # JavaScript文件
│       └── main.js      # 主脚本文件
```

## 模板说明

### base.html

基础布局模板，定义了页面的整体结构：

- 导航栏（包含链接到首页、API文档、API状态、管理平台、登录和注册）
- 内容区域（使用 `{% block content %}{% endblock %}` 插槽）
- 页脚信息
- CSS和JavaScript引用

### index.html

首页模板，继承自base.html，包含：

- 欢迎信息
- API端点列表展示
- API测试工具（可以直接在页面上测试API）

### auth/login.html

登录页面模板，继承自base.html，包含：

- 简洁的登录表单（学号和密码）
- 表单验证和错误提示
- 记住登录状态选项
- 注册页面链接

### auth/register.html

注册页面模板，继承自base.html，包含：

- 用户注册表单（学号、姓名、邮箱、密码等）
- 客户端表单验证
- 专业列表动态加载
- 登录页面链接

### api_docs.html

API文档页面，继承自base.html，包含：

- 详细的API接口说明
- 请求参数和响应结果示例
- 链接到API测试工具

### admin/dashboard.html

管理控制台页面，继承自base.html，包含：

- 用户管理功能
- 课程管理功能
- 系统状态监控

## 用户认证流程

前端实现了完整的用户认证流程：

1. **注册流程**：
   - 用户填写注册表单
   - 客户端表单验证（学号格式、密码强度等）
   - 发送注册请求至后端API
   - 处理注册结果（成功/失败提示）
   - 注册成功后引导至登录页面

2. **登录流程**：
   - 用户填写登录表单
   - 发送登录请求至后端API
   - 处理登录结果
   - 登录成功后保存token并跳转至首页
   - 更新导航栏显示（隐藏登录/注册按钮，显示个人中心/退出登录）

3. **会话管理**：
   - 使用localStorage存储认证token
   - 页面加载时检查登录状态
   - 对需要认证的API请求自动添加Authorization头
   - 提供退出登录功能

## 样式说明

采用简洁的样式设计，主要特点：

1. 使用 Flexbox 和 Grid 布局
2. 响应式设计，适配移动设备
3. 使用简洁的色彩方案（主色：#3f51b5，辅助色：#2c3e50）
4. 轻量级的CSS，无需额外框架

## JavaScript功能

主要JavaScript功能集中在以下几个方面：

1. API测试工具的实现（发送请求并显示结果）
2. 消息提示组件
3. 管理控制台中的数据加载和展示
4. 表单验证和提交
5. 用户认证状态管理（登录状态检查、退出登录）

## 前端与API交互

前端与API的交互主要通过fetch API实现：

```javascript
async function callApi(endpoint, method, data) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    // 如果有认证token，添加到请求头
    const token = localStorage.getItem('auth_token');
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(endpoint, options);
    return await response.json();
}
```

## 安全考虑

虽然前端仅用于API测试，但仍考虑了基本的安全措施：

1. 使用 Flask 的 `url_for()` 生成URL，避免硬编码
2. 实现基本的表单验证
3. 支持JWT Token认证
4. 管理控制台页面需要认证和授权
5. 密码输入框使用type="password"防止明文显示
6. 客户端密码强度校验

## 未来改进方向

如果需要进一步完善前端，可以考虑：

1. 引入前端框架（如Vue.js或React）进行重构
2. 改进UI/UX设计
3. 添加更多的交互功能
4. 实现更完善的错误处理
5. 添加更多的API测试工具功能
6. 增强用户个人中心功能
7. 实现记住登录状态功能

## 注意事项

- 前端代码主要用于API测试，不适用于生产环境
- 管理控制台功能可能需要根据实际API实现进行调整
- 样式和脚本文件未进行压缩，生产环境应考虑优化 