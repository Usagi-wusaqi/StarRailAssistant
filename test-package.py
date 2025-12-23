#!/usr/bin/env python3
"""
包测试脚本 - 验证生成的包是否能正常工作
"""

import zipfile
import tempfile
import subprocess
import sys
from pathlib import Path
import shutil

def log(message, level="INFO"):
    """日志输出"""
    print(f"[{level}] {message}")

def test_package(zip_path):
    """测试指定的包"""
    log(f"🧪 Testing package: {zip_path.name}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 解压包
        log("📦 Extracting package...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_path)

        # 检查关键文件
        log("🔍 Checking key files...")

        key_files = {
            "SRA.exe": ".NET frontend executable",
            "SRA-cli.bat": "Python backend launcher",
            "main.py": "Python main script",
            "python.exe": "Python runtime",
            "SRACore": "Core Python modules"
        }

        missing_files = []
        for file_name, description in key_files.items():
            file_path = temp_path / file_name
            if file_path.exists():
                log(f"✅ Found: {description}")
            else:
                log(f"❌ Missing: {description}", "ERROR")
                missing_files.append(file_name)

        if missing_files:
            log(f"❌ Package incomplete: missing {missing_files}", "ERROR")
            return False

        # 测试 Python 脚本
        log("🐍 Testing Python script...")
        python_exe = temp_path / "python.exe"
        main_py = temp_path / "main.py"

        if python_exe.exists() and main_py.exists():
            try:
                # 测试 Python 脚本是否能导入
                result = subprocess.run([
                    str(python_exe), "-c",
                    "import sys; sys.path.insert(0, '.'); import main; print('✅ Python script imports successfully')"
                ], cwd=temp_path, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    log("✅ Python script test passed")
                else:
                    log(f"❌ Python script test failed: {result.stderr}", "ERROR")
                    return False
            except Exception as e:
                log(f"❌ Python script test error: {e}", "ERROR")
                return False

        # 检查资源文件
        log("📁 Checking resources...")
        resource_dirs = ["resources", "rapidocr_onnxruntime", "tasks"]
        for dir_name in resource_dirs:
            dir_path = temp_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                file_count = len(list(dir_path.rglob("*")))
                log(f"✅ {dir_name}: {file_count} files")
            else:
                log(f"⚠️  {dir_name}: not found", "WARN")

        log(f"✅ Package {zip_path.name} test completed successfully!")
        return True

def main():
    """主函数"""
    log("🚀 Starting package testing...")

    root_path = Path(".")
    zip_files = list(root_path.glob("StarRailAssistant_*.zip"))

    if not zip_files:
        log("❌ No package files found", "ERROR")
        log("💡 Run 'python package_complete.py' first to create packages")
        return False

    log(f"📦 Found {len(zip_files)} packages to test")

    success_count = 0
    for zip_file in zip_files:
        try:
            if test_package(zip_file):
                success_count += 1
            log("")  # 空行分隔
        except Exception as e:
            log(f"💥 Error testing {zip_file.name}: {e}", "ERROR")

    log("=" * 50)
    log(f"🎯 Test Results: {success_count}/{len(zip_files)} packages passed")

    if success_count == len(zip_files):
        log("🎉 All packages passed testing!")
        log("📋 Ready for distribution")
    else:
        log("⚠️  Some packages failed testing", "WARN")
        log("🔧 Check the logs above for details")

    log("=" * 50)
    return success_count == len(zip_files)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)