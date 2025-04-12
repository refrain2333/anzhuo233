"""
用户相关模型
"""
from app import db
from datetime import datetime

class Major(db.Model):
    """专业模型"""
    __tablename__ = 'major'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='专业名称')
    college = db.Column(db.String(50), comment='学院名称')
    
    # 关系
    users = db.relationship('User', backref='major', lazy='dynamic')
    
    def __repr__(self):
        return f'<Major {self.name}>'

class User(db.Model):
    """用户模型"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, comment='学号，唯一')
    auth0_id = db.Column(db.String(50), unique=True, nullable=False, comment='Auth0 用户ID，唯一')
    name = db.Column(db.String(50), comment='用户姓名')
    email = db.Column(db.String(100), unique=True, nullable=False, comment='用户邮箱，唯一')
    email_verified = db.Column(db.Boolean, default=False, comment='邮箱是否已验证')
    password_hash = db.Column(db.String(128), comment='密码哈希（可选，若使用Auth0可能不直接使用）')
    avatar_url = db.Column(db.String(255), comment='头像URL')
    bio = db.Column(db.Text, comment='个人简介')
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'), comment='专业ID，外键')
    total_study_time = db.Column(db.Integer, default=0, comment='总学习时长（分钟）')
    gpa = db.Column(db.Numeric(3, 2), default=0.00, comment='GPA成绩')
    exp_points = db.Column(db.Integer, default=0, comment='经验值')
    level = db.Column(db.Integer, default=1, comment='用户等级')
    is_admin = db.Column(db.Boolean, default=False, comment='是否为管理员')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    status = db.Column(db.Enum('active', 'inactive', 'banned'), default='active', comment='用户状态')
    
    # 关系
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.name}>'

class UserProfile(db.Model):
    """用户画像模型"""
    __tablename__ = 'user_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID，外键')
    learning_style = db.Column(db.Enum('visual', 'auditory', 'kinesthetic', 'mixed'), comment='学习风格')
    preferred_time = db.Column(db.Enum('morning', 'afternoon', 'evening', 'night'), comment='偏好学习时间')
    avg_focus_duration = db.Column(db.Integer, comment='平均专注时长（分钟）')
    strengths = db.Column(db.Text, comment='学习优势')
    weaknesses = db.Column(db.Text, comment='学习弱点')
    study_habits = db.Column(db.Text, comment='学习习惯')
    notification_email_enabled = db.Column(db.Boolean, default=True, comment='是否启用邮箱通知')
    notification_app_enabled = db.Column(db.Boolean, default=True, comment='是否启用应用内通知')
    notification_types = db.Column(db.Text, comment='通知类型偏好（JSON或逗号分隔字符串）')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后更新时间')
    
    def __repr__(self):
        return f'<UserProfile {self.user_id}>' 