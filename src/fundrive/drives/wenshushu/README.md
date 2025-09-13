# 文叔叔网盘驱动

文叔叔网盘驱动是FunDrive项目中用于访问文叔叔临时文件分享服务的驱动程序。文叔叔是一个免费的临时文件分享平台，支持匿名上传和下载，无需注册即可使用。

## 功能特性

### ✅ 已实现功能

- **匿名登录**: 无需注册，匿名使用服务
- **文件上传**: 支持单文件上传和分块上传
- **文件下载**: 通过分享链接下载文件
- **分享功能**: 自动生成公开分享链接和管理链接
- **存储查询**: 查看存储空间使用情况
- **文件管理**: 查看已上传文件列表
- **搜索功能**: 在已上传文件中搜索
- **秒传功能**: 支持相同文件的快速上传

### ❌ 不支持功能（平台限制）

- **目录结构**: 文叔叔不支持文件夹概念
- **文件删除**: 无法删除已分享的文件
- **文件修改**: 无法修改已上传的文件
- **永久存储**: 文件有过期时间限制

## 安装要求

### 系统依赖
```bash
pip install requests
pip install orjson
pip install tqdm
pip install funget
pip install funsecret
pip install funutil
```

### 加密依赖（上传功能需要）
```bash
pip install pycryptodomex
pip install base58
```

### FunDrive核心
```bash
pip install fundrive
```

## 配置方法

文叔叔支持匿名使用，无需配置账号信息。驱动会自动进行匿名登录。

## 使用方法

### 基本使用

```python
from fundrive.drives.wenshushu import WSSDrive

# 创建驱动实例
drive = WSSDrive()

# 匿名登录
if drive.login():
    print("登录成功")
    
    # 上传文件
    success = drive.upload_file(
        filepath="./test.txt",
        fid="",  # 文叔叔不支持目录结构
        filename="test.txt"
    )
    
    if success:
        print("上传成功")
        
        # 查看已上传文件
        files = drive.get_file_list()
        for file in files:
            print(f"文件: {file.name}")
            print(f"分享链接: {file.ext.get('share_url', '')}")
```

### 文件上传

```python
# 上传单个文件
success = drive.upload_file(
    filepath="./document.pdf",
    fid="",
    filename="my_document.pdf"
)

# 上传时自定义参数
success = drive.upload_file(
    filepath="./large_file.zip",
    fid="",
    filename="large_file.zip",
    chunk_size=4194304,  # 4MB分块
    max_workers=4        # 4个并发线程
)
```

### 文件下载

```python
# 通过分享链接下载文件
share_url = "https://www.wenshushu.cn/f/xxxxxxxxxx"
success = drive.download_file(
    fid=share_url,
    filedir="./downloads",
    filename="downloaded_file.pdf"
)
```

### 文件信息查询

```python
# 获取已上传文件列表
files = drive.get_file_list()
for file in files:
    print(f"文件名: {file.name}")
    print(f"大小: {file.size} bytes")
    print(f"上传时间: {file.ext.get('upload_time')}")
    print(f"分享链接: {file.ext.get('share_url')}")
    print(f"管理链接: {file.ext.get('mgr_url')}")

# 获取特定文件信息
file_info = drive.get_file_info(file_id)
if file_info:
    print(f"文件详情: {file_info.name}")
```

### 存储空间查询

```python
# 获取存储空间信息
storage_info = drive.get_storage_info()
if storage_info:
    print(f"已用空间: {storage_info['used_space_gb']} GB")
    print(f"剩余空间: {storage_info['free_space_gb']} GB")
    print(f"总空间: {storage_info['total_space_gb']} GB")
```

### 文件搜索

```python
# 在已上传文件中搜索
results = drive.search("关键词")
for file in results:
    print(f"找到文件: {file.name}")
    print(f"分享链接: {file.ext.get('share_url')}")
```

### 错误处理

```python
try:
    drive = WSSDrive()
    
    if not drive.login():
        print("登录失败")
        return
    
    # 检查文件是否存在
    if not os.path.exists("./test.txt"):
        print("文件不存在")
        return
    
    # 上传文件
    success = drive.upload_file(
        filepath="./test.txt",
        fid="",
        filename="test.txt"
    )
    
    if success:
        print("上传成功")
    else:
        print("上传失败")
        
except Exception as e:
    print(f"操作失败: {e}")
```

## 示例脚本

项目提供了完整的示例脚本 `example.py`，支持多种运行模式：

### 快速演示
```bash
cd /path/to/fundrive/src/fundrive/drives/wenshushu
python example.py --demo
```

### 完整测试
```bash
python example.py --test
```

### 交互式演示
```bash
python example.py --interactive
```

## API参考

### WSSDrive类

#### 构造函数
```python
WSSDrive(**kwargs)
```

#### 核心方法

| 方法 | 描述 | 返回值 |
|------|------|--------|
| `login()` | 匿名登录 | `bool` |
| `exist(fid, filename)` | 检查文件是否存在 | `bool` |
| `get_file_list(fid)` | 获取已上传文件列表 | `List[DriveFile]` |
| `get_file_info(fid)` | 获取文件信息 | `Optional[DriveFile]` |
| `upload_file(filepath, fid, filename)` | 上传文件 | `bool` |
| `download_file(fid, filedir, filename)` | 下载文件 | `bool` |
| `search(keyword, fid)` | 搜索文件 | `List[DriveFile]` |
| `get_storage_info()` | 获取存储空间信息 | `Dict[str, Any]` |

#### 不支持的操作

| 方法 | 描述 | 返回值 |
|------|------|--------|
| `mkdir(fid, dirname)` | 创建目录 | `False` |
| `delete(fid)` | 删除文件 | `False` |
| `get_dir_list(fid)` | 获取目录列表 | `[]` |
| `get_dir_info(fid)` | 获取目录信息 | `None` |

### DriveFile对象

```python
class DriveFile:
    fid: str          # 文件ID
    name: str         # 文件名称
    size: int         # 文件大小（字节）
    ext: dict         # 扩展信息
```

扩展信息字段：
- `type`: 类型（"file"）
- `upload_time`: 上传时间
- `share_url`: 公开分享链接
- `mgr_url`: 管理链接
- `local_path`: 本地文件路径

## 分享链接格式

文叔叔支持两种分享链接格式：

1. **公开链接**: `https://www.wenshushu.cn/f/{tid}`
2. **管理链接**: `https://www.wenshushu.cn/mgr/{tid}`

其中 `{tid}` 是任务ID，长度为11位。

## 常见问题

### Q: 为什么无法创建文件夹？
A: 文叔叔不支持文件夹概念，所有文件都在根目录下。

### Q: 上传的文件会保存多久？
A: 文叔叔的文件有过期时间限制，具体时间取决于服务条款。

### Q: 为什么无法删除已上传的文件？
A: 文叔叔不提供删除已分享文件的功能，文件会在过期后自动删除。

### Q: 上传大文件时出现错误怎么办？
A: 可以调整分块大小和并发数：
```python
drive.upload_file(
    filepath="large_file.zip",
    fid="",
    chunk_size=2097152,  # 2MB分块
    max_workers=2        # 减少并发数
)
```

### Q: 如何获取文件的分享链接？
A: 上传成功后，可以从文件信息中获取：
```python
files = drive.get_file_list()
for file in files:
    share_url = file.ext.get('share_url')
    if share_url:
        print(f"分享链接: {share_url}")
```

### Q: 支持哪些文件类型？
A: 文叔叔支持所有文件类型，但可能对某些类型有大小限制。

## 错误码说明

| 错误码 | 描述 | 解决方法 |
|--------|------|----------|
| 1021 | 操作太频繁 | 等待指定时间后重试 |
| 网络错误 | 连接超时 | 检查网络连接，重试 |
| 文件不存在 | 本地文件不存在 | 检查文件路径 |
| 分享链接无效 | 链接格式错误或已过期 | 检查链接格式和有效性 |

## 性能优化建议

1. **分块上传**: 对于大文件，使用合适的分块大小（1-4MB）
2. **并发控制**: 根据网络情况调整并发线程数
3. **错误重试**: 实现上传失败的重试机制
4. **秒传检测**: 利用文叔叔的秒传功能加速上传

## 安全注意事项

1. **临时性质**: 文叔叔是临时分享服务，不适合长期存储
2. **公开分享**: 所有上传的文件都会生成公开分享链接
3. **数据安全**: 不要上传敏感或机密文件
4. **链接保护**: 妥善保管分享链接，避免泄露

## 使用限制

1. **文件大小**: 单文件大小可能有限制
2. **存储空间**: 免费用户有存储空间限制
3. **过期时间**: 文件会在一定时间后自动删除
4. **并发限制**: 同时上传的文件数量可能有限制

## 贡献指南

欢迎提交Issue和Pull Request来改进文叔叔驱动：

1. Fork项目仓库
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/farfarfun/fundrive.git
cd fundrive

# 安装开发依赖
pip install -e ".[dev]"

# 安装文叔叔驱动依赖
pip install pycryptodomex base58 orjson

# 运行测试
python -m pytest tests/
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 更新日志

### v1.0.0
- ✅ 实现匿名登录功能
- ✅ 支持文件上传和分块上传
- ✅ 实现分享链接下载
- ✅ 添加存储空间查询
- ✅ 支持文件搜索功能
- ✅ 完善错误处理和日志记录

## 相关链接

- [FunDrive项目主页](https://github.com/farfarfun/fundrive)
- [文叔叔官网](https://www.wenshushu.cn)
- [API文档](https://github.com/farfarfun/fundrive/blob/main/docs/api.md)
- [问题反馈](https://github.com/farfarfun/fundrive/issues)
