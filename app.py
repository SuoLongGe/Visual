#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职数洞见 - 招聘数据可视化API
主应用文件
"""

import logging
from flask import Flask
from flask_cors import CORS

from routes.city_routes import city_bp
from routes.industry_routes import industry_bp
from routes.experience_routes import experience_bp
from routes.salary_3d_routes import salary_3d_bp
from utils.response import ResponseBuilder

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    CORS(app)  # 允许跨域请求
    
    # 注册蓝图
    app.register_blueprint(city_bp)
    app.register_blueprint(industry_bp)
    app.register_blueprint(experience_bp)
    app.register_blueprint(salary_3d_bp)
    
    # 注册错误处理器
    @app.errorhandler(404)
    def not_found(error):
        return ResponseBuilder.not_found("接口不存在")
    
    @app.errorhandler(500)
    def internal_error(error):
        return ResponseBuilder.internal_error("服务器内部错误")
    
    return app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    print("启动职数洞见API服务...")
    print("API文档: http://localhost:5000/api/overview")
    print("城市分析: http://localhost:5000/api/charts/city")
    app.run(debug=True, host='0.0.0.0', port=5000)
