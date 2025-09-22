# FunDrive API 文档

## 项目概述

FunDrive 是一个统一的云存储驱动框架，支持20个主流云存储平台的统一操作接口。通过标准化的API设计，开发者可以使用相同的代码操作不同的云存储服务。

## 核心类说明

### BaseDrive 基类

所有云存储驱动的基类，定义了统一的接口规范。

#### 核心方法

##### login(*args, **kwargs) -> bool
**功能**: 登录认证到云存储服务
**参数**: 
- `*args`: 位置参数，具体参数因驱动而异
- `**kwargs`: 关键字参数，具体参数因驱动而异
**返回值**: bool - 登录是否成功
**示例**:
```python
# Google Drive
drive.login(credentials_path="credentials.json")

# Amazon S3
drive.login(access_key_id="xxx", secret_access_key="xxx", region_name="us-east-1", bucket_name="my-bucket")
```

##### exist(fid: str, *args, **kwargs) -> bool
**功能**: 检查文件或目录是否存在
**参数**:
- `fid`: str - 文件或目录的唯一标识符
- `*args, **kwargs`: 扩展参数
**返回值**: bool - 文件是否存在
**示例**:
```python
exists = drive.exist("root/documents/file.txt")
```

##### mkdir(fid: str, name: str, return_if_exist: bool = True, *args, **kwargs) -> str
**功能**: 创建目录
**参数**:
- `fid`: str - 父目录ID
- `name`: str - 新目录名称
- `return_if_exist`: bool - 目录已存在时是否返回现有目录ID
- `*args, **kwargs`: 扩展参数
**返回值**: str - 新创建或已存在的目录ID
**示例**:
```python
new_dir_id = drive.mkdir("root", "新文件夹")
```

##### delete(fid: str, *args, **kwargs) -> bool
**功能**: 删除文件或目录
**参数**:
- `fid`: str - 要删除的文件或目录ID
- `*args, **kwargs`: 扩展参数
**返回值**: bool - 删除是否成功
**示例**:
```python
success = drive.delete("file_id_to_delete")
```

##### get_file_list(fid: str, *args, **kwargs) -> List[DriveFile]
**功能**: 获取指定目录下的文件列表
**参数**:
- `fid`: str - 目录ID
- `*args, **kwargs`: 扩展参数
**返回值**: List[DriveFile] - 文件列表
**示例**:
```python
files = drive.get_file_list("root")
for file in files:
    print(f"文件名: {file.name}, 大小: {file.size}")
```

##### get_dir_list(fid: str, *args, **kwargs) -> List[DriveFile]
**功能**: 获取指定目录下的子目录列表
**参数**:
- `fid`: str - 目录ID
- `*args, **kwargs`: 扩展参数
**返回值**: List[DriveFile] - 目录列表
**示例**:
```python
dirs = drive.get_dir_list("root")
for dir in dirs:
    print(f"目录名: {dir.name}")
```

##### get_file_info(fid: str, *args, **kwargs) -> Optional[DriveFile]
**功能**: 获取文件详细信息
**参数**:
- `fid`: str - 文件ID
- `*args, **kwargs`: 扩展参数
**返回值**: Optional[DriveFile] - 文件信息对象
**示例**:
```python
file_info = drive.get_file_info("file_id")
if file_info:
    print(f"文件大小: {file_info.size} 字节")
```

##### get_dir_info(fid: str, *args, **kwargs) -> DriveFile
**功能**: 获取目录详细信息
**参数**:
- `fid`: str - 目录ID
- `*args, **kwargs`: 扩展参数
**返回值**: DriveFile - 目录信息对象
**示例**:
```python
dir_info = drive.get_dir_info("dir_id")
print(f"目录名: {dir_info.name}")
```

##### upload_file(filepath: str, fid: str, *args, **kwargs) -> bool
**功能**: 上传文件到云存储
**参数**:
- `filepath`: str - 本地文件路径
- `fid`: str - 目标目录ID
- `*args, **kwargs`: 扩展参数（如filename、overwrite等）
**返回值**: bool - 上传是否成功
**示例**:
```python
success = drive.upload_file("/local/path/file.txt", "root", filename="新文件名.txt")
```

##### download_file(fid: str, save_dir: Optional[str] = None, filename: Optional[str] = None, filepath: Optional[str] = None, overwrite: bool = False, *args, **kwargs) -> bool
**功能**: 从云存储下载文件
**参数**:
- `fid`: str - 文件ID
- `save_dir`: Optional[str] - 保存目录
- `filename`: Optional[str] - 保存文件名
- `filepath`: Optional[str] - 完整保存路径
- `overwrite`: bool - 是否覆盖已存在文件
- `*args, **kwargs`: 扩展参数
**返回值**: bool - 下载是否成功
**示例**:
```python
success = drive.download_file("file_id", save_dir="./downloads", filename="下载文件.txt")
```

#### 高级功能方法

##### search(keyword: str, *args, **kwargs) -> List[DriveFile]
**功能**: 搜索文件
**参数**:
- `keyword`: str - 搜索关键词
- `*args, **kwargs`: 扩展参数
**返回值**: List[DriveFile] - 搜索结果列表

##### share(fid: str, *args, **kwargs) -> Optional[str]
**功能**: 创建文件分享链接
**参数**:
- `fid`: str - 文件ID
- `*args, **kwargs`: 扩展参数
**返回值**: Optional[str] - 分享链接

##### get_quota(*args, **kwargs) -> Dict[str, Any]
**功能**: 获取存储配额信息
**返回值**: Dict[str, Any] - 配额信息字典

### DriveFile 文件信息类

文件和目录信息的容器类，继承自dict。

#### 核心属性

- `fid`: str - 文件/目录唯一标识符
- `name`: str - 文件/目录名称
- `size`: int - 文件大小（字节）
- `is_dir`: bool - 是否为目录
- `created_time`: Optional[datetime] - 创建时间
- `modified_time`: Optional[datetime] - 修改时间
- `ext`: Dict[str, Any] - 扩展信息字典

#### 使用示例

```python
file = DriveFile({
    "fid": "file_123",
    "name": "document.pdf",
    "size": 1024000,
    "is_dir": False
})

print(f"文件名: {file.name}")
print(f"文件大小: {file.size} 字节")
print(f"是否为目录: {file.is_dir}")
```

## 支持的云存储驱动

### 🌟 全球主流服务
1. **GoogleDrive** - Google Drive云存储
2. **OneDrive** - Microsoft OneDrive
3. **DropboxDrive** - Dropbox云存储
4. **S3Drive** - Amazon S3对象存储

### 💻 代码托管平台
5. **GitHubDrive** - GitHub仓库存储
6. **GiteeDrive** - Gitee仓库存储

### 🇨🇳 国内主流服务
7. **BaiDuDrive** - 百度网盘
8. **AlipanDrive** - 阿里云盘（Aligo版本）
9. **AliopenDrive** - 阿里云盘（Open API版本）
10. **OSSDrive** - 阿里云OSS（Python SDK版本）
11. **OSSUtilDrive** - 阿里云OSS（ossutil命令行工具版本）

### 🔧 通用协议和工具
12. **WebDAVDrive** - WebDAV协议
13. **OSDrive** - 本地文件系统
14. **PCloudDrive** - PCloud云存储
15. **MediaFireDrive** - MediaFire文件分享
16. **LanzouDrive** - 蓝奏云

### 🔬 学术和专业服务
17. **ZenodoDrive** - Zenodo学术数据存储
18. **TianChiDrive** - 天池数据科学平台
19. **TSingHuaDrive** - 清华云盘
20. **OpenXLabDrive** - OpenXLab AI平台
21. **WSSDrive** - 文叔叔临时存储

## 异常处理

### 常见异常类型

- `DriveError`: 驱动基础异常
- `AuthenticationError`: 认证失败异常
- `FileNotFoundError`: 文件未找到异常
- `PermissionError`: 权限不足异常
- `NetworkError`: 网络连接异常
- `QuotaExceededError`: 存储配额超限异常

### 异常处理示例

```python
from fundrive.core.exceptions import DriveError, AuthenticationError

try:
    drive = GoogleDrive()
    drive.login(credentials_path="credentials.json")
    success = drive.upload_file("local_file.txt", "root")
except AuthenticationError as e:
    print(f"认证失败: {e}")
except DriveError as e:
    print(f"驱动错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 工具函数

### 驱动工厂函数

```python
from fundrive import create_drive

# 通过名称创建驱动
drive = create_drive("google")
drive.login()

# 获取所有可用驱动
available_drives = get_available_drives()
print(f"可用驱动: {list(available_drives.keys())}")
```

### 日志记录工具

```python
from funutil import getLogger

logger = getLogger("fundrive")
logger.info("操作开始")
logger.success("操作成功")
logger.error("操作失败")
logger.warning("操作警告")
```

## 最佳实践

### 1. 错误处理
- 始终使用try-catch处理可能的异常
- 根据不同异常类型采取相应的处理策略
- 记录详细的错误日志便于调试

### 2. 认证管理
- 使用funsecret安全存储认证信息
- 避免在代码中硬编码敏感信息
- 定期更新访问令牌

### 3. 文件操作
- 大文件上传下载时显示进度信息
- 使用适当的分块大小提高传输效率
- 实现断点续传机制

### 4. 性能优化
- 使用连接池减少网络开销
- 实现文件信息缓存避免重复查询
- 批量操作时使用并发处理

## 常见问题

### Q: 如何处理不同驱动的认证差异？
A: 每个驱动都有自己的认证方式，通过login方法的参数来区分。建议使用funsecret统一管理认证信息。

### Q: 如何实现跨平台文件同步？
A: 可以组合使用多个驱动实例，通过统一的API实现文件在不同平台间的同步。

### Q: 大文件上传如何优化？
A: 驱动内部会自动处理大文件的分块上传，支持进度显示和断点续传。

### Q: 如何处理网络异常？
A: 驱动内置了重试机制，可以通过配置参数调整重试次数和间隔。

---

更多详细信息请参考：
- [快速开始指南](QUICK_START.md)
- [开发指南](DEVELOPMENT_GUIDE.md)
- [变更日志](CHANGELOG.md)
