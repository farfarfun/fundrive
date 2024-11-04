from .alipan import AlipanDrive
from .lanzou import LanZouDrive, LanZouSnapshot
from .opendatalab import OpenDataLabDrive
from .os import OSDrive
from .oss import OSSDrive
from .tianchi import TianChiDrive
from .tsinghua import TSingHuaDrive
from .tsinghua import download as download_tsinghua
from .wenshushu import WSSDrive

__all__ = [
    "TSingHuaDrive",
    "download_tsinghua",
    "TianChiDrive",
    "OSSDrive",
    "OpenDataLabDrive",
    "LanZouDrive",
    "LanZouSnapshot",
    "WSSDrive",
    "AlipanDrive",
    "OSDrive",
]
