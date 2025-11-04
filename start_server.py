#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动服务器脚本
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'flask', 'flask_cors', 'pymysql', 'pandas', 'numpy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_database_connection():
    """检查数据库连接"""
    try:
        from database import DatabaseManager
        db_manager = DatabaseManager('default')
        
        # 尝试执行简单查询
        result = db_manager.execute_query("SELECT 1", fetch_one=True)
        if result:
            print("✓ 数据库连接成功")
            return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("请检查:")
        print("1. MySQL服务是否启动")
        print("2. 数据库配置是否正确 (config.py)")
        print("3. 数据库 'vision' 是否存在")
        print("4. 表 'data' 是否存在")
        return False

def open_frontend():
    """打开前端页面"""
    import webbrowser
    import threading
    
    def open_browser():
        time.sleep(3)  # 等待后端启动
        html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
        if os.path.exists(html_file):
            webbrowser.open(f"file://{html_file}")
            print(f"🌐 前端页面已打开: {html_file}")
        else:
            print("❌ 找不到前端页面文件 index.html")
    
    # 在新线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

def main():
    """主函数"""
    print("🏢 职数洞见 - 招聘数据可视化平台")
    print("=" * 50)
    
    # 检查依赖
    print("检查依赖包...")
    if not check_dependencies():
        sys.exit(1)
    
    # 检查数据库连接
    print("检查数据库连接...")
    if not check_database_connection():
        sys.exit(1)
    
    # 检查前端页面
    if os.path.exists("index.html"):
        print("✅ 前端页面文件存在")
        open_frontend()
    else:
        print("⚠️  前端页面文件不存在，将只启动API服务")
    
    # 启动服务器
    print("🚀 启动API服务器...")
    print("服务器地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/overview")
    print("前端页面: 将自动在浏览器中打开")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 启动Flask应用
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止，感谢使用！")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
