"""
FunDrive 统一云存储驱动模块

支持20个主流云存储服务的统一接口操作
按流行度和使用频率排序，方便用户快速找到合适的驱动
"""

# 🌟 全球主流服务 - 最受欢迎的云存储服务
try:
    from .google import GoogleDrive
except ImportError:
    GoogleDrive = None

try:
    from .onedrive import OneDrive
except ImportError:
    OneDrive = None

try:
    from .dropbox import DropboxDrive
except ImportError:
    DropboxDrive = None

try:
    from .amazon import S3Drive
except ImportError:
    S3Drive = None

# 💻 代码托管平台 - 开发者常用
try:
    from .github import GitHubDrive
except ImportError:
    GitHubDrive = None

try:
    from .gitee import GiteeDrive
except ImportError:
    GiteeDrive = None

# 🇨🇳 国内主流服务 - 国内用户首选
try:
    from .baidu import BaiDuDrive
except ImportError:
    BaiDuDrive = None

try:
    from .alipan import AliPanDrive, AliPanOpenDrive
except ImportError:
    AliPanDrive = None
    AliPanOpenDrive = None

try:
    from .oss import OssDrive
except ImportError:
    OssDrive = None

try:
    from .ossutil import OSSUtilDrive
except ImportError:
    OSSUtilDrive = None

# 🔧 通用协议和工具 - 兼容性强
try:
    from .webdav import WebDAVDrive
except ImportError:
    WebDAVDrive = None

try:
    from .pcloud import PCloudDrive
except ImportError:
    PCloudDrive = None

try:
    from .mediafire import MediaFireDrive
except ImportError:
    MediaFireDrive = None

try:
    from .lanzou import LanzouDrive
except ImportError:
    LanzouDrive = None

try:
    from .os import OSDrive, LocalDrive
except ImportError:
    OSDrive = None
    LocalDrive = None

# 🔬 学术和专业服务 - 特定用途
try:
    from .zenodo import ZenodoDrive
except ImportError:
    ZenodoDrive = None

try:
    from .tsinghua import TSingHuaDrive
except ImportError:
    TSingHuaDrive = None

try:
    from .openxlab import OpenXLabDrive
except ImportError:
    OpenXLabDrive = None

try:
    from .tianchi import TianChiDrive
except ImportError:
    TianChiDrive = None

try:
    from .wenshushu import WSSDrive
except ImportError:
    WSSDrive = None

# 驱动注册表 - 按流行度排序
AVAILABLE_DRIVES = {
    # 🌟 全球主流服务
    "google": GoogleDrive,
    "onedrive": OneDrive,
    "dropbox": DropboxDrive,
    "amazon": S3Drive,
    "s3": S3Drive,  # S3别名
    # 💻 代码托管平台
    "github": GitHubDrive,
    "gitee": GiteeDrive,
    # 🇨🇳 国内主流服务
    "baidu": BaiDuDrive,
    "alipan": AliPanDrive,
    "alipan_open": AliPanOpenDrive,
    "oss": OssDrive,
    "ossutil": OSSUtilDrive,
    # 🔧 通用协议和工具
    "webdav": WebDAVDrive,
    "pcloud": PCloudDrive,
    "mediafire": MediaFireDrive,
    "lanzou": LanzouDrive,
    "local": LocalDrive,
    "os": LocalDrive,  # 本地文件系统别名
    # 🔬 学术和专业服务
    "zenodo": ZenodoDrive,
    "tsinghua": TSingHuaDrive,
    "openxlab": OpenXLabDrive,
    "tianchi": TianChiDrive,
    "wenshushu": WSSDrive,
}

# 过滤掉未安装的驱动
AVAILABLE_DRIVES = {k: v for k, v in AVAILABLE_DRIVES.items() if v is not None}


def get_drive(drive_type: str, *args, **kwargs):
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
    drive_type = drive_type.lower()

    if drive_type not in AVAILABLE_DRIVES:
        available = ", ".join(sorted(AVAILABLE_DRIVES.keys()))
        raise ValueError(f"不支持的驱动类型: {drive_type}. 可用驱动: {available}")

    drive_class = AVAILABLE_DRIVES[drive_type]
    if drive_class is None:
        raise ImportError(
            f"驱动 {drive_type} 的依赖未安装，请运行: pip install fundrive[{drive_type}]"
        )

    return drive_class(*args, **kwargs)


def list_available_drives():
    """
    列出所有可用的驱动类型

    Returns:
        dict: 驱动类型到驱动类的映射
    """
    return AVAILABLE_DRIVES.copy()


# 导出所有可用的驱动类
__all__ = [
    # 核心函数
    "get_drive",
    "list_available_drives",
    "AVAILABLE_DRIVES",
    # 驱动类 - 按流行度排序
    "GoogleDrive",
    "OneDrive",
    "DropboxDrive",
    "S3Drive",
    "GitHubDrive",
    "GiteeDrive",
    "BaiDuDrive",
    "AliPanDrive",
    "AliPanOpenDrive",
    "OssDrive",
    "OSSUtilDrive",
    "WebDAVDrive",
    "PCloudDrive",
    "MediaFireDrive",
    "LanzouDrive",
    "OSDrive",
    "LocalDrive",
    "ZenodoDrive",
    "TSingHuaDrive",
    "OpenXLabDrive",
    "TianChiDrive",
    "WSSDrive",
]

# 过滤掉None值的导出
__all__ = [name for name in __all__ if globals().get(name) is not None]
