#!/usr/bin/env python3
"""
完整打包脚本 - 创建包含 Python 运行时的完整包
确保生成的包能够独立运行，无需额外安装 Python
"""

import json
import os
import shutil
import sys
import subprocess
from pathlib import Path
import traceback

def log(message, level="INFO"):
    """统一的日志输出"""
    print(f"[{level}] {message}")

def safe_rmtree(path):
    """安全删除目录，处理文件锁定问题"""
    import time
    max_retries = 3
    for i in range(max_retries):
        try:
            if path.exists():
                shutil.rmtree(path)
            return True
        except PermissionError as e:
            if i < max_retries - 1:
                log(f"⚠️  File locked, retrying in 2 seconds... ({i+1}/{max_retries})", "WARN")
                time.sleep(2)
            else:
                log(f"❌ Could not remove {path}: {e}", "ERROR")
                return False
        except Exception as e:
            log(f"❌ Error removing {path}: {e}", "ERROR")
            return False
    return False

def create_complete_package(root_path, version):
    """创建完整的可运行包"""
    log("📦 Creating complete runnable package...")

    # 创建主分发目录
    main_dist = root_path / "main.dist"
    if main_dist.exists():
        shutil.rmtree(main_dist)
    main_dist.mkdir()

    # 1. 复制 .NET 前端
    log("📦 Copying .NET frontend...")
    dotnet_publish = root_path / "SRAFrontend/bin/Release/net8.0/win-x64/publish"
    if dotnet_publish.exists():
        for item in dotnet_publish.iterdir():
            if item.is_file():
                shutil.copy2(item, main_dist / item.name)
            else:
                shutil.copytree(item, main_dist / item.name, dirs_exist_ok=True)
        log("✅ .NET frontend copied")
    else:
        log("❌ .NET publish directory not found", "ERROR")
        return False

    # 2. 复制 Python 运行时和脚本
    log("🐍 Setting up Python runtime...")

    # 复制 Python 可执行文件
    python_exe = Path(sys.executable)
    if python_exe.exists():
        shutil.copy2(python_exe, main_dist / "python.exe")
        log("✅ Python executable copied")

    # 复制 Python DLLs (如果存在)
    python_dir = python_exe.parent
    for dll_pattern in ["python*.dll", "vcruntime*.dll", "msvcp*.dll"]:
        for dll_file in python_dir.glob(dll_pattern):
            try:
                shutil.copy2(dll_file, main_dist / dll_file.name)
                log(f"✅ Copied: {dll_file.name}")
            except Exception as e:
                log(f"⚠️  Could not copy {dll_file.name}: {e}", "WARN")

    # 复制 Python 标准库 (简化版)
    python_lib = python_dir / "Lib"
    if python_lib.exists():
        lib_dist = main_dist / "Lib"
        lib_dist.mkdir()

        # 复制关键的标准库模块
        essential_modules = [
            "json", "os", "sys", "pathlib", "shutil", "subprocess",
            "threading", "time", "datetime", "re", "collections",
            "urllib", "http", "email", "logging", "xml", "html",
            "encodings", "importlib", "site-packages"
        ]

        for module in essential_modules:
            src_path = python_lib / module
            if src_path.exists():
                try:
                    if src_path.is_file():
                        shutil.copy2(src_path, lib_dist / module)
                    else:
                        shutil.copytree(src_path, lib_dist / module, dirs_exist_ok=True)
                    log(f"✅ Copied stdlib: {module}")
                except Exception as e:
                    log(f"⚠️  Could not copy {module}: {e}", "WARN")

    # 3. 复制项目的 Python 文件
    log("📦 Copying project Python files...")

    # 复制主要文件
    main_files = ["main.py"]
    for file_name in main_files:
        src_file = root_path / file_name
        if src_file.exists():
            shutil.copy2(src_file, main_dist / file_name)
            log(f"✅ Copied: {file_name}")

    # 复制 SRACore 目录
    sracore_src = root_path / "SRACore"
    if sracore_src.exists():
        shutil.copytree(sracore_src, main_dist / "SRACore", dirs_exist_ok=True)
        log("✅ Copied: SRACore")

    # 4. 复制依赖包
    log("📦 Copying Python dependencies...")

    try:
        import site
        site_packages_paths = site.getsitepackages()
        if hasattr(site, 'getusersitepackages'):
            site_packages_paths.append(site.getusersitepackages())

        # 创建 site-packages 目录
        site_packages_dist = main_dist / "Lib" / "site-packages"
        site_packages_dist.mkdir(parents=True, exist_ok=True)

        # 关键依赖包
        critical_packages = [
            "PIL", "cv2", "numpy", "rapidocr_onnxruntime",
            "loguru", "rich", "schedule", "psutil", "plyer",
            "pyscreeze", "pygetwindow", "pyautogui", "pynput"
        ]

        for pkg_name in critical_packages:
            found = False
            for site_path in site_packages_paths:
                site_path = Path(site_path)
                if not site_path.exists():
                    continue

                # 查找包
                pkg_paths = list(site_path.glob(f"{pkg_name}*"))
                for pkg_path in pkg_paths:
                    if pkg_path.is_dir() and not pkg_path.name.endswith('.dist-info'):
                        try:
                            dst_path = site_packages_dist / pkg_path.name
                            if not dst_path.exists():
                                shutil.copytree(pkg_path, dst_path, dirs_exist_ok=True)
                                log(f"✅ Copied package: {pkg_path.name}")
                                found = True
                                break
                        except Exception as e:
                            log(f"⚠️  Failed to copy {pkg_path.name}: {e}", "WARN")

                if found:
                    break

            if not found:
                log(f"⚠️  Package not found: {pkg_name}", "WARN")

    except Exception as e:
        log(f"⚠️  Error copying dependencies: {e}", "WARN")

    # 5. 复制资源文件
    log("📦 Copying resources...")
    resource_dirs = ["resources", "rapidocr_onnxruntime", "tasks"]
    for dir_name in resource_dirs:
        src_dir = root_path / dir_name
        if src_dir.exists():
            shutil.copytree(src_dir, main_dist / dir_name, dirs_exist_ok=True)
            log(f"✅ Copied: {dir_name}")

    # 6. 复制其他必要文件
    other_files = ["LICENSE", "README.md", "version.json"]
    for file_name in other_files:
        src_file = root_path / file_name
        if src_file.exists():
            shutil.copy2(src_file, main_dist / file_name)
            log(f"✅ Copied: {file_name}")

    # 7. 创建启动脚本
    log("🔧 Creating startup scripts...")

    # 创建 SRA-cli.bat (主启动脚本)
    bat_content = '''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0;%~dp0\\Lib;%~dp0\\Lib\\site-packages;%PYTHONPATH%
"%~dp0python.exe" main.py %*
if errorlevel 1 (
    echo.
    echo 程序执行出错，按任意键退出...
    pause >nul
)
'''
    (main_dist / "SRA-cli.bat").write_text(bat_content, encoding='utf-8')

    # 创建 SRA-cli.exe 的替代 (复制 python.exe)
    try:
        shutil.copy2(main_dist / "python.exe", main_dist / "SRA-cli.exe")
        log("✅ Created SRA-cli.exe")
    except Exception as e:
        log(f"⚠️  Could not create SRA-cli.exe: {e}", "WARN")

    # 创建 Python 路径配置
    pth_content = '''import sys
import os
base_dir = os.path.dirname(__file__)
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'Lib'))
sys.path.insert(0, os.path.join(base_dir, 'Lib', 'site-packages'))
'''
    (main_dist / "sitecustomize.py").write_text(pth_content, encoding='utf-8')

    # 创建 pyvenv.cfg 文件
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    pyvenv_content = f'''home = {sys.executable}
include-system-site-packages = false
version = {python_version}
'''
    (main_dist / "pyvenv.cfg").write_text(pyvenv_content, encoding='utf-8')

    log("✅ Complete package created successfully")
    return True

def create_packages(root_path, version):
    """创建所有版本的包"""
    log("📦 Creating all package variants...")

    version_str = version['version']
    main_dist = root_path / "main.dist"

    if not main_dist.exists():
        log("❌ main.dist not found", "ERROR")
        return False

    # 完整包
    log("📦 Creating Full package...")
    full_zip = f"StarRailAssistant_v{version_str}"
    shutil.make_archive(str(root_path / full_zip), "zip", main_dist, ".")

    # 核心包 (Python 组件)
    log("📦 Creating Core package...")
    core_temp = root_path / "core_temp"
    if core_temp.exists():
        shutil.rmtree(core_temp)
    core_temp.mkdir()

    # 复制 Python 相关文件到核心包
    python_items = ["python.exe", "main.py", "SRACore", "Lib", "SRA-cli.bat", "sitecustomize.py"]
    for item in python_items:
        src = main_dist / item
        if src.exists():
            if src.is_file():
                shutil.copy2(src, core_temp / item)
            else:
                shutil.copytree(src, core_temp / item, dirs_exist_ok=True)

    core_zip = f"StarRailAssistant_Core_v{version_str}"
    shutil.make_archive(str(root_path / core_zip), "zip", core_temp, ".")
    safe_rmtree(core_temp)

    # 精简包 (只有 .NET 前端)
    dotnet_publish = root_path / "SRAFrontend/bin/Release/net8.0/win-x64/publish"
    if dotnet_publish.exists():
        log("📦 Creating Lite package...")
        lite_zip = f"StarRailAssistant_Lite_v{version_str}"
        shutil.make_archive(str(root_path / lite_zip), "zip", dotnet_publish, ".")

    # 清理
    safe_rmtree(main_dist)

    log("✅ All packages created!")
    return True

def main():
    """主函数"""
    try:
        root_path = Path(sys.argv[0]).resolve().parent
        log(f"🚀 Starting complete packaging from: {root_path}")

        # 读取版本信息
        version_file = root_path / "version.json"
        if not version_file.exists():
            log("❌ version.json not found", "ERROR")
            return False

        with version_file.open("r", encoding="utf-8") as f:
            version = json.load(f)

        version_str = version['version']
        log(f"📋 Version: {version_str}")

        # 清理旧文件
        log("🧹 Cleaning old files...")
        for old_zip in root_path.glob("StarRailAssistant_*.zip"):
            old_zip.unlink()

        if (root_path / "version_info.txt").exists():
            (root_path / "version_info.txt").unlink()

        # 创建完整包
        if not create_complete_package(root_path, version):
            log("💥 Failed to create complete package", "ERROR")
            return False

        # 创建所有包变体
        if not create_packages(root_path, version):
            log("💥 Failed to create packages", "ERROR")
            return False

        # 创建版本信息
        log("📝 Creating version info...")
        version_content = f"v{version_str}\n\n{version['Announcement'][0]['content']}"
        (root_path / "version_info.txt").write_text(version_content, encoding="utf-8")

        # 报告结果
        log("=" * 50)
        log("🎉 Complete packaging finished!")
        log(f"📋 Version: v{version_str}")
        log("📦 Generated files:")
        for zip_file in root_path.glob("StarRailAssistant_*.zip"):
            size = zip_file.stat().st_size / (1024 * 1024)
            log(f"  - {zip_file.name} ({size:.2f} MB)")
        log("  - version_info.txt")
        log("")
        log("🔧 Usage instructions:")
        log("  1. 解压 StarRailAssistant_v*.zip")
        log("  2. 运行 SRA-cli.bat 或 SRA.exe (前端)")
        log("  3. 如果遇到问题，检查是否有 .NET 8.0 Runtime")
        log("=" * 50)

        return True

    except Exception as e:
        log(f"💥 Fatal error: {e}", "ERROR")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)