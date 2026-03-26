# OneDrive 网盘驱动

## 📖 网站介绍

[OneDrive](https://onedrive.live.com) 是Microsoft提供的云存储服务，与Office 365深度集成，为用户提供安全可靠的文件存储和协作功能。

- **存储容量**: 免费 5GB，付费最高 6TB（Microsoft 365）
- **文件大小限制**: 单文件最大 250GB
- **API 限制**: 每应用每秒10次请求，每用户每秒1000次请求
- **支持格式**: 支持所有文件格式，与Office文档深度集成

## ✨ 功能支持

### ✅ 已实现功能
- [x] OAuth2 认证登录
- [x] 文件上传/下载（支持大文件分块上传和进度显示）
- [x] 目录创建/删除
- [x] 文件和目录信息获取
- [x] 文件搜索（全盘搜索）
- [x] 分享链接创建
- [x] 存储配额查询
- [x] 小文件直接上传，大文件分块上传

### ❌ 不支持功能
- [ ] 回收站管理（Microsoft Graph API限制）
- [ ] 文件版本历史（需要SharePoint API）
- [ ] 密码保护的分享链接（需要SharePoint权限）
- [ ] 保存他人分享文件（需要特殊权限）

## 🔧 配置指南

### 获取 Microsoft Graph API 凭据

#### 1. 注册Azure应用
1. 访问 [Azure Portal](https://portal.azure.com/)
2. 进入"Azure Active Directory" > "App registrations"
3. 点击"New registration"创建新应用
4. 填写应用名称，选择支持的账户类型
5. 设置重定向URI为 `http://localhost:8080/callback`

#### 2. 配置API权限
1. 在应用页面，进入"API permissions"
2. 点击"Add a permission" > "Microsoft Graph"
3. 选择"Delegated permissions"
4. 添加以下权限：
   - `Files.ReadWrite.All` - 读写所有文件
   - `offline_access` - 获取刷新令牌

#### 3. 创建客户端密钥
1. 进入"Certificates & secrets"
2. 点击"New client secret"
3. 设置描述和过期时间
4. 复制生成的密钥值（只显示一次）

### 配置方法

```python
# 方法1: 直接传参
drive = OneDrive(
    client_id="your_client_id",
    client_secret="your_client_secret",
    access_token="your_access_token",
    refresh_token="your_refresh_token"
)

# 方法2: 使用nltsecret配置
nltsecret set fundrive onedrive client_id "your_client_id"
nltsecret set fundrive onedrive client_secret "your_client_secret"
nltsecret set fundrive onedrive access_token "your_access_token"
nltsecret set fundrive onedrive refresh_token "your_refresh_token"

# 方法3: 环境变量
export ONEDRIVE_CLIENT_ID="your_client_id"
export ONEDRIVE_CLIENT_SECRET="your_client_secret"
export ONEDRIVE_ACCESS_TOKEN="your_access_token"
```

### OAuth2授权流程

首次使用需要完成OAuth2授权：

1. 运行程序，会显示授权URL
2. 在浏览器中访问授权URL
3. 登录Microsoft账户并授权应用
4. 获取授权码并换取访问令牌
5. 保存访问令牌和刷新令牌供后续使用

## 🚀 使用示例

### 基本使用

```python
from fundrive.drives.onedrive import OneDrive

# 初始化驱动
drive = OneDrive()

# 登录
if drive.login():
    print("登录成功！")
    
    # 获取存储配额
    quota = drive.get_quota()
    print(f"总空间: {quota['total']/(1024**3):.2f} GB")
    print(f"已使用: {quota['used']/(1024**3):.2f} GB")
    
    # 列出根目录文件
    files = drive.get_file_list("root")
    for file in files:
        print(f"文件: {file.name} ({file.size} bytes)")
    
    # 上传文件
    success = drive.upload_file("/local/path/file.txt", "root", "uploaded_file.txt")
    if success:
        print("文件上传成功！")
    
    # 搜索文件
    results = drive.search("test")
    print(f"找到 {len(results)} 个文件")
    
    # 创建分享链接
    share_link = drive.share("file_id")
    if share_link:
        print(f"分享链接: {share_link}")
```

### 高级功能

```python
# 目录操作
dir_id = drive.mkdir("root", "new_folder")
drive.delete("file_or_dir_id")

# 文件操作
drive.download_file("file_id", filedir="/local/path", filename="downloaded.txt")

# 搜索功能
results = drive.search("关键词")

# 获取文件信息
file_info = drive.get_file_info("file_id")
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"大小: {file_info.size} bytes")
    print(f"创建时间: {file_info.create_time}")
```

## 🧪 测试

### 完整测试
```bash
cd src/fundrive/drives/onedrive
python example.py --test
```

### 交互式演示
```bash
cd src/fundrive/drives/onedrive
python example.py --interactive
```

## 📋 依赖要求

```bash
# 安装HTTP请求库
pip install requests

# 项目依赖
pip install nltsecret funutil
```

## 🔒 安全说明

### 凭据安全
- **client_id**: 应用标识符，相对安全但不应公开
- **client_secret**: 应用密钥，必须严格保密
- **access_token**: 访问令牌，必须严格保密
- **refresh_token**: 刷新令牌，必须严格保密

### 权限范围
当前驱动请求以下权限：
- `Files.ReadWrite.All`: 读写用户的所有文件
- `offline_access`: 获取刷新令牌以便长期访问

### 最佳实践
1. 定期轮换客户端密钥
2. 监控API使用量，避免超出限制
3. 在生产环境中使用证书认证
4. 不要在代码中硬编码凭据信息

## 🐛 常见问题

### Q1: 授权失败
**错误信息**: `AADSTS70011: The provided value for the input parameter 'scope' is not valid`

**解决方案**:
1. 检查Azure应用的API权限配置
2. 确保已授予管理员同意
3. 验证重定向URI配置正确

### Q2: 令牌过期
**错误信息**: `401 Unauthorized`

**解决方案**:
驱动会自动尝试刷新令牌，如果仍有问题：
1. 检查refresh_token是否有效
2. 重新进行OAuth2授权
3. 确保客户端密钥未过期

### Q3: 文件上传失败
**可能原因**:
- 文件名包含非法字符
- 存储空间不足
- 网络连接问题

**解决方案**:
```python
# 检查存储空间
quota = drive.get_quota()
if quota['available'] < file_size:
    print("存储空间不足")

# 检查文件名
import re
safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
```

### Q4: 搜索结果不准确
**解决方案**:
OneDrive搜索基于文件名和内容，可能需要时间索引：
1. 新上传的文件可能需要几分钟才能被搜索到
2. 使用更具体的关键词
3. 考虑使用文件类型过滤

## 📊 性能优化

### 批量操作
```python
# 避免频繁的单个文件操作
def batch_upload(file_list, parent_id):
    results = []
    for file_path in file_list:
        result = drive.upload_file(file_path, parent_id)
        results.append(result)
    return results
```

### 大文件处理
```python
# 大文件自动使用分块上传
# 小于4MB的文件直接上传，大于4MB的文件分块上传
# 分块大小为320KB，符合Microsoft Graph API建议
```

## 📈 版本历史

- **v1.0.0** (2024-12-11): 初始版本，实现基本功能
  - OAuth2认证
  - 文件上传下载（支持大文件分块）
  - 目录操作
  - 搜索和分享功能

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个驱动！

## 📄 许可证

本项目遵循项目根目录的LICENSE文件。
