#!/usr/bin/env python3
"""
混合打包脚本 - 尝试 nuitka 编译，失败时使用 Python 脚本替代
确保生成的包能够正常运行
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

def run_command(cmd, cwd=None, timeout=300):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def try_nuitka_compile(root_path, version):
    """尝试使用 nuitka 编译"""
    log("🔨 Attempting nuitka compilation...")

    # 检查 nuitka 是否可用
    success, _, _ = run_command("python -c \"import nuitka\"")
    if not success:
        log("⚠️  Nuitka not available, installing...", "WARN")
        success, _, stderr = run_command("pip install nuitka")
        if not success:
            log(f"❌ Failed to install nuitka: {stderr}", "ERROR")
            return False

    # 尝试 nuitka 编译
    nuitka_cmd = (
        "python -m nuitka --standalone --mingw64 "
        "--windows-console-mode=force --windows-uac-admin "
        f"--windows-icon-from-ico=resources\\SRAicon.ico "
        "--company-name='StarRailAssistant Team' --product-name=StarRailAssistant "
        f"--file-version={version['version'].split('-')[0]} "
        f"--product-version={version['version'].split('-')[0]} "
        "--file-description='StarRailAssistant Component' "
        "--copyright='Copyright © 2024 Shasnow' "
        "--assume-yes-for-downloads --output-filename=SRA-cli "
        "--remove-output main.py"
    )

    log("🔨 Running nuitka compilation (this may take several minutes)...")
    success, stdout, stderr = run_command(nuitka_cmd, cwd=root_path, timeout=900)  # 15 minutes timeout

    if success and (root_path / "main.dist").exists():
        log("✅ Nuitka compilation successful!")
        return True
    else:
        log(f"❌ Nuitka compilation failed: {stderr}", "ERROR")
        return False

def create_python_fallback(root_path, version):
    """创建 Python 脚本替代方案"""
    log("🐍 Creating Python fallback solution...")

    # 创建 main.dist 目录
    main_dist = root_path / "main.dist"
    if main_dist.exists():
        shutil.rmtree(main_dist)
    main_dist.mkdir()

    # 复制 Python 环境和脚本
    log("📦 Copying Python components...")

    # 复制主要的 Python 文件
    python_files = ["main.py", "SRACore"]
    for item in python_files:
        src = root_path / item
        if src.exists():
            if src.is_file():
                shutil.copy2(src, main_dist / item)
                log(f"✅ Copied: {item}")
            else:
                shutil.copytree(src, main_dist / item, dirs_exist_ok=True)
                log(f"✅ Copied directory: {item}")

    # 创建启动脚本替代 SRA-cli.exe
    log("🔧 Creating startup scripts...")

    # 创建 SRA-cli.exe 的批处理替代
    bat_content = '''@echo off
cd /d "%~dp0"
python main.py %*
'''
    (main_dist / "SRA-cli.bat").write_text(bat_content, encoding='utf-8')

    # 创建 Python 启动器 (重命名为 .exe 以兼容前端)
    py_launcher = '''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 设置工作目录
os.chdir(Path(__file__).parent)

# 导入并运行主程序
try:
    import main
    main.main()
except Exception as e:
    print(f"Error: {e}")
    input("Press Enter to exit...")
    sys.exit(1)
'''
    (main_dist / "SRA-cli.py").write_text(py_launcher, encoding='utf-8')

    # 复制 Python 可执行文件作为 SRA-cli.exe (如果可能)
    python_exe = Path(sys.executable)
    if python_exe.exists():
        try:
            shutil.copy2(python_exe, main_dist / "python.exe")
            log("✅ Copied Python executable")

            # 创建一个简单的 exe 启动器
            exe_launcher = '''@echo off
"%~dp0python.exe" "%~dp0main.py" %*
'''
            (main_dist / "SRA-cli.bat").write_text(exe_launcher, encoding='utf-8')
        except Exception as e:
            log(f"⚠️  Could not copy Python executable: {e}", "WARN")

    # 复制必要的 Python 库 (简化版本)
    try:
        import site
        site_packages = Path(site.getsitepackages()[0])

        # 复制关键依赖
        critical_packages = [
            "PIL", "cv2", "numpy", "rapidocr_onnxruntime",
            "loguru", "rich", "schedule", "psutil"
        ]

        lib_dir = main_dist / "lib"
        lib_dir.mkdir(exist_ok=True)

        for pkg in critical_packages:
            pkg_path = site_packages / pkg
            if pkg_path.exists():
                try:
                    if pkg_path.is_dir():
                        shutil.copytree(pkg_path, lib_dir / pkg, dirs_exist_ok=True)
                    else:
                        shutil.copy2(pkg_path, lib_dir / pkg)
                    log(f"✅ Copied package: {pkg}")
                except Exception as e:
                    log(f"⚠️  Failed to copy {pkg}: {e}", "WARN")

    except Exception as e:
        log(f"⚠️  Could not copy Python libraries: {e}", "WARN")

    log("✅ Python fallback solution created")
    return True

def create_packages(root_path, version):
    """创建所有包"""
    log("📦 Creating packages...")

    main_dist = root_path / "main.dist"
    if not main_dist.exists():
        log("❌ main.dist directory not found", "ERROR")
        return False

    # 复制 .NET 前端到 main.dist
    log("📦 Integrating .NET frontend...")
    dotnet_publish = root_path / "SRAFrontend/bin/Release/net8.0/win-x64/publish"
    if dotnet_publish.exists():
        # 复制 .NET 文件到 main.dist，但不覆盖 Python 文件
        for item in dotnet_publish.iterdir():
            dst = main_dist / item.name
            if not dst.exists():  # 不覆盖已存在的文件
                if item.is_file():
                    shutil.copy2(item, dst)
                else:
                    shutil.copytree(item, dst, dirs_exist_ok=True)
        log("✅ .NET frontend integrated")
    else:
        log("⚠️  .NET publish directory not found", "WARN")

    # 复制资源文件
    log("📦 Copying resources...")
    resource_dirs = ["resources", "rapidocr_onnxruntime", "tasks"]
    for dir_name in resource_dirs:
        src_dir = root_path / dir_name
        dst_dir = main_dist / dir_name
        if src_dir.exists():
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
            log(f"✅ Copied: {dir_name}")

    # 复制 SRACore 配置
    sracore_dst = main_dist / "SRACore"
    if not sracore_dst.exists():
        sracore_dst.mkdir()

    sracore_src = root_path / "SRACore"
    if sracore_src.exists():
        # 复制 i18n
        i18n_src = sracore_src / "i18n"
        if i18n_src.exists():
            i18n_dst = sracore_dst / "i18n"
            if i18n_dst.exists():
                shutil.rmtree(i18n_dst)
            shutil.copytree(i18n_src, i18n_dst)

        # 复制配置文件
        config_src = sracore_src / "config.toml"
        if config_src.exists():
            shutil.copy2(config_src, sracore_dst / "config.toml")

    # 复制其他文件
    other_files = ["LICENSE", "README.md", "version.json"]
    for file_name in other_files:
        src_file = root_path / file_name
        if src_file.exists():
            shutil.copy2(src_file, main_dist / file_name)

    # 创建包
    version_str = version['version']

    # 核心包 (编译后的 Python 部分)
    log("📦 Creating Core package...")
    core_zip = f"StarRailAssistant_Core_v{version_str}"
    shutil.make_archive(
        str(root_path / core_zip),
        "zip",
        main_dist,
        "."
    )

    # 精简包 (只有 .NET 前端)
    if dotnet_publish.exists():
        log("📦 Creating Lite package...")
        lite_zip = f"StarRailAssistant_Lite_v{version_str}"
        shutil.make_archive(
            str(root_path / lite_zip),
            "zip",
            dotnet_publish,
            "."
        )

    # 完整包 (所有组件)
    log("📦 Creating Full package...")
    full_zip = f"StarRailAssistant_v{version_str}"
    shutil.make_archive(
        str(root_path / full_zip),
        "zip",
        main_dist,
        "."
    )

    # 清理
    shutil.rmtree(main_dist)

    log("✅ All packages created successfully!")
    return True

def main():
    """主函数"""
    try:
        root_path = Path(sys.argv[0]).resolve().parent
        log(f"🚀 Starting hybrid packaging from: {root_path}")

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

        if (root_path / "main.dist").exists():
            shutil.rmtree(root_path / "main.dist")

        # 尝试 nuitka 编译
        nuitka_success = try_nuitka_compile(root_path, version)

        # 如果 nuitka 失败，使用 Python 替代方案
        if not nuitka_success:
            log("🔄 Nuitka failed, using Python fallback...")
            if not create_python_fallback(root_path, version):
                log("💥 Python fallback also failed", "ERROR")
                return False

        # 创建包
        if not create_packages(root_path, version):
            log("💥 Package creation failed", "ERROR")
            return False

        # 创建版本信息
        log("📝 Creating version info...")
        version_content = f"v{version_str}\n\n{version['Announcement'][0]['content']}"
        (root_path / "version_info.txt").write_text(version_content, encoding="utf-8")

        # 报告结果
        log("=" * 50)
        log("🎉 Packaging completed successfully!")
        log(f"📋 Version: v{version_str}")
        log(f"🔧 Method: {'Nuitka compilation' if nuitka_success else 'Python fallback'}")

        log("📦 Generated files:")
        for zip_file in root_path.glob("StarRailAssistant_*.zip"):
            size = zip_file.stat().st_size / (1024 * 1024)
            log(f"  - {zip_file.name} ({size:.2f} MB)")
        log("  - version_info.txt")
        log("=" * 50)

        return True

    except Exception as e:
        log(f"💥 Fatal error: {e}", "ERROR")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)