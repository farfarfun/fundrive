# GitHub 驱动

GitHub是全球最大的代码托管平台，本驱动将GitHub仓库作为云存储来操作，支持文件的上传、下载、管理等功能。特别适合存储代码、文档、配置文件等，并享受版本控制的优势。

## 功能特性

### ✅ 核心功能
- **仓库文件管理** - 完整的文件CRUD操作
- **文件上传下载** - 支持单文件和批量操作
- **目录操作** - 创建、删除、列表查看
- **版本控制** - 每次操作都有Git提交记录
- **分支管理** - 支持指定分支进行操作

### ✅ 高级功能
- **文件搜索** - 基于GitHub搜索API的强大搜索
- **分享链接** - 生成GitHub文件的公开链接
- **仓库统计** - 获取仓库大小、星标、语言等信息
- **原始链接** - 获取文件的raw.githubusercontent.com链接
- **提交信息** - 自定义Git提交信息

### 🔧 技术特点
- 基于GitHub REST API v3
- 支持Personal Access Token认证
- 自动处理文件编码（Base64）
- 完整的错误处理和中文日志
- 支持大文件上传（受GitHub限制）

## 安装依赖

```bash
pip install requests orjson funsecret funutil
```

## 配置方法

### 前置条件

1. **创建GitHub Personal Access Token**
   - 访问 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - 点击 "Generate new token (classic)"
   - 选择必要的权限：`repo` (完整仓库访问权限)
   - 复制生成的token

2. **准备GitHub仓库**
   - 确保有一个可以读写的GitHub仓库
   - 记录仓库所有者和仓库名称

### 方法1: 使用funsecret（推荐）

```bash
# 设置GitHub认证信息
funsecret set fundrive.github.access_token "your_personal_access_token"
funsecret set fundrive.github.repo_owner "your_username"
funsecret set fundrive.github.repo_name "your_repository_name"
```

### 方法2: 环境变量

```bash
export GITHUB_ACCESS_TOKEN="your_personal_access_token"
export GITHUB_REPO_OWNER="your_username"
export GITHUB_REPO_NAME="your_repository_name"
```

### 方法3: 代码中设置

```python
from fundrive.drives.github import GitHubDrive

drive = GitHubDrive(
    access_token="your_personal_access_token",
    repo_owner="your_username",
    repo_name="your_repository_name",
    branch="main"  # 可选，默认为main
)
```

## 使用示例

### 基本操作

```python
from fundrive.drives.github import GitHubDrive

# 创建驱动实例
drive = GitHubDrive()

# 登录连接
if drive.login():
    print("✅ GitHub连接成功")
    
    # 获取仓库信息
    repo_info = drive.get_quota()
    print(f"仓库: {repo_info['repo_name']}")
    print(f"大小: {repo_info['size_mb']} MB")
    print(f"星标: {repo_info['stars']}")
    
    # 列出根目录文件
    files = drive.get_file_list("")
    for file in files:
        print(f"📄 {file.name} ({file.size} bytes)")
    
    # 列出根目录子目录
    dirs = drive.get_dir_list("")
    for dir in dirs:
        print(f"📁 {dir.name}")
else:
    print("❌ GitHub连接失败")
```

### 文件上传

```python
# 上传本地文件
success = drive.upload_file(
    filepath="/path/to/local/file.txt",
    fid="docs",  # 目标目录
    filename="uploaded_file.txt",  # 可选：重命名
    commit_message="Upload file via FunDrive"  # 自定义提交信息
)

if success:
    print("✅ 文件上传成功")

# 上传文本内容
success = drive.upload_file(
    filepath=None,
    fid="config",
    filename="settings.json",
    content='{"key": "value"}',
    commit_message="Add configuration file"
)
```

### 文件下载

```python
# 下载单个文件
success = drive.download_file(
    fid="docs/README.md",  # GitHub文件路径
    filedir="./downloads",  # 本地保存目录
    filename="downloaded_readme.md"  # 可选：重命名
)

# 下载整个目录
success = drive.download_dir(
    fid="docs",  # GitHub目录路径
    filedir="./downloads",  # 本地保存目录
    overwrite=True  # 覆盖已存在文件
)
```

### 目录操作

```python
# 创建目录（通过创建.gitkeep文件）
drive.mkdir("", "new_folder")

# 检查文件是否存在
exists = drive.exist("docs/README.md")
print(f"文件存在: {exists}")

# 获取文件信息
file_info = drive.get_file_info("docs/README.md")
if file_info:
    print(f"文件大小: {file_info.size}")
    print(f"SHA: {file_info.ext['sha'][:8]}...")

# 删除文件
drive.delete("old_file.txt")
```

### 高级功能

```python
# 搜索文件
results = drive.search("README")
for file in results:
    print(f"找到: {file.name} 在 {file.fid}")

# 创建分享链接
share_url = drive.create_share_link("docs/README.md")
print(f"分享链接: {share_url}")

# 获取原始内容链接
raw_url = drive.get_raw_url("docs/README.md")
print(f"原始链接: {raw_url}")

# 获取仓库统计信息
stats = drive.get_quota()
print(f"仓库语言: {stats['language']}")
print(f"创建时间: {stats['created_at']}")
print(f"最后更新: {stats['updated_at']}")
```

## 运行示例

```bash
# 进入驱动目录
cd src/fundrive/drives/github

# 运行快速演示
python example.py --demo

# 运行完整测试
python example.py --test

# 运行交互式演示
python example.py --interactive

# 查看帮助
python example.py --help
```

## API参考

### GitHubDrive类

#### 初始化参数
- `access_token`: GitHub个人访问令牌
- `repo_owner`: 仓库所有者用户名
- `repo_name`: 仓库名称
- `branch`: 操作的分支名称（默认: main）

#### 核心方法

##### login(access_token, repo_owner, repo_name, branch) -> bool
连接到GitHub仓库

##### exist(fid, filename=None) -> bool
检查文件是否存在

##### mkdir(fid, dirname) -> bool
创建目录（通过.gitkeep文件）

##### delete(fid) -> bool
删除文件

##### get_file_list(fid="") -> List[DriveFile]
获取指定目录的文件列表

##### get_dir_list(fid="") -> List[DriveFile]
获取指定目录的子目录列表

##### get_file_info(fid) -> Optional[DriveFile]
获取文件详细信息

##### get_dir_info(fid) -> Optional[DriveFile]
获取目录信息

##### upload_file(filepath, fid, filename=None, content=None, commit_message=None) -> bool
上传文件到GitHub

##### download_file(fid, filedir=".", filename=None, callback=None) -> bool
从GitHub下载文件

##### download_dir(fid, filedir="./cache", overwrite=False) -> bool
下载整个目录

#### 高级方法

##### search(keyword, fid="") -> List[DriveFile]
搜索包含关键词的文件

##### get_quota() -> Dict[str, Any]
获取仓库统计信息

##### create_share_link(fid) -> str
创建文件的GitHub分享链接

##### get_raw_url(fid) -> str
获取文件的原始内容链接

## GitHub限制说明

### 文件大小限制
- **单文件大小**: 最大100MB
- **仓库大小**: 建议不超过1GB，硬限制100GB
- **推送大小**: 单次推送最大2GB

### API限制
- **认证用户**: 5000次请求/小时
- **搜索API**: 30次请求/分钟
- **文件内容**: 单个文件最大1MB（API限制）

### 最佳实践
- 适合存储代码、文档、配置文件
- 不适合存储大型二进制文件
- 建议使用Git LFS处理大文件
- 注意API速率限制

## 版本控制特性

### Git集成
- 每次文件操作都会创建Git提交
- 支持自定义提交信息
- 保留完整的版本历史
- 支持分支操作

### 提交信息格式
```python
# 默认提交信息
"Upload file: filename.txt"
"Delete file: filename.txt"
"Create directory: dirname"

# 自定义提交信息
drive.upload_file(
    filepath="file.txt",
    fid="docs",
    commit_message="feat: add new documentation"
)
```

## 安全注意事项

1. **Token保护**: 不要在代码中硬编码访问令牌，使用funsecret或环境变量
2. **权限最小化**: 只授予必要的仓库权限
3. **公开仓库**: 注意文件会公开可见
4. **私有仓库**: 确保访问令牌有足够权限
5. **敏感信息**: 不要上传包含密码、密钥等敏感信息的文件

## 常见问题

### Q: 如何处理大文件？
A: GitHub对单文件有100MB限制，对于大文件建议：
- 使用Git LFS
- 分割文件
- 使用其他云存储服务

### Q: 如何处理二进制文件？
A: 驱动自动处理二进制文件的Base64编码，但注意GitHub API对文件大小的限制。

### Q: 如何切换分支？
A: 在初始化时指定分支：
```python
drive = GitHubDrive(branch="develop")
```

### Q: 如何处理API限制？
A: 
- 使用认证token提高限制
- 实现重试机制
- 缓存结果减少请求

### Q: 支持GitHub Enterprise吗？
A: 需要修改base_url指向企业版API地址。

## 故障排除

### 连接问题
```python
# 检查token和仓库信息
import requests
headers = {"Authorization": f"token {your_token}"}
response = requests.get("https://api.github.com/user", headers=headers)
print(response.json())
```

### 权限问题
- 确保token有repo权限
- 检查仓库是否存在
- 验证用户对仓库的访问权限

### 文件上传失败
- 检查文件大小是否超限
- 验证文件路径格式
- 确认分支是否存在

## 贡献指南

欢迎提交问题报告和功能请求！

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/farfarfun/fundrive.git
cd fundrive

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python -m pytest tests/drives/test_github.py
```

### 提交规范
- 遵循PEP 8代码规范
- 添加适当的类型注解
- 编写单元测试
- 更新相关文档

## 更新日志

### v1.0.0 (2024-01-XX)
- ✅ 初始版本发布
- ✅ 实现完整的GitHub API支持
- ✅ 支持文件上传下载
- ✅ 添加搜索和分享功能
- ✅ 完善错误处理和日志
- ✅ 支持版本控制集成

---

**注意**: GitHub有文件大小和API使用限制，请合理使用。建议主要用于代码、文档等文本文件的管理。
