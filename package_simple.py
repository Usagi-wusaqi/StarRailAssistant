#!/usr/bin/env python3
"""
简化版打包脚本 - 跳过 nuitka 编译，只创建基本的 zip 包
用于快速测试构建流程
"""

import json
import os
import shutil
import sys
from pathlib import Path

if __name__ == "__main__":
    root_path = Path(sys.argv[0]).resolve().parent

    with (root_path / "version.json").open(mode="r", encoding="utf-8") as f:
        version = json.load(f)

    print("Creating simplified packages...")

    # 创建临时目录
    temp_dir = root_path / "temp_dist"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    print("Copying .NET Frontend...")
    # 复制 .NET 发布的文件
    dotnet_publish_path = root_path / "SRAFrontend/bin/Release/net8.0/win-x64/publish"
    if dotnet_publish_path.exists():
        shutil.copytree(dotnet_publish_path, temp_dir, dirs_exist_ok=True)
    else:
        print("Warning: .NET publish directory not found")

    print("Copying resources...")
    # 复制资源文件
    resource_dirs = ["resources", "rapidocr_onnxruntime", "tasks"]
    for dir_name in resource_dirs:
        src_dir = root_path / dir_name
        if src_dir.exists():
            shutil.copytree(src_dir, temp_dir / dir_name, dirs_exist_ok=True)
        else:
            print(f"Warning: {dir_name} directory not found")

    # 复制 SRACore 配置
    sracore_src = root_path / "SRACore"
    if sracore_src.exists():
        sracore_dst = temp_dir / "SRACore"
        sracore_dst.mkdir(exist_ok=True)

        # 复制 i18n 目录
        i18n_src = sracore_src / "i18n"
        if i18n_src.exists():
            shutil.copytree(i18n_src, sracore_dst / "i18n", dirs_exist_ok=True)

        # 复制配置文件
        config_file = sracore_src / "config.toml"
        if config_file.exists():
            shutil.copy(config_file, sracore_dst / "config.toml")

    # 复制其他必要文件
    other_files = ["LICENSE", "README.md", "version.json"]
    for file_name in other_files:
        src_file = root_path / file_name
        if src_file.exists():
            shutil.copy(src_file, temp_dir / file_name)

    print("Creating zip packages...")

    # 创建完整版 zip
    full_zip_name = f"StarRailAssistant_v{version['version']}"
    shutil.make_archive(
        base_name=str(root_path / full_zip_name),
        format="zip",
        root_dir=temp_dir,
        base_dir=".",
    )
    print(f"Created: {full_zip_name}.zip")

    # 创建精简版 zip (只有 .NET 部分)
    if dotnet_publish_path.exists():
        lite_zip_name = f"StarRailAssistant_Lite_v{version['version']}"
        shutil.make_archive(
            base_name=str(root_path / lite_zip_name),
            format="zip",
            root_dir=dotnet_publish_path,
            base_dir=".",
        )
        print(f"Created: {lite_zip_name}.zip")

    # 创建核心版 zip (模拟，因为没有 nuitka 编译)
    core_zip_name = f"StarRailAssistant_Core_v{version['version']}"
    core_temp = root_path / "core_temp"
    if core_temp.exists():
        shutil.rmtree(core_temp)
    core_temp.mkdir()

    # 复制 Python 文件作为核心版的占位符
    python_files = ["main.py", "SRACore"]
    for item in python_files:
        src_path = root_path / item
        if src_path.exists():
            if src_path.is_file():
                shutil.copy(src_path, core_temp / item)
            else:
                shutil.copytree(src_path, core_temp / item, dirs_exist_ok=True)

    shutil.make_archive(
        base_name=str(root_path / core_zip_name),
        format="zip",
        root_dir=core_temp,
        base_dir=".",
    )
    print(f"Created: {core_zip_name}.zip")

    # 清理临时目录
    shutil.rmtree(temp_dir)
    shutil.rmtree(core_temp)

    print("Creating version info...")
    # 创建版本信息文件
    (root_path / "version_info.txt").write_text(
        f"v{version['version']}\n\n{version['Announcement'][0]['content']}",
        encoding="utf-8"
    )

    print("Simplified packaging completed!")
    print(f"Version: v{version['version']}")