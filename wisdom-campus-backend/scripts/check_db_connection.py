#!/usr/bin/env python
"""
数据库连接测试脚本
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

# 加载环境变量
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# 从环境变量获取数据库连接信息
db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://FZG1234C:FZG1234C@115.120.215.107:3306/xuesheng233')
print(f"数据库URL: {db_url}")

# 解析连接信息
# 格式: mysql+pymysql://username:password@host:port/database
parts = db_url.replace('mysql+pymysql://', '').split('@')
credentials = parts[0].split(':')
host_info = parts[1].split('/')

username = credentials[0]
password = credentials[1]
host_port = host_info[0].split(':')
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 3306
database = host_info[1]

print("=" * 40)
print(f"尝试连接到数据库：{database}")
print(f"主机: {host}")
print(f"端口: {port}")
print(f"用户名: {username}")
print("=" * 40)

try:
    # 建立连接
    print("正在连接到MySQL服务器...")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        charset='utf8mb4'
    )
    
    # 测试能否创建数据库（如果不存在）
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    
    print("✅ 成功连接到MySQL服务器并创建/确认数据库")
    
    # 再次连接，直接连接到指定数据库
    conn.close()
    conn = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    
    print(f"✅ 成功连接到数据库 {database}")
    conn.close()
    print("数据库连接测试完成")
    
except Exception as e:
    print(f"❌ 连接数据库时出错: {e}")
    sys.exit(1) 