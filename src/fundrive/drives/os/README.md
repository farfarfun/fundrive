# 本地文件系统驱动

本地文件系统驱动提供了对本地磁盘文件系统的统一访问接口，使您可以像操作云存储一样操作本地文件系统。这对于开发、测试和本地文件管理非常有用。

## 🚀 特性

- ✅ **统一接口**: 与其他云存储驱动相同的API接口
- ✅ **高性能**: 直接操作本地文件系统，无网络延迟
- ✅ **完全兼容**: 支持所有BaseDrive接口方法
- ✅ **安全可靠**: 本地存储，数据完全可控
- ✅ **易于使用**: 无需任何认证配置

## 📦 安装依赖

本地文件系统驱动无需额外依赖，随FunDrive核心包一起安装：

```bash
pip install fundrive
```

## 🔧 配置方法

### 方法一：使用 nltsecret（推荐）

```bash
# 配置根目录路径
nltsecret set fundrive os root_path "/path/to/your/storage"
```

### 方法二：环境变量

```bash
export OS_ROOT_PATH="/path/to/your/storage"
```

### 方法三：直接指定

```python
from fundrive.drives.os import OsDrive

# 直接指定根目录
drive = OsDrive(root_path="/path/to/your/storage")
```

## 💻 使用示例

### 基础使用

```python
from fundrive.drives.os import OsDrive

# 创建驱动实例
drive = OsDrive(root_path="/home/user/my_storage")

# 初始化（本地文件系统无需真正的登录）
drive.login()

# 上传文件（实际是复制文件）
drive.upload_file("/source/file.txt", "/", filename="uploaded_file.txt")

# 下载文件（实际是复制文件）
files = drive.get_file_list("/")
if files:
    file_id = files[0].fid
    drive.download_file(file_id, filedir="/download/path", filename="downloaded_file.txt")

# 创建文件夹
drive.mkdir("/", "new_folder")

# 获取文件列表
files = drive.get_file_list("/")
for file in files:
    print(f"文件: {file.name}, 大小: {file.size} 字节")

# 获取文件夹列表
dirs = drive.get_dir_list("/")
for dir in dirs:
    print(f"文件夹: {dir.name}")
```

### 高级功能

```python
# 检查文件是否存在
exists = drive.exist("/", "file.txt")
print(f"文件存在: {exists}")

# 获取文件信息
file_info = drive.get_file_info(file_id)
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"文件大小: {file_info.size}")
    print(f"修改时间: {file_info.ext.get('mtime', 'N/A')}")

# 删除文件或文件夹
result = drive.delete(file_id)
print(f"删除结果: {result}")

# 递归操作
def process_directory(drive, path="/"):
    """递归处理目录中的所有文件"""
    files = drive.get_file_list(path)
    dirs = drive.get_dir_list(path)
    
    # 处理文件
    for file in files:
        print(f"处理文件: {file.name}")
        # 执行文件操作...
    
    # 递归处理子目录
    for dir in dirs:
        sub_path = f"{path.rstrip('/')}/{dir.name}"
        process_directory(drive, sub_path)

# 使用示例
process_directory(drive)
```

### 批量操作

```python
import os
from pathlib import Path


# 批量上传目录
def upload_directory(drive, local_dir, remote_dir="/"):
    """批量上传本地目录到存储"""
    local_path = Path(local_dir)

    for item in local_path.rglob("*"):
        if item.is_file():
            # 计算相对路径
            rel_path = item.relative_to(local_path)
            remote_path = str(rel_path.parent) if rel_path.parent != Path(".") else "/"

            # 确保远程目录存在
            if remote_path != "/":
                drive.mkdir(remote_dir, remote_path)

            # 上传文件
            drive.upload_file(str(item), f"{remote_dir.rstrip('/')}/{remote_path}",
                              filename=item.name)
            print(f"已上传: {rel_path}")


# 批量下载目录
def download_directory(drive, remote_dir="/", local_dir="./downloads"):
    """批量下载存储目录到本地"""
    os.makedirs(local_dir, exist_ok=True)

    def download_recursive(remote_path, local_path):
        # 下载文件
        files = drive.get_file_list(remote_path)
        for file in files:
            drive.download_file(file.fid, filedir=local_path, filename=file.name)
            print(f"已下载: {file.name}")

        # 递归下载子目录
        dirs = drive.get_dir_list(remote_path)
        for dir in dirs:
            sub_remote = f"{remote_path.rstrip('/')}/{dir.name}"
            sub_local = os.path.join(local_path, dir.name)
            os.makedirs(sub_local, exist_ok=True)
            download_recursive(sub_remote, sub_local)

    download_recursive(remote_dir, local_dir)


# 使用示例
upload_directory(drive, "/home/user/documents", "/backup")
download_directory(drive, "/backup", "/home/user/restore")
```

## 🧪 测试功能

### 运行完整测试

```bash
cd src/fundrive/drives/os
python example.py --test
```

测试内容包括：
- ✅ 登录认证
- ✅ 获取文件列表
- ✅ 获取目录列表
- ✅ 创建目录
- ✅ 文件上传
- ✅ 文件存在检查
- ✅ 获取文件信息
- ✅ 文件下载
- ✅ 删除文件

### 运行交互式演示

```bash
python example.py --interactive
```

交互式演示支持：
- 📁 查看根目录文件
- 📂 查看根目录文件夹
- ⬆️ 上传文件
- 📁 创建文件夹

## 📋 支持的功能

| 功能 | 支持状态 | 说明 |
|------|---------|------|
| 登录认证 | ✅ | 无需真正认证，直接返回成功 |
| 文件上传 | ✅ | 复制文件到指定目录 |
| 文件下载 | ✅ | 复制文件到目标位置 |
| 文件列表 | ✅ | 获取指定目录下的文件 |
| 目录列表 | ✅ | 获取指定目录下的子目录 |
| 创建目录 | ✅ | 创建新目录，支持递归创建 |
| 删除文件 | ✅ | 删除文件或目录 |
| 文件信息 | ✅ | 获取文件大小、修改时间等信息 |
| 文件存在检查 | ✅ | 检查文件或目录是否存在 |
| 权限管理 | ✅ | 遵循系统文件权限 |

## 🎯 使用场景

### 开发和测试
```python
# 在开发环境中使用本地存储进行测试
test_drive = OsDrive(root_path="./test_storage")
test_drive.login()

# 执行各种测试操作
test_drive.upload_file("test_file.txt", "/", "uploaded_test.txt")
```

### 本地文件管理
```python
# 作为本地文件管理工具
file_manager = OsDrive(root_path="/home/user/documents")
file_manager.login()

# 统一的文件操作接口
files = file_manager.get_file_list("/projects")
for file in files:
    if file.name.endswith('.log'):
        file_manager.delete(file.fid)  # 清理日志文件
```

### 数据备份
```python
# 本地数据备份
backup_drive = OsDrive(root_path="/backup/storage")
backup_drive.login()

# 备份重要文件
backup_drive.upload_file("/important/data.db", "/daily", "data_backup.db")
```

### 混合存储策略

```python
# 结合云存储和本地存储
from fundrive.drives.google import GoogleDrive

local_drive = OsDrive(root_path="/local/cache")
cloud_drive = GoogleDrive()


# 本地缓存策略
def get_file_with_cache(file_id, filename):
    # 先检查本地缓存
    if local_drive.exist("/cache", filename):
        return local_drive.download_file(file_id, "/tmp", filename)

    # 从云端下载并缓存
    cloud_drive.download_file(file_id, "/tmp", filename)
    local_drive.upload_file(f"/tmp/{filename}", "/cache", filename)
    return True
```

## ⚠️ 注意事项

### 路径处理
- **绝对路径**: 建议使用绝对路径作为root_path
- **路径分隔符**: 自动处理不同操作系统的路径分隔符
- **特殊字符**: 避免在文件名中使用特殊字符

### 权限管理
- **读写权限**: 确保对root_path有足够的读写权限
- **目录权限**: 创建目录时会继承父目录权限
- **文件权限**: 上传的文件会保持原有权限

### 性能考虑
- **大文件处理**: 大文件操作直接在本地进行，性能优异
- **并发访问**: 支持多进程/多线程并发访问
- **磁盘空间**: 注意监控磁盘空间使用情况

### 最佳实践
- **定期清理**: 定期清理不需要的文件和目录
- **备份策略**: 重要数据建议结合云存储进行备份
- **监控日志**: 启用日志记录便于问题排查

## 🔧 故障排除

### 常见问题

1. **权限不足**
   ```
   问题: 无法创建文件或目录
   解决: 检查root_path的读写权限
   ```

2. **路径不存在**
   ```
   问题: 指定的root_path不存在
   解决: 确保root_path存在或自动创建
   ```

3. **磁盘空间不足**
   ```
   问题: 文件上传失败
   解决: 检查磁盘剩余空间
   ```

### 调试模式

```python
import logging
from nltlog import getLogger

# 启用调试日志
logger = getLogger("fundrive")
logger.setLevel(logging.DEBUG)

# 创建驱动实例
drive = OsDrive(root_path="/path/to/storage")
```

## 📚 相关资源

- [Python pathlib 文档](https://docs.python.org/3/library/pathlib.html)
- [Python os 模块文档](https://docs.python.org/3/library/os.html)
- [FunDrive 项目主页](https://github.com/farfarfun/fundrive)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进本地文件系统驱动：

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码更改
4. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../../../../LICENSE) 文件。
