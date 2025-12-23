#!/usr/bin/env python3
"""
改进的简化版打包脚本 - 跳过 nuitka 编译，只创建基本的 zip 包
增强错误处理和详细日志输出
"""

import json
import os
import shutil
import sys
from pathlib import Path
import traceback

def log(message, level="INFO"):
    """统一的日志输出"""
    print(f"[{level}] {message}")

def safe_copy(src, dst, description=""):
    """安全的文件/目录复制"""
    try:
        if src.is_file():
            shutil.copy2(src, dst)
            log(f"✅ Copied file: {description or src.name}")
        elif src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            log(f"✅ Copied directory: {description or src.name}")
        else:
            log(f"⚠️  Source not found: {src}", "WARN")
            return False
        return True
    except Exception as e:
        log(f"❌ Failed to copy {src}: {e}", "ERROR")
        return False

def safe_remove(path):
    """安全的删除操作"""
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            log(f"🗑️  Removed: {path}")
    except Exception as e:
        log(f"⚠️  Failed to remove {path}: {e}", "WARN")

def create_zip_safe(base_name, root_dir, base_dir=".", description=""):
    """安全的 zip 创建"""
    try:
        if not Path(root_dir).exists():
            log(f"❌ Source directory not found: {root_dir}", "ERROR")
            return False

        zip_path = shutil.make_archive(
            base_name=str(base_name),
            format="zip",
            root_dir=root_dir,
            base_dir=base_dir,
        )

        zip_size = Path(zip_path).stat().st_size / (1024 * 1024)  # MB
        log(f"✅ Created {description}: {Path(zip_path).name} ({zip_size:.2f} MB)")
        return True
    except Exception as e:
        log(f"❌ Failed to create zip {description}: {e}", "ERROR")
        return False

if __name__ == "__main__":
    try:
        root_path = Path(sys.argv[0]).resolve().parent
        log(f"🚀 Starting enhanced packaging from: {root_path}")

        # 读取版本信息
        version_file = root_path / "version.json"
        if not version_file.exists():
            log("❌ version.json not found", "ERROR")
            sys.exit(1)

        with version_file.open(mode="r", encoding="utf-8") as f:
            version = json.load(f)

        version_str = version['version']
        log(f"📋 Version: {version_str}")

        # 清理旧的构建文件
        log("🧹 Cleaning old build files...")
        for old_zip in root_path.glob("StarRailAssistant_*.zip"):
            safe_remove(old_zip)
        safe_remove(root_path / "version_info.txt")

        # 创建临时目录
        temp_dir = root_path / "temp_dist"
        safe_remove(temp_dir)
        temp_dir.mkdir()
        log(f"📁 Created temp directory: {temp_dir}")

        # 检查并复制 .NET 发布文件
        dotnet_publish_path = root_path / "SRAFrontend/bin/Release/net8.0/win-x64/publish"
        log(f"🔍 Checking .NET publish path: {dotnet_publish_path}")

        if dotnet_publish_path.exists():
            log("📦 Copying .NET Frontend...")
            if safe_copy(dotnet_publish_path, temp_dir, ".NET Frontend"):
                # 验证关键文件
                exe_file = temp_dir / "SRA.exe"
                if exe_file.exists():
                    log("✅ Main executable found in package")
                else:
                    log("⚠️  Main executable not found", "WARN")
            else:
                log("❌ Failed to copy .NET frontend", "ERROR")
        else:
            log("❌ .NET publish directory not found - did dotnet publish succeed?", "ERROR")
            sys.exit(1)

        # 复制资源文件
        log("📦 Copying resources...")
        resource_dirs = {
            "resources": "Game resources",
            "rapidocr_onnxruntime": "OCR runtime",
            "tasks": "Task definitions"
        }

        for dir_name, description in resource_dirs.items():
            src_dir = root_path / dir_name
            if src_dir.exists():
                safe_copy(src_dir, temp_dir / dir_name, description)
            else:
                log(f"⚠️  {description} directory not found: {dir_name}", "WARN")

        # 复制 SRACore 配置
        log("📦 Copying SRACore configuration...")
        sracore_src = root_path / "SRACore"
        if sracore_src.exists():
            sracore_dst = temp_dir / "SRACore"
            sracore_dst.mkdir(exist_ok=True)

            # 复制 i18n 目录
            i18n_src = sracore_src / "i18n"
            if i18n_src.exists():
                safe_copy(i18n_src, sracore_dst / "i18n", "Internationalization files")

            # 复制配置文件
            config_file = sracore_src / "config.toml"
            if config_file.exists():
                safe_copy(config_file, sracore_dst / "config.toml", "Core configuration")
        else:
            log("⚠️  SRACore directory not found", "WARN")

        # 复制其他必要文件
        log("📦 Copying additional files...")
        other_files = {
            "LICENSE": "License file",
            "README.md": "Documentation",
            "version.json": "Version information"
        }

        for file_name, description in other_files.items():
            src_file = root_path / file_name
            if src_file.exists():
                safe_copy(src_file, temp_dir / file_name, description)

        # 创建 zip 包
        log("📦 Creating zip packages...")
        success_count = 0

        # 完整版 zip
        full_zip_name = f"StarRailAssistant_v{version_str}"
        if create_zip_safe(
            root_path / full_zip_name,
            temp_dir,
            ".",
            "Full package"
        ):
            success_count += 1

        # 精简版 zip (只有 .NET 部分)
        if dotnet_publish_path.exists():
            lite_zip_name = f"StarRailAssistant_Lite_v{version_str}"
            if create_zip_safe(
                root_path / lite_zip_name,
                dotnet_publish_path,
                ".",
                "Lite package"
            ):
                success_count += 1

        # 核心版 zip (Python 组件)
        log("📦 Creating core package...")
        core_temp = root_path / "core_temp"
        safe_remove(core_temp)
        core_temp.mkdir()

        # 复制 Python 文件作为核心版
        python_components = {
            "main.py": "Main entry point",
            "SRACore": "Core Python modules"
        }

        for item, description in python_components.items():
            src_path = root_path / item
            if src_path.exists():
                safe_copy(src_path, core_temp / item, description)

        core_zip_name = f"StarRailAssistant_Core_v{version_str}"
        if create_zip_safe(
            root_path / core_zip_name,
            core_temp,
            ".",
            "Core package"
        ):
            success_count += 1

        # 清理临时目录
        log("🧹 Cleaning up temporary directories...")
        safe_remove(temp_dir)
        safe_remove(core_temp)

        # 创建版本信息文件
        log("📝 Creating version info file...")
        try:
            version_content = f"v{version_str}\n\n{version['Announcement'][0]['content']}"
            (root_path / "version_info.txt").write_text(version_content, encoding="utf-8")
            log("✅ Version info file created")
        except Exception as e:
            log(f"❌ Failed to create version info: {e}", "ERROR")

        # 最终报告
        log("=" * 50)
        log(f"🎉 Packaging completed! Created {success_count}/3 packages")
        log(f"📋 Version: v{version_str}")

        # 列出生成的文件
        log("📦 Generated files:")
        for zip_file in root_path.glob("StarRailAssistant_*.zip"):
            size = zip_file.stat().st_size / (1024 * 1024)
            log(f"  - {zip_file.name} ({size:.2f} MB)")

        if (root_path / "version_info.txt").exists():
            log(f"  - version_info.txt")

        log("=" * 50)

    except Exception as e:
        log(f"💥 Fatal error during packaging: {e}", "ERROR")
        log("Stack trace:", "ERROR")
        traceback.print_exc()
        sys.exit(1)