#!/usr/bin/env python3
"""
一键启动脚本 — 开发模式同时启动后端 uvicorn 和前端 Vite 开发服务器。
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")


def main():
    print("🚀 启动后端 uvicorn (port 8000)...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
    )

    print("🚀 启动前端 Vite 开发服务器 (port 5173)...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
    )

    print("\n📋 前端: http://localhost:5173")
    print("📋 后端: http://localhost:8000")
    print("📋 API:  http://localhost:8000/docs")
    print("按 Ctrl+C 停止所有服务\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("已停止")


if __name__ == "__main__":
    main()
