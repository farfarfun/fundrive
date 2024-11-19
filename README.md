# 统一云存储接口

## 概述

统一云存储接口（Unified Cloud Storage Interface，简称 UCSI）是一个开源工具，旨在为各种云存储服务提供统一的 API。无论您使用的是 Google Drive、Dropbox、OneDrive 还是其他任何云存储服务，UCSI 都能抽象掉不同 API 的复杂性，使开发者能够通过一个一致的接口与多个云存储服务进行交互。

## 功能特点

- **统一 API**：通过一个 API 与多个云存储服务进行交互。
- **可扩展性**：通过实现提供的接口，轻松添加对新云存储服务的支持。
- **文件管理**：在不同的云存储服务之间上传、下载、删除和列出文件。
- **权限管理**：统一管理不同云存储服务的权限和访问控制。
- **跨平台支持**：支持多种编程语言和平台，方便集成到现有项目中。

## 安装

### 使用 pip 安装

```bash
pip install fundrive
```

### 从源码安装

```bash
python install git+https://github.com/farfarfun/fundrive.git
```

## 快速开始

以下是一个简单的示例，展示如何使用 UCSI 上传文件到 Google Drive。

```python
from fundrive import AliDrive

# 初始化 Google Drive 客户端
client = AliDrive('google_drive')

# 上传文件
client.upload_file('/path/to/local/file.txt', 'remote_file.txt')

# 列出文件
files = client.list_files()
for file in files:
    print(file['name'])
```

## 支持的云存储服务

| 序号 | 网盘             | 支持内容          |
| :--: | :--------------- | :------------- |
|  1   | [蓝奏云](#3.1)   | 上传/下载/删除    |
|  2   | [OSS](#3.2)      | 上传/下载/删除   |
|  3   | [github](#3.3)   | 上传/下载/删除   |
|  4   | [gitee](#3.4)    | 上传/下载/删除   |
|  5   | [百度网盘](#3.5) | TODO            |
|  6   | [阿里云盘](#3.6) | TODO            |
|  7   | [Google Drive](#3.6) | TODO       |
|  8   | [Dropbox](#3.6) | TODO            |
|  9   | [OneDrive](#3.6) | TODO           |
|  10  | [Amazon S3](#3.6) | TODO          |

- 更多服务即将推出...

## 贡献

我们欢迎任何形式的贡献！如果您想为 UCSI 做出贡献，请遵循以下步骤：

1. Fork 项目仓库。
2. 创建一个新的分支 (`git checkout -b feature/your-feature-name`)。
3. 提交您的更改 (`git commit -am 'Add some feature'`)。
4. 推送到分支 (`git push origin feature/your-feature-name`)。
5. 创建一个新的 Pull Request。

## 许可证

本项目采用 MIT 许可证。有关更多信息，请参阅 [LICENSE](LICENSE) 文件。

## 联系我们

如果您有任何问题或建议，请通过 [issues](https://github.com/yourusername/ucsi/issues) 或 [email](mailto:your-email@example.com) 联系我们。

---

感谢您使用统一云存储接口！我们希望这个工具能够简化您的云存储集成工作。



#参考
百度云盘的 python-api，[官方 API](https://openapi.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list)  
蓝奏云的 python-api [参考](https://github.com/zaxtyson/LanZouCloud-API)
