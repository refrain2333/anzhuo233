"""
Swagger文档配置
"""
from flask_swagger_ui import get_swaggerui_blueprint

def setup_swagger(app):
    """设置Swagger UI"""
    SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
    API_URL = '/api/swagger.json'  # URL for API documentation JSON
    
    # 添加swagger.json路由
    @app.route('/api/swagger.json')
    def swagger_json():
        """返回swagger.json"""
        from flask import jsonify
        swagger_doc = {
            "swagger": "2.0",
            "info": {
                "title": "智慧校园学习助手系统API",
                "description": "API文档",
                "version": "1.0.0"
            },
            "basePath": "/",
            "schemes": [
                "http",
                "https"
            ],
            "consumes": [
                "application/json"
            ],
            "produces": [
                "application/json"
            ],
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "JWT授权头。示例：\"Authorization: Bearer {token}\""
                }
            },
            "paths": {
                "/api/v1/auth/login": {
                    "post": {
                        "tags": ["认证"],
                        "summary": "用户登录",
                        "description": "使用学号和密码登录系统",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "student_id": {
                                            "type": "string",
                                            "description": "学号"
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "登录成功"
                            },
                            "400": {
                                "description": "请求参数错误"
                            },
                            "401": {
                                "description": "登录失败"
                            },
                            "404": {
                                "description": "用户不存在"
                            }
                        }
                    }
                },
                "/api/v1/auth/register": {
                    "post": {
                        "tags": ["认证"],
                        "summary": "用户注册",
                        "description": "注册新用户",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "student_id": {
                                            "type": "string",
                                            "description": "学号"
                                        },
                                        "email": {
                                            "type": "string",
                                            "description": "邮箱"
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码"
                                        },
                                        "name": {
                                            "type": "string",
                                            "description": "姓名"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "注册成功"
                            },
                            "400": {
                                "description": "请求参数错误"
                            },
                            "409": {
                                "description": "用户已存在"
                            }
                        }
                    }
                }
            }
        }
        return jsonify(swagger_doc)
    
    # 创建Swagger UI blueprint
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "智慧校园学习助手系统API文档"
        }
    )
    
    # 注册blueprint
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL) 