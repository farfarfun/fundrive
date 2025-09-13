# 阿里云盘驱动

阿里云盘是阿里巴巴推出的个人云存储服务，提供安全可靠的文件存储和同步功能。FunDrive 提供了两种阿里云盘驱动实现：

## 🚀 驱动类型

### 1. AlipanDrive (推荐)
- **基于**: aligo 库
- **认证方式**: refresh_token
- **功能**: 完整的阿里云盘API功能
- **稳定性**: 高
- **推荐场景**: 个人使用、完整功能需求

### 2. AliopenDrive
- **基于**: 阿里云盘开放API
- **认证方式**: access_token
- **功能**: 基础文件操作
- **稳定性**: 中等
- **推荐场景**: 企业应用、API集成

## 📦 安装依赖

```bash
# 安装阿里云盘驱动依赖
pip install fundrive[alipan]

# 或者手动安装依赖
pip install aligo requests
```

## 🔧 配置方法

### 方法一：使用 funsecret（推荐）

```bash
# 配置 AlipanDrive (基于aligo)
funsecret set fundrive alipan refresh_token "your_refresh_token"

# 配置 AliopenDrive (基于开放API)
funsecret set fundrive alipan access_token "your_access_token"
funsecret set fundrive alipan client_id "your_client_id"
funsecret set fundrive alipan client_secret "your_client_secret"
```

### 方法二：环境变量

```bash
# AlipanDrive 环境变量
export ALIPAN_REFRESH_TOKEN="your_refresh_token"

# AliopenDrive 环境变量
export ALIPAN_ACCESS_TOKEN="your_access_token"
export ALIPAN_CLIENT_ID="your_client_id"
export ALIPAN_CLIENT_SECRET="your_client_secret"
```

## 🔑 获取认证凭据

### AlipanDrive (refresh_token)

1. **安装 aligo 库**:
   ```bash
   pip install aligo
   ```

2. **获取 refresh_token**:
   ```python
   from aligo import Aligo
   
   # 首次登录会弹出二维码，扫码登录
   ali = Aligo()
   
   # 获取 refresh_token
   refresh_token = ali.refresh_token
   print(f"Refresh Token: {refresh_token}")
   ```

3. **保存 refresh_token**:
   ```bash
   funsecret set fundrive alipan refresh_token "your_refresh_token"
   ```

### AliopenDrive (access_token)

1. **注册开发者账号**: 访问 [阿里云盘开放平台](https://www.aliyundrive.com/o/getting_started)

2. **创建应用**: 获取 client_id 和 client_secret

3. **OAuth2 授权流程**: 获取 access_token

4. **保存凭据**:
   ```bash
   funsecret set fundrive alipan access_token "your_access_token"
   funsecret set fundrive alipan client_id "your_client_id"
   funsecret set fundrive alipan client_secret "your_client_secret"
   ```

## 💻 使用示例

### 基础使用

```python
from fundrive.drives.alipan import AlipanDrive, AliopenDrive

# 使用 AlipanDrive (推荐)
drive = AlipanDrive()
drive.login()

# 或使用 AliopenDrive
# drive = AliopenDrive()
# drive.login()

# 上传文件
drive.upload_file("/本地路径/文件.txt", "root", filename="上传文件.txt")

# 下载文件
files = drive.get_file_list("root")
if files:
    file_id = files[0].fid
    drive.download_file(file_id, filedir="/下载路径", filename="下载文件.txt")

# 创建文件夹
drive.mkdir("root", "新文件夹")

# 获取文件列表
files = drive.get_file_list("root")
for file in files:
    print(f"文件: {file.name}, 大小: {file.size} 字节")

# 获取文件夹列表
dirs = drive.get_dir_list("root")
for dir in dirs:
    print(f"文件夹: {dir.name}")
```

### 高级功能

```python
# 检查文件是否存在
exists = drive.exist("root", "文件名.txt")
print(f"文件存在: {exists}")

# 获取文件信息
file_info = drive.get_file_info(file_id)
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"文件大小: {file_info.size}")
    print(f"创建时间: {file_info.ext.get('create_time', 'N/A')}")

# 删除文件或文件夹
result = drive.delete(file_id)
print(f"删除结果: {result}")

# 批量操作
for file in files[:5]:  # 处理前5个文件
    print(f"处理文件: {file.name}")
    # 执行相关操作...
```

## 🧪 测试功能

### 运行完整测试

```bash
cd src/fundrive/drives/alipan
python example.py --test
```

测试内容包括：
- ✅ 登录认证
- ✅ 获取文件列表
- ✅ 获取目录列表
- ✅ 创建目录
- ✅ 文件上传
- ✅ 文件存在检查
- ✅ 获取文件信息
- ✅ 文件下载
- ✅ 删除文件

### 运行交互式演示

```bash
python example.py --interactive
```

交互式演示支持：
- 📁 查看根目录文件
- 📂 查看根目录文件夹
- ⬆️ 上传文件
- 📁 创建文件夹

## 📋 支持的功能

| 功能 | AlipanDrive | AliopenDrive | 说明 |
|------|-------------|--------------|------|
| 登录认证 | ✅ | ✅ | 支持自动登录 |
| 文件上传 | ✅ | ✅ | 支持大文件上传 |
| 文件下载 | ✅ | ✅ | 支持断点续传 |
| 文件列表 | ✅ | ✅ | 获取指定目录文件 |
| 目录列表 | ✅ | ✅ | 获取指定目录子文件夹 |
| 创建目录 | ✅ | ✅ | 支持多级目录创建 |
| 删除文件 | ✅ | ✅ | 支持文件和文件夹删除 |
| 文件信息 | ✅ | ✅ | 获取详细文件属性 |
| 文件搜索 | ✅ | ⚠️ | AlipanDrive功能更完整 |
| 文件分享 | ✅ | ❌ | 仅AlipanDrive支持 |
| 回收站 | ✅ | ❌ | 仅AlipanDrive支持 |

## ⚠️ 注意事项

### 认证相关
- **refresh_token 有效期**: 通常为30天，需要定期更新
- **access_token 有效期**: 通常为2小时，需要使用refresh_token刷新
- **二维码登录**: AlipanDrive首次使用需要扫码登录

### 使用限制
- **API限流**: 阿里云盘有API调用频率限制，请合理控制请求频率
- **文件大小**: 单个文件上传大小限制为100GB
- **并发限制**: 建议控制并发上传/下载数量

### 最佳实践
- **错误处理**: 建议在代码中添加适当的异常处理
- **重试机制**: 网络不稳定时建议实现重试逻辑
- **日志记录**: 启用日志记录便于问题排查

## 🔧 故障排除

### 常见问题

1. **登录失败**
   ```
   问题: 认证失败或token过期
   解决: 重新获取refresh_token或access_token
   ```

2. **上传失败**
   ```
   问题: 文件上传中断或失败
   解决: 检查网络连接，重试上传
   ```

3. **文件不存在**
   ```
   问题: 找不到指定文件或文件夹
   解决: 检查文件路径和权限
   ```

### 调试模式

```python
import logging
from funutil import getLogger

# 启用调试日志
logger = getLogger("fundrive")
logger.setLevel(logging.DEBUG)

# 创建驱动实例
drive = AlipanDrive()
```

## 📚 相关资源

- [阿里云盘官网](https://www.aliyundrive.com/)
- [阿里云盘开放平台](https://www.aliyundrive.com/o/getting_started)
- [aligo 库文档](https://github.com/foyoux/aligo)
- [FunDrive 项目主页](https://github.com/farfarfun/fundrive)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进阿里云盘驱动：

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码更改
4. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../../../../LICENSE) 文件。
