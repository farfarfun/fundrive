# 快速入门指南

5 分钟上手 FunDrive：安装、初始化驱动、上传/下载文件。

## 安装

> 要求 Python >= 3.12。

```bash
# 安装基础包
uv add fundrive

# 安装特定驱动（以 Dropbox 为例）
uv add "fundrive[dropbox]"

# 安装多个驱动
uv add "fundrive[dropbox,oss,google,onedrive,amazon,alipan,baidu,lanzou,webdav,wenshushu,tsinghua]"

# 安装全部驱动
uv add "fundrive[all]"
```

不用 uv 的话，把 `uv add` 换成 `pip install` 即可。

支持哪些驱动、各驱动的实现完整度，见主 [README](../README.md#支持的云存储服务)。

## 基本使用

以 Dropbox 为例：

```python
from fundrive.drives.dropbox import DropboxDrive

# 初始化驱动（凭据在 login() 传入，构造函数不接受凭据参数）
drive = DropboxDrive()

# 登录（不传参时自动从 funsecret 读取已保存的 access_token）
drive.login(access_token="your_dropbox_token")

# 上传文件（远程文件名取本地文件名）
drive.upload_file("/本地路径/文件.txt", "/")

# 下载文件
drive.download_file("/上传文件.txt", filepath="/本地下载路径/文件.txt")

# 获取文件列表
files = drive.get_file_list("/")
for file in files:
    print(f"文件名: {file.name}, 大小: {file.size}")
```

其他驱动的初始化参数和示例代码不完全相同（OAuth 流程、access token 获取方式等因服务商而异），完整示例见主 [README 基本使用](../README.md#基本使用) 一节，以及各驱动目录下的 `example.py`（如 `src/fundrive/drives/dropbox/example.py`）。

## 常用场景

- **文件操作**（上传/下载/删除/移动）、**分享功能**、**回收站管理**、**存储管理**：见主 [README 核心功能](../README.md#核心功能)。
- 接口方法的完整签名和参数说明：见 [API 文档](API.md)。

## 遇到问题

- 先看对应驱动目录下的 `README.md`（比如 `src/fundrive/drives/google/README.md`），大多数驱动特有的认证/配置问题都记录在那里。
- 仍未解决的，欢迎在 [issues](https://github.com/farfarfun/fundrive/issues) 提问。
