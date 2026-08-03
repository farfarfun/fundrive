"""
FunDrive - 统一云存储接口框架

提供统一的接口来操作20个主流云存储服务，包括Google Drive、OneDrive、
Dropbox、Amazon S3、GitHub、百度网盘、阿里云盘等。

主要特性：
- 🌟 统一的API接口，支持20个云存储服务
- 📁 完整的文件操作功能（上传、下载、删除、搜索等）
- 🔐 多种认证方式（OAuth2、API密钥、Token等）
- 🚀 高性能设计（缓存、连接池、重试机制）
- 🛡️ 完善的错误处理和日志记录
- 📖 详细的文档和示例代码

快速开始：
    >>> from fundrive import get_drive
    >>> drive = get_drive('dropbox', access_token='your_token')
    >>> drive.login()
    >>> drive.upload_file('/local/file.txt', '/', 'remote_file.txt')
"""

# 核心类和接口
from .core import BaseDrive, DriveFile, DriveSnapshot
from .core import BaseDriveTest, create_drive_tester
from .core import copy_data

# 异常类
from .core.exceptions import (
    FunDriveError,
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    RateLimitError,
    FileNotFoundError,
    FileExistsError,
    InsufficientStorageError,
    InvalidParameterError,
    OperationNotSupportedError,
    UploadError,
    DownloadError,
)

# 工具函数
from .core.utils import (
    format_size,
    parse_size,
    sanitize_filename,
    get_file_hash,
    ProgressTracker,
)

# 驱动管理函数
#
# 注意：这里刻意不 import AVAILABLE_DRIVES —— 那会触发对全部 22 个驱动的
# 探测导入，把 boto3/oss2/aligo 等 SDK 全部拖进来。它通过下面的模块级
# __getattr__ 懒加载，语义不变。
from .drives import (
    get_drive,
    list_available_drives,
    list_missing_drives,
    DRIVE_SPECS,
)

# 版本信息 —— 单一来源取自包元数据，避免与 pyproject.toml 漂移
try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    try:
        __version__ = _pkg_version("fundrive")
    except PackageNotFoundError:  # 源码树中直接运行、未安装
        __version__ = "0.0.0.dev0"
except ImportError:  # pragma: no cover
    __version__ = "0.0.0.dev0"

__author__ = "farfarfun"
__email__ = "farfarfun@qq.com"
__description__ = "统一云存储接口框架"

# 导出列表
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    # 核心类和接口
    "BaseDrive",
    "DriveFile",
    "DriveSnapshot",
    "BaseDriveTest",
    "create_drive_tester",
    "copy_data",
    # 异常类
    "FunDriveError",
    "AuthenticationError",
    "AuthorizationError",
    "NetworkError",
    "RateLimitError",
    "FileNotFoundError",
    "FileExistsError",
    "InsufficientStorageError",
    "InvalidParameterError",
    "OperationNotSupportedError",
    "UploadError",
    "DownloadError",
    # 工具函数
    "format_size",
    "parse_size",
    "sanitize_filename",
    "get_file_hash",
    "ProgressTracker",
    # 驱动管理
    "get_drive",
    "list_available_drives",
    "list_missing_drives",
    "AVAILABLE_DRIVES",
    "DRIVE_SPECS",
]


def __getattr__(name: str):
    """懒加载 AVAILABLE_DRIVES，避免 ``import fundrive`` 触发全部 SDK 导入。"""
    if name == "AVAILABLE_DRIVES":
        from .drives import AVAILABLE_DRIVES

        globals()["AVAILABLE_DRIVES"] = AVAILABLE_DRIVES
        return AVAILABLE_DRIVES
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_version():
    """获取版本信息"""
    return __version__


def get_supported_drives():
    """
    获取 fundrive 支持的全部驱动类型名称

    不触发任何驱动导入。需要"当前环境依赖已装好"的子集请用
    :func:`list_available_drives`，需要缺失依赖及其安装命令请用
    :func:`list_missing_drives`。

    Returns:
        list: 支持的驱动类型列表
    """
    return list(DRIVE_SPECS)


def create_drive(drive_type: str, **kwargs):
    """
    创建驱动实例的便捷函数

    Args:
        drive_type (str): 驱动类型
        **kwargs: 驱动配置参数

    Returns:
        BaseDrive: 驱动实例

    Examples:
        >>> drive = create_drive('google', credentials_file='creds.json')
        >>> drive = create_drive('dropbox', access_token='token')
    """
    return get_drive(drive_type, **kwargs)


# 添加便捷函数到导出列表
__all__.extend(
    [
        "get_version",
        "get_supported_drives",
        "create_drive",
    ]
)
