# OSSUtil 驱动

基于阿里云官方 ossutil 命令行工具的云存储驱动，提供完整的阿里云 OSS 对象存储操作功能。

## 📋 功能特性

### 🔐 认证登录
- 支持 AccessKey/SecretKey 认证
- 自动配置 ossutil 工具
- 支持多种 endpoint 配置

### 📁 文件和目录操作
- ✅ 文件存在性检查
- ✅ 目录创建和管理
- ✅ 文件和目录删除
- ✅ 获取文件/目录列表
- ✅ 获取文件/目录详细信息

### 📤📥 文件传输
- ✅ 单文件上传/下载
- ✅ 批量文件上传/下载
- ✅ 目录递归上传/下载
- ✅ 支持文件覆盖控制

### 🔍 高级功能
- ✅ 文件搜索（支持关键词和文件类型过滤）
- ✅ 文件分享（生成预签名URL）
- ✅ 存储配额查询
- ✅ 文件复制、移动、重命名
- ✅ 获取下载链接

### 🛠️ 自动化工具管理
- ✅ 自动下载和安装 ossutil 工具
- ✅ 跨平台支持（Windows、macOS、Linux）
- ✅ 自动架构检测（x86_64、arm64）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install fundrive
```

### 2. 配置认证信息

使用 nltsecret 配置认证信息：

```python
from nltsecret import write_secret

# 配置 OSS 认证信息
write_secret("fundrive.ossutil.access_key", "your_access_key")
write_secret("fundrive.ossutil.access_secret", "your_access_secret")
write_secret("fundrive.ossutil.bucket_name", "your_bucket_name")
write_secret("fundrive.ossutil.endpoint", "oss-cn-hangzhou.aliyuncs.com")
```

### 3. 基本使用

```python
from fundrive.drives.ossutil import OSSUtilDrive

# 创建驱动实例
drive = OSSUtilDrive()

# 登录
if drive.login():
    print("✅ 登录成功")
    
    # 获取文件列表
    files = drive.get_file_list("")
    print(f"根目录有 {len(files)} 个文件")
    
    # 上传文件
    if drive.upload_file("local_file.txt", "remote_dir/"):
        print("✅ 文件上传成功")
    
    # 下载文件
    if drive.download_file("remote_file.txt", save_dir="./downloads"):
        print("✅ 文件下载成功")
else:
    print("❌ 登录失败")
```

## 📖 详细使用说明

### 认证登录

```python
# 方法1: 使用配置的认证信息
drive = OSSUtilDrive()
drive.login()

# 方法2: 直接传入认证信息
drive.login(
    access_key="your_access_key",
    access_secret="your_access_secret", 
    bucket_name="your_bucket_name",
    endpoint="oss-cn-hangzhou.aliyuncs.com"
)
```

### 文件操作

```python
# 检查文件是否存在
if drive.exist("path/to/file.txt"):
    print("文件存在")

# 获取文件信息
file_info = drive.get_file_info("path/to/file.txt")
if file_info:
    print(f"文件大小: {file_info.size} bytes")
    print(f"修改时间: {file_info.update_time}")

# 上传文件
success = drive.upload_file(
    filepath="local_file.txt",
    fid="remote_dir/",
    overwrite=True
)

# 下载文件
success = drive.download_file(
    fid="remote_file.txt",
    save_dir="./downloads",
    filename="new_name.txt",
    overwrite=True
)
```

### 目录操作

```python
# 创建目录
dir_id = drive.mkdir("parent_dir", "new_directory")

# 获取目录列表
dirs = drive.get_dir_list("some_directory")
for dir in dirs:
    print(f"目录: {dir.name}")

# 获取文件列表
files = drive.get_file_list("some_directory")
for file in files:
    print(f"文件: {file.name} ({file.size} bytes)")
```

### 批量操作

```python
# 上传整个目录
success = drive.upload_dir(
    local_dir="./local_folder",
    remote_dir="remote_folder/",
    overwrite=True
)

# 下载整个目录
success = drive.download_dir(
    remote_dir="remote_folder/",
    local_dir="./downloads",
    overwrite=True
)
```

### 搜索功能

```python
# 搜索文件
results = drive.search(
    keyword="report",
    fid="documents/",  # 在指定目录搜索
    file_type="txt"    # 指定文件类型
)

for result in results:
    print(f"找到: {result.name}")
```

### 文件分享

```python
# 生成分享链接
share_result = drive.share(
    "path/to/file.txt",
    expire_days=7,  # 7天有效期
    description="文件分享"
)

if share_result and share_result["total"] > 0:
    share_url = share_result["links"][0]["url"]
    print(f"分享链接: {share_url}")
```

### 文件管理

```python
# 复制文件
success = drive.copy("source_file.txt", "destination_dir/")

# 移动文件
success = drive.move("source_file.txt", "destination_dir/")

# 重命名文件
success = drive.rename("old_name.txt", "new_name.txt")

# 删除文件或目录
success = drive.delete("path/to/file_or_directory")
```

### 存储配额查询

```python
quota = drive.get_quota()
if quota:
    print(f"Bucket: {quota['bucket_name']}")
    print(f"已用空间: {quota['used_space']} bytes")
    print(f"对象数量: {quota['object_count']}")
    print(f"访问域名: {quota['endpoint']}")
```

## 🔧 配置选项

### 必需配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `access_key` | 阿里云 AccessKey ID | `LTAI5t...` |
| `access_secret` | 阿里云 AccessKey Secret | `xxx...` |
| `bucket_name` | OSS Bucket 名称 | `my-bucket` |
| `endpoint` | OSS 访问域名 | `oss-cn-hangzhou.aliyuncs.com` |

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `region` | OSS 区域 | 从 endpoint 自动推断 |
| `ossutil_path` | ossutil 工具路径 | 自动下载到临时目录 |

### 支持的 Endpoint

| 区域 | Endpoint |
|------|----------|
| 华东1（杭州） | `oss-cn-hangzhou.aliyuncs.com` |
| 华东2（上海） | `oss-cn-shanghai.aliyuncs.com` |
| 华北1（青岛） | `oss-cn-qingdao.aliyuncs.com` |
| 华北2（北京） | `oss-cn-beijing.aliyuncs.com` |
| 华北3（张家口） | `oss-cn-zhangjiakou.aliyuncs.com` |
| 华南1（深圳） | `oss-cn-shenzhen.aliyuncs.com` |
| 西南1（成都） | `oss-cn-chengdu.aliyuncs.com` |
| 中国香港 | `oss-cn-hongkong.aliyuncs.com` |
| 美国西部1（硅谷） | `oss-us-west-1.aliyuncs.com` |
| 美国东部1（弗吉尼亚） | `oss-us-east-1.aliyuncs.com` |
| 亚太东南1（新加坡） | `oss-ap-southeast-1.aliyuncs.com` |
| 欧洲中部1（法兰克福） | `oss-eu-central-1.aliyuncs.com` |

## 🧪 测试和示例

### 运行示例

```bash
# 基本功能测试
python -m fundrive.drives.ossutil.example basic

# 高级功能测试
python -m fundrive.drives.ossutil.example advanced

# 快速演示
python -m fundrive.drives.ossutil.example demo

# 交互式测试
python -m fundrive.drives.ossutil.example interactive
```

### 测试覆盖

- ✅ 登录认证测试
- ✅ 文件上传/下载测试
- ✅ 目录操作测试
- ✅ 搜索功能测试
- ✅ 分享功能测试
- ✅ 批量操作测试
- ✅ 错误处理测试

## ⚠️ 注意事项

### 1. ossutil 工具依赖
- 驱动会自动下载和配置 ossutil 工具
- 首次使用时可能需要网络连接下载工具
- 支持 Windows、macOS、Linux 多平台

### 2. 权限要求
- 需要 OSS 的读写权限
- 建议使用 RAM 子账号，限制权限范围
- 确保 Bucket 存在且有访问权限

### 3. 性能考虑
- 大文件传输建议使用分片上传
- 批量操作时注意 API 调用频率限制
- 建议在网络稳定的环境下使用

### 4. 安全建议
- 不要在代码中硬编码 AccessKey
- 使用 nltsecret 安全存储认证信息
- 定期轮换 AccessKey
- 使用 HTTPS 传输

## 🐛 常见问题

### Q: 登录失败怎么办？
A: 检查以下配置：
- AccessKey 和 SecretKey 是否正确
- Bucket 名称是否存在
- Endpoint 是否匹配 Bucket 所在区域
- 网络连接是否正常

### Q: 文件上传失败？
A: 可能的原因：
- 本地文件不存在或无读取权限
- 远程目录路径不正确
- OSS 存储空间不足
- 网络连接中断

### Q: ossutil 工具下载失败？
A: 解决方案：
- 检查网络连接
- 手动下载 ossutil 并指定路径
- 使用代理或镜像源

### Q: 如何处理大文件传输？
A: 建议：
- 使用分片上传/下载
- 设置合适的超时时间
- 实现断点续传机制
- 监控传输进度

## 📚 相关文档

- [阿里云 OSS 官方文档](https://help.aliyun.com/zh/oss/)
- [ossutil 工具文档](https://help.aliyun.com/zh/oss/developer-reference/ossutil-overview/)
- [FunDrive 项目文档](../../docs/)
- [nltsecret 配置管理](https://github.com/farfarfun/nltsecret)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个驱动！

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../../../LICENSE) 文件。
