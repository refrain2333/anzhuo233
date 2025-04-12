"""
学习资源与徽章相关模型
"""
from app import db
from datetime import datetime
from app.models.user import User

class Badge(db.Model):
    """徽章模型"""
    __tablename__ = 'badge'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='徽章名称')
    description = db.Column(db.Text, comment='徽章描述')
    type = db.Column(db.String(20), comment='徽章类型')
    
    def __repr__(self):
        return f'<Badge {self.name}>'

class UserBadge(db.Model):
    """用户徽章关联模型"""
    __tablename__ = 'user_badge'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id', ondelete='CASCADE'), nullable=False, comment='徽章ID，外键')
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow, comment='授予时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('badges', lazy='dynamic'))
    badge = db.relationship('Badge', backref=db.backref('users', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UserBadge {self.user_id} - {self.badge_id}>'

class LearningResource(db.Model):
    """学习资源模型"""
    __tablename__ = 'learning_resource'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, comment='资源标题')
    url = db.Column(db.String(255), nullable=False, comment='资源URL')
    type = db.Column(db.Enum('video', 'article', 'book', 'tool', 'other'), nullable=False, comment='资源类型')
    category = db.Column(db.String(50), comment='资源分类')
    description = db.Column(db.Text, comment='资源描述')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='上传者ID，外键')
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, comment='上传日期')
    view_count = db.Column(db.Integer, default=0, comment='查看次数')
    rating = db.Column(db.Numeric(3, 2), default=0.00, comment='评分')
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending', comment='资源审批状态')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), comment='审核者ID，外键')
    review_date = db.Column(db.DateTime, comment='审核日期')
    review_comments = db.Column(db.Text, comment='审核备注')
    
    # 关系
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref=db.backref('uploaded_resources', lazy='dynamic'))
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref=db.backref('reviewed_resources', lazy='dynamic'))
    recommendations = db.relationship('ResourceRecommendation', backref='resource', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('ResourceComment', backref='resource', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LearningResource {self.title}>'

class ResourceRecommendation(db.Model):
    """资源推荐模型"""
    __tablename__ = 'resource_recommendation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    resource_id = db.Column(db.Integer, db.ForeignKey('learning_resource.id', ondelete='CASCADE'), nullable=False, comment='资源ID，外键')
    reason = db.Column(db.Text, comment='推荐原因')
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow, comment='推荐时间')
    api_response = db.Column(db.Text, comment='API响应数据')
    
    # 关系
    user = db.relationship('User', backref=db.backref('resource_recommendations', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ResourceRecommendation {self.user_id} - {self.resource_id}>'

class ResourceComment(db.Model):
    """资源评论模型"""
    __tablename__ = 'resource_comment'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('learning_resource.id', ondelete='CASCADE'), nullable=False, comment='资源ID，外键')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    content = db.Column(db.Text, nullable=False, comment='评论内容')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('resource_comments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ResourceComment {self.id}>'

class LearningBehavior(db.Model):
    """学习行为记录模型"""
    __tablename__ = 'learning_behavior'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    behavior_type = db.Column(db.Enum('study_time', 'task_completion', 'note_creation', 'post_interaction'), 
                             nullable=False, comment='行为类型')
    target_id = db.Column(db.Integer, comment='目标ID，具体对象ID')
    duration = db.Column(db.Integer, comment='持续时间（分钟）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='行为发生时间')
    
    # 关系
    user = db.relationship('User', backref=db.backref('learning_behaviors', lazy='dynamic'))
    
    def __repr__(self):
        return f'<LearningBehavior {self.user_id} - {self.behavior_type}>'

class LearningAnalysis(db.Model):
    """学习分析模型"""
    __tablename__ = 'learning_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow, comment='分析日期')
    study_efficiency = db.Column(db.Numeric(3, 2), default=0.00, comment='学习效率')
    behavior_summary = db.Column(db.Text, comment='行为总结')
    suggestion = db.Column(db.Text, comment='改进建议')
    api_response = db.Column(db.Text, comment='API响应数据')
    
    # 关系
    user = db.relationship('User', backref=db.backref('learning_analyses', lazy='dynamic'))
    
    def __repr__(self):
        return f'<LearningAnalysis {self.user_id} - {self.analysis_date}>' 