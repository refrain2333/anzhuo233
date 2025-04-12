"""
统一API响应格式工具
提供标准化的API响应格式，确保所有API返回结构一致
"""
from flask import jsonify, make_response

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

def api_success(data=None, message="操作成功", code=200):
    """
    成功响应
    
    参数:
        data (Any): 响应数据
        message (str): 提示信息
        code (int): 业务状态码
    
    返回:
        tuple: (JSON响应, HTTP状态码)
    """
    return api_response(
        success=True,
        message=message,
        data=data,
        code=code
    )

def api_error(message="操作失败", error_code=400, http_status=400, data=None):
    """
    错误响应
    
    参数:
        message (str): 错误信息
        error_code (int): 业务错误码
        http_status (int): HTTP状态码
        data (Any): 额外的错误数据
    
    返回:
        tuple: (JSON响应, HTTP状态码)
    """
    return api_response(
        success=False,
        message=message,
        code=error_code,
        data=data,
        http_status=http_status
    ) 