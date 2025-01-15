# FunDrive

FunDrive 是一个统一的网盘操作接口框架，旨在提供一个标准化的方式来操作不同的网盘服务。

## V2.0有大改动，升级注意

## 支持的云存储服务

| 序号  | 网盘                                               | 支持内容       | 对应的包         |
| :---: | :------------------------------------------------- | :------------- | :--------------- |
|   1   | [蓝奏云](src/fundrive/drives/lanzou/README.md)     | 上传/下载/删除 | fundrive-lanzou  |
|   2   | [OSS](src/fundrive/drives/oss/README.md)           | 上传/下载/删除 | fundrive[oss]    |
|   3   | [github](src/fundrive/fungit/README.md)            | 上传/下载/删除 | fundrive         |
|   4   | [gitee](src/fundrive/fungit/README.md)             | 上传/下载/删除 | fundrive         |
|   5   | [阿里云盘](src/fundrive/drives/alipan/README.md)   | 上传/下载/删除 | fundrive[alipan] |
|   6   | [百度网盘](src/fundrive/drives/baidu/README.md)    | 上传/下载/删除 | fundrive[baidu]  |
|   7   | [谷歌网盘](src/fundrive/drives/google/README.md)   | TODO           | fundrive         |
|   8   | [Dropbox](src/fundrive/drives/dropbox/README.md)   | TODO           | fundrive         |
|   9   | [OneDrive](src/fundrive/drives/onedrive/README.md) | TODO           | fundrive         |
|  10   | [Amazon](src/fundrive/drives/amazon/README.md)     | TODO           | fundrive         |

- 更多服务即将推出...


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


## 使用方法


### 基础文件操作示例

```python
# 初始化网盘实例
drive = YourDrive()  # 替换为具体的网盘实现

# 上传文件
drive.upload_file("/本地路径/文件.txt", "目标目录ID")

# 下载文件
drive.download_file(
    fid="文件ID",
    filedir="下载目录",
    filename="保存的文件名"
)

# 创建目录
new_dir_id = drive.mkdir("父目录ID", "新目录名")

# 获取文件列表
files = drive.get_file_list("目录ID")
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

## 扩展开发

要实现新的网盘支持，只需继承 `BaseDrive` 类并实现相应的方法即可。主要需要实现以下核心方法：

- `login()`: 登录认证
- `upload_file()`: 文件上传
- `download_file()`: 文件下载
- `get_file_list()`: 获取文件列表
- `mkdir()`: 创建目录
- `delete()`: 删除文件/目录

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

