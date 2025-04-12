#!/usr/bin/env python
"""
执行SQL脚本创建数据库表
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

# 解析连接信息
parts = db_url.replace('mysql+pymysql://', '').split('@')
credentials = parts[0].split(':')
host_info = parts[1].split('/')

username = credentials[0]
password = credentials[1]
host_port = host_info[0].split(':')
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 3306
database = host_info[1]

print(f"准备执行SQL脚本创建表...")

# 加载SQL文件
sql_file_path = os.path.join(project_root, 'app', 'models', '数据库.sql')
if not os.path.exists(sql_file_path):
    print(f"❌ SQL文件不存在: {sql_file_path}")
    sys.exit(1)

print(f"找到SQL文件: {sql_file_path}")

try:
    # 打开并读取SQL文件
    with open(sql_file_path, 'r', encoding='utf-8') as file:
        sql_script = file.read()
    
    print(f"SQL文件读取成功，大小：{len(sql_script)} 字节")
    
    # 建立数据库连接
    conn = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    
    print(f"成功连接到数据库 {database}，开始执行SQL脚本...")
    
    # 分割并执行SQL语句
    cursor = conn.cursor()
    
    # 分割SQL语句（以分号结尾的部分为一条语句）
    statements = sql_script.split(';')
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements):
        # 跳过空语句
        cleaned = statement.strip()
        if not cleaned:
            continue
        
        try:
            cursor.execute(cleaned)
            success_count += 1
            if i % 10 == 0:
                print(f"已执行 {i}/{len(statements)} 条语句...")
        except Exception as e:
            error_count += 1
            print(f"❌ 执行语句时出错 [{i+1}/{len(statements)}]: {str(e)}")
            print(f"出错的语句: {cleaned[:100]}...")
    
    # 提交更改
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"SQL脚本执行完成！")
    print(f"成功执行: {success_count} 条语句")
    print(f"执行出错: {error_count} 条语句")
    
except Exception as e:
    print(f"❌ 执行过程中出错: {str(e)}")
    sys.exit(1) 