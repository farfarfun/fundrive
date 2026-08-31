# Zenodo驱动

[Zenodo](https://zenodo.org/) 是由 CERN 运营的开放科研数据仓库，上传的存储库（deposition）发布后会自动获得 DOI 和公开访问链接，常用于学术数据、代码、论文附件的长期存档。FunDrive 的 Zenodo 驱动基于 [Zenodo REST API](https://developers.zenodo.org/#rest-api) 实现。

## 📦 安装依赖

```bash
pip install fundrive[zenodo]
```

## 🔧 配置方法

### 方法一：使用 funsecret（推荐）

```bash
funsecret set fundrive zenodo access_token "your_zenodo_access_token"
```

Access token 在 Zenodo 个人设置的 [Applications -> Personal access tokens](https://zenodo.org/account/settings/applications/tokens/new/) 页面创建。

### 方法二：直接指定

```python
from fundrive.drives.zenodo import ZenodoDrive

drive = ZenodoDrive()
drive.login(access_token="your_zenodo_access_token")
```

沙盒环境（[sandbox.zenodo.org](https://sandbox.zenodo.org/)，用于测试、不占用正式 DOI 配额）：

```python
drive = ZenodoDrive(sandbox=True)
```

## 💻 使用示例

### 基础使用

```python
from fundrive.drives.zenodo import ZenodoDrive

drive = ZenodoDrive()
drive.login()

# 创建一个新存储库（Zenodo 中没有"目录"概念，mkdir 对应创建一个新 deposition）
deposition_id = drive.mkdir(fid="", name="我的数据集")

# 上传文件到存储库
drive.upload_file("/本地路径/data.csv", deposition_id, filename="data.csv")

# 检查文件是否存在
exists = drive.exist(f"{deposition_id}/data.csv")

# 下载文件（fid 格式固定为 record_id/filename）
drive.download_file(f"{deposition_id}/data.csv", save_dir="/本地下载路径")

# 列出存储库里的文件
files = drive.get_file_list(deposition_id)
for file in files:
    print(f"文件: {file.name}, 大小: {file.size}")

# 删除文件（fid 里带 "/" 删单个文件，不带则删整个存储库）
drive.delete(f"{deposition_id}/data.csv")
```

### 搜索公开记录

```python
results = drive.search("climate data", file_type="dataset")
for r in results:
    print(r.name)
```

## 📋 支持的功能

| 功能 | 支持状态 | 说明 |
|------|---------|------|
| 连接认证 | ✅ | access token 登录 |
| 创建存储库（`mkdir`） | ✅ | Zenodo 无目录层级，`mkdir` 创建一个新 deposition |
| 文件上传 | ✅ | |
| 文件下载 | ✅ | `fid` 需为 `record_id/filename` 格式 |
| 文件列表 | ✅ | |
| 文件存在检查 | ✅ | |
| 删除文件/存储库 | ✅ | |
| 记录搜索 | ✅ | 搜索 Zenodo 公开记录 |
| 分享 | ⚠️ | 存储库发布（publish）后自动获得公开 DOI 链接，无需单独调用分享接口，`share()` 只打日志不做实际操作 |
| 回收站 | ❌ | Zenodo 平台不提供回收站功能 |
| 预签名上传 URL | ❌ | Zenodo 使用 bucket API 上传，不提供预签名 URL |

## ⚠️ 注意事项

- Zenodo 面向的是"发布数据集/论文附件后长期归档"的场景，和网盘型驱动（webdav/alipan 等）的"任意读写"语义不完全一致——存储库一旦发布（published）就不再允许直接修改文件，需要走新版本流程。
- 文件/记录相关的 `fid` 统一使用 `record_id/filename` 格式，和其他驱动按路径寻址不同。
- 沙盒环境（`sandbox=True`）和正式环境使用不同的 access token，互不通用。

## 📚 相关资源

- [Zenodo REST API 文档](https://developers.zenodo.org/#rest-api)
- [Zenodo 官网](https://zenodo.org/)
- [FunDrive 项目主页](https://github.com/farfarfun/fundrive)

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../../../../LICENSE) 文件。
