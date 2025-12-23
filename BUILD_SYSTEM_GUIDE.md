# 🚀 Fork 构建系统完整指南

## 📋 概述

这个构建系统专为你的 StarRailAssistant 复刻仓库设计，提供了完整的自动化测试构建流程。

## 🎯 主要特性

### ✅ 已解决的问题
- ❌ **原始问题**: 复刻仓库构建失败 (pre_check 限制)
- ❌ **资源问题**: XAML 资源引用错误 (TestNotificationText)
- ❌ **编译问题**: Nuitka 编译复杂性和失败
- ❌ **错误处理**: 缺乏详细的构建诊断

### ✅ 新增功能
- 🔧 **自动修复**: 智能检测和修复常见构建问题
- 📦 **多版本打包**: 完整版、精简版、核心版
- 🚀 **自动发布**: 推送到 master 分支自动创建测试 Release
- 📊 **详细日志**: 完整的构建过程跟踪和错误诊断
- 💾 **缓存优化**: .NET 和 Python 依赖缓存加速构建

## 🛠️ 构建系统组件

### 1. GitHub Actions 工作流

#### `robust-build.yml` - 主构建流程
- **触发条件**: 推送到 `master` 分支或手动触发
- **功能**: 完整的构建、打包、发布流程
- **超时**: 30 分钟保护
- **缓存**: 智能依赖缓存

#### `fork-build.yml` - 基础构建流程
- **功能**: 简化的构建流程
- **用途**: 快速测试和验证

#### `test-dotnet.yml` - .NET 专项测试
- **功能**: 仅测试 .NET 构建部分
- **用途**: 诊断 .NET 相关问题

### 2. Python 脚本

#### `package_enhanced.py` - 增强打包脚本
```bash
python package_enhanced.py
```
- **功能**: 创建三种版本的安装包
- **特性**: 详细日志、错误处理、文件验证
- **输出**:
  - `StarRailAssistant_v*.zip` (完整版)
  - `StarRailAssistant_Lite_v*.zip` (精简版)
  - `StarRailAssistant_Core_v*.zip` (核心版)

#### `fix-build-issues.py` - 构建问题修复
```bash
python fix-build-issues.py
```
- **功能**: 自动检测和修复构建问题
- **检查项**: .NET 环境、资源文件、构建测试
- **修复**: 自动补全缺失的资源定义

#### `merge-to-master.py` - 分支合并助手
```bash
python merge-to-master.py
# 或指定分支
python merge-to-master.py --branch feature-branch
```

### 3. 批处理脚本

#### `merge-to-master.bat` - Windows 快捷方式
- **功能**: Windows 用户友好的合并界面
- **检查**: 自动验证 Python 和 Git 环境

## 🚀 使用流程

### 日常开发流程

1. **在功能分支开发**
   ```bash
   git checkout -b feature/new-feature
   # 开发你的功能...
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **合并到 master 进行测试构建**
   ```bash
   # 方法一: 使用脚本
   python merge-to-master.py --branch feature/new-feature

   # 方法二: 手动合并
   git checkout master
   git merge feature/new-feature --no-ff
   git push origin master
   ```

3. **查看构建结果**
   - 访问 GitHub Actions 页面查看构建进度
   - 构建成功后自动创建测试 Release
   - 下载测试版本进行验证

### 故障排除流程

1. **构建失败时**
   ```bash
   # 运行诊断脚本
   python fix-build-issues.py

   # 手动测试本地构建
   dotnet restore SRAFrontend/SRAFrontend.csproj
   dotnet build SRAFrontend/SRAFrontend.csproj -c Release
   dotnet publish SRAFrontend/SRAFrontend.csproj -c Release -r win-x64 --self-contained false
   ```

2. **资源文件问题**
   - 脚本会自动检测和修复 `Resources.Designer.cs` 中缺失的资源
   - 手动检查 `SRAFrontend/Localization/` 目录

3. **Python 依赖问题**
   ```bash
   pip install -r requirements.txt
   python package_enhanced.py
   ```

## 📦 构建产物说明

### 自动生成的文件

| 文件名 | 大小 | 说明 |
|--------|------|------|
| `StarRailAssistant_v*.zip` | ~33MB | 完整版 - 包含所有组件 |
| `StarRailAssistant_Lite_v*.zip` | ~15MB | 精简版 - 仅前端应用 |
| `StarRailAssistant_Core_v*.zip` | ~0.03MB | 核心版 - Python 组件 |
| `version_info.txt` | <1KB | 版本信息文件 |

### Release 命名规则

测试 Release 使用时间戳命名:
```
test-build-20241223-143022
```

包含完整的构建信息和下载说明。

## 🔧 高级配置

### 自定义构建触发

修改 `.github/workflows/robust-build.yml`:
```yaml
on:
  push:
    branches: [ master, develop ]  # 添加其他分支
  pull_request:
    branches: [ master ]
```

### 修改包名格式

编辑 `package_enhanced.py` 中的命名逻辑:
```python
full_zip_name = f"MyCustomName_v{version_str}"
```

### 禁用自动 Release

注释掉工作流中的 `Create release` 步骤。

## 📊 监控和维护

### 构建状态检查
- GitHub Actions 页面显示所有构建历史
- 每个构建都有详细的日志和时间统计
- 失败的构建会显示具体错误信息

### 定期维护
- 清理旧的测试 Release (建议保留最近 10 个)
- 更新依赖版本 (requirements.txt, .csproj)
- 检查 GitHub Actions 配额使用情况

## 🎉 成功指标

构建系统成功运行的标志:
- ✅ 推送到 master 分支后 5-10 分钟内完成构建
- ✅ 自动创建包含所有文件的测试 Release
- ✅ 生成的安装包可以正常运行
- ✅ 构建日志清晰显示每个步骤的状态

## 🆘 获取帮助

如果遇到问题:
1. 查看 GitHub Actions 的详细日志
2. 运行 `python fix-build-issues.py` 进行自动诊断
3. 检查本文档的故障排除部分
4. 在仓库中创建 Issue 描述具体问题

---

**🎊 恭喜！你现在拥有一个完全自动化的测试构建系统！**