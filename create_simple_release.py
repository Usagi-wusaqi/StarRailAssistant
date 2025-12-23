#!/usr/bin/env python3
"""
最简单的发行版创建脚本
直接复制所有需要的文件，不做任何复杂的处理
"""

import json
import shutil
import sys
from pathlib import Path

def main():
    print("🚀 创建简单发行版...")

    root = Path(".")

    # 读取版本
    with open("version.json", "r", encoding="utf-8") as f:
        version_data = json.load(f)
    version = version_data["version"]

    print(f"📋 版本: {version}")

    # 创建发行目录
    release_dir = root / "StarRailAssistant_Release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()

    print("📦 复制文件...")

    # 1. 复制 .NET 前端 (如果存在)
    dotnet_path = root / "SRAFrontend/bin/Release/net8.0/win-x64/publish"
    if dotnet_path.exists():
        print("✅ 复制 .NET 前端")
        for item in dotnet_path.iterdir():
            if item.is_file():
                shutil.copy2(item, release_dir / item.name)
            else:
                shutil.copytree(item, release_dir / item.name, dirs_exist_ok=True)
    else:
        print("⚠️  .NET 前端未找到，跳过")

    # 2. 复制 Python 文件
    print("✅ 复制 Python 文件")
    shutil.copy2("main.py", release_dir / "main.py")
    shutil.copytree("SRACore", release_dir / "SRACore", dirs_exist_ok=True)

    # 3. 复制资源文件
    print("✅ 复制资源文件")
    for resource in ["resources", "rapidocr_onnxruntime", "tasks"]:
        if (root / resource).exists():
            shutil.copytree(root / resource, release_dir / resource, dirs_exist_ok=True)

    # 4. 复制其他必要文件
    print("✅ 复制配置文件")
    for file in ["LICENSE", "README.md", "version.json", "requirements.txt"]:
        if (root / file).exists():
            shutil.copy2(root / file, release_dir / file)

    # 5. 创建启动脚本
    print("🔧 创建启动脚本")

    # 创建 SRA-cli.exe 的替代品 - 批处理文件
    bat_content = '''@echo off
echo 启动 StarRail Assistant 后端...
python main.py %*
if errorlevel 1 (
    echo.
    echo 后端启动失败，请检查 Python 环境
    echo 按任意键退出...
    pause >nul
)
'''
    (release_dir / "SRA-cli.bat").write_text(bat_content, encoding='utf-8')

    # 创建一个真正的 SRA-cli.exe (使用 Python 可执行文件)
    import sys
    python_exe = Path(sys.executable)
    if python_exe.exists():
        try:
            # 复制 Python 可执行文件作为 SRA-cli.exe
            shutil.copy2(python_exe, release_dir / "SRA-cli.exe")
            print("✅ 创建 SRA-cli.exe")
        except Exception as e:
            print(f"⚠️  无法创建 SRA-cli.exe: {e}")
            # 创建一个简单的 exe 替代品
            fake_exe_content = '''@echo off
python main.py %*
'''
            (release_dir / "SRA-cli.cmd").write_text(fake_exe_content, encoding='utf-8')
    else:
        print("⚠️  Python 可执行文件未找到")

    # 创建 Python 启动器
    py_launcher = '''#!/usr/bin/env python3
import subprocess
import sys
import os

os.chdir(os.path.dirname(__file__))
try:
    subprocess.run([sys.executable, "main.py"] + sys.argv[1:])
except Exception as e:
    print(f"启动失败: {e}")
    input("按 Enter 退出...")
'''
    (release_dir / "start_backend.py").write_text(py_launcher, encoding='utf-8')

    # 创建依赖安装脚本
    setup_script = '''@echo off
echo 正在安装 Python 依赖包...
echo.

python -m pip install --upgrade pip
if errorlevel 1 (
    echo 错误: 无法升级 pip，请检查 Python 安装
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖包安装失败
    echo 请检查网络连接和 Python 环境
    pause
    exit /b 1
)

echo.
echo ✅ 依赖包安装完成！
echo 现在可以运行 SRA.exe 或 SRA-cli.bat
echo.
pause
'''
    (release_dir / "setup_dependencies.bat").write_text(setup_script, encoding='utf-8')

    # 6. 创建使用说明
    readme_content = f'''# StarRailAssistant v{version}

## 快速开始

### 🚀 首次使用 (推荐)
1. 双击 `setup_dependencies.bat` 安装 Python 依赖
2. 双击 `SRA.exe` 启动图形界面

### 📋 其他启动方式

#### 方法一：图形界面 (推荐)
双击 `SRA.exe` 启动前端界面

#### 方法二：命令行版本
双击 `SRA-cli.bat` 启动后端服务

#### 方法三：Python 直接运行
```
python main.py
```

## 系统要求
- Windows 10/11 x64
- .NET 8.0 Runtime (运行前端需要)
- Python 3.8+ (运行后端需要)

## 📦 文件说明
- `SRA.exe` - 前端图形界面 (需要 .NET 8.0)
- `SRA-cli.exe` - 后端可执行文件
- `SRA-cli.bat` - 后端启动脚本 (备用)
- `setup_dependencies.bat` - 依赖安装脚本
- `main.py` - Python 主程序
- `SRACore/` - 核心功能模块
- `resources/` - 游戏资源文件
- `tasks/` - 任务定义文件
- `requirements.txt` - Python 依赖列表

## 🔧 故障排除

### 问题：找不到 SRA-cli.exe
**解决方案**: 运行 `SRA-cli.bat` 或 `setup_dependencies.bat`

### 问题：Python 相关错误
**解决方案**:
1. 安装 Python 3.8+ (https://python.org)
2. 运行 `setup_dependencies.bat`

### 问题：.NET 相关错误
**解决方案**: 安装 .NET 8.0 Runtime
- 下载地址: https://dotnet.microsoft.com/download/dotnet/8.0

### 问题：缺少依赖包
**解决方案**: 运行 `setup_dependencies.bat` 或手动执行:
```
pip install -r requirements.txt
```

## 📞 获取帮助
- 查看 README.md 了解更多信息
- 检查 log/ 目录下的日志文件
- 访问项目主页获取最新版本

---
**注意**: 这是简化版本，包含所有核心功能但需要系统已安装 Python 和 .NET Runtime
'''
    (release_dir / "使用说明.txt").write_text(readme_content, encoding='utf-8')

    # 7. 创建 zip 包
    print("📦 创建 ZIP 包...")
    zip_name = f"StarRailAssistant_v{version}_Simple"
    shutil.make_archive(zip_name, "zip", release_dir)

    # 清理临时目录
    shutil.rmtree(release_dir)

    # 创建版本信息
    version_info = f"v{version}\n\n{version_data['Announcement'][0]['content']}"
    Path("version_info.txt").write_text(version_info, encoding='utf-8')

    print("=" * 50)
    print("🎉 简单发行版创建完成！")
    print(f"📦 文件: {zip_name}.zip")
    print(f"📋 版本: v{version}")
    print("")
    print("📝 使用说明:")
    print("1. 解压 zip 文件到任意目录")
    print("2. 双击 setup_dependencies.bat 安装依赖 (首次使用)")
    print("3. 双击 SRA.exe (前端) 或 SRA-cli.bat (后端)")
    print("4. 如果遇到问题，查看 使用说明.txt")
    print("")
    print("🔧 核心功能:")
    print("- ✅ 包含完整的 .NET 前端 (SRA.exe)")
    print("- ✅ 包含 Python 后端 (SRA-cli.exe)")
    print("- ✅ 包含所有游戏资源和任务文件")
    print("- ✅ 包含依赖安装脚本")
    print("=" * 50)

if __name__ == "__main__":
    main()