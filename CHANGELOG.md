# FunDrive 项目变更日志

本文档记录了 FunDrive 项目的所有重要变更，按版本倒序排列，每个版本按
`新增` / `修复` / `变更` / `废弃` 四类记录；无内容的类别标注「无」。

## [未发布]

### 新增

- README 补齐「从 1.x 升级到 2.x」小节：给出新旧 API 对照表（`local_dir`/`filedir`
  → `save_dir`、`local_path` → `filepath`、三个顶层别名的新导入路径等），原来这里
  只有一行「V2.0有大改动，升级注意」没有任何可操作内容。
- CHANGELOG 补回缺失的 `[2.0.0]` 小节，集中记录 1.x → 2.x 的破坏性变更。
- 新增 `tests/test_call_site_contract.py`：用 AST 守住**调用点**契约（现有
  `test_drive_contract.py` 只比对方法定义，抓不到调用点传错参数名）。覆盖
  `filedir=` 误用、清华云盘与蓝奏云快照的下载调用、`mkdir` 不得返回布尔字面量、
  具名关键字不得写在 `*args` 之前、`BaseDrive` 吞掉多余 kwargs。
- 蓝奏云补上可运行的 `example.py`（原文件 0 字节），只读演示，不做任何写操作。

### 修复

- `drives/github/drive.py`、`drives/gitee/drive.py` 的分享链接告警日志误用 stdlib
  logging 的 `%s` 占位符，farlog（loguru）不支持该语法，参数被静默丢弃；改为 `{}`
  占位符（ruff 的 `PLE1205` 对 loguru 风格有误判，已在 `pyproject.toml` 的
  `lint.ignore` 里统一关掉，不再逐行加 `# noqa`）。
- `BaseDrive.__init__` 不再把子类没消费的 kwargs 转发给 `object.__init__`，
  `get_drive("dropbox", access_token="x")` 之类调用不再抛
  `TypeError: object.__init__() takes exactly one argument`。
- `LanZouDrive.move_file` 漏了 `return`，`move()` 声明返回 `bool` 却恒为 `None`。
- `LanZouDrive.mkdir` 和 `Pan115Drive.mkdir` 声明 `-> str` 却返回布尔值，
  `upload_dir` / `copy_data` 会把 `True` 当目录ID继续用，后续上传全部落错位置。
- `LanZouSnapshot.download()` 用了 `dir_path=` / `url=` 两个不存在的参数名、且漏传
  必填的 `fid`，必抛 `TypeError`；同时给 `LanZouDrive.download_file` 补上
  `url` / `pwd` 关键字参数和文件信息为空的保护。
- 清华云盘模块级 `download()` 用 `filedir=` 调下载接口（形参是 `save_dir`）：
  文件静默落到当前目录，目录下载直接 `TypeError`。另外 9 个驱动的 `example.py`
  共 13 处同类误用一并改正。
- `Pan115Drive.download_file` / `get_download_url` 写成
  `get_file_info(fid=fid, *args, **kwargs)`，只要调用方传了位置参数就报
  `got multiple values for argument 'fid'`；`BaseDrive.download_dir` /
  `upload_dir` 与百度驱动的 `download()` 也是同样的混用，改为不透传 `*args`。
- `Pan115Drive` 其余方法改走 `_require_client()`，未登录时抛 `AuthenticationError`
  而不是 `AttributeError: 'NoneType' object has no attribute ...`。
- `fundrive.core.copy_data` 不再把 `mkdir` 的返回值当布尔用，中转目录改用
  `tempfile.mkdtemp()` 并在 `finally` 里清理，不再往进程当前目录写 `tmp/`。

### 变更

- 新增真正的 `all` extra（PEP 621 自引用），`uv add "fundrive[all]"` 才能一次装齐
  全部驱动——此前 `all` 只存在于 `[dependency-groups]`，不会出现在 PyPI 元数据里。
- 删除 `pyproject.toml` 里拼错的空 extra `plcoud`（正确的 `pcloud` 保留）和已失效的
  `[tool.setuptools]` 配置段（构建后端是 hatchling）。
- 蓝奏云 README 按真实 API 重写：原文档里的 `ignore_limits()`、`login_by_cookie()`、
  `down_dir_by_url()`、`sync_files()` 以及 `example/lanzou_example.py` 都不存在。
- README / `docs/QUICK_START.md` 的示例改为可运行：类名纠正为 `OSSDrive`、
  `TSingHuaDrive`、`WSSDrive`，Dropbox 的凭据改为 `login()` 传入，上传/下载示例
  不再把第三个位置参数当文件名用，安装命令统一为 `uv add`。
- `drives/webdav`、`drives/os`、`drives/pan115`、`drives/lanzou` 的公开方法补齐中文
  docstring（Args / Returns / Raises）。
- `uv.lock` 不再纳入版本管理（见 PR #10），`.gitignore` 已忽略；CI 与文档相应改用
  `uv sync --group dev`，2.0.89 条目里提到的 `uv sync --locked --group dev` 和
  「恢复并重新生成 `uv.lock`」只对当时的仓库状态有效。

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

## [2.0.0] - 2025-01-09

> 这是 1.x → 2.x 的分界版本，接口有破坏性变更。可操作的迁移对照表见
> [README「从 1.x 升级到 2.x」](README.md#从-1x-升级到-2x)。

### 新增

- `DriveFile` 升级为带一等公民字段的结构：`fid` / `name` / `size` / `time` / `ext`
  都有同名属性，`f.size` 与 `f["size"]` 等价；1.x 里只能从 `ext` 字典里翻大小。
- `BaseDrive` 补齐 `move` / `copy` / `rename` / `search` / `get_quota` /
  回收站系列 / `get_download_url` / `get_upload_url` 等高级接口。
- 全量类型标注，错误统一收敛到 `fundrive.core.exceptions`。

### 修复

- 无

### 变更（破坏性）

- **下载接口的本地目录参数统一为 `save_dir`**：1.x 的 `download_file(fid, local_dir,
  filedir=...)` 和 `download_dir(fid, local_dir, ...)` 里 `local_dir` / `filedir`
  两个名字并存且语义重叠，2.x 一律叫 `save_dir`。按关键字调用的代码必须改名，按位置
  调用的不受影响。
- **`upload_file` 的本地路径参数由 `local_path` 改为 `filepath`**（`upload_dir`
  对应改为 `filedir`）。
- **`fundrive.drives` 顶层不再导出 `LanZouSnapshot`、`download_tsinghua`、
  `OpenDataLabDrive`**，改从各自子包导入；其余驱动类名仍可从 `fundrive.drives`
  惰性取用，并新增 `get_drive("<drive_type>")` 工厂。
- **`get_file_info()` / `get_dir_info()` 查不到时返回 `None`**，调用方需要判空。
- **`requires-python` 由 `>=3.8` 提升到 `>=3.12`。**

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
