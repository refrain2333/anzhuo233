"""
学习模块序列化 Schema
"""
from app import ma
from app.models.learning import Semester, Course, CourseSchedule, Grade, MajorCourse, StudyPlan, Task, FocusRecord, CheckIn
from marshmallow import fields, validates, ValidationError
from datetime import datetime, time

class SemesterSchema(ma.SQLAlchemyAutoSchema):
    """学期序列化Schema"""
    class Meta:
        model = Semester
        load_instance = True  # 反序列化时创建模型实例
        include_fk = True     # 包含外键
    
    @validates('start_date')
    def validate_start_date(self, value):
        """验证开始日期"""
        if value and value > datetime.now().date():
            raise ValidationError("开始日期不能晚于当前日期")
            
    @validates('end_date')
    def validate_end_date(self, value, **kwargs):
        """验证结束日期"""
        start_date = kwargs.get('data', {}).get('start_date')
        if start_date and value and value < start_date:
            raise ValidationError("结束日期不能早于开始日期")

class CourseSchema(ma.SQLAlchemyAutoSchema):
    """课程序列化Schema"""
    class Meta:
        model = Course
        load_instance = True
        include_fk = True
    
    semester = fields.Nested(SemesterSchema, only=('id', 'name'), dump_only=True)
    
    @validates('code')
    def validate_code(self, value):
        """验证课程代码格式"""
        if not (value and len(value) >= 3):
            raise ValidationError("课程代码长度必须大于等于3个字符")

class CourseScheduleSchema(ma.SQLAlchemyAutoSchema):
    """课程安排序列化Schema"""
    class Meta:
        model = CourseSchedule
        load_instance = True
        include_fk = True
    
    course = fields.Nested(CourseSchema, only=('id', 'name', 'code'), dump_only=True)
    
    @validates('start_time')
    def validate_start_time(self, value):
        """验证开始时间"""
        if value and (value < time(6, 0) or value > time(22, 0)):
            raise ValidationError("课程开始时间应在6:00至22:00之间")
            
    @validates('end_time')
    def validate_end_time(self, value, **kwargs):
        """验证结束时间"""
        start_time = kwargs.get('data', {}).get('start_time')
        if start_time and value and value <= start_time:
            raise ValidationError("结束时间必须晚于开始时间")

class GradeSchema(ma.SQLAlchemyAutoSchema):
    """成绩序列化Schema"""
    class Meta:
        model = Grade
        load_instance = True
        include_fk = True

    course = fields.Nested(CourseSchema, only=('id', 'name', 'code', 'credit'), dump_only=True)

    @validates('score')
    def validate_score(self, value):
        """验证成绩分数"""
        if value and (value < 0 or value > 100):
            raise ValidationError("成绩必须在0-100之间")

class MajorCourseSchema(ma.SQLAlchemyAutoSchema):
    """专业课程序列化Schema"""
    class Meta:
        model = MajorCourse
        load_instance = True
        include_fk = True
    
    course = fields.Nested(CourseSchema, only=('id', 'name', 'code', 'credit'), dump_only=True)

class StudyPlanSchema(ma.SQLAlchemyAutoSchema):
    """学习计划序列化Schema"""
    class Meta:
        model = StudyPlan
        load_instance = True
        include_fk = True
    
    @validates('end_date')
    def validate_end_date(self, value, **kwargs):
        """验证结束日期"""
        start_date = kwargs.get('data', {}).get('start_date')
        if start_date and value and value < start_date:
            raise ValidationError("结束日期不能早于开始日期")
    
    @validates('progress')
    def validate_progress(self, value):
        """验证进度百分比"""
        if value and (value < 0 or value > 100):
            raise ValidationError("进度必须在0-100之间")

class TaskSchema(ma.SQLAlchemyAutoSchema):
    """任务序列化Schema"""
    class Meta:
        model = Task
        load_instance = True
        include_fk = True
    
    plan = fields.Nested(StudyPlanSchema, only=('id', 'title'), dump_only=True)
    
    @validates('deadline')
    def validate_deadline(self, value):
        """验证截止日期"""
        if value and value < datetime.now():
            raise ValidationError("截止日期不能早于当前时间")

class FocusRecordSchema(ma.SQLAlchemyAutoSchema):
    """专注记录序列化Schema"""
    class Meta:
        model = FocusRecord
        load_instance = True
        include_fk = True
    
    task = fields.Nested(TaskSchema, only=('id', 'content', 'priority'), dump_only=True)
    
    @validates('duration')
    def validate_duration(self, value):
        """验证专注时长"""
        if value and (value <= 0 or value > 1440):  # 最长24小时
            raise ValidationError("专注时长必须大于0且不超过1440分钟（24小时）")
    
    @validates('focus_score')
    def validate_focus_score(self, value):
        """验证专注度评分"""
        if value and (value < 0 or value > 100):
            raise ValidationError("专注度评分必须在0-100之间")

class CheckInSchema(ma.SQLAlchemyAutoSchema):
    """打卡序列化Schema"""
    class Meta:
        model = CheckIn
        load_instance = True
        include_fk = True
    
    @validates('check_in_date')
    def validate_check_in_date(self, value):
        """验证打卡日期"""
        if value and value > datetime.now().date():
            raise ValidationError("打卡日期不能晚于当前日期") 