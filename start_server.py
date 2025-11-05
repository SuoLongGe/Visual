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
        # 前端现在由Vite开发服务器运行
        url = "http://localhost:3000/"
        webbrowser.open(url)
        print(f"🌐 前端页面地址: {url}")
        print("💡 提示: 请确保前端开发服务器已启动 (cd fronted && npm run dev)")
    
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
    frontend_index = os.path.join("fronted", "index.html")
    frontend_package = os.path.join("fronted", "package.json")
    if os.path.exists(frontend_index) and os.path.exists(frontend_package):
        print("✅ 前端项目文件存在")
        open_frontend()
    else:
        print("⚠️  前端页面文件不存在，将只启动API服务")
        print("💡 提示: 前端项目位于 fronted/ 目录，请先启动前端开发服务器")
    
    # 启动服务器
    print("🚀 启动API服务器...")
    print("服务器地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/overview")
    print("前端页面: http://localhost:3000 (需要单独启动前端开发服务器)")
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
