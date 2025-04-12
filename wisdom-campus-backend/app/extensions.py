"""
扩展模块 - 用于存放Flask扩展实例
避免循环导入问题
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow

# 实例化扩展，但不传入应用实例
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow() 