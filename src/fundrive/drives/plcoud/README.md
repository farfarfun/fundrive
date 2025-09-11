# pCloud 网盘驱动

基于 pCloud 官方 HTTP JSON Protocol API 实现的 Python 网盘驱动，提供完整的文件和文件夹操作功能。

## 功能特性

### 🔐 认证系统
- 支持用户名/密码登录
- 支持 Auth Token 认证
- 自动获取和管理认证令牌

### 📁 文件夹操作
- 创建文件夹 (`mkdir`)
- 列出文件夹内容 (`get_file_list`, `get_dir_list`)
- 删除文件夹 (`delete`)
- 重命名文件夹 (`rename`)
- 复制文件夹 (`copy`)
- 移动文件夹 (`move`)

### 📄 文件操作
- 上传文件 (`upload_file`)
- 下载文件 (`download_file`)
- 删除文件 (`delete`)
- 重命名文件 (`rename`)
- 复制文件 (`copy`)
- 移动文件 (`move`)
- 获取下载链接 (`get_download_url`)

### 🔍 高级功能
- 文件搜索 (`search`)
- 文件分享 (`share`)
- 配额查询 (`get_quota`)
- 文件/文件夹信息获取 (`get_file_info`, `get_dir_info`)

## 快速开始

### 安装依赖

```bash
pip install requests funutil
```

### 基本使用

```python
from fundrive.drives.plcoud.drive import PCloudDrive

# 创建驱动实例
drive = PCloudDrive()

# 登录
drive.login("your_email@example.com", "your_password")

# 获取根目录文件列表
files = drive.get_file_list("0")  # "0" 是根目录 ID
for file in files:
    print(f"📄 {file.name} ({file.size} bytes)")

# 上传文件
drive.upload_file("/path/to/local/file.txt", "0")

# 下载文件
drive.download_file("file_id", filepath="/path/to/download/file.txt")
```

## API 参考

### 认证方法

#### `login(username=None, password=None, auth_token=None)`
登录到 pCloud 账户

**参数:**
- `username` (str, 可选): pCloud 邮箱地址
- `password` (str, 可选): pCloud 密码
- `auth_token` (str, 可选): 已有的认证令牌

**返回:**
- `bool`: 登录是否成功

**示例:**
```python
# 使用用户名密码登录
success = drive.login("user@example.com", "password")

# 使用 token 登录
success = drive.login(auth_token="your_auth_token")
```

### 文件夹操作

#### `mkdir(fid, name)`
在指定目录下创建新文件夹

**参数:**
- `fid` (str): 父目录 ID
- `name` (str): 新文件夹名称

**返回:**
- `str`: 新创建文件夹的 ID，失败返回空字符串

#### `get_file_list(fid)`
获取指定目录下的文件列表

**参数:**
- `fid` (str): 目录 ID

**返回:**
- `List[DriveFile]`: 文件列表

#### `get_dir_list(fid)`
获取指定目录下的子目录列表

**参数:**
- `fid` (str): 目录 ID

**返回:**
- `List[DriveFile]`: 目录列表

### 文件操作

#### `upload_file(filepath, fid)`
上传文件到指定目录

**参数:**
- `filepath` (str): 本地文件路径
- `fid` (str): 目标目录 ID

**返回:**
- `bool`: 上传是否成功

#### `download_file(fid, filedir=None, filename=None, filepath=None, overwrite=False)`
下载文件

**参数:**
- `fid` (str): 文件 ID
- `filedir` (str, 可选): 下载目录
- `filename` (str, 可选): 保存文件名
- `filepath` (str, 可选): 完整保存路径
- `overwrite` (bool): 是否覆盖已存在文件

**返回:**
- `bool`: 下载是否成功

### 通用操作

#### `delete(fid)`
删除文件或文件夹

**参数:**
- `fid` (str): 文件或文件夹 ID

**返回:**
- `bool`: 删除是否成功

#### `rename(fid, new_name)`
重命名文件或文件夹

**参数:**
- `fid` (str): 文件或文件夹 ID
- `new_name` (str): 新名称

**返回:**
- `bool`: 重命名是否成功

#### `move(source_fid, target_fid)`
移动文件或文件夹

**参数:**
- `source_fid` (str): 源文件/文件夹 ID
- `target_fid` (str): 目标目录 ID

**返回:**
- `bool`: 移动是否成功

#### `copy(source_fid, target_fid)`
复制文件或文件夹

**参数:**
- `source_fid` (str): 源文件/文件夹 ID
- `target_fid` (str): 目标目录 ID

**返回:**
- `bool`: 复制是否成功

### 高级功能

#### `search(keyword, fid=None, file_type=None)`
搜索文件或文件夹

**参数:**
- `keyword` (str): 搜索关键词
- `fid` (str, 可选): 搜索范围目录 ID
- `file_type` (str, 可选): 文件类型过滤

**返回:**
- `List[DriveFile]`: 搜索结果列表

#### `share(*fids, password="", expire_days=0, description="")`
分享文件或文件夹

**参数:**
- `*fids` (str): 要分享的文件/文件夹 ID
- `password` (str, 可选): 分享密码
- `expire_days` (int, 可选): 过期天数
- `description` (str, 可选): 分享描述

**返回:**
- `dict`: 包含分享链接等信息的字典

#### `get_quota()`
获取网盘配额信息

**返回:**
- `dict`: 包含总容量、已用容量、剩余容量的字典

## 错误处理

所有方法都包含完善的错误处理机制，使用 `logger.error` 记录详细的错误信息，便于调试和维护。

```python
import logging

# 配置日志级别以查看错误信息
logging.basicConfig(level=logging.ERROR)

# 使用驱动
drive = PCloudDrive()
if not drive.login("wrong_email", "wrong_password"):
    # 错误信息会自动记录到日志中
    print("登录失败，请检查日志获取详细信息")
```

## 完整示例

查看 `example/pcloud_example.py` 文件获取完整的使用示例，包括：

- 基本文件操作
- 批量操作
- 错误处理
- 高级功能演示

## API 文档参考

本驱动基于 pCloud 官方 API 实现，每个方法的注释中都包含对应的官方文档链接：

- [pCloud API 官方文档](https://docs.pcloud.com/)
- [认证相关 API](https://docs.pcloud.com/methods/general/userinfo.html)
- [文件夹操作 API](https://docs.pcloud.com/methods/folder/)
- [文件操作 API](https://docs.pcloud.com/methods/file/)

## 注意事项

1. **认证安全**: 请妥善保管你的 pCloud 账户信息，不要在代码中硬编码密码
2. **API 限制**: pCloud API 可能有调用频率限制，请合理控制请求频率
3. **文件大小**: 大文件上传可能需要较长时间，建议添加进度显示
4. **网络异常**: 所有网络操作都可能因网络问题失败，请做好重试机制

## 许可证

本项目遵循项目根目录的许可证条款。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个驱动！
