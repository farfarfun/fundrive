# pCloud 网盘驱动

基于 pCloud 官方 HTTP JSON Protocol API 实现的 Python 网盘驱动，提供完整的文件和文件夹操作功能。

## 🌐 关于 pCloud

**pCloud** 是一家瑞士云存储服务提供商，成立于 2013 年。pCloud 以其强大的安全性、隐私保护和用户友好的界面而闻名。

### 主要特点
- **安全性**: 提供客户端加密（pCloud Crypto），确保数据安全
- **跨平台**: 支持 Windows、macOS、Linux、iOS、Android 等多个平台
- **同步功能**: 实时同步文件到所有设备
- **分享功能**: 支持文件和文件夹的公开分享
- **版本历史**: 保留文件的历史版本，支持恢复
- **大文件支持**: 支持上传大文件，无文件大小限制

### 服务信息
- **官方网站**: [https://www.pcloud.com/](https://www.pcloud.com/)
- **API 文档**: [https://docs.pcloud.com/](https://docs.pcloud.com/)
- **免费容量**: 10GB（注册即送）
- **付费计划**: Premium 500GB、Premium Plus 2TB 等

## 🚀 功能特性

### ✅ 支持的功能
- **认证系统**: 用户名/密码登录、Auth Token 认证
- **文件操作**: 上传、下载、删除、重命名、复制、移动
- **目录操作**: 创建、列表、删除、重命名、复制、移动
- **高级功能**: 文件搜索、文件分享、配额查询
- **信息获取**: 文件/目录详细信息、下载链接

### ❌ 不支持的功能
- **回收站功能**: pCloud 不提供回收站 API
- **预签名上传**: 使用直接上传 API
- **分享链接保存**: 不支持通过分享链接保存文件

## 📦 安装和配置

### 依赖要求

```bash
pip install requests funutil nltsecret funget
```

### 配置认证信息

使用 `nltsecret` 配置管理工具设置认证信息：

```bash
# 设置用户名
nltsecret set fundrive.pcloud.username "your_username"

# 设置密码
nltsecret set fundrive.pcloud.password "your_password"
```

或者在代码中直接传入：

```python
from fundrive.drives.pcloud.drive import PCloudDrive

# 使用用户名密码
drive = PCloudDrive()
success = drive.login(username="your_username", password="your_password")

# 或使用 Auth Token（如果已有）
success = drive.login(auth_token="your_auth_token")
```

## 🔧 基本使用

### 初始化和登录

```python
from fundrive.drives.pcloud.drive import PCloudDrive

# 创建驱动实例
drive = PCloudDrive()

# 登录（使用 nltsecret 配置的认证信息）
if drive.login():
    print("登录成功")
else:
    print("登录失败")
```

### 文件和目录操作

```python
# 获取根目录文件列表
files = drive.get_file_list("0")  # "0" 是根目录 ID
for file in files:
    print(f"文件: {file.name} ({file.size} bytes)")

# 获取根目录子目录列表
dirs = drive.get_dir_list("0")
for dir in dirs:
    print(f"目录: {dir.name}")

# 创建目录
new_dir_id = drive.mkdir("0", "新建目录")
print(f"新目录 ID: {new_dir_id}")

# 上传文件
success = drive.upload_file("/path/to/local/file.txt", "0")
if success:
    print("文件上传成功")

# 下载文件
success = drive.download_file("file_id", "/path/to/save/")
if success:
    print("文件下载成功")
```

### 高级功能

```python
# 搜索文件
results = drive.search("关键词", limit=10)
for result in results:
    print(f"搜索结果: {result.name}")

# 分享文件
share_result = drive.share("file_id", password="123456", expire_days=7)
if share_result:
    print(f"分享链接: {share_result['link']}")

# 获取配额信息
quota = drive.get_quota()
if quota:
    total_gb = quota["total"] / (1024**3)
    used_gb = quota["used"] / (1024**3)
    print(f"总容量: {total_gb:.2f} GB, 已用: {used_gb:.2f} GB")
```

## 📖 示例代码

本驱动提供了完整的示例代码，支持多种运行模式：

```bash
# 进入驱动目录
cd src/fundrive/drives/pcloud/

# 基础功能测试
python example.py --test

# 完整功能演示
python example.py --demo

# 简单使用示例
python example.py --simple

# 默认运行（简单示例）
python example.py
```

## 🔗 相关链接

- **pCloud 官网**: [https://www.pcloud.com/](https://www.pcloud.com/)
- **pCloud API 文档**: [https://docs.pcloud.com/](https://docs.pcloud.com/)
- **HTTP JSON Protocol**: [https://docs.pcloud.com/protocols/http_json_protocol/](https://docs.pcloud.com/protocols/http_json_protocol/)
- **FunDrive 项目**: [https://github.com/farfarfun/fundrive](https://github.com/farfarfun/fundrive)

## ⚠️ 注意事项

1. **API 限制**: pCloud API 有请求频率限制，请合理使用
2. **文件大小**: 虽然 pCloud 支持大文件，但上传时间取决于网络状况
3. **认证安全**: 请妥善保管用户名、密码和 Auth Token
4. **区域服务器**: pCloud 有多个区域服务器，默认使用 `api.pcloud.com`

## 🐛 问题反馈

如果在使用过程中遇到问题，请：

1. 检查网络连接和认证信息
2. 查看日志输出中的错误信息
3. 参考 pCloud 官方 API 文档
4. 在项目仓库中提交 Issue

## 📄 许可证

本驱动遵循 FunDrive 项目的开源许可证。
