# Dropbox 网盘驱动

基于 fundrive 框架的 Dropbox 网盘驱动实现，提供统一的网盘操作接口。

## 产品介绍

Dropbox 是全球领先的云存储服务提供商，为个人和企业用户提供安全可靠的文件存储、同步和分享服务。本驱动基于 Dropbox API v2 实现，支持文件的上传、下载、管理和分享等核心功能。

### 主要特性

- ✅ **完整的文件操作**: 支持文件和目录的增删改查
- ✅ **高效传输**: 支持大文件分块上传，带进度显示
- ✅ **智能搜索**: 基于 Dropbox 搜索 API，支持文件类型筛选
- ✅ **便捷分享**: 创建公开分享链接，支持过期时间设置
- ✅ **空间管理**: 实时查询存储空间使用情况
- ✅ **统一接口**: 遵循 fundrive BaseDrive 规范
- ✅ **配置管理**: 集成 funsecret，支持多种配置方式
- ✅ **错误处理**: 完善的异常处理和中文日志记录

### 功能对比

| 功能 | 支持状态 | 说明 |
|------|---------|------|
| 登录认证 | ✅ 支持 | 基于 Access Token |
| 文件上传 | ✅ 支持 | 支持大文件分块上传 |
| 文件下载 | ✅ 支持 | 支持进度显示 |
| 目录操作 | ✅ 支持 | 创建、删除、列表 |
| 文件搜索 | ✅ 支持 | 支持关键词和类型筛选 |
| 文件移动 | ✅ 支持 | 移动文件和目录 |
| 文件复制 | ✅ 支持 | 复制文件和目录 |
| 文件重命名 | ✅ 支持 | 重命名文件和目录 |
| 分享链接 | ✅ 支持 | 创建公开分享链接 |
| 空间查询 | ✅ 支持 | 查询存储配额信息 |
| 回收站 | ❌ 不支持 | Dropbox 无回收站概念 |
| 密码分享 | ❌ 不支持 | Dropbox 不支持密码保护 |
| 保存分享 | ❌ 不支持 | 需手动下载后上传 |

## 安装配置

### 依赖要求

```bash
pip install dropbox funsecret funutil tqdm
```

### API 配置

#### 1. 获取 Dropbox API 访问令牌

1. 访问 [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. 点击 "Create app" 创建新应用
3. 选择 "Scoped access" 和 "Full Dropbox"
4. 填写应用名称并创建
5. 在应用设置页面生成 Access Token

#### 2. 配置访问令牌

**方式一：使用 funsecret（推荐）**

```python
from funsecret import write_secret

# 配置 Dropbox 访问令牌
write_secret("dropbox", "access_token", "your_access_token_here")
```

**方式二：环境变量**

```bash
export DROPBOX_ACCESS_TOKEN="your_access_token_here"
```

**方式三：直接传参**

```python
drive = DropboxDrive()
drive.login(access_token="your_access_token_here")
```

## 使用示例

### 基础使用

```python
from fundrive.drives.dropbox import DropboxDrive

# 创建驱动实例
drive = DropboxDrive()

# 登录（自动读取配置）
if drive.login():
    print("登录成功")
    
    # 获取根目录文件列表
    files = drive.get_file_list("/")
    print(f"根目录有 {len(files)} 个文件")
    
    # 获取空间使用情况
    quota = drive.get_quota()
    print(f"已用空间: {quota['used_space'] / (1024**3):.2f} GB")
```

### 文件操作

```python
# 上传文件
success = drive.upload_file("local_file.txt", "/remote_folder")
if success:
    print("文件上传成功")

# 下载文件
success = drive.download_file("/remote_file.txt", filepath="local_file.txt")
if success:
    print("文件下载成功")

# 创建目录
drive.mkdir("/new_folder")

# 删除文件或目录
drive.delete("/old_file.txt")
```

### 高级功能

```python
# 搜索文件
results = drive.search("关键词", file_type="image")
print(f"找到 {len(results)} 个图片文件")

# 移动文件
drive.move("/source/file.txt", "/target/folder")

# 复制文件
drive.copy("/source/file.txt", "/target/folder")

# 重命名文件
drive.rename("/old_name.txt", "new_name.txt")

# 创建分享链接
share_result = drive.share("/file.txt", expire_days=7)
if share_result:
    print(f"分享链接: {share_result['links'][0]['url']}")
```

### 批量操作

```python
# 批量上传
files_to_upload = ["file1.txt", "file2.txt", "file3.txt"]
for file_path in files_to_upload:
    drive.upload_file(file_path, "/upload_folder")

# 批量分享
files_to_share = ["/file1.txt", "/file2.txt"]
share_result = drive.share(*files_to_share, expire_days=30)
```

## 运行示例

项目提供了完整的示例程序，支持多种运行模式：

```bash
# 基础功能测试
python example.py --test

# 完整功能演示
python example.py --demo

# 简单使用示例
python example.py --simple
```

### 示例程序功能

- **基础测试**: 登录、配额查询、文件列表、目录操作
- **完整演示**: 文件上传下载、搜索、移动复制、分享链接
- **简单示例**: 最基本的使用方法展示

## API 文档

### 核心方法

#### `login(access_token: str = None) -> bool`
登录到 Dropbox 服务

**参数:**
- `access_token`: 访问令牌，可选，默认从配置读取

**返回:** 登录是否成功

#### `upload_file(filepath: str, fid: str, overwrite: bool = False) -> bool`
上传文件到指定目录

**参数:**
- `filepath`: 本地文件路径
- `fid`: 目标目录路径
- `overwrite`: 是否覆盖已存在文件

**返回:** 上传是否成功

#### `download_file(fid: str, filepath: str = None, overwrite: bool = False) -> bool`
下载文件到本地

**参数:**
- `fid`: 远程文件路径
- `filepath`: 本地保存路径
- `overwrite`: 是否覆盖已存在文件

**返回:** 下载是否成功

#### `search(keyword: str, fid: str = None, file_type: str = None) -> List[DriveFile]`
搜索文件和目录

**参数:**
- `keyword`: 搜索关键词
- `fid`: 搜索范围目录，默认全盘搜索
- `file_type`: 文件类型筛选（image、video、audio、doc、archive）

**返回:** 匹配的文件列表

#### `share(*fids: str, expire_days: int = 0) -> dict`
创建分享链接

**参数:**
- `fids`: 要分享的文件或目录路径列表
- `expire_days`: 链接有效期（天），0表示永不过期

**返回:** 分享链接信息

### 完整 API 列表

| 方法 | 功能 | 支持状态 |
|------|------|---------|
| `login()` | 登录认证 | ✅ |
| `exist()` | 检查文件是否存在 | ✅ |
| `mkdir()` | 创建目录 | ✅ |
| `delete()` | 删除文件或目录 | ✅ |
| `get_file_list()` | 获取文件列表 | ✅ |
| `get_dir_list()` | 获取目录列表 | ✅ |
| `get_file_info()` | 获取文件信息 | ✅ |
| `get_dir_info()` | 获取目录信息 | ✅ |
| `upload_file()` | 上传文件 | ✅ |
| `download_file()` | 下载文件 | ✅ |
| `search()` | 搜索文件 | ✅ |
| `move()` | 移动文件 | ✅ |
| `copy()` | 复制文件 | ✅ |
| `rename()` | 重命名文件 | ✅ |
| `share()` | 创建分享链接 | ✅ |
| `get_quota()` | 获取空间配额 | ✅ |
| `get_recycle_list()` | 获取回收站列表 | ❌ 警告实现 |
| `restore()` | 恢复文件 | ❌ 警告实现 |
| `clear_recycle()` | 清空回收站 | ❌ 警告实现 |
| `save_shared()` | 保存分享内容 | ❌ 警告实现 |

## 注意事项

### 使用限制

1. **API 限制**: Dropbox API 有请求频率限制，建议合理控制请求频率
2. **文件大小**: 单个文件最大支持 350GB
3. **路径格式**: 使用 Unix 风格路径，以 `/` 开头
4. **文件名**: 不支持某些特殊字符，如 `<>:"|?*`

### 功能说明

1. **回收站**: Dropbox 没有传统意义的回收站，删除的文件会进入版本历史
2. **版本恢复**: 可通过 Dropbox 网页版恢复最近 30 天内的文件版本
3. **分享密码**: Dropbox 不支持密码保护的分享链接
4. **保存分享**: 无法直接保存他人分享的内容，需手动下载后上传

### 性能优化

1. **批量操作**: 对于大量文件操作，建议分批处理
2. **大文件上传**: 自动使用分块上传，提高成功率
3. **网络重试**: 内置网络异常重试机制
4. **进度显示**: 上传下载过程显示实时进度

## 故障排除

### 常见问题

**Q: 登录失败，提示 "Invalid access token"**
A: 检查访问令牌是否正确，确保令牌未过期且有足够权限

**Q: 上传大文件失败**
A: 检查网络连接，大文件会自动分块上传，请耐心等待

**Q: 搜索结果为空**
A: 确认搜索关键词正确，Dropbox 搜索可能需要一些时间索引新文件

**Q: 分享链接创建失败**
A: 检查文件是否存在，确保有分享权限

### 错误代码

| 错误类型 | 说明 | 解决方案 |
|---------|------|---------|
| `AuthError` | 认证失败 | 检查访问令牌 |
| `ApiError` | API 调用失败 | 检查网络和参数 |
| `FileNotFoundError` | 文件不存在 | 确认文件路径正确 |
| `InsufficientSpaceError` | 存储空间不足 | 清理空间或升级账户 |

### 调试模式

启用详细日志输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

drive = DropboxDrive()
# 现在会输出详细的调试信息
```

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个驱动！

### 开发环境

1. 克隆项目仓库
2. 安装开发依赖：`pip install -e .[dev]`
3. 运行测试：`python -m pytest tests/`
4. 检查代码风格：`black . && flake8 .`

### 提交规范

- 遵循项目的代码风格
- 添加适当的测试用例
- 更新相关文档
- 提交信息使用中文

---

## 相关链接

- 📦 [fundrive 项目主页](https://github.com/farfarfun/fundrive)
- 📚 [Dropbox API 文档](https://www.dropbox.com/developers/documentation)
- 🔧 [funsecret 配置管理](https://github.com/farfarfun/funsecret)
- 🛠️ [开发规范文档](../../DEVELOPMENT_GUIDE.md)

**版本**: 1.0.0  
**作者**: fundrive 开发团队  
**许可**: MIT License
