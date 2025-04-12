# 用户注册流程与邮箱验证

## 注册流程概述

智慧校园学习助手系统的用户注册采用以下流程：

1. 用户访问注册页面，填写必要信息（学号、姓名、邮箱、密码）
2. 表单提交后，系统检查学号是否已存在
3. 系统调用Auth0 API创建用户账户，并标记为需要邮箱验证
4. 系统在本地数据库创建用户记录，状态标记为`inactive`（等待验证）
5. 返回注册成功信息，并将用户引导至验证等待页面
6. Auth0自动向用户邮箱发送验证邮件
7. 用户在验证等待页面可以：
   - 查看验证状态
   - 重新发送验证邮件
   - 取消注册（删除账号）
8. 如果60秒内未验证，系统自动删除未验证账号
9. 用户点击邮件中的验证链接完成验证
10. 验证成功后，系统更新用户状态为`active`并允许登录

## 未验证账号处理机制

为了提高用户体验，系统对未验证账号有特殊处理：

1. **重复注册处理**：
   - 如果用户使用相同学号和邮箱重复注册（例如因网络问题重试），系统视为更新操作而非拒绝
   - 如果学号已被其他邮箱注册或已验证，则拒绝注册

2. **自动清理机制**：
   - 验证等待页面显示60秒倒计时
   - 60秒后自动触发清理过程，删除未验证账号
   - 系统后台定期清理超过1分钟未验证的账号

3. **手动取消功能**：
   - 用户可以点击"取消注册"按钮主动删除账号
   - 取消后可以使用相同学号和邮箱重新注册

## 关键API端点

### 1. 用户注册

```
POST /api/v1/auth/register
```

**请求参数：**
```json
{
  "student_id": "20221113230",
  "name": "张三",
  "email": "zhangsan@example.com",
  "password": "password123"
}
```

**成功响应：**
```json
{
  "success": true,
  "code": 200,
  "message": "注册成功，请查收验证邮件完成注册",
  "data": {
    "user_id": 1,
    "auth0_id": "auth0|1234567890",
    "email": "zhangsan@example.com",
    "student_id": "20221113230",
    "email_verified": false,
    "verification_pending": true
  }
}
```

### 2. 检查验证状态

```
POST /api/v1/auth/check-verification
```

**请求参数：**
```json
{
  "auth0_id": "auth0|1234567890"
}
```

**成功响应：**
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "email_verified": true,
    "can_login": true
  }
}
```

### 3. 重新发送验证邮件

```
POST /api/v1/auth/resend-verification
```

**请求参数：**
```json
{
  "auth0_id": "auth0|1234567890"
}
```

**成功响应：**
```json
{
  "success": true,
  "code": 200,
  "message": "验证邮件已重新发送，请查收"
}
```

### 4. 取消注册

```
POST /api/v1/auth/cancel-registration
```

**请求参数：**
```json
{
  "auth0_id": "auth0|1234567890"
}
```

**成功响应：**
```json
{
  "success": true,
  "code": 200,
  "message": "注册已取消，您可以重新注册",
  "data": {
    "student_id": "20221113230",
    "email": "zhangsan@example.com",
    "auth0_deleted": true
  }
}
```

### 5. 清理未验证用户

```
POST /api/v1/auth/cleanup-unverified
```

**请求参数：**
```json
{
  "minutes": 1
}
```

**成功响应：**
```json
{
  "success": true,
  "code": 200,
  "message": "清理完成，已删除 3 个未验证用户",
  "data": {
    "deleted_count": 3
  }
}
```

### 6. 验证等待页面

```
GET /api/v1/auth/verification-waiting?auth0_id=auth0|1234567890&email=zhangsan@example.com
```

## 邮箱验证注意事项

1. **自动验证检查**：验证等待页面会每30秒自动检查一次验证状态
2. **手动验证检查**：用户可以点击"刷新验证状态"按钮手动检查
3. **验证超时**：邮件验证链接有效期默认为24小时（由Auth0控制）
4. **重发间隔**：为防止滥用，重发按钮有10秒冷却时间
5. **自动清理**：未验证账号将在60秒后自动删除
6. **手动取消**：用户可以随时取消注册，释放学号和邮箱

## 开发说明

### 前端实现

#### 验证等待页面特性

验证等待页面不仅显示验证状态，还包含多项用户友好功能：

1. **60秒倒计时**：提示用户完成验证的时间限制
2. **验证状态实时更新**：每30秒自动查询一次
3. **取消注册按钮**：允许用户放弃当前注册
4. **重新发送验证邮件**：解决没收到邮件的问题

```javascript
// 倒计时功能
const countdownInterval = setInterval(function() {
    timeLeft--;
    countdownEl.textContent = timeLeft;
    
    if (timeLeft <= 0) {
        clearInterval(countdownInterval);
        triggerCleanup();
    }
}, 1000);

// 取消注册
async function cancelRegistration() {
    try {
        const response = await fetch('/api/v1/auth/cancel-registration', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                auth0_id: auth0Id
            })
        });
        
        // 处理响应...
    } catch (error) {
        // 错误处理...
    }
}
```

### 后端实现

#### 重复注册处理逻辑

```python
# 检查学号是否已被注册
existing_user = User.query.filter_by(student_id=student_id).first()
if existing_user:
    # 如果已存在用户，但邮箱相同且未验证，则允许更新而不是拒绝
    if existing_user.email == email and not existing_user.email_verified:
        # 记录最后一次注册尝试时间，更新用户信息
        # ...继续创建流程
    else:
        # 拒绝注册
```

#### 自动清理机制

```python
# 计算截止时间
cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

# 查找所有未验证且注册时间早于截止时间的用户
unverified_users = User.query.filter(
    User.email_verified == False,
    User.auth0_updated_at < cutoff_time
).all()

# 删除这些用户
```

## 未来优化方向

1. 添加第三方登录选项（微信、QQ等）
2. 实现手机号验证作为备选验证方式
3. 增加验证过程的安全性检查
4. 优化邮件模板，提高用户体验
5. 在数据库层面添加定时任务，定期清理未验证用户 