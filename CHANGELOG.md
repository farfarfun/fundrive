# FunDrive 项目变更日志

本文档记录了 FunDrive 项目的所有重要变更，按版本倒序排列，每个版本按
`新增` / `修复` / `变更` / `废弃` 四类记录；无内容的类别标注「无」。

## [未发布]

### 修复

- `drives/github/drive.py`、`drives/gitee/drive.py` 的分享链接告警日志误用 stdlib
  logging 的 `%s` 占位符，farlog（loguru）不支持该语法，参数被静默丢弃；改为 `{}`
  占位符（ruff 的 `PLE1205` 对 loguru 的 `{}` + 位置参数风格有误判，已按行加
  `# noqa: PLE1205` 说明）。

## [2.0.89] - 2026-10-02

### 新增

- `fundrive.core.utils` 新增 `sanitize_url()` / `redact_secrets()`：写日志前统一
  把 URL 与异常信息里的 `access_token`、`password`、`signature` 等值打码。
- 新增四组测试：凭据脱敏（`tests/test_credential_logging.py`）、`login()` 失败语义
  （`tests/test_login_contract.py`）、115 驱动错误传播（`tests/test_pan115_drive.py`）、
  ossutil 凭据文件权限（`tests/test_ossutil_config_permissions.py`）。

### 修复

- Zenodo 驱动不再把 `access_token` 放进请求查询参数（改用 Zenodo 官方推荐的
  `Authorization: Bearer`），因此 `response.url` 和 requests 异常信息里不再带明文
  令牌；写日志的 URL/异常文本再额外过一遍脱敏。
- 115 驱动的 `exist()` / `get_file_info()` / `get_dir_info()` 不再用
  `except Exception` 把网络、认证、SDK 错误伪装成「文件不存在」：只有 SDK 明确抛
  `FileNotFoundError` 才视为不存在，其余错误抛 `FunDriveError` 并带上 `fid` 与原始
  异常类型；未登录时抛 `AuthenticationError` 而不是 `AttributeError`。
- 天池、OpenXLab、清华云盘的 `login()` 在探测接口返回非 200 或请求异常时返回
  `False`，不再把「无法验证」当成登录成功；未配置的凭据不再以 `None` 写进
  cookies / headers。清华云盘缺少 `share_key` 时直接返回 `False`。
- ossutil 驱动写出的凭据配置文件权限收紧为 `0600`（目录 `0700`）。
- 恢复并重新生成 `uv.lock`，与 `pyproject.toml` 对齐。
- 统一 WebDAV（webdav4）与文叔叔驱动的异常类型、类型标注和配置读取规范
  （改动早于本版本提交，但首次随 2.0.89 发布）。

### 变更

- `requires-python` 回到 `>=3.12`，`funget>=1.1.69`、`fundrive-alipan>=1.3.13`，
  `pan115` extra 的 `p115client` 去掉 `python_version >= '3.12'` 标记。上一轮自动
  修复把下限降到 3.10 并把 `funget` 退回 1.1.58，既与 PyPI 上 2.0.88 的实际元数据
  不一致，也会让 `fundrive[pan115]` 在 3.10 上装不到 `p115client`（SPEC §2 要求
  `funget>=1.1.63`，而该版本起 `funget` 自身要求 Python >= 3.12）。
- CI 与文档统一改用 uv：`uv sync --locked --group dev`、`uv run ruff`、
  `uv run pytest`、`uv build`，不再用 pip 安装项目与工具链。
- 文档：开发指南的凭据排查步骤改为只输出「是否已配置」且凭据从环境变量注入；
  API 文档与代码示例统一为内置泛型标注（`list[...]` / `dict[...]` / `X | None`）；
  README 贡献流程给出中文 `<类型>: <做了什么>` 提交信息示例。

### 废弃

- 无

## [2.0.88] - 2026-09-07

### 新增

- 无

### 修复

- 无

### 变更

- 更新依赖版本，少量代码格式调整。

### 废弃

- 无

> 勘误：本版本此前还记有「恢复 uv 锁文件」「统一 WebDAV 与文叔叔驱动的异常类型」
> 「支持 Python 3.10 及以上」三条，但这些改动并未随 2.0.88 发布（PyPI 上 2.0.88 的
> `Requires-Python` 仍是 `>=3.12`），已移出本节。

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
