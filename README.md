# FunDrive

FunDrive 是一个统一的网盘操作接口框架，旨在提供一个标准化的方式来操作不同的网盘服务。

## 📚 文档导航

- **[📖 API接口文档](doc/API.md)** - 完整的API接口说明，适合开发者集成使用
- **[📋 变更日志](doc/CHANGELOG.md)** - 版本变更记录和更新说明
- **[🚀 快速入门指南](doc/QUICK_START.md)** - 5分钟快速上手，包含常用场景示例
- **[🔧 开发指南](doc/DEVELOPMENT_GUIDE.md)** - 开发者贡献指南和最佳实践
- **[📊 性能优化指南](doc/OPTIMIZATION_GUIDE.md)** - 性能优化建议和最佳实践

## V2.0有大改动，升级注意

## 支持的云存储服务

### 📊 驱动实现状态总览

| 序号 | 网盘服务 | 核心 | 高级 | 示例 | 规范 | 状态 | 包名 |
|:---:|:--------|:---:|:---:|:---:|:---:|:---:|:-----|
| 1 | **[Google Drive](src/fundrive/drives/google/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[google]` |
| 2 | **[OneDrive](src/fundrive/drives/onedrive/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[onedrive]` |
| 3 | **[Dropbox](src/fundrive/drives/dropbox/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[dropbox]` |
| 4 | **[Amazon S3](src/fundrive/drives/amazon/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[amazon]` |
| 5 | **[GitHub](src/fundrive/drives/github/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[github]` |
| 6 | **[百度网盘](src/fundrive/drives/baidu/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[baidu]` |
| 7 | **[阿里云盘 (Aligo)](src/fundrive/drives/alipan/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[alipan]` |
| 8 | **[阿里云盘 (Open)](src/fundrive/drives/alipan/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[alipan]` |
| 9 | **[阿里云OSS](src/fundrive/drives/oss/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[oss]` |
| 10 | **[Gitee](src/fundrive/drives/gitee/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[gitee]` |
| 11 | **[WebDAV](src/fundrive/drives/webdav/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[webdav]` |
| 12 | **[pCloud](src/fundrive/drives/pcloud/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[pcloud]` |
| 13 | **[MediaFire](src/fundrive/drives/mediafire/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive` |
| 14 | **[蓝奏云](src/fundrive/drives/lanzou/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[lanzou]` |
| 15 | **[Zenodo](src/fundrive/drives/zenodo/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[zenodo]` |
| 16 | **[本地文件系统](src/fundrive/drives/os/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive` |
| 17 | **[清华云盘](src/fundrive/drives/tsinghua/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[tsinghua]` |
| 18 | **[OpenXLab](src/fundrive/drives/openxlab/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive` |
| 19 | **[天池](src/fundrive/drives/tianchi/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive` |
| 20 | **[文叔叔](src/fundrive/drives/wenshushu/README.md)** | ✅ | ✅ | ✅ | ✅ | 🎉 | `fundrive[wenshushu]` |

### 📋 功能实现详情

#### 核心功能 (BaseDrive 接口)
- **登录认证** (`login`)
- **文件存在检查** (`exist`)
- **文件上传** (`upload_file`)
- **文件下载** (`download_file`)
- **目录创建** (`mkdir`)
- **文件/目录删除** (`delete`)
- **获取文件列表** (`get_file_list`)
- **获取目录列表** (`get_dir_list`)
- **获取文件信息** (`get_file_info`)
- **获取目录信息** (`get_dir_info`)

#### 高级功能
- **文件搜索** (`search`)
- **文件移动** (`move`)
- **文件复制** (`copy`)
- **文件重命名** (`rename`)
- **文件分享** (`share`)
- **获取配额** (`get_quota`)
- **回收站管理** (`get_recycle_list`, `restore`, `clear_recycle`)
- **保存分享** (`save_shared`)

#### 开发规范符合度
- ✅ **完全符合**: 包含标准化示例文件、完整文档、统一测试框架
- ⚠️ **部分符合**: 基本功能实现但缺少示例文件或文档
- ❌ **不符合**: 缺少关键组件或不遵循开发规范

### 🎉 生产就绪驱动 (全部完成！)
所有驱动已完全实现并符合开发规范，推荐在生产环境使用：

#### 🌟 全球主流服务
1. **[Google Drive](src/fundrive/drives/google/README.md)** - 全球最大云存储服务，15GB免费空间，OAuth2认证
2. **[OneDrive](src/fundrive/drives/onedrive/README.md)** - Microsoft云存储服务，与Office深度集成，5GB免费空间
3. **[Dropbox](src/fundrive/drives/dropbox/README.md)** - 老牌云存储服务，同步稳定，2GB免费空间
4. **[Amazon S3](src/fundrive/drives/amazon/README.md)** - 企业级对象存储，支持无限扩展，按使用付费

#### 💻 代码托管平台
5. **[GitHub](src/fundrive/drives/github/README.md)** - 全球最大代码托管平台，1亿+开发者使用
6. **[Gitee](src/fundrive/drives/gitee/README.md)** - 国内领先代码托管平台，访问速度更快

#### 🇨🇳 国内主流服务
7. **[百度网盘](src/fundrive/drives/baidu/README.md)** - 国内最大个人云存储，2TB免费空间
8. **[阿里云盘 (Aligo)](src/fundrive/drives/alipan/README.md)** - 阿里巴巴出品，100GB免费空间，不限速
9. **[阿里云盘 (Open)](src/fundrive/drives/alipan/README.md)** - 开放API版本，企业级功能
10. **[阿里云OSS](src/fundrive/drives/oss/README.md)** - 企业级对象存储，性能稳定，支持多种存储类别

#### 🔧 通用协议和工具
11. **[WebDAV](src/fundrive/drives/webdav/README.md)** - 通用协议，支持多种WebDAV服务器
12. **[pCloud](src/fundrive/drives/pcloud/README.md)** - 欧洲云存储，10GB免费空间，加密存储
13. **[MediaFire](src/fundrive/drives/mediafire/README.md)** - 国外文件分享平台，10GB免费空间
14. **[蓝奏云](src/fundrive/drives/lanzou/README.md)** - 轻量级文件分享，国内访问快
15. **[本地文件系统](src/fundrive/drives/os/README.md)** - 本地文件操作统一接口

#### 🔬 学术和专业服务
16. **[Zenodo](src/fundrive/drives/zenodo/README.md)** - 学术数据存储，开放获取，DOI支持
17. **[清华云盘](src/fundrive/drives/tsinghua/README.md)** - 学术共享平台，只读访问
18. **[OpenXLab](src/fundrive/drives/openxlab/README.md)** - AI模型和数据集平台
19. **[天池](src/fundrive/drives/tianchi/README.md)** - 阿里云大数据竞赛平台
20. **[文叔叔](src/fundrive/drives/wenshushu/README.md)** - 临时文件分享，匿名上传


## 功能特点

- 统一的文件操作接口
- 支持文件和目录的基本操作
- 灵活的文件信息管理
- 完整的网盘功能支持

## 核心功能

### 文件操作
- 文件上传/下载
- 目录创建/删除
- 文件移动/复制
- 文件重命名
- 文件搜索

### 分享功能
- 创建分享链接
- 保存他人分享
- 设置分享密码
- 控制分享有效期

### 回收站管理
- 查看回收站文件
- 恢复已删除文件
- 清空回收站

### 存储管理
- 获取存储配额
- 获取文件下载链接
- 获取文件上传链接


## 安装

### 使用 pip 安装

```bash
pip install fundrive[alipan]
```

### 从源码安装

```bash
python install git+https://github.com/farfarfun/fundrive.git
```


## 🚀 快速开始

### 安装

```bash
# 安装基础包
pip install fundrive

# 安装特定驱动（以 Dropbox 为例）
pip install fundrive[dropbox]

# 安装 Google Drive 驱动
pip install fundrive[google]

# 安装 OneDrive 驱动
pip install fundrive[onedrive]

# 安装 Amazon S3 驱动
pip install fundrive[amazon]

# 安装清华云盘驱动
pip install fundrive[tsinghua]

# 安装文叔叔驱动
pip install fundrive[wenshushu]

# 安装多个驱动
pip install fundrive[dropbox,oss,google,onedrive,amazon,alipan,baidu,lanzou,webdav,wenshushu,tsinghua]

# 安装全部驱动
pip install fundrive[all]
```

### 基本使用

#### 1. Dropbox 示例（推荐）

```python
from fundrive.drives.dropbox import DropboxDrive

# 初始化驱动
drive = DropboxDrive(access_token="your_dropbox_token")

# 登录
drive.login()

# 上传文件
drive.upload_file("/本地路径/文件.txt", "/", "上传文件.txt")

# 下载文件
drive.download_file("/上传文件.txt", "/本地下载路径/文件.txt")

# 获取文件列表
files = drive.get_file_list("/")
for file in files:
    print(f"文件名: {file.name}, 大小: {file.size}")
```

#### 2. Google Drive 示例（推荐）

```python
from fundrive.drives.google import GoogleDrive

# 初始化驱动
drive = GoogleDrive(
    credentials_file="/path/to/credentials.json",
    token_file="/path/to/token.json"
)

# 登录（首次会打开浏览器进行OAuth授权）
drive.login()

# 上传文件
drive.upload_file("/本地路径/文件.txt", "root", filename="上传文件.txt")

# 下载文件
drive.download_file("file_id", filedir="/本地下载路径", filename="下载文件.txt")

# 获取存储配额
quota = drive.get_quota()
print(f"总空间: {quota['total'] / (1024 ** 3):.2f} GB")
print(f"已使用: {quota['used'] / (1024 ** 3):.2f} GB")

# 搜索文件
results = drive.search("关键词", file_type="pdf")
print(f"找到 {len(results)} 个PDF文件")

# 创建分享链接
share_link = drive.share("file_id")
print(f"分享链接: {share_link}")
```

#### 3. OneDrive 示例（推荐）

```python
from fundrive.drives.onedrive import OneDrive

# 初始化驱动
drive = OneDrive(
    client_id="your_client_id",
    client_secret="your_client_secret",
    access_token="your_access_token"
)

# 登录
drive.login()

# 上传文件（支持大文件分块上传）
drive.upload_file("/本地路径/文件.txt", "root", filename="上传文件.txt")

# 下载文件
drive.download_file("file_id", filedir="/本地下载路径", filename="下载文件.txt")

# 获取存储配额
quota = drive.get_quota()
print(f"总空间: {quota['total'] / (1024 ** 3):.2f} GB")
print(f"已使用: {quota['used'] / (1024 ** 3):.2f} GB")

# 搜索文件
results = drive.search("关键词")
print(f"找到 {len(results)} 个文件")

# 创建分享链接
share_link = drive.share("file_id")
print(f"分享链接: {share_link}")
```

#### 4. Amazon S3 示例（推荐）

```python
from fundrive.drives.amazon import S3Drive

# 初始化驱动
drive = S3Drive(
    access_key_id="your_access_key_id",
    secret_access_key="your_secret_access_key",
    region_name="us-east-1",
    bucket_name="your_bucket_name"
)

# 登录
drive.login()

# 上传文件（支持大文件分片上传）
drive.upload_file("/本地路径/文件.txt", "documents", filename="上传文件.txt")

# 下载文件
drive.download_file("documents/上传文件.txt", filedir="/本地下载路径", filename="下载文件.txt")

# 获取存储桶信息
quota = drive.get_quota()
print(f"存储桶: {quota['bucket_name']}")
print(f"对象数量: {quota['object_count']}")
print(f"总大小: {quota['total_size_gb']} GB")

# 创建分享链接（1小时有效）
share_link = drive.create_share_link("documents/文件.txt", expire_seconds=3600)
print(f"分享链接: {share_link}")

# 搜索文件
results = drive.search("报告", fid="documents")
print(f"找到 {len(results)} 个文件")
```

#### 5. 清华云盘示例

```python
from fundrive.drives.tsinghua import TsinghuaDrive

# 初始化驱动
drive = TsinghuaDrive(
    share_key="your_share_key",
    password="your_password"  # 可选
)

# 登录
drive.login()

# 获取文件列表（只读平台）
files = drive.get_file_list("")
for file in files:
    print(f"📄 {file.name} ({file.size} bytes)")

# 下载文件
drive.download_file("文件ID", filedir="/本地下载路径")

# 搜索文件
results = drive.search("关键词")
print(f"找到 {len(results)} 个文件")
```

#### 6. 文叔叔示例

```python
from fundrive.drives.wenshushu import WenshushuDrive

# 初始化驱动（匿名登录）
drive = WenshushuDrive()

# 登录
drive.login()

# 上传文件（支持进度显示）
success = drive.upload_file("/本地文件.txt", "", filename="上传文件.txt")
if success:
    print("✅ 文件上传成功")

# 获取已上传文件列表
files = drive.get_file_list("")
for file in files:
    print(f"📄 {file.name}")

# 下载文件（通过分享链接）
drive.download_file("分享链接", filedir="/本地下载路径")

# 获取存储配额
quota = drive.get_quota()
print(f"上传次数: {quota.get('upload_count', 0)}")
```

#### 7. 阿里云 OSS 示例

```python
from fundrive.drives.oss import OssDrive

# 初始化驱动
drive = OssDrive(
    access_key_id="your_access_key",
    access_key_secret="your_secret_key",
    bucket_name="your_bucket",
    endpoint="oss-cn-hangzhou.aliyuncs.com"
)

# 使用方法与其他驱动相同
drive.login()
drive.upload_file("/本地文件.txt", "/", "远程文件.txt")
```

#### 5. 使用配置管理（推荐）

```python
# 使用 funsecret 管理配置 - Dropbox
from fundrive.drives.dropbox import DropboxDrive

# 自动从配置中读取 access_token
drive = DropboxDrive()
drive.login()

# 使用 funsecret 管理配置 - Google Drive
from fundrive.drives.google import GoogleDrive

# 预先配置凭据文件路径
# funsecret set fundrive google_drive credentials_file "/path/to/credentials.json"
drive = GoogleDrive()  # 自动从配置读取凭据文件路径
drive.login()

# 使用 funsecret 管理配置 - OneDrive
from fundrive.drives.onedrive import OneDrive

# 预先配置OAuth2凭据
# funsecret set fundrive onedrive client_id "your_client_id"
# funsecret set fundrive onedrive client_secret "your_client_secret"
# funsecret set fundrive onedrive access_token "your_access_token"
drive = OneDrive()  # 自动从配置读取凭据
drive.login()
```

### 🧪 测试驱动功能

每个生产就绪的驱动都提供了标准化的测试功能：

```bash
# 进入驱动目录 - Dropbox
cd src/fundrive/drives/dropbox

# 运行完整测试
python example.py --test

# 运行快速演示
python example.py --demo

# 进入驱动目录 - Google Drive
cd src/fundrive/drives/google

# 运行完整测试（14项测试）
python example.py --test

# 运行交互式演示
python example.py --interactive

# 进入驱动目录 - OneDrive
cd src/fundrive/drives/onedrive

# 运行完整测试（14项测试）
python example.py --test

# 运行交互式演示
python example.py --interactive
```

## 使用方法

### 核心接口说明

所有驱动都实现了统一的 `BaseDrive` 接口：

```python
# 文件操作
drive.upload_file(local_path, remote_dir, filename)  # 上传文件
drive.download_file(remote_path, local_path)  # 下载文件
drive.delete(file_or_dir_path)  # 删除文件/目录

# 目录操作  
drive.mkdir(parent_dir, dir_name)  # 创建目录
drive.get_file_list(dir_path)  # 获取文件列表
drive.get_dir_list(dir_path)  # 获取目录列表

# 信息查询
drive.exist(path)  # 检查文件/目录是否存在
drive.get_file_info(file_path)  # 获取文件信息
drive.get_quota()  # 获取存储配额

# 高级功能
drive.search(keyword, dir_path)  # 搜索文件
drive.share(file_path, expire_days=7)  # 创建分享链接
drive.copy(src_path, dst_path)  # 复制文件
drive.move(src_path, dst_path)  # 移动文件
drive.rename(file_path, new_name)  # 重命名文件
```

### 文件分享示例

```python
# 创建分享
share_info = drive.share(
    "文件ID1", "文件ID2",
    password="分享密码",
    expire_days=7,
    description="分享说明"
)

# 保存他人分享
drive.save_shared(
    shared_url="分享链接",
    fid="保存到的目录ID",
    password="分享密码"
)
```

## 🛠️ 开发者指南

### 实现新的网盘驱动

要实现新的网盘支持，请按照以下步骤：

#### 1. 创建驱动类

```python
from fundrive.core import BaseDrive, DriveFile
from funutil import getLogger

logger = getLogger("fundrive.your_drive")

class YourDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化您的驱动特定配置
    
    def login(self, *args, **kwargs):
        """登录认证 - 必须实现"""
        # 实现登录逻辑
        pass
    
    def upload_file(self, local_path, remote_dir, filename=None, *args, **kwargs):
        """文件上传 - 必须实现"""
        # 实现文件上传逻辑
        pass
    
    def download_file(self, remote_path, local_path, *args, **kwargs):
        """文件下载 - 必须实现"""
        # 实现文件下载逻辑
        pass
    
    # ... 实现其他必需方法
```

#### 2. 使用通用测试框架

```python
# example.py
from fundrive.core import create_drive_tester
from .drive import YourDrive

def create_test_drive():
    """创建测试驱动实例"""
    return YourDrive(your_config_params)

def comprehensive_test():
    """运行综合功能测试"""
    drive = create_test_drive()
    if not drive:
        return False
    
    tester = create_drive_tester(drive, "/test_dir")
    return tester.comprehensive_test()

def quick_demo():
    """运行快速演示"""
    drive = create_test_drive()
    if not drive:
        return False
    
    tester = create_drive_tester(drive, "/demo_dir")
    return tester.quick_demo()
```

#### 3. 开发规范要求

- ✅ **继承 BaseDrive**: 实现所有抽象方法
- ✅ **错误处理**: 使用 `funutil.getLogger` 记录日志
- ✅ **配置管理**: 集成 `funsecret` 配置管理
- ✅ **中文注释**: 所有注释和错误信息使用中文
- ✅ **示例文件**: 提供标准化的 `example.py`
- ✅ **测试框架**: 使用通用测试框架
- ✅ **文档**: 创建 `README.md` 说明特定配置

### 必须实现的核心方法

| 方法 | 说明 | 必需 |
|:-----|:-----|:----:|
| `login()` | 登录认证 | ✅ |
| `exist()` | 检查文件/目录是否存在 | ✅ |
| `upload_file()` | 文件上传 | ✅ |
| `download_file()` | 文件下载 | ✅ |
| `mkdir()` | 创建目录 | ✅ |
| `delete()` | 删除文件/目录 | ✅ |
| `get_file_list()` | 获取文件列表 | ✅ |
| `get_dir_list()` | 获取目录列表 | ✅ |
| `get_file_info()` | 获取文件信息 | ✅ |
| `get_dir_info()` | 获取目录信息 | ✅ |

### 推荐实现的高级方法

| 方法 | 说明 | 推荐度 |
|:-----|:-----|:------:|
| `search()` | 文件搜索 | ⭐⭐⭐ |
| `share()` | 创建分享链接 | ⭐⭐⭐ |
| `get_quota()` | 获取存储配额 | ⭐⭐⭐ |
| `copy()` | 复制文件 | ⭐⭐ |
| `move()` | 移动文件 | ⭐⭐ |
| `rename()` | 重命名文件 | ⭐⭐ |

### 不支持功能的处理

对于网盘 API 不支持的功能，请提供警告实现：

```python
def get_recycle_list(self, *args, **kwargs):
    """获取回收站文件列表 - 不支持的功能"""
    logger.warning("该网盘不支持回收站功能")
    return []

def restore(self, fid, *args, **kwargs):
    """恢复文件 - 不支持的功能"""
    logger.warning("该网盘不支持文件恢复功能")
    return False
```

## 注意事项

- 所有文件和目录操作都基于文件ID（fid）进行
- 文件信息通过 `DriveFile` 类进行封装
- 建议在实现具体网盘接口时添加适当的错误处理
- 注意遵循各网盘服务的使用限制和规范

## 贡献指南

我们欢迎任何形式的贡献！如果您想为 UCSI 做出贡献，请遵循以下步骤：

1. Fork 项目仓库。
2. 创建一个新的分支 (`git checkout -b feature/your-feature-name`)。
3. 提交您的更改 (`git commit -am 'Add some feature'`)。
4. 推送到分支 (`git push origin feature/your-feature-name`)。
5. 创建一个新的 Pull Request。


## 联系我们

如果您有任何问题或建议，请通过 [issues](https://github.com/farfarfun/fundrive/issues) 或 [email](1007530194@qq.com) 联系我们。

---

感谢您使用统一云存储接口！我们希望这个工具能够简化您的云存储集成工作。



#参考
百度云盘的 python-api，[官方 API](https://openapi.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list)  
蓝奏云的 python-api [参考](https://github.com/zaxtyson/LanZouCloud-API)



### [acoooder/aliyunpanshare](https://github.com/acoooder/aliyunpanshare)

狗狗盘搜网站：https://gogopanso.com

全量影视资源：https://link3.cc/alipan

今日新增资源：https://link3.cc/zuixin

