from .alipan import AlipanDrive
from .lanzou import LanZouDrive, LanZouSnapshot
from .openxlab import OpenDataLabDrive, OpenXLabDrive
from .os import OSDrive
from .oss import OSSDrive
from .tianchi import TianChiDrive
from .tsinghua import TSingHuaDrive
from .tsinghua import download as download_tsinghua
from .wenshushu import WSSDrive
from .zenodo import ZenodoDrive

__all__ = [
    "TSingHuaDrive",
    "download_tsinghua",
    "TianChiDrive",
    "OSSDrive",
    "ZenodoDrive",
    "OpenXLabDrive",
    "OpenDataLabDrive",
    "LanZouDrive",
    "LanZouSnapshot",
    "WSSDrive",
    "AlipanDrive",
    "OSDrive",
]
