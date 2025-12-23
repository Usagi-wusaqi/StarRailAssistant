#!/usr/bin/env python3
"""
构建问题修复脚本
自动检测和修复常见的构建问题
"""

import subprocess
import sys
from pathlib import Path
import re

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def log(message, level="INFO"):
    """日志输出"""
    print(f"[{level}] {message}")

def fix_resources_designer():
    """修复 Resources.Designer.cs 文件"""
    log("🔧 Checking Resources.Designer.cs...")

    designer_file = Path("SRAFrontend/Localization/Resources.Designer.cs")
    resx_file = Path("SRAFrontend/Localization/Resources.resx")

    if not designer_file.exists():
        log("❌ Resources.Designer.cs not found", "ERROR")
        return False

    if not resx_file.exists():
        log("❌ Resources.resx not found", "ERROR")
        return False

    # 读取 resx 文件中的所有资源
    with resx_file.open('r', encoding='utf-8') as f:
        resx_content = f.read()

    # 提取所有资源名称
    resource_names = re.findall(r'<data name="([^"]+)"', resx_content)
    log(f"📋 Found {len(resource_names)} resources in .resx file")

    # 读取 designer 文件
    with designer_file.open('r', encoding='utf-8') as f:
        designer_content = f.read()

    # 检查缺失的资源
    missing_resources = []
    for name in resource_names:
        if f"public static string {name}" not in designer_content:
            missing_resources.append(name)

    if missing_resources:
        log(f"⚠️  Found {len(missing_resources)} missing resources: {missing_resources}", "WARN")

        # 为缺失的资源生成代码
        insert_point = designer_content.rfind("    }")
        if insert_point == -1:
            log("❌ Cannot find insertion point in designer file", "ERROR")
            return False

        new_properties = []
        for name in missing_resources:
            # 从 resx 中提取值作为注释
            value_match = re.search(f'<data name="{name}"[^>]*>\\s*<value>([^<]*)</value>', resx_content)
            value = value_match.group(1) if value_match else name

            property_code = f'''
        /// <summary>
        ///   Looks up a localized string similar to {value}.
        /// </summary>
        public static string {name} {{
            get {{
                return ResourceManager.GetString("{name}", resourceCulture);
            }}
        }}'''
            new_properties.append(property_code)

        # 插入新属性
        new_content = (designer_content[:insert_point] +
                      "\n".join(new_properties) + "\n" +
                      designer_content[insert_point:])

        # 写回文件
        with designer_file.open('w', encoding='utf-8') as f:
            f.write(new_content)

        log(f"✅ Added {len(missing_resources)} missing resource properties")
        return True
    else:
        log("✅ All resources are present in designer file")
        return True

def check_dotnet_version():
    """检查 .NET 版本"""
    log("🔍 Checking .NET version...")
    success, stdout, stderr = run_command("dotnet --version")
    if success:
        version = stdout.strip()
        log(f"✅ .NET version: {version}")
        return True
    else:
        log(f"❌ .NET not found: {stderr}", "ERROR")
        return False

def clean_build():
    """清理构建"""
    log("🧹 Cleaning build artifacts...")

    # 清理 .NET
    success, _, _ = run_command("dotnet clean SRAFrontend/SRAFrontend.csproj")
    if success:
        log("✅ .NET clean successful")
    else:
        log("⚠️  .NET clean failed", "WARN")

    # 清理 Python 缓存
    import shutil
    for pycache in Path(".").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            log(f"🗑️  Removed: {pycache}")
        except:
            pass

    # 清理旧的 zip 文件
    for zip_file in Path(".").glob("StarRailAssistant_*.zip"):
        try:
            zip_file.unlink()
            log(f"🗑️  Removed: {zip_file}")
        except:
            pass

def test_build():
    """测试构建"""
    log("🧪 Testing build process...")

    # 测试 .NET restore
    log("📦 Testing .NET restore...")
    success, stdout, stderr = run_command("dotnet restore SRAFrontend/SRAFrontend.csproj")
    if not success:
        log(f"❌ .NET restore failed: {stderr}", "ERROR")
        return False
    log("✅ .NET restore successful")

    # 测试 .NET build
    log("🔨 Testing .NET build...")
    success, stdout, stderr = run_command("dotnet build SRAFrontend/SRAFrontend.csproj -c Release")
    if not success:
        log(f"❌ .NET build failed: {stderr}", "ERROR")
        return False
    log("✅ .NET build successful")

    # 测试 .NET publish
    log("📤 Testing .NET publish...")
    success, stdout, stderr = run_command("dotnet publish SRAFrontend/SRAFrontend.csproj -c Release -r win-x64 --self-contained false")
    if not success:
        log(f"❌ .NET publish failed: {stderr}", "ERROR")
        return False
    log("✅ .NET publish successful")

    return True

def main():
    """主函数"""
    log("🚀 Starting build issue diagnosis and fix...")

    # 检查基本环境
    if not check_dotnet_version():
        log("💥 .NET environment check failed", "ERROR")
        return False

    # 清理构建
    clean_build()

    # 修复资源文件问题
    if not fix_resources_designer():
        log("💥 Resource fix failed", "ERROR")
        return False

    # 测试构建
    if not test_build():
        log("💥 Build test failed", "ERROR")
        return False

    log("🎉 All checks passed! Build should work now.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)