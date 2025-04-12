"""
Auth0诊断工具 - 用于检查Auth0配置问题
"""
import requests
import logging
import json
from flask import current_app, Blueprint, jsonify

logger = logging.getLogger(__name__)

# 创建诊断蓝图
auth0_diag_bp = Blueprint('auth0_diag', __name__)

@auth0_diag_bp.route('/check', methods=['GET'])
def check_auth0_config():
    """
    检查Auth0配置是否正确
    
    返回:
        Auth0配置检查结果
    """
    results = {}
    
    # 获取Auth0配置
    domain = current_app.config.get('AUTH0_DOMAIN')
    client_id = current_app.config.get('AUTH0_CLIENT_ID')
    client_secret = current_app.config.get('AUTH0_CLIENT_SECRET')
    audience = current_app.config.get('AUTH0_AUDIENCE')
    
    # 检查基本配置
    results['config'] = {
        'domain': domain,
        'client_id': client_id[:5] + '...' if client_id else None,
        'client_secret': '已设置' if client_secret else None,
        'audience': audience
    }
    
    # 测试获取管理API令牌
    try:
        token_url = f"https://{domain}/oauth/token"
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": f"https://{domain}/api/v2/",
            "grant_type": "client_credentials"
        }
        token_headers = {"content-type": "application/json"}
        
        token_response = requests.post(token_url, json=token_payload, headers=token_headers)
        
        if token_response.status_code == 200:
            results['management_token'] = {
                'status': 'success',
                'message': '成功获取管理API令牌'
            }
            management_token = token_response.json().get('access_token')
            
            # 获取连接列表
            try:
                connections_url = f"https://{domain}/api/v2/connections"
                connections_headers = {
                    "Authorization": f"Bearer {management_token}"
                }
                connections_response = requests.get(connections_url, headers=connections_headers)
                
                if connections_response.status_code == 200:
                    connections = connections_response.json()
                    db_connections = [
                        {'name': conn.get('name'), 'strategy': conn.get('strategy')} 
                        for conn in connections if conn.get('strategy') == 'auth0'
                    ]
                    results['connections'] = {
                        'status': 'success',
                        'message': f'找到 {len(db_connections)} 个数据库连接',
                        'db_connections': db_connections
                    }
                else:
                    results['connections'] = {
                        'status': 'error',
                        'message': f'获取连接列表失败: {connections_response.status_code}',
                        'details': connections_response.text
                    }
            except Exception as e:
                results['connections'] = {
                    'status': 'error',
                    'message': f'获取连接列表异常: {str(e)}'
                }
            
            # 获取客户端授权设置
            try:
                client_url = f"https://{domain}/api/v2/clients/{client_id}"
                client_headers = {
                    "Authorization": f"Bearer {management_token}"
                }
                client_response = requests.get(client_url, headers=client_headers)
                
                if client_response.status_code == 200:
                    client_data = client_response.json()
                    grant_types = client_data.get('grant_types', [])
                    
                    results['client'] = {
                        'status': 'success',
                        'message': '成功获取客户端信息',
                        'name': client_data.get('name'),
                        'grant_types': grant_types,
                        'has_password_grant': 'password' in grant_types
                    }
                else:
                    results['client'] = {
                        'status': 'error',
                        'message': f'获取客户端信息失败: {client_response.status_code}',
                        'details': client_response.text
                    }
            except Exception as e:
                results['client'] = {
                    'status': 'error',
                    'message': f'获取客户端信息异常: {str(e)}'
                }
        else:
            results['management_token'] = {
                'status': 'error',
                'message': f'获取管理API令牌失败: {token_response.status_code}',
                'details': token_response.text
            }
    except Exception as e:
        results['management_token'] = {
            'status': 'error',
            'message': f'获取管理API令牌异常: {str(e)}'
        }
    
    return jsonify(results)

def check_auth0_client_connections():
    """
    检查Auth0客户端的连接配置
    
    返回:
        连接信息列表
    """
    try:
        # 获取Auth0配置
        domain = current_app.config.get('AUTH0_DOMAIN')
        client_id = current_app.config.get('AUTH0_CLIENT_ID')
        client_secret = current_app.config.get('AUTH0_CLIENT_SECRET')
        
        # 获取管理API令牌
        token_url = f"https://{domain}/oauth/token"
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": f"https://{domain}/api/v2/",
            "grant_type": "client_credentials"
        }
        token_headers = {"content-type": "application/json"}
        
        token_response = requests.post(token_url, json=token_payload, headers=token_headers)
        
        if token_response.status_code != 200:
            logger.error(f"获取管理API令牌失败: {token_response.text}")
            return None
        
        management_token = token_response.json().get('access_token')
        
        # 获取客户端连接
        client_url = f"https://{domain}/api/v2/clients/{client_id}"
        client_headers = {
            "Authorization": f"Bearer {management_token}"
        }
        
        client_response = requests.get(client_url, headers=client_headers)
        
        if client_response.status_code != 200:
            logger.error(f"获取客户端信息失败: {client_response.text}")
            return None
        
        client_data = client_response.json()
        connections = client_data.get('connections', [])
        
        return {
            'client_name': client_data.get('name'),
            'connections': connections
        }
    except Exception as e:
        logger.error(f"检查Auth0客户端连接异常: {str(e)}")
        return None 