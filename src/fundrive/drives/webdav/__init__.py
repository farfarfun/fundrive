"""WebDAV 网盘驱动模块

``WebDavDrive`` 只依赖核心依赖（requests）。``WebDavDrive4`` 是基于
``webdav4`` 的旧实现，属于可选项——它的 import 在这里必须是可容错的，
否则没装 ``webdav4`` 的环境连纯 requests 的 ``WebDavDrive`` 都拿不到。
"""

from .drive import WebDavDrive

__all__ = ["WebDavDrive"]

try:
    from .drive4 import WebDavDrive4  # noqa: F401
except ImportError:  # pragma: no cover - 仅在未安装 webdav4 时触发
    pass
else:
    __all__.append("WebDavDrive4")
