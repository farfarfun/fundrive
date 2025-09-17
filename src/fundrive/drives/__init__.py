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
    from .baidu import BaiduDrive
except ImportError:
    BaiduDrive = None

try:
    from .alipan import AliPanDrive, AliPanOpenDrive
except ImportError:
    AliPanDrive = None
    AliPanOpenDrive = None

try:
    from .oss import OssDrive
except ImportError:
    OssDrive = None

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
    from .os import LocalDrive
except ImportError:
    LocalDrive = None

# 🔬 学术和专业服务 - 特定用途
try:
    from .zenodo import ZenodoDrive
except ImportError:
    ZenodoDrive = None

try:
    from .tsinghua import TsinghuaDrive
except ImportError:
    TsinghuaDrive = None

try:
    from .openxlab import OpenXLabDrive
except ImportError:
    OpenXLabDrive = None

try:
    from .tianchi import TianchiDrive
except ImportError:
    TianchiDrive = None

try:
    from .wenshushu import WenshushuDrive
except ImportError:
    WenshushuDrive = None

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
    "baidu": BaiduDrive,
    "alipan": AliPanDrive,
    "alipan_open": AliPanOpenDrive,
    "oss": OssDrive,
    # 🔧 通用协议和工具
    "webdav": WebDAVDrive,
    "pcloud": PCloudDrive,
    "mediafire": MediaFireDrive,
    "lanzou": LanzouDrive,
    "local": LocalDrive,
    "os": LocalDrive,  # 本地文件系统别名
    # 🔬 学术和专业服务
    "zenodo": ZenodoDrive,
    "tsinghua": TsinghuaDrive,
    "openxlab": OpenXLabDrive,
    "tianchi": TianchiDrive,
    "wenshushu": WenshushuDrive,
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


def get_drive_info():
    """
    获取所有驱动的详细信息

    Returns:
        dict: 包含驱动分类和描述的信息
    """
    return {
        "🌟 全球主流服务": {
            "google": "Google Drive - 全球最大云存储服务，15GB免费空间",
            "onedrive": "OneDrive - Microsoft云存储，与Office深度集成",
            "dropbox": "Dropbox - 老牌云存储服务，同步稳定",
            "amazon": "Amazon S3 - 企业级对象存储，支持无限扩展",
        },
        "💻 代码托管平台": {
            "github": "GitHub - 全球最大代码托管平台",
            "gitee": "Gitee - 国内领先代码托管平台",
        },
        "🇨🇳 国内主流服务": {
            "baidu": "百度网盘 - 国内最大个人云存储，2TB免费空间",
            "alipan": "阿里云盘 - 阿里巴巴出品，100GB免费空间",
            "oss": "阿里云OSS - 企业级对象存储",
        },
        "🔧 通用协议和工具": {
            "webdav": "WebDAV - 通用协议，支持多种WebDAV服务器",
            "pcloud": "pCloud - 欧洲云存储，10GB免费空间",
            "mediafire": "MediaFire - 国外文件分享平台",
            "lanzou": "蓝奏云 - 轻量级文件分享",
            "local": "本地文件系统 - 本地文件操作统一接口",
        },
        "🔬 学术和专业服务": {
            "zenodo": "Zenodo - 学术数据存储，开放获取",
            "tsinghua": "清华云盘 - 学术共享平台",
            "openxlab": "OpenXLab - AI模型和数据集平台",
            "tianchi": "天池 - 阿里云大数据竞赛平台",
            "wenshushu": "文叔叔 - 临时文件分享",
        },
    }


# 导出所有可用的驱动类
__all__ = [
    # 核心函数
    "get_drive",
    "list_available_drives",
    "get_drive_info",
    "AVAILABLE_DRIVES",
    # 驱动类 - 按流行度排序
    "GoogleDrive",
    "OneDrive",
    "DropboxDrive",
    "S3Drive",
    "GitHubDrive",
    "GiteeDrive",
    "BaiduDrive",
    "AliPanDrive",
    "AliPanOpenDrive",
    "OssDrive",
    "WebDAVDrive",
    "PCloudDrive",
    "MediaFireDrive",
    "LanzouDrive",
    "LocalDrive",
    "ZenodoDrive",
    "TsinghuaDrive",
    "OpenXLabDrive",
    "TianchiDrive",
    "WenshushuDrive",
]

# 过滤掉None值的导出
__all__ = [name for name in __all__ if globals().get(name) is not None]
