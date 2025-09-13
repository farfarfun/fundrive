# MediaFire 云存储驱动

MediaFire是一个流行的云存储服务，提供文件存储、共享和同步功能。本驱动基于MediaFire Core API实现，为FunDrive项目提供对MediaFire云存储的完整访问接口。

## 功能特性

### 核心功能
- ✅ **用户认证**: 支持邮箱密码登录和API Key认证
- ✅ **文件管理**: 上传、下载、删除文件
- ✅ **目录操作**: 创建、删除、浏览目录
- ✅ **文件信息**: 获取文件和目录的详细信息
- ✅ **存在检查**: 检查文件或目录是否存在

### 高级功能
- 🔍 **文件搜索**: 支持关键词搜索
- 🔗 **分享链接**: 生成文件分享链接
- 📊 **存储配额**: 查看存储空间使用情况
- 🔄 **会话管理**: 自动管理登录会话

### API支持
- 基于MediaFire Core API v1.5
- 支持文件分块上传下载
- 完整的错误处理和重试机制
- 中文日志和错误信息

## 安装依赖

MediaFire驱动需要以下Python包：

```bash
pip install requests funsecret funutil
```

或者安装完整的FunDrive项目：

```bash
pip install fundrive[mediafire]
```

## 配置说明

### 获取API凭据

1. **注册MediaFire开发者账户**
   - 访问 [MediaFire开发者中心](https://www.mediafire.com/developers/)
   - 注册开发者账户

2. **创建应用程序**
   - 在开发者控制台创建新应用
   - 获取Application ID和API Key

3. **准备认证信息**
   - MediaFire账户邮箱
   - MediaFire账户密码
   - Application ID
   - API Key

### 配置方法

#### 方法1: 使用funsecret（推荐）

```bash
# 设置MediaFire认证信息
funsecret set fundrive mediafire email "your_email@example.com"
funsecret set fundrive mediafire password "your_password"
funsecret set fundrive mediafire app_id "your_app_id"
funsecret set fundrive mediafire api_key "your_api_key"

# 可选：保存会话令牌以避免重复登录
funsecret set fundrive mediafire session_token "your_session_token"
```

#### 方法2: 使用环境变量

```bash
export MEDIAFIRE_EMAIL="your_email@example.com"
export MEDIAFIRE_PASSWORD="your_password"
export MEDIAFIRE_APP_ID="your_app_id"
export MEDIAFIRE_API_KEY="your_api_key"
export MEDIAFIRE_SESSION_TOKEN="your_session_token"  # 可选
```

#### 方法3: 代码中直接传递

```python
from fundrive.drives.mediafire import MediaFireDrive

drive = MediaFireDrive(
    email="your_email@example.com",
    password="your_password",
    app_id="your_app_id",
    api_key="your_api_key"
)
```

## 使用示例

### 基础使用

```python
from fundrive.drives.mediafire import MediaFireDrive

# 创建驱动实例
drive = MediaFireDrive()

# 登录
if drive.login():
    print("✅ 登录成功")
    
    # 获取根目录文件列表
    files = drive.get_file_list("root")
    print(f"根目录有 {len(files)} 个文件")
    
    # 获取根目录文件夹列表
    folders = drive.get_dir_list("root")
    print(f"根目录有 {len(folders)} 个文件夹")
    
    # 上传文件
    success = drive.upload_file("local_file.txt", "root", "uploaded_file.txt")
    if success:
        print("✅ 文件上传成功")
    
    # 下载文件（需要先获取文件ID）
    files = drive.get_file_list("root")
    for file in files:
        if file.name == "uploaded_file.txt":
            success = drive.download_file(file.fid, "./downloads", "downloaded_file.txt")
            if success:
                print("✅ 文件下载成功")
            break
else:
    print("❌ 登录失败")
```

### 高级功能

```python
# 创建目录
drive.mkdir("root", "新建文件夹")

# 搜索文件
results = drive.search("关键词")
print(f"搜索到 {len(results)} 个结果")

# 获取存储配额
quota = drive.get_quota()
if quota:
    print(f"总空间: {quota['total']/(1024**3):.2f} GB")
    print(f"已使用: {quota['used']/(1024**3):.2f} GB")
    print(f"可用空间: {quota['available']/(1024**3):.2f} GB")

# 生成分享链接
share_url = drive.share(file_id)
if share_url:
    print(f"分享链接: {share_url}")

# 删除文件或文件夹
drive.delete(file_id)
```

### 文件信息操作

```python
# 检查文件是否存在
exists = drive.exist("root", "test.txt")
print(f"文件存在: {exists}")

# 获取文件详细信息
file_info = drive.get_file_info(file_id)
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"文件大小: {file_info.size} 字节")
    print(f"创建时间: {file_info.ext.get('created')}")
    print(f"MIME类型: {file_info.ext.get('mimetype')}")

# 获取目录详细信息
dir_info = drive.get_dir_info(folder_id)
if dir_info:
    print(f"文件夹名: {dir_info.name}")
    print(f"文件数量: {dir_info.ext.get('file_count')}")
    print(f"子文件夹数量: {dir_info.ext.get('folder_count')}")
```

## 测试和演示

### 运行测试

```bash
# 进入MediaFire驱动目录
cd src/fundrive/drives/mediafire

# 运行完整功能测试
python example.py --test

# 运行交互式演示
python example.py --interactive

# 查看帮助信息
python example.py --help
```

### 测试内容

完整测试包括以下功能验证：

1. **登录认证测试** - 验证API认证流程
2. **文件列表获取** - 测试文件和目录列表功能
3. **目录创建** - 测试目录创建功能
4. **文件上传** - 测试文件上传功能
5. **存在性检查** - 验证文件存在检查
6. **文件信息获取** - 测试文件信息查询
7. **文件下载** - 测试文件下载功能
8. **搜索功能** - 验证文件搜索功能
9. **存储配额查询** - 测试配额信息获取
10. **文件删除** - 测试文件删除功能

## 错误处理和故障排除

### 常见问题

#### 1. 登录失败
```
❌ MediaFire登录失败: Invalid credentials
```

**解决方案:**
- 检查邮箱和密码是否正确
- 确认Application ID和API Key是否有效
- 验证账户是否被锁定或需要验证

#### 2. API请求失败
```
❌ MediaFire API请求失败: Connection timeout
```

**解决方案:**
- 检查网络连接
- 确认MediaFire服务状态
- 重试请求或增加超时时间

#### 3. 文件上传失败
```
❌ 文件上传失败: File too large
```

**解决方案:**
- 检查文件大小限制
- 确认账户存储空间充足
- 使用分块上传处理大文件

#### 4. 权限不足
```
❌ MediaFire API错误: Access denied
```

**解决方案:**
- 检查API Key权限设置
- 确认应用程序配置正确
- 联系MediaFire技术支持

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 创建驱动实例时会输出详细日志
drive = MediaFireDrive()
```

#### 检查API响应
```python
# 在调试模式下查看原始API响应
try:
    result = drive._make_request("user/get_info.php")
    print(f"API响应: {result}")
except Exception as e:
    print(f"API错误: {e}")
```

#### 验证认证信息
```python
# 检查配置是否正确加载
print(f"邮箱: {drive.email}")
print(f"应用ID: {drive.app_id}")
print(f"API密钥: {drive.api_key[:10]}..." if drive.api_key else "未设置")
```

## 性能优化

### 上传优化
- 对于大文件，MediaFire支持分块上传
- 可以并行上传多个小文件
- 建议文件大小不超过100MB

### 下载优化
- 使用流式下载处理大文件
- 支持断点续传（需要额外实现）
- 可以并行下载多个文件

### 缓存策略
- 缓存会话令牌避免重复登录
- 缓存目录结构减少API调用
- 使用本地缓存存储文件元数据

## 安全注意事项

### 凭据安全
- 不要在代码中硬编码API密钥
- 使用环境变量或加密配置文件
- 定期轮换API密钥

### 网络安全
- 所有API请求都通过HTTPS加密
- 验证SSL证书有效性
- 避免在不安全网络环境下使用

### 数据保护
- 上传前对敏感文件进行加密
- 定期备份重要数据
- 遵守数据保护法规

## API限制和配额

### 请求限制
- MediaFire对API请求有频率限制
- 建议在请求间添加适当延迟
- 实现指数退避重试机制

### 存储限制
- 免费账户有存储空间限制
- 单个文件大小限制
- 每日上传流量限制

### 功能限制
- 某些高级功能需要付费账户
- API访问权限可能受到限制
- 批量操作有数量限制

## 贡献指南

欢迎为MediaFire驱动贡献代码和改进建议！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/farfarfun/fundrive.git
cd fundrive

# 安装开发依赖
pip install -e .[dev]

# 运行测试
python -m pytest tests/test_mediafire.py
```

### 提交规范
- 遵循项目代码风格
- 添加适当的测试用例
- 更新相关文档
- 提交前运行完整测试

### 问题报告
如果发现bug或有功能建议，请在GitHub上创建issue，包含：
- 详细的问题描述
- 复现步骤
- 错误日志
- 环境信息

## 许可证

本项目基于MIT许可证开源，详见LICENSE文件。

## 更新日志

### v1.0.0 (2024-01-XX)
- 🎉 首次发布MediaFire驱动
- ✅ 实现完整的文件管理功能
- ✅ 支持搜索和分享功能
- ✅ 添加完整的测试套件
- 📚 提供详细的使用文档

---

**注意**: MediaFire是MediaFire LLC的商标。本项目与MediaFire LLC无关，仅为第三方客户端实现。
