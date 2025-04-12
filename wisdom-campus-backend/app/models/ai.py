"""
AI助手与通知系统相关模型
"""
from app import db
from datetime import datetime
from app.models.user import User

class AILearningAssistant(db.Model):
    """AI学习助手模型"""
    __tablename__ = 'ai_learning_assistant'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    assistant_type = db.Column(db.Enum('plan_suggestion', 'resource_recommendation', 'study_tip'), 
                             nullable=False, comment='助手类型')
    content = db.Column(db.Text, nullable=False, comment='助手内容')
    api_response = db.Column(db.Text, comment='API响应数据')
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, comment='生成时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('ai_assistants', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AILearningAssistant {self.user_id} - {self.assistant_type}>'

class AIQuestion(db.Model):
    """AI提问模型"""
    __tablename__ = 'ai_question'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    question = db.Column(db.Text, nullable=False, comment='用户提问')
    context_type = db.Column(db.Enum('course', 'note', 'other'), comment='提问上下文类型')
    context_id = db.Column(db.Integer, comment='上下文ID')
    answer = db.Column(db.Text, comment='AI回答')
    api_response = db.Column(db.Text, comment='API响应数据')
    asked_at = db.Column(db.DateTime, default=datetime.utcnow, comment='提问时间')
    satisfaction_rating = db.Column(db.Integer, comment='用户满意度评分（1-5）')
    
    # 关系
    user = db.relationship('User', backref=db.backref('ai_questions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AIQuestion {self.user_id} - {self.question[:20]}>'

class AIConfig(db.Model):
    """AI配置模型"""
    __tablename__ = 'ai_config'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    api_type = db.Column(db.Enum('openai', 'azure', 'anthropic', 'baidu', 'xunfei', 'other'), 
                        default='openai', comment='API类型')
    api_key = db.Column(db.String(255), comment='API密钥，加密存储')
    api_endpoint = db.Column(db.String(255), comment='API端点URL')
    model_name = db.Column(db.String(100), default='gpt-3.5-turbo', comment='模型名称')
    max_tokens = db.Column(db.Integer, default=2000, comment='最大令牌数')
    temperature = db.Column(db.Numeric(3, 2), default=0.70, comment='创造性参数，0-1之间')
    is_enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    quota_used = db.Column(db.Integer, default=0, comment='已使用配额')
    preferred_language = db.Column(db.Enum('zh', 'en', 'auto'), default='zh', comment='偏好语言')
    response_length = db.Column(db.Enum('short', 'medium', 'detailed'), default='medium', comment='回复长度偏好')
    creativity_level = db.Column(db.Enum('factual', 'balanced', 'creative'), default='balanced', comment='创造性水平')
    include_sources = db.Column(db.Boolean, default=True, comment='是否包含引用来源')
    auto_summary = db.Column(db.Boolean, default=False, comment='是否自动生成摘要')
    save_conversation = db.Column(db.Boolean, default=True, comment='是否保存对话历史')
    context_memory = db.Column(db.Integer, default=5, comment='上下文记忆轮数')
    system_prompt = db.Column(db.Text, comment='系统提示词设置')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('ai_config', uselist=False))
    
    def __repr__(self):
        return f'<AIConfig {self.user_id} - {self.api_type}>'

class Notification(db.Model):
    """通知模型"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    title = db.Column(db.String(100), nullable=False, comment='通知标题')
    content = db.Column(db.Text, nullable=False, comment='通知内容')
    type = db.Column(db.Enum('system', 'task', 'community', 'grade', 'other'), nullable=False, comment='通知类型')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    target_type = db.Column(db.Enum('task', 'post', 'grade', 'other'), comment='目标类型')
    target_id = db.Column(db.Integer, comment='目标ID')
    
    # 关系
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Notification {self.user_id} - {self.title}>'

class SearchHistory(db.Model):
    """搜索历史模型"""
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    query = db.Column(db.String(200), nullable=False, comment='搜索查询词')
    search_type = db.Column(db.Enum('note', 'resource', 'post', 'course', 'other'), nullable=False, comment='搜索类型')
    searched_at = db.Column(db.DateTime, default=datetime.utcnow, comment='搜索时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('search_history', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SearchHistory {self.user_id} - {self.query}>'

class AdminLog(db.Model):
    """管理员日志模型"""
    __tablename__ = 'admin_log'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='管理员ID，外键')
    action = db.Column(db.String(100), nullable=False, comment='操作行为')
    target_type = db.Column(db.Enum('user', 'post', 'comment', 'grade', 'resource'), nullable=False, comment='目标类型')
    target_id = db.Column(db.Integer, nullable=False, comment='目标ID')
    detail = db.Column(db.Text, comment='操作详情')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    
    # 关系
    admin = db.relationship('User', backref=db.backref('admin_logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AdminLog {self.admin_id} - {self.action}>' 