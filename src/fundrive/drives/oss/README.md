# 阿里云OSS存储驱动

基于阿里云OSS Python SDK实现的网盘驱动，支持完整的文件和目录操作功能。

## 🌟 关于阿里云OSS

[阿里云对象存储OSS](https://www.aliyun.com/product/oss)（Object Storage Service）是阿里云提供的海量、安全、低成本、高可靠的云存储服务。OSS可以通过网络随时存储和调用包括文本、图片、音频和视频等在内的各种文件。

### 主要特点
- **海量存储空间**：几乎无限的存储容量
- **高可靠性**：99.9999999999%（12个9）的数据持久性
- **高可用性**：99.995%的服务可用性
- **安全防护**：多层次安全防护体系
- **成本优化**：按量付费，多种存储类型可选
- **全球加速**：遍布全球的CDN节点

## 🚀 功能特性

### ✅ 支持的功能
- **认证登录**：支持AccessKey认证和funsecret配置管理
- **文件操作**：上传、下载、删除、重命名文件
- **目录管理**：创建、删除、列举目录
- **批量操作**：支持批量上传下载和递归处理
- **搜索功能**：按文件名和类型搜索文件
- **复制移动**：文件和目录的复制、移动操作
- **分享链接**：生成预签名URL和公共访问链接
- **进度显示**：大文件上传下载进度条显示
- **空间查询**：获取存储空间使用情况

### ❌ 不支持的功能
- **回收站**：OSS没有回收站概念，删除即永久删除
- **密码分享**：OSS不支持密码保护的分享链接
- **分享保存**：无法直接保存他人分享的内容

## 📋 配置要求

### 1. 获取阿里云访问凭证

1. 登录[阿里云控制台](https://ecs.console.aliyun.com/)
2. 进入"访问控制" > "用户管理"
3. 创建用户并获取AccessKey ID和AccessKey Secret
4. 为用户授予OSS相关权限（如AliyunOSSFullAccess）

### 2. 创建OSS Bucket

1. 进入[OSS控制台](https://oss.console.aliyun.com/)
2. 创建新的Bucket
3. 记录Bucket名称和访问域名（Endpoint）

### 3. 配置访问信息

使用funsecret配置管理工具设置以下信息：

```bash
# 设置访问密钥
funsecret set fundrive oss access_key "your_access_key_id"
funsecret set fundrive oss access_secret "your_access_key_secret"

# 设置Bucket信息
funsecret set fundrive oss bucket_name "your_bucket_name"
funsecret set fundrive oss endpoint "oss-cn-hangzhou.aliyuncs.com"
```

### 4. Endpoint说明

不同地域的Endpoint不同，常用的有：
- 华东1（杭州）：`oss-cn-hangzhou.aliyuncs.com`
- 华东2（上海）：`oss-cn-shanghai.aliyuncs.com`
- 华北2（北京）：`oss-cn-beijing.aliyuncs.com`
- 华南1（深圳）：`oss-cn-shenzhen.aliyuncs.com`

完整列表请参考：[OSS访问域名和数据中心](https://help.aliyun.com/document_detail/31837.html)

## 💻 使用示例

### 基本使用

```python
from fundrive.drives.oss.drive import OSSDrive

# 创建驱动实例
drive = OSSDrive()

# 登录（使用funsecret配置）
if drive.login():
    print("登录成功！")

    # 获取根目录文件列表
    files = drive.get_file_list("")
    for file in files:
        print(f"文件: {file.name} ({file.size} bytes)")

    # 上传文件
    if drive.upload_file("local_file.txt", "remote_dir"):
        print("上传成功！")

    # 下载文件
    if drive.download_file("remote_dir/local_file.txt", filepath="downloaded_file.txt"):
        print("下载成功！")
```

### 手动配置登录

```python
# 也可以手动传入配置信息
drive = OSSDrive()
success = drive.login(
    access_key="your_access_key",
    access_secret="your_access_secret", 
    bucket_name="your_bucket",
    endpoint="oss-cn-hangzhou.aliyuncs.com"
)
```

### 高级功能

```python
# 搜索文件
results = drive.search("test", file_type="image")
for file in results:
    print(f"找到图片: {file.name}")

# 生成分享链接
share_info = drive.share("path/to/file.jpg", expire_days=7)
if share_info:
    print(f"分享链接: {share_info['links'][0]['url']}")

# 获取空间使用情况
quota = drive.get_quota()
print(f"已用空间: {quota['used_space']} bytes")
print(f"对象数量: {quota['object_count']}")
```

## 🧪 运行示例

本驱动提供了完整的示例代码，支持多种运行模式：

```bash
# 进入驱动目录
cd src/fundrive/drives/oss

# 简单使用示例（默认）
python example.py

# 基础功能测试
python example.py --test

# 完整功能演示
python example.py --demo

# 简单使用示例
python example.py --simple
```

## 📚 API文档

本驱动基于以下官方文档实现：

- [阿里云OSS官方文档](https://help.aliyun.com/document_detail/32026.html)
- [OSS Python SDK文档](https://oss-python-sdk-doc.readthedocs.io/)
- [OSS API参考](https://help.aliyun.com/document_detail/31947.html)

## ⚠️ 注意事项

1. **权限配置**：确保AccessKey具有足够的OSS操作权限
2. **网络访问**：确保网络可以访问OSS服务
3. **费用控制**：OSS按使用量计费，注意控制成本
4. **数据安全**：重要数据请做好备份
5. **删除操作**：OSS没有回收站，删除操作不可恢复
6. **并发限制**：注意OSS的QPS限制，避免过于频繁的请求

## 🔧 故障排除

### 常见问题

**Q: 登录失败，提示权限错误**
A: 检查AccessKey是否正确，确认用户具有OSS操作权限

**Q: 上传文件失败**
A: 检查网络连接，确认Bucket名称和Endpoint正确

**Q: 下载速度慢**
A: 可以考虑使用CDN加速或选择就近的数据中心

**Q: 分享链接无法访问**
A: 检查Bucket的访问权限设置，确认链接未过期

### 日志调试

驱动使用funutil日志系统，可以通过以下方式查看详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 然后运行你的代码
drive = OSSDrive()
drive.login()  # 会输出详细的调试信息
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个驱动！

## 📄 许可证

本项目遵循项目根目录的许可证协议。
