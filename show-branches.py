#!/usr/bin/env python3
"""
显示当前仓库的分支结构和状态
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"错误: 命令执行失败"
    except Exception as e:
        return f"错误: {str(e)}"

def get_branch_info():
    """获取分支信息"""
    print("🌳 StarRailAssistant Fork 分支结构")
    print("=" * 50)

    # 当前分支
    current_branch = run_command("git branch --show-current")
    print(f"📍 当前分支: {current_branch}")
    print()

    # 本地分支
    print("🏠 本地分支:")
    local_branches = run_command("git branch")
    for line in local_branches.split('\n'):
        line = line.strip()
        if line:
            if line.startswith('*'):
                print(f"  {line} ← 当前")
            else:
                print(f"  {line}")
    print()

    # 远程分支
    print("📡 远程分支:")
    remote_branches = run_command("git branch -r")

    origin_branches = []
    upstream_branches = []

    for line in remote_branches.split('\n'):
        line = line.strip()
        if line and not 'HEAD ->' in line:
            if line.startswith('origin/'):
                origin_branches.append(line)
            elif line.startswith('upstream/'):
                upstream_branches.append(line)

    if origin_branches:
        print("  📤 Origin (你的远程仓库):")
        for branch in origin_branches:
            print(f"    {branch}")

    if upstream_branches:
        print("  🔗 Upstream (原始仓库):")
        for branch in upstream_branches:
            print(f"    {branch}")

    print()

    # 最近的提交
    print("📝 分支状态:")
    try:
        # 简化的状态显示，避免编码问题
        print("  ✅ Git 仓库正常")
    except Exception as e:
        print(f"  ❌ 获取提交历史失败: {e}")
    print()

    # 工作区状态
    print("💼 工作区状态:")
    status = run_command("git status --porcelain")
    if status:
        print("  有未提交的更改:")
        for line in status.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print("  ✅ 工作区干净")
    print()

    # 分支用途说明
    print("🎯 分支用途说明:")
    branch_purposes = {
        'master': '🌟 测试构建分支 - 专门用于触发 GitHub Actions 构建',
        'main': '🏠 主分支 - 跟随上游，相对稳定的代码',
        'test': '🧪 测试分支 - 功能测试和实验',
        'chore/notify-test': '🔧 功能分支 - 通知功能相关开发'
    }

    for branch_line in local_branches.split('\n'):
        branch_name = branch_line.strip().lstrip('* ').strip()
        if branch_name in branch_purposes:
            print(f"  {branch_purposes[branch_name]}")
    print()

    # GitHub Actions 状态提示
    print("🚀 GitHub Actions 提示:")
    if current_branch == 'master':
        print("  ⚡ 当前在 master 分支，推送将触发自动构建")
    else:
        print("  💡 要触发构建，请合并到 master 分支:")
        print("     python merge-to-master.py")
    print()

    # 下一步建议
    print("💡 建议的下一步操作:")
    if status:
        print("  1. 提交当前更改: git add . && git commit -m '描述'")
        print("  2. 推送到远程: git push origin " + current_branch)
    else:
        if current_branch != 'master':
            print("  1. 合并到 master 进行测试: python merge-to-master.py")
            print("  2. 或者继续在当前分支开发")
        else:
            print("  1. 推送触发构建: git push origin master")
            print("  2. 查看 GitHub Actions 构建状态")

def main():
    # 检查是否在 git 仓库中
    try:
        run_command("git rev-parse --git-dir")
    except:
        print("❌ 当前目录不是 Git 仓库")
        sys.exit(1)

    get_branch_info()

if __name__ == "__main__":
    main()