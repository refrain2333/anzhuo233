"""
用户相关的数据序列化Schema
"""
from app import ma
from app.models.user import User, UserProfile, Major
from marshmallow import fields, validate, post_load, validates_schema, ValidationError

class MajorSchema(ma.SQLAlchemyAutoSchema):
    """专业Schema"""
    class Meta:
        model = Major
        load_instance = True
        include_fk = True

class UserProfileSchema(ma.SQLAlchemyAutoSchema):
    """用户画像Schema"""
    class Meta:
        model = UserProfile
        load_instance = True
        include_fk = True
    
    learning_style = fields.String(
        validate=validate.OneOf(['visual', 'auditory', 'kinesthetic', 'mixed']), 
        allow_none=True
    )
    preferred_time = fields.String(
        validate=validate.OneOf(['morning', 'afternoon', 'evening', 'night']), 
        allow_none=True
    )

class UserSchema(ma.SQLAlchemyAutoSchema):
    """用户Schema"""
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ('password_hash',)
    
    # 关联对象
    profile = fields.Nested(UserProfileSchema, exclude=('user_id',))
    major = fields.Nested(MajorSchema, only=('id', 'name', 'college'))
    
    # 额外的字段验证
    email = fields.Email(required=True)
    student_id = fields.String(required=True, validate=validate.Length(min=5, max=20))
    
    @validates_schema
    def validate_user(self, data, **kwargs):
        """验证用户数据"""
        if 'student_id' in data and 'email' in data:
            # 验证学号格式（示例：必须全部是数字）
            if not data['student_id'].isdigit():
                raise ValidationError("学号必须全部是数字")
        
        return data

class UserCreateSchema(ma.Schema):
    """用户创建Schema"""
    student_id = fields.String(required=True, validate=validate.Length(min=5, max=20))
    name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    major_id = fields.Integer(allow_none=True)
    
    @validates_schema
    def validate_create_user(self, data, **kwargs):
        """验证创建用户的数据"""
        if 'student_id' in data:
            # 验证学号格式（示例：必须全部是数字）
            if not data['student_id'].isdigit():
                raise ValidationError("学号必须全部是数字")
        
        return data

class UserUpdateSchema(ma.Schema):
    """用户更新Schema"""
    name = fields.String(validate=validate.Length(min=2, max=50))
    bio = fields.String()
    avatar_url = fields.URL(allow_none=True)
    major_id = fields.Integer(allow_none=True)
    
    # 用户画像相关字段
    learning_style = fields.String(
        validate=validate.OneOf(['visual', 'auditory', 'kinesthetic', 'mixed']), 
        allow_none=True
    )
    preferred_time = fields.String(
        validate=validate.OneOf(['morning', 'afternoon', 'evening', 'night']), 
        allow_none=True
    )
    avg_focus_duration = fields.Integer(allow_none=True)
    strengths = fields.String(allow_none=True)
    weaknesses = fields.String(allow_none=True)
    study_habits = fields.String(allow_none=True)
    notification_email_enabled = fields.Boolean(default=True)
    notification_app_enabled = fields.Boolean(default=True)
    notification_types = fields.String(allow_none=True)

# 初始化Schema实例
user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_profile_schema = UserProfileSchema()
major_schema = MajorSchema()
majors_schema = MajorSchema(many=True)
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema() 