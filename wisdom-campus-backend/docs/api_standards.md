# 智慧校园学习助手系统 API 规范文档

## 一、API 基础规范

### 1.1 路由规范

所有API端点必须遵循以下格式：

```
/api/v1/{模块名}/{功能}
```

例如：
- `/api/v1/auth/login` - 用户登录
- `/api/v1/user/profile` - 获取用户资料
- `/api/v1/learning/courses` - 获取课程列表

### 1.2 请求方法

| 方法   | 用途                           |
|--------|--------------------------------|
| GET    | 获取资源                       |
| POST   | 创建资源                       |
| PUT    | 更新资源（全量替换）           |
| PATCH  | 更新资源（部分修改）           |
| DELETE | 删除资源                       |

### 1.3 状态码

| 状态码 | 描述                                       |
|--------|------------------------------------------|
| 200    | 成功                                     |
| 201    | 创建成功                                 |
| 400    | 请求参数错误                             |
| 401    | 未授权（未登录）                         |
| 403    | 权限不足                                 |
| 404    | 资源不存在                               |
| 409    | 资源冲突（如：用户已存在）               |
| 500    | 服务器错误                               |

## 二、统一响应格式

所有API响应必须采用以下格式：

```json
{
    "success": true/false,
    "code": 200,
    "message": "操作成功/失败原因",
    "data": { ... }
}
```

字段说明：
- `success`: 布尔值，表示请求是否成功
- `code`: 业务状态码（见下文错误码定义）
- `message`: 提示信息
- `data`: 实际数据（成功时返回数据，失败时可为null或包含错误详情）

## 三、错误码体系

错误码格式为5位数字，格式为`AABBB`：
- AA: 模块编号 (10-99)
- BBB: 具体错误编号 (000-999)

| 错误码  | 描述                        | 模块         |
|---------|---------------------------|--------------|
| 10000   | 系统错误                    | 通用         |
| 10001   | 无效的请求参数              | 通用         |
| 10002   | 未授权访问                  | 通用         |
| 10003   | 权限不足                    | 通用         |
| 10004   | 资源不存在                  | 通用         |
| 10005   | 数据库错误                  | 通用         |
| 20001   | 登录失败                    | 认证         |
| 20002   | 用户不存在                  | 认证         |
| 20003   | 密码错误                    | 认证         |
| 20004   | 邮箱未验证                  | 认证         |
| 20005   | 用户已存在                  | 认证         |
| 20006   | 学号已被注册                | 认证         |
| 20007   | 邮箱已被注册                | 认证         |
| 30001   | 用户不存在                  | 用户         |
| 30002   | 更新用户信息失败            | 用户         |
| 40001   | 课程不存在                  | 学习         |
| 40002   | 任务不存在                  | 学习         |

## 四、认证与授权

### 4.1 认证方式

系统使用JWT令牌认证，所有需要认证的API都应该：

- 在请求头中包含 `Authorization: Bearer {token}`
- 使用 `@requires_auth` 装饰器进行保护

### 4.2 认证API

| API 端点                   | 方法 | 描述                  | 需要认证 |
|----------------------------|------|---------------------|---------|
| `/api/v1/auth/login`       | POST | 用户登录             | 否      |
| `/api/v1/auth/register`    | POST | 用户注册             | 否      |
| `/api/v1/auth/check-verification` | POST | 检查邮箱验证状态 | 否 |
| `/api/v1/auth/resend-verification` | POST | 重发验证邮件 | 否 |
| `/api/v1/auth/status`      | GET  | 获取认证状态         | 否      |

## 五、API文档生成

- API文档采用Swagger UI生成
- 访问地址：`/api/docs/`
- 每个API端点都应当添加docstring注释，描述API功能、参数和返回值

## 六、开发规范

### 6.1 代码风格

- 使用PEP 8规范
- 使用4个空格缩进
- 不超过120个字符每行
- 使用蛇形命名法（snake_case）

### 6.2 提交规范

- 遵循 Git Flow 工作流
- 提交信息格式：`{类型}: {描述}`
- 类型包括：feat（新功能）、fix（修复）、docs（文档）、style（格式）、refactor（重构）等

### 6.3 工具类

开发过程中应当使用以下工具类统一API风格：

```python
# 统一响应
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode

# 成功响应
return api_success(
    message="操作成功",
    data=data
)

# 错误响应
return api_error(
    message=ErrorCode.get_message(ErrorCode.INVALID_REQUEST),
    error_code=ErrorCode.INVALID_REQUEST
)
```

## 七、示例代码

### 登录API示例

```python
@auth_bp.route("/login", methods=["POST"])
def api_login():
    """
    用户登录API
    ---
    tags:
      - 认证
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            student_id:
              type: string
              description: 学号
            password:
              type: string
              description: 密码
    responses:
      200:
        description: 登录成功
      400:
        description: 请求参数错误
      401:
        description: 登录失败
    """
    data = request.get_json()
    if not data:
        return api_error(
            message=ErrorCode.get_message(ErrorCode.INVALID_REQUEST),
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    # 业务逻辑
    
    return api_success(
        message="登录成功",
        data=result
    )
``` 