"""
统一API响应格式工具
提供标准化的API响应格式，确保所有API返回结构一致
"""
from flask import jsonify, make_response
import json
from decimal import Decimal
from datetime import datetime, date

# 自定义JSON编码器，处理特殊类型：Decimal, datetime等
class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，用于处理特殊类型的序列化"""
    def default(self, obj):
        # 处理Decimal类型
        if isinstance(obj, Decimal):
            return float(obj)
        # 处理日期时间类型
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        # 其他类型使用默认处理方法
        return super(CustomJSONEncoder, self).default(obj)

def api_response(success=True, message="", data=None, code=200, http_status=200):
    """
    统一API响应格式
    
    参数:
        success (bool): 请求是否成功
        message (str): 提示信息
        data (Any): 响应数据
        code (int): 业务状态码
        http_status (int): HTTP状态码
    
    返回:
        tuple: (JSON响应, HTTP状态码)
    """
    response = {
        "success": success,
        "code": code,
        "message": message,
        "data": data
    }
    # 创建响应对象并设置Content-Type
    resp = make_response(jsonify(response), http_status)
    resp.headers['Content-Type'] = 'application/json; charset=utf-8'
    return resp

def api_success(data=None, message="操作成功", code=0):
    """返回成功的API响应"""
    response = {
        "success": True,
        "code": code,
        "message": message,
        "data": data or {}
    }
    # 使用Flask的jsonify函数，它会自动使用应用配置的JSON编码器
    return jsonify(response)

def api_error(message="操作失败", code=1, status_code=400, errors=None):
    """返回错误的API响应"""
    response = {
        "success": False,
        "code": code,
        "message": message,
        "errors": errors or {}
    }
    # 使用Flask的jsonify函数，它会自动使用应用配置的JSON编码器
    return jsonify(response), status_code 