"""
FunDrive 统一云存储驱动模块

驱动按需懒加载：``import fundrive`` 不会导入任何第三方 SDK，
只有真正取用某个驱动时才导入它的依赖。

设计要点
--------
* :data:`DRIVE_SPECS` 是唯一的事实来源（驱动 key -> 模块/类名/pip extra）。
* 类名拼写错误会**立即抛出** :class:`ImportError`，不再被"依赖没装"掩盖。
  历史上 ``oss``/``webdav``/``lanzou``/``alipan``/``alipan_open`` 五个驱动
  因为注册表里的类名拼错而永久不可用，且因为整段 import 被
  ``except ImportError`` 包住，没有任何报错——本模块的结构就是为了让这类
  错误不可能再静默发生。
* 依赖缺失会抛出带正确 ``pip install`` 提示的 :class:`ImportError`。
"""

import importlib
from typing import Any, Dict, NamedTuple, Optional, Type


class DriveSpec(NamedTuple):
    """一个驱动的加载说明。"""

    module: str
    """相对模块路径，如 ``.oss``。"""

    cls: str
    """模块中导出的驱动类名。"""

    extra: Optional[str] = None
    """安装该驱动所需的 pip extra；``None`` 表示只依赖核心依赖。"""

    pip_target: Optional[str] = None
    """``pip install`` 的目标覆写；默认是 ``fundrive[<extra>]``。"""

    @property
    def install_hint(self) -> str:
        if self.pip_target:
            return self.pip_target
        if self.extra:
            return f"fundrive[{self.extra}]"
        return "fundrive"


# 驱动注册表 —— 按流行度排序。
#
# extra=None 表示该驱动只用到核心依赖（requests / orjson / funget / tqdm /
# nltlog / funsecret），无需额外安装。注意 pyproject 里的 github/gitee/
# onedrive/tsinghua extra 只包含核心依赖，属于空 extra，因此这里标 None。
DRIVE_SPECS: Dict[str, DriveSpec] = {
    # 🌟 全球主流服务
    "google": DriveSpec(".google", "GoogleDrive", "google"),
    "onedrive": DriveSpec(".onedrive", "OneDrive"),
    "dropbox": DriveSpec(".dropbox", "DropboxDrive", "dropbox"),
    "amazon": DriveSpec(".amazon", "S3Drive", "amazon"),
    "s3": DriveSpec(".amazon", "S3Drive", "amazon"),
    # 💻 代码托管平台
    "github": DriveSpec(".github", "GitHubDrive"),
    "gitee": DriveSpec(".gitee", "GiteeDrive"),
    # 🇨🇳 国内主流服务
    "baidu": DriveSpec(".baidu", "BaiDuDrive", "baidu"),
    "alipan": DriveSpec(".alipan", "AlipanDrive", "alipan"),
    "alipan_open": DriveSpec(".alipan", "AliopenDrive", "alipan"),
    "pan115": DriveSpec(".pan115", "Pan115Drive", "pan115"),
    "115": DriveSpec(".pan115", "Pan115Drive", "pan115"),
    "oss": DriveSpec(".oss", "OSSDrive", "oss"),
    "ossutil": DriveSpec(".ossutil", "OSSUtilDrive", "ossutil"),
    # 🔧 通用协议和工具
    "webdav": DriveSpec(".webdav", "WebDavDrive"),
    "pcloud": DriveSpec(".pcloud", "PCloudDrive"),
    "mediafire": DriveSpec(".mediafire", "MediaFireDrive"),
    "lanzou": DriveSpec(".lanzou", "LanZouDrive", "lanzou"),
    "local": DriveSpec(".os", "LocalDrive"),
    "os": DriveSpec(".os", "LocalDrive"),
    # 🔬 学术和专业服务
    "zenodo": DriveSpec(".zenodo", "ZenodoDrive"),
    "tsinghua": DriveSpec(".tsinghua", "TSingHuaDrive"),
    "openxlab": DriveSpec(".openxlab", "OpenXLabDrive"),
    "tianchi": DriveSpec(".tianchi", "TianChiDrive"),
    "wenshushu": DriveSpec(".wenshushu", "WSSDrive", "wenshushu"),
}

# 类名 -> spec，供 ``from fundrive.drives import OSSDrive`` 懒加载使用。
_CLASS_SPECS: Dict[str, DriveSpec] = {spec.cls: spec for spec in DRIVE_SPECS.values()}
_CLASS_SPECS["OSDrive"] = DriveSpec(".os", "OSDrive")

_resolved: Dict[str, Type[Any]] = {}


def _load(spec: DriveSpec) -> Type[Any]:
    """导入并返回驱动类。

    Raises:
        ImportError: 依赖缺失（带 pip 提示），或注册表类名有误（视为 bug）。
    """
    cache_key = f"{spec.module}:{spec.cls}"
    if cache_key in _resolved:
        return _resolved[cache_key]

    try:
        module = importlib.import_module(spec.module, __name__)
    except ImportError as exc:
        missing = getattr(exc, "name", None) or "?"
        raise ImportError(
            f"驱动 {spec.cls} 的依赖 {missing!r} 未安装，"
            f"请运行: pip install {spec.install_hint}"
        ) from exc

    try:
        drive_cls = getattr(module, spec.cls)
    except AttributeError as exc:
        # 注册表和驱动模块不一致 —— 这是 fundrive 自身的 bug，必须大声报错，
        # 绝不能像历史实现那样被当成"依赖没装"而静默丢弃。
        exported = ", ".join(sorted(n for n in vars(module) if n.endswith("Drive")))
        raise ImportError(
            f"fundrive 内部错误：模块 {spec.module} 没有导出 {spec.cls!r}。"
            f"该模块实际导出的驱动类为: {exported or '(无)'}。"
            f"请修正 fundrive/drives/__init__.py 中的 DRIVE_SPECS。"
        ) from exc

    _resolved[cache_key] = drive_cls
    return drive_cls


def get_drive(drive_type: str, *args: Any, **kwargs: Any):
    """
    根据驱动类型获取驱动实例

    Args:
        drive_type (str): 驱动类型名称
        *args: 传递给驱动构造函数的位置参数
        **kwargs: 传递给驱动构造函数的关键字参数

    Returns:
        BaseDrive: 驱动实例

    Raises:
        ValueError: 不支持的驱动类型
        ImportError: 驱动依赖未安装

    Examples:
        >>> drive = get_drive('google', credentials_file='path/to/creds.json')
        >>> drive = get_drive('dropbox', access_token='your_token')
        >>> drive = get_drive('s3', access_key_id='key', secret_access_key='secret')
    """
    key = drive_type.lower()
    spec = DRIVE_SPECS.get(key)
    if spec is None:
        available = ", ".join(sorted(DRIVE_SPECS))
        raise ValueError(f"不支持的驱动类型: {drive_type}. 可用驱动: {available}")

    return _load(spec)(*args, **kwargs)


def list_available_drives() -> Dict[str, Type[Any]]:
    """
    列出当前环境中依赖已装好、可以直接实例化的驱动

    注意：这会尝试导入每个驱动，因此有一定开销。只需要驱动名称时请用
    ``DRIVE_SPECS.keys()``，无需任何导入。

    Returns:
        dict: 驱动类型到驱动类的映射
    """
    result: Dict[str, Type[Any]] = {}
    for key, spec in DRIVE_SPECS.items():
        try:
            result[key] = _load(spec)
        except ImportError:
            continue
    return result


# 向后兼容的别名
list_installed_drives = list_available_drives


def list_missing_drives() -> Dict[str, str]:
    """
    列出依赖缺失的驱动及其安装命令

    Returns:
        dict: 驱动类型到 ``pip install`` 目标的映射
    """
    missing: Dict[str, str] = {}
    for key, spec in DRIVE_SPECS.items():
        try:
            _load(spec)
        except ImportError:
            missing[key] = spec.install_hint
    return missing


def __getattr__(name: str) -> Any:
    """按需加载模块属性。

    * 驱动类名 —— 只导入该驱动，使 ``from fundrive.drives import OSSDrive``
      不必预先导入其它 21 个 SDK。
    * ``AVAILABLE_DRIVES`` —— 首次访问时才做一次全量探测并缓存。语义与
      2.0.80 完全一致（普通 dict，只含依赖已装好的驱动），但不再在
      ``import fundrive`` 时就把所有 SDK 拖进来。
    """
    if name == "AVAILABLE_DRIVES":
        registry = list_available_drives()
        globals()["AVAILABLE_DRIVES"] = registry  # 缓存，后续走正常属性查找
        return registry

    spec = _CLASS_SPECS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return _load(spec)


def __dir__():
    return sorted(__all__)


__all__ = [
    # 核心函数
    "get_drive",
    "list_available_drives",
    "list_installed_drives",
    "list_missing_drives",
    "AVAILABLE_DRIVES",
    "DRIVE_SPECS",
    "DriveSpec",
    # 驱动类 - 按流行度排序
    "GoogleDrive",
    "OneDrive",
    "DropboxDrive",
    "S3Drive",
    "GitHubDrive",
    "GiteeDrive",
    "BaiDuDrive",
    "AlipanDrive",
    "AliopenDrive",
    "Pan115Drive",
    "OSSDrive",
    "OSSUtilDrive",
    "WebDavDrive",
    "PCloudDrive",
    "MediaFireDrive",
    "LanZouDrive",
    "OSDrive",
    "LocalDrive",
    "ZenodoDrive",
    "TSingHuaDrive",
    "OpenXLabDrive",
    "TianChiDrive",
    "WSSDrive",
]
