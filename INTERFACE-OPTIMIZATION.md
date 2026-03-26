# 接口优化方案与约定（向上兼容）

本文档由 CTO 细化，作为 FunDrive 统一网盘接口的**规范基准**。所有新增与修改必须遵守**向上兼容**原则：不破坏现有调用方。

**规范来源**：`src/fundrive/core/base.py` 中的 `BaseDrive` 与 `DriveFile` 为唯一接口定义来源。

---

## 1. 核心接口契约

### 1.1 方法签名（与 BaseDrive 一致）

以下签名为**规范签名**。各驱动实现时：

- **必须**保持相同的位置参数顺序与名称（至少通过 `*args, **kwargs` 兼容）。
- **可以**增加仅通过 `**kwargs` 传递的可选参数，不得改变已有参数语义。
- **禁止**移除参数、改变参数顺序或必填/可选关系。

| 方法 | 规范签名 | 返回值 |
|------|----------|--------|
| `login` | `(self, *args, **kwargs)` | `bool` |
| `exist` | `(self, fid: str, *args, **kwargs)` | `bool` |
| `mkdir` | `(self, fid: str, name: str, return_if_exist: bool = True, *args, **kwargs)` | `str`（新创建或已存在目录的 ID） |
| `delete` | `(self, fid: str, *args, **kwargs)` | `bool` |
| `get_file_list` | `(self, fid: str, *args, **kwargs)` | `List[DriveFile]` |
| `get_dir_list` | `(self, fid: str, *args, **kwargs)` | `List[DriveFile]` |
| `get_file_info` | `(self, fid: str, *args, **kwargs)` | `Optional[DriveFile]` |
| `get_dir_info` | `(self, fid: str, *args, **kwargs)` | `DriveFile`（基类注释为不可为 None；实现可返回 `Optional[DriveFile]`，调用方需做空检查） |
| `upload_file` | `(self, filepath: str, fid: str, *args, **kwargs)` | `bool` |
| `download_file` | `(self, fid: str, save_dir=None, filename=None, filepath=None, overwrite=False, *args, **kwargs)` | `bool` |

**根目录 fid 约定**：不同驱动对“根”的表示可能不同（如 `""`、`"root"`、`"/"`）。调用方应使用驱动文档或 `root_fid` 属性（若已登录）；实现方应在文档中明确本驱动的根 fid。

---

### 1.2 DriveFile 契约

- **必有字段**：`fid` (str)、`name` (str)。
- **推荐字段**：`size` (int, 字节)、`is_dir` (bool)。
- **扩展**：通过 `ext` 或字典形式存放驱动特有字段；消费方不得依赖未在文档中声明的扩展字段。

---

## 2. 配置约定

### 2.1 配置优先级（从高到低）

1. 构造函数显式传入的关键字参数。
2. `funsecret.read_secret(key, namespace="fundrive")`。
3. 环境变量（键名建议：`FUNDRIVE_<DRIVE>_<KEY>`，如 `FUNDRIVE_BAIDU_ACCESS_TOKEN`）。

### 2.2 funsecret 键名约定

- 格式：`fundrive.<drive_name>.<param>`，例如 `fundrive.pan115.cookie_path`。
- namespace 统一使用 `"fundrive"`。

### 2.3 敏感信息

- 不得在日志或异常消息中输出密钥、token、cookie 等。
- 推荐通过 funsecret 或环境变量注入，避免硬编码。

---

## 3. 调用约定

### 3.1 调用方

- **推荐**：核心参数用关键字传递（如 `upload_file(filepath=..., fid=...)`），便于阅读与兼容。
- **兼容**：必须支持按规范签名顺序的位置参数调用（与现有 API 文档一致）。

### 3.2 实现方（各驱动）

- 必须接受并忽略未使用的 `*args, **kwargs`，不得因“多余”关键字参数报错（保证上层传参的兼容性）。
- 新增可选能力只通过 `**kwargs` 增加，且需在驱动 README 或 docstring 中说明。

### 3.3 路径解析

- 下载目标路径：与 `get_filepath(save_dir=..., filename=..., filepath=...)` 语义一致；`filepath` 优先，否则 `save_dir` + `filename`。
- 上传：`filepath` 为本地绝对或相对路径，`fid` 为目标目录 ID。

---

## 4. 向上兼容规则

- **不删除**：任何已对外暴露的方法或参数不删除。
- **不收紧**：已接受的值域/类型不得收紧（例如原先接受 `fid=""` 表示根目录的，不得改为必填非空）。
- **不改变顺序**：规范中列出的位置参数顺序不得改变。
- **可选扩展**：新参数仅能以可选形式加入（默认值保持原有行为）；新方法可加，旧方法签名保持。

---

## 5. 文档与实现对齐

- **API 文档**（如 `docs/API.md`）中的方法说明应与本文档及 `base.py` 一致；若存在差异，以 `base.py` 与本文档为准并更新 API 文档。
- **开发指南**（如 `docs/DEVELOPMENT_GUIDE.md`）中涉及接口的部分应引用本文档，并遵循“必须实现的方法”与“可选方法”的划分。
- 各驱动 `README.md` 应注明：本驱动对根 fid 的约定、支持的 `**kwargs` 扩展、以及任何与通用约定不同的行为。

---

## 6. 修订与生效

- 对本文档的修订需经技术评审，且需在文档中注明**兼容性影响**（无破坏性变更方可直接生效）。
- 实现与文档的不一致问题，优先以本文档和 `base.py` 为准进行修正，并同步更新 `docs/API.md` 与 `docs/DEVELOPMENT_GUIDE.md`。

---

*文档版本：1.0 | 来源：FUN-7 CTO 细化 | 向上兼容*
