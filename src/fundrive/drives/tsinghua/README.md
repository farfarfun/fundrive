# 清华云盘驱动

清华云盘驱动是FunDrive项目中用于访问清华大学云盘分享文件的驱动程序。该驱动基于清华云盘的分享链接API实现，支持浏览和下载公开分享的文件和目录。

## 功能特性

### ✅ 已实现功能

- **分享链接访问**: 支持通过分享链接访问公开文件
- **文件浏览**: 列出分享目录中的文件和子目录
- **文件下载**: 下载单个文件或整个目录
- **文件信息**: 获取文件和目录的详细信息
- **搜索功能**: 在分享内容中搜索文件
- **路径导航**: 支持多级目录浏览

### ❌ 不支持功能（只读限制）

- **文件上传**: 分享链接为只读，不支持上传
- **文件删除**: 分享链接为只读，不支持删除
- **目录创建**: 分享链接为只读，不支持创建目录
- **文件修改**: 分享链接为只读，不支持修改文件

## 安装要求

### 系统依赖
```bash
pip install requests
pip install funget
pip install funsecret
pip install funutil
```

### FunDrive核心
```bash
pip install fundrive
```

## 配置方法

### 方法1: 使用funsecret（推荐）
```bash
# 设置分享链接key
funsecret set fundrive.tsinghua.share_key "your_share_key"

# 设置分享密码（如果有）
funsecret set fundrive.tsinghua.password "your_password"
```

### 方法2: 环境变量
```bash
export TSINGHUA_SHARE_KEY="your_share_key"
export TSINGHUA_PASSWORD="your_password"  # 可选
```

### 方法3: 代码中直接设置
```python
from fundrive.drives.tsinghua import TSingHuaDrive

drive = TSingHuaDrive(
    share_key="your_share_key",
    password="your_password"  # 可选
)
```

## 使用方法

### 基本使用

```python
from fundrive.drives.tsinghua import TSingHuaDrive

# 创建驱动实例
drive = TSingHuaDrive(share_key="your_share_key")

# 登录（设置分享链接）
if drive.login():
    print("登录成功")

    # 列出根目录文件
    files = drive.get_file_list("")
    for file in files:
        print(f"文件: {file.name}, 大小: {file.size}")

    # 列出根目录子目录
    dirs = drive.get_dir_list("")
    for dir in dirs:
        print(f"目录: {dir.name}")

    # 下载文件
    if files:
        success = drive.download_file(
            fid=files[0].fid,
            filedir="./downloads",
            filename=files[0].name
        )
        print(f"下载结果: {success}")
```

### 高级功能

#### 文件搜索
```python
# 搜索包含关键词的文件
results = drive.search("pdf")
for file in results:
    print(f"找到文件: {file.name} 在 {file.fid}")
```

#### 目录下载
```python
# 下载整个目录
success = drive.download_dir(
    fid="/documents",
    filedir="./downloads/documents",
    overwrite=True
)
```

#### 文件信息查询
```python
# 获取文件详细信息
file_info = drive.get_file_info("/path/to/file.pdf")
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"大小: {file_info.size}")
    print(f"修改时间: {file_info.ext.get('modified')}")
```

#### 检查文件存在性
```python
# 检查文件是否存在
exists = drive.exist("/path/to/file.pdf")
print(f"文件存在: {exists}")

# 检查目录中是否有特定文件
exists = drive.exist("/documents", "report.pdf")
print(f"文件存在: {exists}")
```

### 错误处理

```python
try:
    drive = TSingHuaDrive(share_key="your_share_key")
    
    if not drive.login():
        print("登录失败，请检查分享链接")
        return
    
    files = drive.get_file_list("")
    if not files:
        print("分享链接可能无效或为空")
        return
        
    # 进行文件操作...
    
except Exception as e:
    print(f"操作失败: {e}")
```

## 示例脚本

项目提供了完整的示例脚本 `example.py`，支持多种运行模式：

### 快速演示
```bash
cd /path/to/fundrive/src/fundrive/drives/tsinghua
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

### TSingHuaDrive类

#### 构造函数
```python
TSingHuaDrive(
    share_key: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
)
```

#### 核心方法

| 方法 | 描述 | 返回值 |
|------|------|--------|
| `login(share_key, password)` | 登录/设置分享链接 | `bool` |
| `exist(fid, filename)` | 检查文件是否存在 | `bool` |
| `get_file_list(fid)` | 获取文件列表 | `List[DriveFile]` |
| `get_dir_list(fid)` | 获取目录列表 | `List[DriveFile]` |
| `get_file_info(fid)` | 获取文件信息 | `Optional[DriveFile]` |
| `get_dir_info(fid)` | 获取目录信息 | `Optional[DriveFile]` |
| `download_file(fid, filedir, filename)` | 下载文件 | `bool` |
| `download_dir(fid, filedir, overwrite)` | 下载目录 | `bool` |
| `search(keyword, fid)` | 搜索文件 | `List[DriveFile]` |

#### 只读操作（不支持）

| 方法 | 描述 | 返回值 |
|------|------|--------|
| `mkdir(fid, dirname)` | 创建目录 | `False` |
| `delete(fid)` | 删除文件/目录 | `False` |
| `upload_file(...)` | 上传文件 | `False` |

### DriveFile对象

```python
class DriveFile:
    fid: str          # 文件/目录路径
    name: str         # 文件/目录名称
    size: int         # 文件大小（字节）
    ext: dict         # 扩展信息
```

扩展信息字段：
- `type`: 类型（"file" 或 "folder"）
- `modified`: 修改时间
- `share_key`: 分享链接key
- `file_path` / `folder_path`: 完整路径

## 获取分享链接

1. 访问清华云盘网站：https://cloud.tsinghua.edu.cn
2. 找到要分享的文件或目录
3. 点击分享按钮，创建分享链接
4. 从分享链接URL中提取share_key

分享链接格式：`https://cloud.tsinghua.edu.cn/d/{share_key}/`

## 常见问题

### Q: 如何获取分享链接的key？
A: 分享链接格式为 `https://cloud.tsinghua.edu.cn/d/{share_key}/`，其中 `{share_key}` 就是需要的key。

### Q: 为什么无法上传文件？
A: 清华云盘分享链接是只读的，不支持上传、删除或修改操作。

### Q: 下载大文件时出现超时怎么办？
A: 可以增加超时时间或使用断点续传功能（如果支持）。

### Q: 如何处理需要密码的分享链接？
A: 在创建驱动实例时传入 `password` 参数，或通过配置设置。

### Q: 搜索功能的范围是什么？
A: 搜索会递归遍历所有子目录，查找文件名包含关键词的文件。

## 错误码说明

| 错误码 | 描述 | 解决方法 |
|--------|------|----------|
| 404 | 分享链接不存在 | 检查share_key是否正确 |
| 403 | 访问被拒绝 | 检查分享密码或权限设置 |
| 500 | 服务器错误 | 稍后重试或联系管理员 |

## 性能优化建议

1. **批量操作**: 尽量批量获取文件列表，减少API调用次数
2. **缓存结果**: 对于不经常变化的目录结构，可以缓存结果
3. **并发下载**: 下载多个文件时可以使用多线程
4. **断点续传**: 对于大文件，实现断点续传机制

## 安全注意事项

1. **凭据保护**: 不要在代码中硬编码分享链接信息
2. **权限控制**: 只访问有权限的分享内容
3. **数据验证**: 下载文件后验证完整性
4. **日志安全**: 避免在日志中记录敏感信息

## 贡献指南

欢迎提交Issue和Pull Request来改进清华云盘驱动：

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

# 运行测试
python -m pytest tests/
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 更新日志

### v1.0.0
- ✅ 实现基本的分享链接访问功能
- ✅ 支持文件和目录浏览
- ✅ 实现文件下载功能
- ✅ 添加搜索功能
- ✅ 完善错误处理和日志记录

## 相关链接

- [FunDrive项目主页](https://github.com/farfarfun/fundrive)
- [清华云盘官网](https://cloud.tsinghua.edu.cn)
- [API文档](https://github.com/farfarfun/fundrive/blob/main/docs/api.md)
- [问题反馈](https://github.com/farfarfun/fundrive/issues)
