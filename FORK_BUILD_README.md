# Fork 测试构建说明

这个文档说明如何在你的复刻仓库中使用 `master` 分支进行测试构建。

## 🎯 目标

- 使用 `master` 分支专门用于合并其他分支的更改
- 通过 GitHub Actions 自动构建测试版本
- 生成可下载的测试 Release

## 🚀 快速开始

### 1. 设置分支

确保你有一个 `master` 分支用于测试构建：

```bash
# 如果还没有 master 分支，创建一个
git checkout -b master

# 推送到远程
git push origin master
```

### 2. 合并分支进行测试

#### 方法一：使用辅助脚本（推荐）

```bash
# 使用 Python 脚本自动合并
python merge-to-master.py

# 或者指定特定分支
python merge-to-master.py --branch your-feature-branch

# 查看所有可用分支
python merge-to-master.py --list
```

#### 方法二：手动合并

```bash
# 1. 切换到 master 分支
git checkout master

# 2. 拉取最新更改
git pull origin master

# 3. 合并你的功能分支
git merge your-feature-branch --no-ff

# 4. 推送到远程触发构建
git push origin master
```

### 3. 查看构建结果

1. 推送到 `master` 分支后，GitHub Actions 会自动开始构建
2. 访问你的仓库的 Actions 页面查看构建进度
3. 构建成功后会自动创建一个测试 Release
4. 在 Releases 页面下载测试版本

## 📋 工作流说明

### 触发条件

GitHub Actions 构建会在以下情况触发：

- 推送代码到 `master` 分支
- 创建针对 `master` 分支的 Pull Request
- 手动触发（在 Actions 页面点击 "Run workflow"）

### 构建产物

每次成功构建会生成以下文件：

- `StarRailAssistant_*.zip` - 完整版免安装包
- `StarRailAssistant_Lite_*.zip` - 精简版免安装包
- `StarRailAssistant_Core_*.zip` - 核心版免安装包
- `StarRailAssistant_*_Setup.exe` - 安装程序

### Release 命名

测试 Release 使用以下命名格式：
```
test-{版本号}-{时间戳}
```

例如：`test-v2.0.1-20241223-143022`

## 🔧 自定义配置

### 修改触发分支

如果你想使用不同的分支名，编辑 `.github/workflows/fork-build.yml`：

```yaml
on:
  push:
    branches: [ your-test-branch ]  # 改为你的分支名
  pull_request:
    branches: [ your-test-branch ]
```

### 禁用自动 Release

如果你只想构建而不创建 Release，可以注释掉工作流中的 `create_test_release` job。

## 📝 使用建议

1. **保持 master 分支纯净**：只用于测试构建，不要在上面直接开发
2. **定期清理**：定期删除旧的测试 Release 以节省空间
3. **测试流程**：
   - 在功能分支开发
   - 合并到 master 进行测试构建
   - 测试通过后再合并到主分支

## 🛠️ 故障排除

### 构建失败

1. 检查 Actions 页面的错误日志
2. 确保所有依赖文件都已提交
3. 检查 Python 和 .NET 代码是否有语法错误

### 合并冲突

1. 手动解决冲突：
   ```bash
   git checkout master
   git merge your-branch
   # 解决冲突后
   git add .
   git commit
   git push origin master
   ```

### 权限问题

确保你的 GitHub 仓库设置中：
- Actions 权限已启用
- 允许创建 Release

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看 GitHub Actions 的详细日志
2. 检查这个 README 的故障排除部分
3. 在仓库中创建 Issue 描述问题