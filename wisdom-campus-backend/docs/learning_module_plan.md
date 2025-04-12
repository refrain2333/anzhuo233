# 智慧校园学习助手系统 - 学习模块实现计划

## 问题修复记录

### 已修复的问题

1. **学习模块导入缺失子模块错误**
   - 问题：学习模块的`__init__.py`文件中导入了不存在的子模块（courses, grades, tasks, focus, checkin, plans）
   - 解决方案：暂时注释掉导入语句，并添加临时路由提示模块正在建设中
   - 文件路径：`app/api/v1/learning/__init__.py`

2. **User模型字段不匹配问题**
   - 问题：认证模块中引用了User模型中不存在的字段（verification_sent_at, last_login, grade, last_active）
   - 解决方案：
     - 移除User模型中不存在的`verification_sent_at`字段
     - 在认证模块中移除对`last_login`和`last_active`字段的引用
     - 移除对`grade`字段的引用，改为存储在Auth0的user_metadata中
     - 在User模型中注释掉`last_active`字段定义，添加TODO注释说明需要数据库迁移

### 待完成的工作

1. **数据库迁移**
   - 问题：系统检测到了缺少的数据库字段，需要执行迁移脚本更新数据库结构
   - 建议：
     - 执行`数据库更新.sql`脚本，确保数据库结构与模型定义一致
     - 为`user`表添加`last_active`字段，示例SQL:
     ```sql
     ALTER TABLE user ADD COLUMN last_active DATETIME COMMENT '最后活跃时间' AFTER auth0_updated_at;
     ```

## 数据库同步建议

由于模型定义和数据库表结构之间存在不一致，建议采取以下措施：

1. **执行数据库检查脚本**：使用`数据库更新-验证功能.sql`脚本检查所有必要字段是否存在

2. **添加缺失字段**：
   ```sql
   -- 为user表添加缺失的字段
   ALTER TABLE user ADD COLUMN last_active DATETIME COMMENT '最后活跃时间' AFTER auth0_updated_at;
   
   -- 创建对应的索引
   CREATE INDEX idx_user_last_active ON user(last_active);
   ```

3. **更新模型定义**：修改完成后，取消User模型中对应字段的注释

## 学习模块实现计划

### 1. 课程管理模块（courses.py）

**功能点：**
- 获取课程列表（支持分页、筛选）
- 获取课程详情
- 获取用户选课列表
- 选课/退课功能
- 课程表查询

**API端点：**
- GET `/api/v1/learning/courses` - 获取课程列表
- GET `/api/v1/learning/courses/{id}` - 获取课程详情
- GET `/api/v1/learning/courses/my` - 获取用户选课列表
- POST `/api/v1/learning/courses/{id}/enroll` - 选课
- DELETE `/api/v1/learning/courses/{id}/enroll` - 退课
- GET `/api/v1/learning/schedules` - 获取用户课程表

### 2. 成绩模块（grades.py）

**功能点：**
- 获取用户成绩列表
- 获取成绩统计信息
- 成绩分析与趋势

**API端点：**
- GET `/api/v1/learning/grades` - 获取用户成绩列表
- GET `/api/v1/learning/grades/analysis` - 获取成绩分析
- GET `/api/v1/learning/grades/trend` - 获取成绩趋势

### 3. 任务模块（tasks.py）

**功能点：**
- 创建/编辑/删除任务
- 获取任务列表
- 更新任务状态
- 设置提醒

**API端点：**
- GET `/api/v1/learning/tasks` - 获取任务列表
- POST `/api/v1/learning/tasks` - 创建任务
- GET `/api/v1/learning/tasks/{id}` - 获取任务详情
- PUT `/api/v1/learning/tasks/{id}` - 更新任务
- DELETE `/api/v1/learning/tasks/{id}` - 删除任务
- PUT `/api/v1/learning/tasks/{id}/status` - 更新任务状态

### 4. 专注记录模块（focus.py）

**功能点：**
- 开始/结束专注记录
- 获取专注历史记录
- 专注统计分析

**API端点：**
- POST `/api/v1/learning/focus/start` - 开始专注
- POST `/api/v1/learning/focus/end` - 结束专注
- GET `/api/v1/learning/focus/records` - 获取专注记录
- GET `/api/v1/learning/focus/analysis` - 获取专注分析

### 5. 每日打卡模块（checkin.py）

**功能点：**
- 日常学习打卡
- 获取打卡记录
- 连续打卡统计

**API端点：**
- POST `/api/v1/learning/checkin` - 打卡
- GET `/api/v1/learning/checkin/records` - 获取打卡记录
- GET `/api/v1/learning/checkin/streak` - 获取连续打卡天数

### 6. 学习计划模块（plans.py）

**功能点：**
- 创建/编辑/删除学习计划
- 获取计划列表
- 更新计划进度
- 计划分析与建议

**API端点：**
- GET `/api/v1/learning/plans` - 获取学习计划列表
- POST `/api/v1/learning/plans` - 创建学习计划
- GET `/api/v1/learning/plans/{id}` - 获取学习计划详情
- PUT `/api/v1/learning/plans/{id}` - 更新学习计划
- DELETE `/api/v1/learning/plans/{id}` - 删除学习计划
- PUT `/api/v1/learning/plans/{id}/progress` - 更新计划进度

## 实现优先级

1. 课程管理模块（基础功能）
2. 任务模块（日常学习管理）
3. 专注记录模块（记录学习时间）
4. 成绩模块（学习成果展示）
5. 每日打卡模块（习惯养成）
6. 学习计划模块（长期规划）

## 技术实现要点

1. 所有API使用统一的响应格式（`api_success`/`api_error`）
2. 权限控制：使用JWT验证用户身份
3. 错误处理：使用统一的错误码和错误信息
4. 数据校验：使用marshmallow进行数据验证
5. 文档支持：所有API支持Swagger文档自动生成 