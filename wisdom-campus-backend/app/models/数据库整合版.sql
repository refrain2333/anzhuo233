-- 创建数据库
CREATE DATABASE IF NOT EXISTS xuesheng233 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE xuesheng233;

-- 先创建独立的基础表（无外键依赖）
-- 表：专业表 (Major)
CREATE TABLE major (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '专业名称',
    college VARCHAR(50) COMMENT '学院名称'
);

-- 表：学期表 (Semester)
CREATE TABLE semester (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL COMMENT '学期名称，如"2023-秋"',
    start_date DATE NOT NULL COMMENT '学期开始日期',
    end_date DATE NOT NULL COMMENT '学期结束日期',
    status ENUM('upcoming', 'active', 'completed') DEFAULT 'upcoming' COMMENT '学期状态'
);

-- 表：徽章表 (Badge)
CREATE TABLE badge (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '徽章名称',
    description TEXT COMMENT '徽章描述',
    type ENUM('study', 'focus', 'share', 'community') NOT NULL COMMENT '徽章类型'
);

-- 再创建依赖基础表的表
-- 表：用户表 (User) - 已集成更新内容
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) UNIQUE COMMENT '学号，唯一，可选字段',
    auth0_id VARCHAR(50) UNIQUE NOT NULL COMMENT 'Auth0 用户ID，唯一',
    auth0_sid VARCHAR(100) NULL COMMENT 'Auth0 会话ID',
    auth0_aud VARCHAR(100) NULL COMMENT 'Auth0 受众',
    auth0_iss VARCHAR(255) NULL COMMENT 'Auth0 发行者',
    name VARCHAR(100) COMMENT '用户姓名，从Auth0获取',
    nickname VARCHAR(50) COMMENT '用户昵称，从Auth0获取',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '用户邮箱，唯一',
    email_verified BOOLEAN DEFAULT FALSE COMMENT '邮箱是否已验证，从Auth0获取',
    avatar_url VARCHAR(255) COMMENT '头像URL，从Auth0获取',
    bio TEXT COMMENT '个人简介',
    major_id INT COMMENT '专业ID，外键',
    current_semester_id INT COMMENT '当前学期ID，外键',
    total_study_time INT DEFAULT 0 COMMENT '总学习时长（分钟）',
    gpa DECIMAL(3,2) DEFAULT 0.00 COMMENT 'GPA成绩',
    exp_points INT DEFAULT 0 COMMENT '经验值',
    level INT DEFAULT 1 COMMENT '用户等级',
    is_admin BOOLEAN DEFAULT FALSE COMMENT '是否为管理员',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    auth0_updated_at DATETIME COMMENT 'Auth0用户信息最后更新时间 (updated_at字段)',
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active' COMMENT '用户状态',
    FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE SET NULL,
    FOREIGN KEY (current_semester_id) REFERENCES semester(id) ON DELETE SET NULL
);

-- 表：课程表 (Course)
CREATE TABLE course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '课程名称',
    code VARCHAR(20) UNIQUE NOT NULL COMMENT '课程代码，唯一',
    semester_id INT COMMENT '学期ID，外键',
    credit DECIMAL(3,1) COMMENT '学分',
    FOREIGN KEY (semester_id) REFERENCES semester(id) ON DELETE SET NULL
);

-- 创建依赖于user和course的表
-- 表：用户画像表 (UserProfile)
CREATE TABLE user_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    learning_style ENUM('visual', 'auditory', 'kinesthetic', 'mixed') COMMENT '学习风格',
    preferred_time ENUM('morning', 'afternoon', 'evening', 'night') COMMENT '偏好学习时间',
    avg_focus_duration INT COMMENT '平均专注时长（分钟）',
    strengths TEXT COMMENT '学习优势',
    weaknesses TEXT COMMENT '学习弱点',
    study_habits TEXT COMMENT '学习习惯',
    notification_email_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用邮箱通知',
    notification_app_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用应用内通知',
    notification_types TEXT COMMENT '通知类型偏好（JSON或逗号分隔字符串）',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：课程安排表 (CourseSchedule)
CREATE TABLE course_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL COMMENT '课程ID，外键',
    user_id INT NOT NULL COMMENT '用户ID，外键',
    day_of_week ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday') NOT NULL COMMENT '星期几',
    start_time TIME NOT NULL COMMENT '开始时间',
    end_time TIME NOT NULL COMMENT '结束时间',
    location VARCHAR(100) COMMENT '上课地点',
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：成绩表 (Grade)
CREATE TABLE grade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    course_id INT NOT NULL COMMENT '课程ID，外键',
    score DECIMAL(5,2) COMMENT '成绩',
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE
);

-- 表：专业课程表 (MajorCourse)
CREATE TABLE major_course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    major_id INT NOT NULL COMMENT '专业ID，外键',
    course_id INT NOT NULL COMMENT '课程ID，外键',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否为必修课',
    FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE
);

-- 表：学习计划表 (StudyPlan)
CREATE TABLE study_plan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    title VARCHAR(100) NOT NULL COMMENT '计划标题',
    description TEXT COMMENT '计划描述',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    progress DECIMAL(5,2) DEFAULT 0.00 COMMENT '进度百分比',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    status ENUM('active', 'completed', 'abandoned') DEFAULT 'active' COMMENT '计划状态',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：任务表 (Task)
CREATE TABLE task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    plan_id INT COMMENT '学习计划ID，外键',
    content VARCHAR(200) NOT NULL COMMENT '任务内容',
    deadline DATETIME COMMENT '截止日期',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '优先级',
    status ENUM('pending', 'in_progress', 'reviewing', 'revising', 'completed', 'delayed', 'cancelled') DEFAULT 'pending' COMMENT '任务状态',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES study_plan(id) ON DELETE SET NULL
);

-- 表：专注记录表 (FocusRecord)
CREATE TABLE focus_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    duration INT NOT NULL COMMENT '专注时长（分钟）',
    focus_score INT COMMENT '专注度评分',
    task_id INT COMMENT '关联任务ID，外键',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE SET NULL
);

-- 表：打卡表 (CheckIn)
CREATE TABLE check_in (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    check_in_date DATE NOT NULL COMMENT '打卡日期',
    streak_count INT DEFAULT 0 COMMENT '连续打卡天数',
    note VARCHAR(200) COMMENT '打卡备注',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：笔记表 (Note)
CREATE TABLE note (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    title VARCHAR(100) NOT NULL COMMENT '笔记标题',
    content TEXT COMMENT '笔记内容',
    category VARCHAR(50) COMMENT '笔记分类',
    is_starred BOOLEAN DEFAULT FALSE COMMENT '是否星标',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    share_count INT DEFAULT 0 COMMENT '分享次数',
    summary TEXT COMMENT '笔记摘要',
    summary_generated_at DATETIME COMMENT '摘要生成时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：笔记文件表 (NoteFile)
CREATE TABLE note_file (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL COMMENT '笔记ID，外键',
    file_url VARCHAR(255) NOT NULL COMMENT '文件URL',
    file_type ENUM('pdf', 'image', 'word', 'text') NOT NULL COMMENT '文件类型',
    file_size INT NOT NULL COMMENT '文件大小（字节）',
    file_name VARCHAR(100) NOT NULL COMMENT '文件名',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    api_processed BOOLEAN DEFAULT FALSE COMMENT '是否已通过API处理',
    api_response TEXT COMMENT 'API处理结果',
    FOREIGN KEY (note_id) REFERENCES note(id) ON DELETE CASCADE
);

-- 表：笔记标签表 (NoteTag)
CREATE TABLE note_tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL COMMENT '笔记ID，外键',
    tag_name VARCHAR(50) NOT NULL COMMENT '标签名称',
    FOREIGN KEY (note_id) REFERENCES note(id) ON DELETE CASCADE
);

-- 表：帖子表 (Post)
CREATE TABLE post (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    title VARCHAR(100) NOT NULL COMMENT '帖子标题',
    content TEXT NOT NULL COMMENT '帖子内容',
    category ENUM('note_share', 'qa', 'discussion') NOT NULL COMMENT '帖子类别',
    is_anonymous BOOLEAN DEFAULT FALSE COMMENT '是否匿名',
    likes_count INT DEFAULT 0 COMMENT '点赞数',
    comments_count INT DEFAULT 0 COMMENT '评论数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    status ENUM('normal', 'reported', 'banned') DEFAULT 'normal' COMMENT '帖子状态',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：评论表 (Comment)
CREATE TABLE comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL COMMENT '帖子ID，外键',
    user_id INT NOT NULL COMMENT '用户ID，外键',
    content TEXT NOT NULL COMMENT '评论内容',
    parent_id INT COMMENT '父评论ID，外键，用于回复',
    likes_count INT DEFAULT 0 COMMENT '点赞数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    status ENUM('normal', 'reported', 'banned') DEFAULT 'normal' COMMENT '评论状态',
    FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comment(id) ON DELETE SET NULL
);

-- 表：点赞表 (LikeRecord)
CREATE TABLE like_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    target_type ENUM('post', 'comment') NOT NULL COMMENT '点赞目标类型',
    target_id INT NOT NULL COMMENT '点赞目标ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：收藏表 (Favorite)
CREATE TABLE favorite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    target_type ENUM('post', 'note', 'resource') NOT NULL COMMENT '收藏目标类型',
    target_id INT NOT NULL COMMENT '收藏目标ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：私信表 (Message)
CREATE TABLE message (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL COMMENT '发送者ID，外键',
    receiver_id INT NOT NULL COMMENT '接收者ID，外键',
    content TEXT NOT NULL COMMENT '私信内容',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    FOREIGN KEY (sender_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：用户徽章表 (UserBadge)
CREATE TABLE user_badge (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    badge_id INT NOT NULL COMMENT '徽章ID，外键',
    awarded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '授予时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badge(id) ON DELETE CASCADE
);

-- 表：学习资源表 (LearningResource)
CREATE TABLE learning_resource (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL COMMENT '资源标题',
    url VARCHAR(255) NOT NULL COMMENT '资源URL',
    type ENUM('video', 'article', 'book', 'tool', 'other') NOT NULL COMMENT '资源类型',
    category VARCHAR(50) COMMENT '资源分类',
    description TEXT COMMENT '资源描述',
    uploaded_by INT NOT NULL COMMENT '上传者ID，外键',
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传日期',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    rating DECIMAL(3,2) DEFAULT 0.00 COMMENT '评分',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '资源审批状态',
    reviewed_by INT COMMENT '审核者ID，外键',
    review_date DATETIME COMMENT '审核日期',
    review_comments TEXT COMMENT '审核备注',
    FOREIGN KEY (uploaded_by) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES user(id) ON DELETE SET NULL
);

-- 表：资源推荐表 (ResourceRecommendation)
CREATE TABLE resource_recommendation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    resource_id INT NOT NULL COMMENT '资源ID，外键',
    reason TEXT COMMENT '推荐原因',
    recommended_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '推荐时间',
    api_response TEXT COMMENT 'API响应数据',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES learning_resource(id) ON DELETE CASCADE
);

-- 表：资源评论表 (ResourceComment)
CREATE TABLE resource_comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL COMMENT '资源ID，外键',
    user_id INT NOT NULL COMMENT '用户ID，外键',
    content TEXT NOT NULL COMMENT '评论内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (resource_id) REFERENCES learning_resource(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：学习行为表 (LearningBehavior)
CREATE TABLE learning_behavior (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    behavior_type ENUM('study_time', 'task_completion', 'note_creation', 'post_interaction') NOT NULL COMMENT '行为类型',
    target_id INT COMMENT '目标ID，具体对象ID',
    duration INT COMMENT '持续时间（分钟）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '行为发生时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：学习分析表 (LearningAnalysis)
CREATE TABLE learning_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析日期',
    study_efficiency DECIMAL(3,2) DEFAULT 0.00 COMMENT '学习效率',
    behavior_summary TEXT COMMENT '行为总结',
    suggestion TEXT COMMENT '改进建议',
    api_response TEXT COMMENT 'API响应数据',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：AI学习助手表 (AILearningAssistant)
CREATE TABLE ai_learning_assistant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    assistant_type ENUM('plan_suggestion', 'resource_recommendation', 'study_tip') NOT NULL COMMENT '助手类型',
    content TEXT NOT NULL COMMENT '助手内容',
    api_response TEXT COMMENT 'API响应数据',
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：AI提问表 (AIQuestion) - 补充缺失的表
CREATE TABLE ai_question (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    question TEXT NOT NULL COMMENT '用户提问',
    context_type ENUM('course', 'note', 'other') COMMENT '提问上下文类型',
    context_id INT COMMENT '上下文ID',
    answer TEXT COMMENT 'AI回答',
    api_response TEXT COMMENT 'API响应数据',
    asked_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提问时间',
    satisfaction_rating INT COMMENT '用户满意度评分（1-5）',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：AI配置表 (AIConfig)
CREATE TABLE ai_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    api_type ENUM('openai', 'azure', 'anthropic', 'baidu', 'xunfei', 'other') DEFAULT 'openai' COMMENT 'API类型',
    api_key VARCHAR(255) COMMENT 'API密钥，加密存储',
    api_endpoint VARCHAR(255) COMMENT 'API端点URL',
    model_name VARCHAR(100) DEFAULT 'gpt-3.5-turbo' COMMENT '模型名称',
    max_tokens INT DEFAULT 2000 COMMENT '最大令牌数',
    temperature DECIMAL(3,2) DEFAULT 0.70 COMMENT '创造性参数，0-1之间',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    quota_used INT DEFAULT 0 COMMENT '已使用配额',
    preferred_language ENUM('zh', 'en', 'auto') DEFAULT 'zh' COMMENT '偏好语言',
    response_length ENUM('short', 'medium', 'detailed') DEFAULT 'medium' COMMENT '回复长度偏好',
    creativity_level ENUM('factual', 'balanced', 'creative') DEFAULT 'balanced' COMMENT '创造性水平',
    include_sources BOOLEAN DEFAULT TRUE COMMENT '是否包含引用来源',
    auto_summary BOOLEAN DEFAULT FALSE COMMENT '是否自动生成摘要',
    save_conversation BOOLEAN DEFAULT TRUE COMMENT '是否保存对话历史',
    context_memory INT DEFAULT 5 COMMENT '上下文记忆轮数',
    system_prompt TEXT COMMENT '系统提示词设置',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ai_config (user_id)
);

-- 表：通知表 (Notification)
CREATE TABLE notification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    title VARCHAR(100) NOT NULL COMMENT '通知标题',
    content TEXT NOT NULL COMMENT '通知内容',
    type ENUM('system', 'task', 'community', 'grade', 'other') NOT NULL COMMENT '通知类型',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    target_type ENUM('task', 'post', 'grade', 'other') COMMENT '目标类型',
    target_id INT COMMENT '目标ID',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：搜索历史表 (SearchHistory)
CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    query VARCHAR(200) NOT NULL COMMENT '搜索查询词',
    search_type ENUM('note', 'resource', 'post', 'course', 'other') NOT NULL COMMENT '搜索类型',
    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '搜索时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 表：管理员日志表 (AdminLog)
CREATE TABLE admin_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL COMMENT '管理员ID，外键',
    action VARCHAR(100) NOT NULL COMMENT '操作行为',
    target_type ENUM('user', 'post', 'comment', 'grade', 'resource') NOT NULL COMMENT '目标类型',
    target_id INT NOT NULL COMMENT '目标ID',
    detail TEXT COMMENT '操作详情',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    FOREIGN KEY (admin_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 创建索引以优化查询性能
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_auth0_id ON user(auth0_id);
CREATE INDEX idx_user_auth0_sid ON user(auth0_sid);
CREATE INDEX idx_user_auth0_aud ON user(auth0_aud);
CREATE INDEX idx_user_auth0_iss ON user(auth0_iss);
CREATE INDEX idx_course_code ON course(code);
CREATE INDEX idx_task_user_id ON task(user_id);
CREATE INDEX idx_task_deadline ON task(deadline);
CREATE INDEX idx_task_plan_id ON task(plan_id);
CREATE INDEX idx_note_user_id ON note(user_id);
CREATE INDEX idx_post_user_id ON post(user_id);
CREATE INDEX idx_post_category ON post(category);
CREATE INDEX idx_comment_post_id ON comment(post_id);
CREATE INDEX idx_comment_user_id ON comment(user_id);
CREATE INDEX idx_notification_user_id ON notification(user_id);
CREATE INDEX idx_notification_is_read ON notification(is_read);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_query ON search_history(query);
CREATE INDEX idx_course_schedule_user_id ON course_schedule(user_id);
CREATE INDEX idx_course_schedule_course_id ON course_schedule(course_id);
CREATE INDEX idx_note_file_note_id ON note_file(note_id);
CREATE INDEX idx_note_tag_note_id ON note_tag(note_id);
CREATE INDEX idx_message_sender_id ON message(sender_id);
CREATE INDEX idx_message_receiver_id ON message(receiver_id);
CREATE INDEX idx_learning_resource_uploaded_by ON learning_resource(uploaded_by);
CREATE INDEX idx_resource_recommendation_user_id ON resource_recommendation(user_id);
CREATE INDEX idx_resource_comment_resource_id ON resource_comment(resource_id);
CREATE INDEX idx_semester_status ON semester(status);
CREATE INDEX idx_user_current_semester ON user(current_semester_id);
CREATE INDEX idx_ai_config_user_id ON ai_config(user_id);
CREATE INDEX idx_ai_config_api_type ON ai_config(api_type);

-- 创建唯一约束以避免重复数据
ALTER TABLE grade ADD UNIQUE INDEX idx_user_course_unique (user_id, course_id);
ALTER TABLE check_in ADD UNIQUE INDEX idx_user_check_in_date_unique (user_id, check_in_date);
ALTER TABLE like_record ADD UNIQUE INDEX idx_user_target_unique (user_id, target_type, target_id);
ALTER TABLE favorite ADD UNIQUE INDEX idx_user_favorite_unique (user_id, target_type, target_id);

-- 插入初始数据
-- 插入专业数据
INSERT INTO major (name, college) VALUES 
    ('计算机科学与技术', '计算机学院'),
    ('电子工程', '电子信息学院'),
    ('机械工程', '机械学院'),
    ('经济学', '经济管理学院');

-- 插入学期数据
INSERT INTO semester (name, start_date, end_date, status) VALUES 
    ('2023-秋', '2023-09-01', '2024-01-15', 'active'),
    ('2024-春', '2024-02-20', '2024-06-30', 'upcoming'),
    ('2022-秋', '2022-09-01', '2023-01-15', 'completed');

-- 插入课程数据
INSERT INTO course (name, code, semester_id, credit) VALUES 
    ('数据结构', 'CS101', 1, 3.0),
    ('操作系统', 'CS202', 1, 4.0),
    ('电路原理', 'EE101', 1, 3.5),
    ('微观经济学', 'ECON101', 1, 3.0);

-- 插入专业课程关联数据
INSERT INTO major_course (major_id, course_id, is_required) VALUES 
    (1, 1, TRUE),  -- 计算机科学与技术 - 数据结构 (必修)
    (1, 2, TRUE),  -- 计算机科学与技术 - 操作系统 (必修)
    (2, 3, TRUE),  -- 电子工程 - 电路原理 (必修)
    (4, 4, TRUE);  -- 经济学 - 微观经济学 (必修)

-- 插入徽章数据
INSERT INTO badge (name, description, type) VALUES 
    ('学习新星', '完成第一个学习计划', 'study'),
    ('专注达人', '单次专注超过60分钟', 'focus'),
    ('分享达人', '分享10篇笔记或资源', 'share'),
    ('社区之星', '获得100个点赞', 'community');

-- 创建alembic_version表（用于迁移记录）
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);

-- 生成迁移记录
INSERT INTO alembic_version (version_num) VALUES ('数据库模型一致性更新'); 