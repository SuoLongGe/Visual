#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 同时启动后端API和前端页面
"""

import subprocess
import webbrowser
import time
import os
import sys
from threading import Thread

def start_backend():
    """启动后端API服务"""
    print("🚀 启动后端API服务...")
    try:
        # 启动Flask应用
        subprocess.run([sys.executable, "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 后端启动失败: {e}")
    except KeyboardInterrupt:
        print("\n🛑 后端服务已停止")

def open_frontend():
    """打开前端页面"""
    print("🌐 打开前端页面...")
    time.sleep(3)  # 等待后端启动
    
    # 打开前端开发服务器地址（如果运行）或后端地址
    url = "http://localhost:3000/"
    webbrowser.open(url)
    print(f"✅ 前端页面地址: {url}")
    print("💡 提示: 请确保前端开发服务器已启动 (cd fronted && npm run dev)")

def main():
    """主函数"""
    print("=" * 50)
    print("🏢 职数洞见 - 招聘数据分析平台")
    print("=" * 50)
    print()
    
    # 检查必要文件
    required_files = ["app.py", "fronted/index.html", "fronted/package.json"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return
    
    print("📋 系统检查:")
    print("✅ app.py - 后端API服务")
    print("✅ fronted/ - 前端项目目录")
    print()
    
    # 在新线程中打开前端页面
    frontend_thread = Thread(target=open_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # 启动后端服务
    try:
        start_backend()
    except KeyboardInterrupt:
        print("\n👋 感谢使用职数洞见平台！")

if __name__ == "__main__":
    main()

