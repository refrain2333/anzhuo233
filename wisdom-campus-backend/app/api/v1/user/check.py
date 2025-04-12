"""
学号查询接口模块
提供学号查询用户信息的API接口
"""
from flask import request, jsonify
from app.models.user import User
from app.utils.response import api_success, api_error
from app.utils.error_codes import ErrorCode
import logging

# 配置日志
logger = logging.getLogger(__name__)

def check_student_id_exists():
    """
    检查学号是否存在
    
    查询参数:
        student_id: 学号
        
    返回:
        成功: 返回用户信息（不包含敏感信息）
        失败: 返回错误信息
    """
    # 获取学号参数
    student_id = request.args.get('student_id')
    
    if not student_id:
        return api_error(
            message="学号不能为空", 
            error_code=ErrorCode.INVALID_REQUEST
        )
    
    # 查询数据库
    try:
        user = User.query.filter_by(student_id=student_id).first()
        
        # 判断用户是否存在
        if user:
            logger.info(f"学号查询成功: {student_id}")
            return api_success(
                data={
                    'exists': True,
                    'student_id': student_id,
                    'email': user.email,  # 返回邮箱用于登录
                    'name': user.name,
                    'email_verified': user.email_verified
                }
            )
        else:
            logger.info(f"学号不存在: {student_id}")
            return api_success(
                data={
                    'exists': False,
                    'student_id': student_id
                }
            )
    except Exception as e:
        logger.error(f"查询学号时发生错误: {str(e)}")
        return api_error(
            message="查询学号失败",
            error_code=ErrorCode.DB_ERROR
        ) 