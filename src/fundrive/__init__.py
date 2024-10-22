import logging

from .drives import AlipanDrive, LanZouDrive, LanZouSnapshot, OpenDataLabDrive, OSSDrive, TianChiDrive, TSingHuaDrive
from .fungit import GiteeDrive, GithubDrive

logger = logging.getLogger("fundrive")
logger.setLevel(level=logging.INFO)
__all__ = [
    "LanZouDrive",
    "OSSDrive",
    "TianChiDrive",
    "TSingHuaDrive",
    "OpenDataLabDrive",
    "GithubDrive",
    "LanZouDrive",
    "LanZouSnapshot",
    "GiteeDrive",
    "AlipanDrive",
]
