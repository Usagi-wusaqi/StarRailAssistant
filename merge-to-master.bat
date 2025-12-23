@echo off
chcp 65001 >nul
echo 🚀 StarRailAssistant Fork 测试构建助手
echo.

REM 检查是否安装了 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.6+
    pause
    exit /b 1
)

REM 检查是否在 Git 仓库中
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo ❌ 当前目录不是 Git 仓库
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 运行 Python 脚本
python merge-to-master.py %*

echo.
echo 按任意键退出...
pause >nul