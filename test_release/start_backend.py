#!/usr/bin/env python3
import subprocess
import sys
import os

os.chdir(os.path.dirname(__file__))
try:
    subprocess.run([sys.executable, "main.py"] + sys.argv[1:])
except Exception as e:
    print(f"启动失败: {e}")
    input("按 Enter 退出...")
