@echo off
echo 启动 StarRail Assistant 后端...
python main.py %*
if errorlevel 1 (
    echo.
    echo 后端启动失败，请检查 Python 环境
    echo 按任意键退出...
    pause >nul
)
