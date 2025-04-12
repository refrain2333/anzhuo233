-- 创建数据库
CREATE DATABASE IF NOT EXISTS xuesheng233 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE xuesheng233;

-- 用户模块相关表
-- 表：用户表 (User)
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) UNIQUE NOT NULL COMMENT '学号，唯一',
    auth0_id VARCHAR(50) UNIQUE NOT NULL COMMENT 'Auth0 用户ID，唯一',
    name VARCHAR(50) COMMENT '用户姓名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '用户邮箱，唯一',
    email_verified BOOLEAN DEFAULT FALSE COMMENT '邮箱是否已验证',
    password_hash VARCHAR(128) COMMENT '密码哈希（可选，若使用Auth0可能不直接使用）',
    avatar_url VARCHAR(255) COMMENT '头像URL',
    bio TEXT COMMENT '个人简介',
    major_id INT COMMENT '专业ID，外键',
    total_study_time INT DEFAULT 0 COMMENT '总学习时长（分钟）',
    gpa DECIMAL(3,2) DEFAULT 0.00 COMMENT 'GPA成绩',
    exp_points INT DEFAULT 0 COMMENT '经验值',
    level INT DEFAULT 1 COMMENT '用户等级',
    is_admin BOOLEAN DEFAULT FALSE COMMENT '是否为管理员',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active' COMMENT '用户状态'
);

-- 表：专业表 (Major)
CREATE TABLE major (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '专业名称',
    college VARCHAR(50) COMMENT '学院名称'
);

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

-- 学习模块相关表
-- 表：课程表 (Course)
CREATE TABLE course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '课程名称',
    code VARCHAR(20) UNIQUE NOT NULL COMMENT '课程代码，唯一',
    semester VARCHAR(20) COMMENT '学期',
    credit DECIMAL(3,1) COMMENT '学分'
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

-- 表：任务表 (Task)
CREATE TABLE task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    plan_id INT COMMENT '学习计划ID，外键',
    content VARCHAR(200) NOT NULL COMMENT '任务内容',
    deadline DATETIME COMMENT '截止日期',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '优先级',
    status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending' COMMENT '任务状态',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
    -- FOREIGN KEY (plan_id) REFERENCES study_plan(id) ON DELETE SET NULL -- 后续定义study_plan表后再添加
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

-- 笔记模块相关表
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

-- 社区模块相关表
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

-- 表：点赞表 (Like)
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

-- 成就模块相关表
-- 表：徽章表 (Badge)
CREATE TABLE badge (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '徽章名称',
    description TEXT COMMENT '徽章描述',
    type ENUM('study', 'focus', 'share', 'community') NOT NULL COMMENT '徽章类型'
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

-- 学习计划模块相关表
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

-- 知识图谱模块相关表
-- 表：知识点表 (KnowledgePoint)
CREATE TABLE knowledge_point (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '知识点名称',
    description TEXT COMMENT '知识点描述',
    category VARCHAR(50) COMMENT '知识点分类',
    course_id INT COMMENT '课程ID，外键',
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE SET NULL
);

-- 表：知识点关系表 (KnowledgeRelation)
CREATE TABLE knowledge_relation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL COMMENT '父知识点ID，外键',
    child_id INT NOT NULL COMMENT '子知识点ID，外键',
    relation_type ENUM('prerequisite', 'related', 'application') NOT NULL COMMENT '关系类型',
    FOREIGN KEY (parent_id) REFERENCES knowledge_point(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES knowledge_point(id) ON DELETE CASCADE
);

-- 表：用户知识掌握度表 (UserKnowledgeMastery)
CREATE TABLE user_knowledge_mastery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    knowledge_id INT NOT NULL COMMENT '知识点ID，外键',
    mastery_level DECIMAL(3,2) DEFAULT 0.00 COMMENT '掌握度（0-100）',
    last_assessed DATETIME COMMENT '最后评估时间',
    confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT '自信度（0-100）',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_point(id) ON DELETE CASCADE
);

-- 学习资源模块相关表
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
    FOREIGN KEY (uploaded_by) REFERENCES user(id) ON DELETE CASCADE
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

-- 学习分析模块相关表
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

-- AI辅助模块相关表
-- 表：AI提问表 (AIQuestion)
CREATE TABLE ai_question (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    question TEXT NOT NULL COMMENT '用户提问',
    context_type ENUM('course', 'note', 'knowledge_point') COMMENT '提问上下文类型',
    context_id INT COMMENT '上下文ID',
    answer TEXT COMMENT 'AI回答',
    api_response TEXT COMMENT 'API响应数据',
    asked_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提问时间',
    satisfaction_rating INT COMMENT '用户满意度评分（1-5）',
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

-- 通知模块相关表
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

-- 搜索历史模块相关表
-- 表：搜索历史表 (SearchHistory)
CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID，外键',
    query VARCHAR(200) NOT NULL COMMENT '搜索查询词',
    search_type ENUM('note', 'resource', 'post', 'course', 'other') NOT NULL COMMENT '搜索类型',
    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '搜索时间',
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 管理员模块相关表
-- 表：举报表 (Report)
CREATE TABLE report (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL COMMENT '举报人ID，外键',
    target_type ENUM('post', 'comment', 'note', 'resource') NOT NULL COMMENT '举报目标类型',
    target_id INT NOT NULL COMMENT '举报目标ID',
    reason TEXT NOT NULL COMMENT '举报原因',
    status ENUM('pending', 'processed', 'rejected') DEFAULT 'pending' COMMENT '处理状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '举报时间',
    FOREIGN KEY (reporter_id) REFERENCES user(id) ON DELETE CASCADE
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

-- 完善外键约束（之前未定义的表）
ALTER TABLE user ADD FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE SET NULL;
ALTER TABLE task ADD FOREIGN KEY (plan_id) REFERENCES study_plan(id) ON DELETE SET NULL;

-- 创建索引以优化查询性能
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_auth0_id ON user(auth0_id);
CREATE INDEX idx_course_code ON course(code);
CREATE INDEX idx_task_user_id ON task(user_id);
CREATE INDEX idx_task_deadline ON task(deadline);
CREATE INDEX idx_note_user_id ON note(user_id);
CREATE INDEX idx_post_user_id ON post(user_id);
CREATE INDEX idx_comment_post_id ON comment(post_id);
CREATE INDEX idx_notification_user_id ON notification(user_id);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);

-- 插入初始数据（可选，仅作示例）
INSERT INTO major (name, college) VALUES ('计算机科学与技术', '计算机学院');
INSERT INTO major (name, college) VALUES ('电子工程', '电子信息学院');
