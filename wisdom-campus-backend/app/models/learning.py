"""
学习模块相关模型
"""
from app import db
from datetime import datetime
from sqlalchemy.orm import relationship
from app.models.user import Semester, User, Major

class Course(db.Model):
    """课程模型"""
    __tablename__ = 'course'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='课程名称')
    code = db.Column(db.String(20), unique=True, nullable=False, comment='课程代码，唯一')
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='SET NULL'), comment='学期ID，外键')
    credit = db.Column(db.Numeric(3, 1), comment='学分')
    
    # 关系
    schedules = db.relationship('CourseSchedule', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    grades = db.relationship('Grade', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    major_courses = db.relationship('MajorCourse', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.name}>'

class CourseSchedule(db.Model):
    """课程安排模型"""
    __tablename__ = 'course_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False, comment='课程ID，外键')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    day_of_week = db.Column(db.Enum('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'), 
                            nullable=False, comment='星期几')
    start_time = db.Column(db.Time, nullable=False, comment='开始时间')
    end_time = db.Column(db.Time, nullable=False, comment='结束时间')
    location = db.Column(db.String(100), comment='上课地点')
    
    def __repr__(self):
        return f'<CourseSchedule {self.course_id} - {self.day_of_week}>'

class Grade(db.Model):
    """成绩模型"""
    __tablename__ = 'grade'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False, comment='课程ID，外键')
    score = db.Column(db.Numeric(5, 2), comment='成绩')
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录时间')
    
    def __repr__(self):
        return f'<Grade {self.user_id} - {self.course_id}>'

class MajorCourse(db.Model):
    """专业课程模型"""
    __tablename__ = 'major_course'
    
    id = db.Column(db.Integer, primary_key=True)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id', ondelete='CASCADE'), nullable=False, comment='专业ID，外键')
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False, comment='课程ID，外键')
    is_required = db.Column(db.Boolean, default=False, comment='是否为必修课')
    
    def __repr__(self):
        return f'<MajorCourse {self.major_id} - {self.course_id}>'

class StudyPlan(db.Model):
    """学习计划模型"""
    __tablename__ = 'study_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    title = db.Column(db.String(100), nullable=False, comment='计划标题')
    description = db.Column(db.Text, comment='计划描述')
    start_date = db.Column(db.Date, nullable=False, comment='开始日期')
    end_date = db.Column(db.Date, comment='结束日期')
    progress = db.Column(db.Numeric(5, 2), default=0.00, comment='进度百分比')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    status = db.Column(db.Enum('active', 'completed', 'abandoned'), default='active', comment='计划状态')
    
    # 关系
    tasks = db.relationship('Task', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudyPlan {self.title}>'

class Task(db.Model):
    """任务模型"""
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id', ondelete='SET NULL'), comment='学习计划ID，外键')
    content = db.Column(db.String(200), nullable=False, comment='任务内容')
    deadline = db.Column(db.DateTime, comment='截止日期')
    priority = db.Column(db.Enum('low', 'medium', 'high'), default='medium', comment='优先级')
    status = db.Column(db.Enum('pending', 'in_progress', 'reviewing', 'revising', 'completed', 'delayed', 'cancelled'), 
                      default='pending', comment='任务状态')
    
    # 关系
    focus_records = db.relationship('FocusRecord', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Task {self.content[:20]}>'

class FocusRecord(db.Model):
    """专注记录模型"""
    __tablename__ = 'focus_record'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    duration = db.Column(db.Integer, nullable=False, comment='专注时长（分钟）')
    focus_score = db.Column(db.Integer, comment='专注度评分')
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='SET NULL'), comment='关联任务ID，外键')
    
    def __repr__(self):
        return f'<FocusRecord {self.user_id} - {self.start_time}>'

class CheckIn(db.Model):
    """打卡模型"""
    __tablename__ = 'check_in'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, comment='用户ID，外键')
    check_in_date = db.Column(db.Date, nullable=False, comment='打卡日期')
    streak_count = db.Column(db.Integer, default=0, comment='连续打卡天数')
    note = db.Column(db.String(200), comment='打卡备注')
    
    def __repr__(self):
        return f'<CheckIn {self.user_id} - {self.check_in_date}>' 