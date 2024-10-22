import logging

from .drives import AlipanDrive, LanZouDrive, LanZouSnapshot, OpenDataLabDrive, OSSDrive, TianChiDrive, TSingHuaDrive
from .fungit import GiteeDrive, GithubDrive

logger = logging.getLogger("fundrive")


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
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
