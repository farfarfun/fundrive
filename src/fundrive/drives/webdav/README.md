# WebDAV驱动

WebDAV（Web Distributed Authoring and Versioning）是一个基于HTTP的协议，允许用户在远程Web服务器上编辑和管理文件。FunDrive的WebDAV驱动提供了对各种WebDAV服务器的统一访问接口。

## 🚀 支持的服务

- ✅ **Nextcloud** - 开源私有云平台
- ✅ **ownCloud** - 企业文件同步和共享
- ✅ **坚果云** - 国内知名云存储服务
- ✅ **Seafile** - 开源文件同步和共享平台
- ✅ **Apache HTTP Server** - 启用WebDAV模块的Apache服务器
- ✅ **Nginx** - 配置WebDAV模块的Nginx服务器
- ✅ **其他WebDAV服务** - 任何符合WebDAV标准的服务器

## 📦 安装依赖

```bash
# 安装WebDAV驱动依赖
pip install fundrive[webdav]

# 或者手动安装依赖
pip install webdavclient3 requests
```

## 🔧 配置方法

### 方法一：使用 funsecret（推荐）

```bash
# 配置WebDAV服务器信息
funsecret set fundrive webdav url "https://your-webdav-server.com/webdav"
funsecret set fundrive webdav username "your_username"
funsecret set fundrive webdav password "your_password"

# 可选配置
funsecret set fundrive webdav timeout "30"  # 连接超时时间（秒）
```

### 方法二：环境变量

```bash
export WEBDAV_URL="https://your-webdav-server.com/webdav"
export WEBDAV_USERNAME="your_username"
export WEBDAV_PASSWORD="your_password"
export WEBDAV_TIMEOUT="30"
```

### 方法三：直接指定

```python
from fundrive.drives.webdav import WebDavDrive

# 直接指定连接参数
drive = WebDavDrive(
    url="https://your-webdav-server.com/webdav",
    username="your_username",
    password="your_password",
    timeout=30
)
```

## 🔑 常见服务配置

### Nextcloud

```bash
# Nextcloud WebDAV配置
funsecret set fundrive webdav url "https://your-nextcloud.com/remote.php/dav/files/USERNAME/"
funsecret set fundrive webdav username "your_username"
funsecret set fundrive webdav password "your_password"
```

### 坚果云

```bash
# 坚果云WebDAV配置
funsecret set fundrive webdav url "https://dav.jianguoyun.com/dav/"
funsecret set fundrive webdav username "your_email@example.com"
funsecret set fundrive webdav password "your_app_password"  # 注意：需要使用应用密码
```

### ownCloud

```bash
# ownCloud WebDAV配置
funsecret set fundrive webdav url "https://your-owncloud.com/remote.php/webdav/"
funsecret set fundrive webdav username "your_username"
funsecret set fundrive webdav password "your_password"
```

### Seafile

```bash
# Seafile WebDAV配置
funsecret set fundrive webdav url "https://your-seafile.com/seafdav/"
funsecret set fundrive webdav username "your_username"
funsecret set fundrive webdav password "your_password"
```

## 💻 使用示例

### 基础使用

```python
from fundrive.drives.webdav import WebDavDrive

# 创建驱动实例
drive = WebDavDrive()

# 连接到WebDAV服务器
drive.login()

# 上传文件
drive.upload_file("/本地路径/文件.txt", "/", filename="上传文件.txt")

# 下载文件
files = drive.get_file_list("/")
if files:
    file_id = files[0].fid
    drive.download_file(file_id, filedir="/下载路径", filename="下载文件.txt")

# 创建文件夹
drive.mkdir("/", "新文件夹")

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
exists = drive.exist("/", "文件.txt")
print(f"文件存在: {exists}")

# 获取文件信息
file_info = drive.get_file_info(file_id)
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"文件大小: {file_info.size}")
    print(f"修改时间: {file_info.ext.get('modified', 'N/A')}")

# 删除文件或文件夹
result = drive.delete(file_id)
print(f"删除结果: {result}")

# 递归操作
def sync_directory(drive, local_dir, remote_dir="/"):
    """同步本地目录到WebDAV服务器"""
    import os
    from pathlib import Path
    
    local_path = Path(local_dir)
    
    for item in local_path.rglob("*"):
        if item.is_file():
            # 计算相对路径
            rel_path = item.relative_to(local_path)
            remote_path = f"{remote_dir.rstrip('/')}/{rel_path.parent}".replace("\\", "/")
            
            # 确保远程目录存在
            if str(rel_path.parent) != ".":
                drive.mkdir(remote_dir, str(rel_path.parent))
            
            # 上传文件
            drive.upload_file(str(item), remote_path, filename=item.name)
            print(f"已同步: {rel_path}")

# 使用示例
sync_directory(drive, "/home/user/documents", "/backup")
```

### 批量操作

```python
# 批量上传
def batch_upload(drive, file_list, remote_dir="/"):
    """批量上传文件"""
    for local_file in file_list:
        if os.path.exists(local_file):
            filename = os.path.basename(local_file)
            try:
                result = drive.upload_file(local_file, remote_dir, filename=filename)
                if result:
                    print(f"✅ {filename} 上传成功")
                else:
                    print(f"❌ {filename} 上传失败")
            except Exception as e:
                print(f"❌ {filename} 上传异常: {e}")


# 批量下载
def batch_download(drive, remote_dir="/", local_dir="./downloads"):
    """批量下载目录中的所有文件"""
    os.makedirs(local_dir, exist_ok=True)

    files = drive.get_file_list(remote_dir)
    for file in files:
        try:
            result = drive.download_file(file.fid, filedir=local_dir, filename=file.name)
            if result:
                print(f"✅ {file.name} 下载成功")
            else:
                print(f"❌ {file.name} 下载失败")
        except Exception as e:
            print(f"❌ {file.name} 下载异常: {e}")


# 使用示例
file_list = ["/path/to/file1.txt", "/path/to/file2.pdf"]
batch_upload(drive, file_list, "/uploads")
batch_download(drive, "/documents", "/home/user/downloads")
```

## 🧪 测试功能

### 运行完整测试

```bash
cd src/fundrive/drives/webdav
python example.py --test
```

测试内容包括：
- ✅ 连接认证
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
| 连接认证 | ✅ | 支持基本认证和摘要认证 |
| 文件上传 | ✅ | 支持各种文件类型上传 |
| 文件下载 | ✅ | 支持断点续传 |
| 文件列表 | ✅ | 获取指定目录文件 |
| 目录列表 | ✅ | 获取指定目录子文件夹 |
| 创建目录 | ✅ | 支持递归创建目录 |
| 删除文件 | ✅ | 支持文件和文件夹删除 |
| 文件信息 | ✅ | 获取文件大小、修改时间等 |
| 文件存在检查 | ✅ | 检查文件或目录是否存在 |
| 文件移动 | ✅ | 支持文件和目录移动 |
| 文件复制 | ✅ | 支持文件复制操作 |
| 属性查询 | ✅ | 获取WebDAV属性信息 |

## 🎯 使用场景

### 私有云存储
```python
# 连接到Nextcloud私有云
drive = WebDavDrive(
    url="https://my-nextcloud.com/remote.php/dav/files/username/",
    username="username",
    password="password"
)

# 备份重要文件
drive.upload_file("/important/document.pdf", "/backup/", "document_backup.pdf")
```

### 企业文件共享
```python
# 连接到企业ownCloud
drive = WebDavDrive(
    url="https://company-owncloud.com/remote.php/webdav/",
    username="employee@company.com",
    password="password"
)

# 共享项目文件
project_files = ["/project/report.docx", "/project/data.xlsx"]
for file in project_files:
    drive.upload_file(file, "/shared/project/", os.path.basename(file))
```

### 跨平台同步
```python
# 使用坚果云进行跨平台同步
drive = WebDavDrive(
    url="https://dav.jianguoyun.com/dav/",
    username="user@example.com",
    password="app_password"
)

# 同步配置文件
config_files = ["~/.vimrc", "~/.bashrc", "~/.gitconfig"]
for config in config_files:
    if os.path.exists(os.path.expanduser(config)):
        drive.upload_file(os.path.expanduser(config), "/configs/", 
                         os.path.basename(config))
```

## ⚠️ 注意事项

### 认证相关
- **应用密码**: 某些服务（如坚果云）需要使用应用密码而非登录密码
- **二次认证**: 启用2FA的账户需要生成应用专用密码
- **HTTPS**: 建议使用HTTPS连接确保安全性

### 路径处理
- **路径格式**: 使用Unix风格的路径分隔符（/）
- **中文路径**: 确保WebDAV服务器支持UTF-8编码
- **特殊字符**: 避免在文件名中使用WebDAV不支持的特殊字符

### 性能优化
- **连接池**: 内部使用连接池提高性能
- **超时设置**: 根据网络环境调整超时时间
- **并发限制**: 控制并发上传/下载数量避免服务器过载

### 兼容性
- **服务器版本**: 确保WebDAV服务器版本兼容
- **协议支持**: 某些功能可能需要特定的WebDAV扩展
- **文件大小**: 注意服务器的文件大小限制

## 🔧 故障排除

### 常见问题

1. **连接失败**
   ```
   问题: 无法连接到WebDAV服务器
   解决: 检查URL格式、网络连接和防火墙设置
   ```

2. **认证失败**
   ```
   问题: 用户名或密码错误
   解决: 确认凭据正确，检查是否需要应用密码
   ```

3. **上传失败**
   ```
   问题: 文件上传中断或失败
   解决: 检查文件大小限制和服务器存储空间
   ```

4. **路径错误**
   ```
   问题: 找不到指定路径
   解决: 确认WebDAV根路径配置正确
   ```

### 调试模式

```python
import logging
from funutil import getLogger

# 启用调试日志
logger = getLogger("fundrive")
logger.setLevel(logging.DEBUG)

# 创建驱动实例
drive = WebDavDrive(
    url="https://your-server.com/webdav",
    username="username",
    password="password"
)
```

### 连接测试

```python
def test_webdav_connection(url, username, password):
    """测试WebDAV连接"""
    try:
        drive = WebDavDrive(url=url, username=username, password=password)
        result = drive.login()
        if result:
            print("✅ WebDAV连接成功")
            
            # 测试基本操作
            files = drive.get_file_list("/")
            print(f"📁 根目录包含 {len(files)} 个文件")
            
            dirs = drive.get_dir_list("/")
            print(f"📂 根目录包含 {len(dirs)} 个文件夹")
            
        else:
            print("❌ WebDAV连接失败")
    except Exception as e:
        print(f"❌ 连接异常: {e}")

# 使用示例
test_webdav_connection(
    "https://your-server.com/webdav",
    "username",
    "password"
)
```

## 📚 相关资源

- [WebDAV协议规范](https://tools.ietf.org/html/rfc4918)
- [Nextcloud WebDAV文档](https://docs.nextcloud.com/server/latest/user_manual/files/access_webdav.html)
- [ownCloud WebDAV文档](https://doc.owncloud.com/server/admin_manual/configuration/files/files_locking_transactional.html)
- [坚果云WebDAV设置](https://help.jianguoyun.com/?p=2064)
- [FunDrive 项目主页](https://github.com/farfarfun/fundrive)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进WebDAV驱动：

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码更改
4. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../../../../LICENSE) 文件。
