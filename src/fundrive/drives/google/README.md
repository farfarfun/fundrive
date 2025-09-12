# Google Drive 网盘驱动

## 📖 网站介绍

[Google Drive](https://drive.google.com) 是Google提供的云存储服务，为用户提供安全可靠的文件存储和同步功能。

- **存储容量**: 免费 15GB，付费最高 30TB（Google One）
- **文件大小限制**: 单文件最大 5TB
- **API 限制**: 每用户每100秒1000次请求，每100秒10000次请求
- **支持格式**: 支持所有文件格式，包括Google Workspace文档

## ✨ 功能支持

### ✅ 已实现功能
- [x] OAuth2 认证登录
- [x] 文件上传/下载（支持大文件和进度显示）
- [x] 目录创建/删除
- [x] 文件和目录信息获取
- [x] 文件搜索（支持关键词和文件类型过滤）
- [x] 分享链接创建
- [x] 存储配额查询
- [x] 文件复制/移动/重命名
- [x] 回收站文件列表和恢复

### ❌ 不支持功能
- [ ] 密码保护的分享链接（Google Drive API限制）
- [ ] 分享链接过期时间设置（Google Drive API限制）
- [ ] 批量清空回收站（Google Drive API限制）
- [ ] 保存他人分享文件（需要特殊权限）

## 🔧 配置指南

### 获取 Google Drive API 凭据

#### 1. 创建Google Cloud项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 在项目中启用Google Drive API

#### 2. 创建OAuth2凭据
1. 进入"APIs & Services" > "Credentials"
2. 点击"Create Credentials" > "OAuth client ID"
3. 选择"Desktop application"
4. 下载凭据文件（credentials.json）

#### 3. 设置OAuth同意屏幕
1. 进入"APIs & Services" > "OAuth consent screen"
2. 选择"External"用户类型
3. 填写应用信息
4. 添加测试用户（如果应用未发布）

### 配置方法

```python
# 方法1: 直接传参
drive = GoogleDrive(
    credentials_file="/path/to/credentials.json",
    token_file="/path/to/token.json"
)

# 方法2: 使用funsecret配置
from funsecret import save_secret
save_secret("fundrive.google_drive.credentials_file", "/path/to/credentials.json", namespace="fundrive")
save_secret("fundrive.google_drive.token_file", "/path/to/token.json", namespace="fundrive")

# 方法3: 环境变量
export GOOGLE_DRIVE_CREDENTIALS_FILE="/path/to/credentials.json"
export GOOGLE_DRIVE_TOKEN_FILE="/path/to/token.json"
```

### 首次授权流程

首次使用时，程序会自动打开浏览器进行OAuth授权：

1. 浏览器会打开Google授权页面
2. 登录Google账户并授权应用访问
3. 授权成功后，访问令牌会自动保存到token.json
4. 后续使用会自动刷新令牌，无需重新授权

## 🚀 使用示例

### 基本使用

```python
from fundrive.drives.google import GoogleDrive

# 初始化驱动
drive = GoogleDrive()

# 登录（首次会打开浏览器授权）
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
    results = drive.search("test", file_type="pdf")
    print(f"找到 {len(results)} 个PDF文件")
    
    # 创建分享链接
    share_link = drive.share("file_id")
    if share_link:
        print(f"分享链接: {share_link}")
```

### 高级功能

```python
# 文件操作
drive.copy("source_file_id", "target_dir_id", "new_name.txt")
drive.move("file_id", "new_parent_id")
drive.rename("file_id", "new_name.txt")

# 目录操作
dir_id = drive.mkdir("parent_id", "new_folder")
drive.delete("file_or_dir_id")

# 搜索功能
results = drive.search("关键词", fid="search_in_dir_id", file_type="image")

# 下载文件
drive.download_file("file_id", filedir="/local/path", filename="downloaded.txt")
```

## 🧪 测试

### 快速演示
```bash
cd src/fundrive/drives/google
python example.py --demo
```

### 完整测试
```bash
cd src/fundrive/drives/google
python example.py --test
```

### 交互式演示
```bash
cd src/fundrive/drives/google
python example.py --interactive
```

## 📋 依赖要求

```bash
# 安装Google API客户端库
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# 项目依赖
pip install funsecret funutil
```

## 🔒 安全说明

### 凭据文件安全
- **credentials.json**: 包含OAuth客户端信息，相对安全但不应公开
- **token.json**: 包含访问令牌，必须严格保密
- 建议将这些文件放在安全目录，设置适当的文件权限

### 权限范围
当前驱动请求以下权限：
- `https://www.googleapis.com/auth/drive`: 完整的Google Drive访问权限

### 最佳实践
1. 定期轮换OAuth客户端密钥
2. 监控API使用量，避免超出配额
3. 在生产环境中使用服务账户认证
4. 不要在代码中硬编码凭据信息

## 🐛 常见问题

### Q1: 首次授权时浏览器无法打开
**解决方案**:
```python
# 在服务器环境中，可以手动获取授权码
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES)
auth_url, _ = flow.authorization_url(prompt='consent')
print(f'请访问此URL进行授权: {auth_url}')
code = input('输入授权码: ')
flow.fetch_token(code=code)
```

### Q2: 配额超限错误
**错误信息**: `Quota exceeded for quota metric 'Queries' and limit 'Queries per day'`

**解决方案**:
1. 检查API使用量：访问Google Cloud Console > APIs & Services > Quotas
2. 申请配额增加或等待配额重置
3. 优化代码减少API调用频率

### Q3: 文件下载失败
**可能原因**:
- Google Workspace文档（如Google Docs）需要导出为特定格式
- 文件权限不足

**解决方案**:
```python
# 对于Google Workspace文档，需要导出
def export_google_doc(file_id, mime_type='application/pdf'):
    request = service.files().export_media(fileId=file_id, mimeType=mime_type)
    # 处理导出内容...
```

### Q4: 令牌过期问题
**解决方案**:
驱动会自动处理令牌刷新，如果仍有问题：
1. 删除token.json文件
2. 重新运行程序进行授权
3. 检查credentials.json是否有效

## 📊 性能优化

### 批量操作
```python
# 避免频繁的单个文件操作，使用批量查询
def batch_get_file_info(file_ids):
    batch = service.new_batch_http_request()
    for file_id in file_ids:
        batch.add(service.files().get(fileId=file_id))
    batch.execute()
```

### 分页处理
```python
# 处理大量文件时使用分页
def list_all_files():
    page_token = None
    while True:
        results = service.files().list(
            pageSize=1000,
            pageToken=page_token
        ).execute()
        
        files = results.get('files', [])
        # 处理文件...
        
        page_token = results.get('nextPageToken')
        if not page_token:
            break
```

## 📈 版本历史

- **v1.0.0** (2024-12-11): 初始版本，实现基本功能
  - OAuth2认证
  - 文件上传下载
  - 目录操作
  - 搜索和分享功能

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个驱动！

## 📄 许可证

本项目遵循项目根目录的LICENSE文件。
