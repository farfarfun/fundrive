# Amazon S3 驱动

Amazon S3（Simple Storage Service）是亚马逊提供的对象存储服务，提供高可用性、可扩展性和数据持久性。本驱动基于boto3 SDK实现，支持完整的S3操作功能。

## 功能特性

### ✅ 核心功能
- **存储桶管理** - 连接和操作S3存储桶
- **对象上传** - 支持单文件和批量上传，自动分片上传大文件
- **对象下载** - 支持单文件和目录下载，断点续传
- **目录操作** - 创建、删除、列表查看（基于对象前缀模拟）
- **文件管理** - 复制、移动、重命名、删除操作
- **权限控制** - 基于IAM的细粒度权限管理

### ✅ 高级功能
- **搜索功能** - 基于对象键的关键词搜索
- **分享链接** - 生成预签名URL临时分享链接
- **存储统计** - 获取存储桶使用情况和对象统计
- **多存储类** - 支持标准、低频访问、归档等存储类别
- **版本控制** - 支持对象版本管理（需存储桶启用）
- **元数据管理** - 自定义对象元数据和标签

### 🔧 技术特点
- 基于官方boto3 SDK
- 支持多种认证方式
- 自动重试和错误处理
- 进度回调支持
- 兼容S3 API的其他服务

## 安装依赖

```bash
pip install boto3 funsecret funutil
```

## 配置方法

### 方法1: 使用funsecret（推荐）

```bash
# 设置AWS认证信息
funsecret set fundrive.amazon.access_key_id "your_access_key_id"
funsecret set fundrive.amazon.secret_access_key "your_secret_access_key"
funsecret set fundrive.amazon.region_name "us-east-1"
funsecret set fundrive.amazon.bucket_name "your_bucket_name"

# 可选：自定义端点（用于兼容S3的服务）
funsecret set fundrive.amazon.endpoint_url "https://s3.amazonaws.com"
```

### 方法2: 环境变量

```bash
export AWS_ACCESS_KEY_ID="your_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key"
export AWS_DEFAULT_REGION="us-east-1"
export S3_BUCKET_NAME="your_bucket_name"
export S3_ENDPOINT_URL="https://s3.amazonaws.com"  # 可选
```

### 方法3: 代码中设置

```python
from fundrive.drives.amazon import S3Drive

drive = S3Drive(
    access_key_id="your_access_key_id",
    secret_access_key="your_secret_access_key",
    region_name="us-east-1",
    bucket_name="your_bucket_name",
    endpoint_url="https://s3.amazonaws.com"  # 可选
)
```

## 使用示例

### 基本操作

```python
from fundrive.drives.amazon import S3Drive

# 创建驱动实例
drive = S3Drive()

# 登录连接
if drive.login():
    print("✅ S3连接成功")
    
    # 获取存储桶信息
    quota = drive.get_quota()
    print(f"存储桶: {quota['bucket_name']}")
    print(f"对象数量: {quota['object_count']}")
    print(f"总大小: {quota['total_size_gb']} GB")
    
    # 列出根目录文件
    files = drive.get_file_list("")
    for file in files:
        print(f"📄 {file.name} ({file.size} bytes)")
    
    # 列出根目录子目录
    dirs = drive.get_dir_list("")
    for dir in dirs:
        print(f"📁 {dir.name}")
else:
    print("❌ S3连接失败")
```

### 文件上传

```python
# 上传单个文件
success = drive.upload_file(
    filepath="/path/to/local/file.txt",
    fid="documents",  # 目标目录
    filename="uploaded_file.txt"  # 可选：重命名
)

if success:
    print("✅ 文件上传成功")

# 带进度回调的上传
def progress_callback(bytes_transferred, total_bytes):
    percent = (bytes_transferred / total_bytes) * 100
    print(f"上传进度: {percent:.1f}%")

drive.upload_file(
    filepath="/path/to/large/file.zip",
    fid="uploads",
    callback=progress_callback
)
```

### 文件下载

```python
# 下载单个文件
success = drive.download_file(
    fid="documents/file.txt",  # S3对象键
    filedir="./downloads",  # 本地保存目录
    filename="downloaded_file.txt"  # 可选：重命名
)

# 下载整个目录
success = drive.download_dir(
    fid="documents",  # S3目录前缀
    filedir="./downloads",  # 本地保存目录
    overwrite=True  # 覆盖已存在文件
)
```

### 目录操作

```python
# 创建目录（创建目录标记对象）
drive.mkdir("", "new_folder")

# 检查对象是否存在
exists = drive.exist("documents/file.txt")
print(f"文件存在: {exists}")

# 获取文件信息
file_info = drive.get_file_info("documents/file.txt")
if file_info:
    print(f"文件大小: {file_info.size}")
    print(f"最后修改: {file_info.ext['last_modified']}")
    print(f"存储类别: {file_info.ext['storage_class']}")

# 删除文件或目录
drive.delete("documents/old_file.txt")  # 删除文件
drive.delete("old_folder/")             # 删除目录及所有内容
```

### 高级功能

```python
# 搜索文件
results = drive.search("report", fid="documents")
for file in results:
    print(f"找到: {file.name} 在 {file.fid}")

# 创建分享链接（1小时有效）
share_url = drive.create_share_link("documents/file.txt", expire_seconds=3600)
print(f"分享链接: {share_url}")

# 复制对象
drive.copy_object("source/file.txt", "backup/file_copy.txt")

# 移动对象
drive.move_object("temp/file.txt", "archive/file.txt")
```

## 运行示例

```bash
# 进入驱动目录
cd src/fundrive/drives/amazon

# 运行快速演示
python example.py --demo

# 查看帮助
python example.py --help
```

## API参考

### S3Drive类

#### 初始化参数
- `access_key_id`: AWS访问密钥ID
- `secret_access_key`: AWS秘密访问密钥  
- `region_name`: AWS区域名称（默认: us-east-1）
- `bucket_name`: S3存储桶名称
- `endpoint_url`: 自定义端点URL（可选）

#### 核心方法

##### login(access_key_id, secret_access_key, region_name, bucket_name) -> bool
连接到Amazon S3服务

##### exist(fid, filename=None) -> bool
检查对象是否存在

##### mkdir(fid, dirname) -> bool
创建目录标记对象

##### delete(fid) -> bool
删除对象或目录

##### get_file_list(fid="") -> List[DriveFile]
获取指定目录的文件列表

##### get_dir_list(fid="") -> List[DriveFile]
获取指定目录的子目录列表

##### get_file_info(fid) -> Optional[DriveFile]
获取文件详细信息

##### get_dir_info(fid) -> Optional[DriveFile]
获取目录信息

##### upload_file(filepath, fid, filename=None, callback=None) -> bool
上传文件到S3

##### download_file(fid, filedir=".", filename=None, callback=None) -> bool
从S3下载文件

##### download_dir(fid, filedir="./cache", overwrite=False) -> bool
下载整个目录

#### 高级方法

##### search(keyword, fid="") -> List[DriveFile]
搜索包含关键词的文件

##### get_quota() -> Dict[str, Any]
获取存储桶使用统计

##### create_share_link(fid, expire_seconds=3600) -> str
创建预签名分享链接

##### copy_object(source_fid, target_fid) -> bool
复制对象

##### move_object(source_fid, target_fid) -> bool
移动对象

## 存储桶要求

### 权限配置
确保AWS用户具有以下S3权限：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

### 存储桶配置
- 确保存储桶已创建并可访问
- 建议启用版本控制以支持文件历史
- 可配置生命周期规则自动管理存储类别
- 可启用服务器端加密保护数据

## 兼容性说明

### S3兼容服务
本驱动支持兼容S3 API的其他云存储服务：

- **MinIO** - 开源对象存储
- **阿里云OSS** - 通过S3兼容接口
- **腾讯云COS** - 通过S3兼容接口
- **华为云OBS** - 通过S3兼容接口

使用时设置相应的`endpoint_url`即可。

### 目录模拟
S3是对象存储，不支持真正的目录结构。本驱动通过以下方式模拟目录：
- 使用对象键前缀表示目录路径
- 创建以`/`结尾的空对象作为目录标记
- 列表操作使用分隔符模拟目录层级

## 性能优化

### 上传优化
- 大文件（>100MB）自动使用分片上传
- 支持并发上传提高速度
- 可设置自定义分片大小

### 下载优化
- 支持范围请求实现断点续传
- 并发下载多个文件
- 本地缓存减少重复下载

### 网络优化
- 自动重试机制处理网络异常
- 连接池复用减少建连开销
- 压缩传输减少带宽使用

## 常见问题

### Q: 如何处理大文件上传？
A: 驱动自动检测文件大小，大于100MB的文件会使用分片上传，支持断点续传和进度显示。

### Q: 如何设置存储类别？
A: 在上传时通过metadata参数指定：
```python
drive.upload_file(
    filepath="file.txt",
    fid="archive",
    metadata={"StorageClass": "GLACIER"}
)
```

### Q: 如何处理权限错误？
A: 检查AWS用户权限配置，确保具有必要的S3操作权限。参考上面的权限配置示例。

### Q: 支持哪些认证方式？
A: 支持多种认证方式：
- Access Key + Secret Key
- IAM角色（EC2实例）
- AWS CLI配置文件
- 环境变量
- STS临时凭证

### Q: 如何使用其他S3兼容服务？
A: 设置相应的endpoint_url：
```python
# MinIO示例
drive = S3Drive(
    endpoint_url="http://localhost:9000",
    access_key_id="minioadmin",
    secret_access_key="minioadmin"
)
```

## 安全注意事项

1. **凭证保护**: 不要在代码中硬编码AWS凭证，使用funsecret或环境变量
2. **权限最小化**: 只授予必要的S3权限，避免过度授权
3. **传输加密**: 使用HTTPS端点确保传输安全
4. **存储加密**: 启用S3服务器端加密保护静态数据
5. **访问日志**: 启用CloudTrail记录S3操作日志
6. **分享链接**: 预签名URL有时效性，注意设置合理的过期时间

## 故障排除

### 连接问题
```python
# 检查网络连接
import boto3
client = boto3.client('s3')
try:
    client.list_buckets()
    print("AWS连接正常")
except Exception as e:
    print(f"连接失败: {e}")
```

### 权限问题
```python
# 测试存储桶权限
try:
    drive.get_file_list("")
    print("存储桶访问正常")
except Exception as e:
    print(f"权限错误: {e}")
```

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用boto3调试日志
boto3.set_stream_logger('boto3', logging.DEBUG)
```

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
python -m pytest tests/drives/test_amazon.py
```

### 提交规范
- 遵循PEP 8代码规范
- 添加适当的类型注解
- 编写单元测试
- 更新相关文档

## 更新日志

### v1.0.0 (2024-01-XX)
- ✅ 初始版本发布
- ✅ 实现完整的S3 API支持
- ✅ 支持大文件分片上传
- ✅ 添加进度回调功能
- ✅ 完善错误处理和日志
- ✅ 支持S3兼容服务

---

**注意**: 使用Amazon S3服务会产生费用，请注意控制使用量和成本。建议设置账单警报监控费用。
