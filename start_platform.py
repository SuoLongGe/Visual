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
    
    # 获取当前目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, "index.html")
    
    # 打开HTML文件
    if os.path.exists(html_file):
        webbrowser.open(f"file://{html_file}")
        print(f"✅ 前端页面已打开: {html_file}")
    else:
        print(f"❌ 找不到前端页面文件: {html_file}")

def main():
    """主函数"""
    print("=" * 50)
    print("🏢 职数洞见 - 招聘数据分析平台")
    print("=" * 50)
    print()
    
    # 检查必要文件
    required_files = ["app.py", "index.html"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return
    
    print("📋 系统检查:")
    print("✅ app.py - 后端API服务")
    print("✅ index.html - 前端页面")
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

