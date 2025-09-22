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
from .drives import (
    get_drive,
    list_available_drives,
    AVAILABLE_DRIVES,
)

# 版本信息
__version__ = "2.0.39"
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
    "AVAILABLE_DRIVES",
]


def get_version():
    """获取版本信息"""
    return __version__


def get_supported_drives():
    """
    获取支持的驱动列表

    Returns:
        list: 支持的驱动类型列表
    """
    return list(AVAILABLE_DRIVES.keys())


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
