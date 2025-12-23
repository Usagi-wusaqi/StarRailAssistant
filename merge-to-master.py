#!/usr/bin/env python3
"""
分支合并到 master 的辅助脚本
用于将其他分支的更改合并到 master 分支进行测试构建
"""

import subprocess
import sys
import argparse
from datetime import datetime

def run_command(cmd, check=True):
    """执行命令并返回结果"""
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        sys.exit(1)
    return result

def get_current_branch():
    """获取当前分支名"""
    result = run_command("git branch --show-current")
    return result.stdout.strip()

def get_all_branches():
    """获取所有本地分支"""
    result = run_command("git branch")
    branches = []
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line and not line.startswith('*'):
            branches.append(line)
        elif line.startswith('* '):
            branches.append(line[2:])
    return branches

def merge_branch_to_master(source_branch, create_commit=True):
    """将指定分支合并到 master"""
    print(f"\n开始将 {source_branch} 合并到 master...")

    # 确保工作区干净
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print("⚠️  工作区有未提交的更改，请先提交或暂存")
        return False

    # 切换到 master 分支
    print("切换到 master 分支...")
    run_command("git checkout master")

    # 拉取最新的 master
    print("拉取最新的 master 分支...")
    run_command("git pull origin master", check=False)

    # 合并源分支
    print(f"合并 {source_branch} 到 master...")
    result = run_command(f"git merge {source_branch} --no-ff", check=False)

    if result.returncode != 0:
        print(f"❌ 合并失败: {result.stderr}")
        print("请手动解决冲突后重试")
        return False

    if create_commit:
        # 创建合并提交
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"Merge {source_branch} for testing - {timestamp}"
        run_command(f'git commit --amend -m "{commit_msg}"', check=False)

    print(f"✅ 成功将 {source_branch} 合并到 master")
    return True

def push_to_remote():
    """推送到远程仓库"""
    print("\n推送 master 分支到远程仓库...")
    result = run_command("git push origin master", check=False)

    if result.returncode != 0:
        print(f"❌ 推送失败: {result.stderr}")
        return False

    print("✅ 成功推送到远程仓库")
    print("🚀 GitHub Actions 构建将自动开始...")
    return True

def main():
    parser = argparse.ArgumentParser(description="将分支合并到 master 进行测试构建")
    parser.add_argument("--branch", "-b", help="要合并的源分支名")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用分支")
    parser.add_argument("--no-push", action="store_true", help="不自动推送到远程")
    parser.add_argument("--no-commit", action="store_true", help="不创建合并提交")

    args = parser.parse_args()

    # 检查是否在 git 仓库中
    result = run_command("git rev-parse --git-dir", check=False)
    if result.returncode != 0:
        print("❌ 当前目录不是 Git 仓库")
        sys.exit(1)

    # 列出分支
    if args.list:
        branches = get_all_branches()
        print("可用的分支:")
        for branch in branches:
            print(f"  - {branch}")
        return

    # 获取要合并的分支
    source_branch = args.branch
    if not source_branch:
        branches = get_all_branches()
        current = get_current_branch()

        print("可用的分支:")
        for i, branch in enumerate(branches, 1):
            marker = " (当前)" if branch == current else ""
            print(f"  {i}. {branch}{marker}")

        try:
            choice = input(f"\n请选择要合并的分支 (1-{len(branches)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(branches):
                    source_branch = branches[idx]
                else:
                    print("❌ 无效的选择")
                    sys.exit(1)
            else:
                source_branch = choice
        except KeyboardInterrupt:
            print("\n操作已取消")
            sys.exit(0)

    if source_branch == "master":
        print("❌ 不能将 master 分支合并到自己")
        sys.exit(1)

    # 确认操作
    print(f"\n将要执行的操作:")
    print(f"  源分支: {source_branch}")
    print(f"  目标分支: master")
    print(f"  推送到远程: {'否' if args.no_push else '是'}")

    confirm = input("\n确认执行? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("操作已取消")
        sys.exit(0)

    # 执行合并
    success = merge_branch_to_master(source_branch, not args.no_commit)
    if not success:
        sys.exit(1)

    # 推送到远程
    if not args.no_push:
        success = push_to_remote()
        if not success:
            sys.exit(1)

    print(f"\n🎉 完成! {source_branch} 已合并到 master 分支")
    if not args.no_push:
        print("📱 可以在 GitHub Actions 页面查看构建进度")

if __name__ == "__main__":
    main()