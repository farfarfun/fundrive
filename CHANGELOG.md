# FunDrive 项目变更日志

本文档记录了 FunDrive 项目的所有重要变更，按版本倒序排列，每个版本按
`新增` / `修复` / `变更` / `废弃` 四类记录；无内容的类别标注「无」。

## [2025-09-22] - 新增 OSSUtil 云存储驱动

### 新增

- 新增 `OSSUtilDrive` 驱动：基于阿里云官方 ossutil 命令行工具的云存储驱动
  - 支持完整的阿里云 OSS 对象存储操作功能
  - 自动检测平台/架构并下载配置 ossutil 工具，支持 Windows、macOS、Linux
  - 实现登录、文件操作、目录操作、上传下载等核心方法
  - 支持文件搜索、分享、配额查询等高级功能
  - 集成 funsecret 进行认证信息管理
- 项目现支持 21 个云存储平台；阿里云 OSS 现有 `OSSDrive`（Python SDK）与
  `OSSUtilDrive`（命令行工具）两个驱动可选

### 修复

- 无

### 变更

- 补充 ossutil 驱动使用文档，更新 API 文档

### 废弃

- 无

## [2024-12-11] - 项目全面优化和标准化

### 新增

- 新增 `BaseDriveTest` 通用测试框架，供各驱动统一复用测试逻辑

### 修复

- 修复 `BaseDriveTest` 属性错误问题，移除无效属性赋值
- 修复 pCloud 驱动路径处理兼容性问题：
  - 新增 `_normalize_fid` / `_get_folder_id_by_path` 方法，实现逐级路径解析
  - `exist`/`mkdir`/`get_file_list`/`get_dir_list`/`get_file_info`/`rename`/`copy`/`delete`/`share`/`download`/`search`
    等方法统一改用 `folderid` 参数，移除对 `path` 参数的依赖

### 变更

- 标准化所有生产就绪驱动（pCloud、阿里云 OSS、Zenodo、Dropbox）的 `example.py`，
  统一为直接运行综合测试，移除快速演示与命令行参数解析
- 将 `example.py` / `test.py` 中的 `print` 替换为统一的 logger 方法
  （当时统一到 `funutil.getLogger`；组织规范升级后已改为 `farlog`，见后续版本）
- 重新组织 `DEVELOPMENT_GUIDE.md` 等开发文档结构，补充开发规范与故障排除指南

### 废弃

- 无

---

*本文档将持续更新，记录 FunDrive 项目的所有重要变更。*
