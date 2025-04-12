"""
学习模块API
"""
from flask import Blueprint

learning_bp = Blueprint('learning', __name__)

# TODO: 以下模块尚未实现，需要创建相应的子模块文件
# 暂时注释掉导入不存在的模块，避免导入错误
# from . import courses, grades, tasks, focus, checkin, plans

# 临时路由，表示模块正在建设中
@learning_bp.route('/')
def learning_index():
    return {
        "status": "success",
        "message": "学习模块API正在建设中",
        "data": {
            "module": "learning",
            "planned_features": [
                "课程管理", "成绩查询", "任务计划", 
                "专注记录", "每日打卡", "学习计划"
            ]
        }
    } 