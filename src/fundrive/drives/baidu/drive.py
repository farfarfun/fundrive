import os
import re
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Set

from fundrives.baidu import BaiduPCSApi, BaiduPCSError, PcsFile, PcsSharedPath
from funget import simple_download
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


def convert(file: PcsFile) -> DriveFile:
    return DriveFile(
        fid=file.path,
        name=os.path.basename(file.path),
        size=file.size,
        ext=file._asdict(),
    )


SHARED_URL_PREFIX = "https://pan.baidu.com/s/"


def _unify_shared_url(url: str) -> str:
    """Unify input shared url"""

    # For Standard url
    temp = r"pan\.baidu\.com/s/(.+?)(\?|$)"
    m = re.search(temp, url)
    if m:
        return SHARED_URL_PREFIX + m.group(1)

    # For surl url
    temp = r"baidu\.com.+?\?surl=(.+?)(\?|$)"
    m = re.search(temp, url)
    if m:
        return SHARED_URL_PREFIX + "1" + m.group(1)

    raise ValueError(f"The shared url is not a valid url. {url}")


class BaiDuDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(BaiDuDrive, self).__init__(*args, **kwargs)
        self.drive: BaiduPCSApi = None

    def login(self, bduss, stoken, ptoken, *args, **kwargs) -> bool:
        self.drive = BaiduPCSApi(bduss=bduss, stoken=stoken, ptoken=ptoken)
        return True

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        path = f"{fid}/{name}"
        self.drive.makedir(path)
        return path

    def delete(self, fid, *args, **kwargs) -> bool:
        return self.drive.remove(fid)

    def exist(self, fid, *args, **kwargs) -> bool:
        return self.drive.exists(fid)

    def upload_file(
        self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        with open(local_path, "rb") as f:
            self.drive.upload_file(f, remotepath=fid)
        return True

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        return convert(self.drive.meta(fid)[0]) if self.drive.is_file(fid) else None

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        return convert(self.drive.meta(fid)[0]) if self.drive.is_dir(fid) else None

    def get_file_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        return [convert(file) for file in self.drive.list(fid) if file.is_file]

    def get_dir_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        return [convert(file) for file in self.drive.list(fid) if file.is_dir]

    def download_file(self, fid, local_dir, overwrite=False, *args, **kwargs) -> bool:
        link = self.drive.download_link(fid)

        headers = {
            "User-Agent": "softxm;netdisk",
            "Connection": "Keep-Alive",
            "Cookie": f"BDUSS={self.drive.bduss};ptoken={self.drive.ptoken}",
        }
        try:
            simple_download(
                link,
                filepath=f"{local_dir}/{os.path.basename(fid)}",
                headers=headers,
                overwrite=overwrite,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to download file {fid}: {e}")
            return False

    def save_shared(
        self, shared_url: str, remote_dir: str, password: Optional[str] = None
    ):
        shared_url = _unify_shared_url(shared_url)

        if password:
            self.drive.access_shared(
                shared_url,
                password,
            )

        shared_paths = deque(self.drive.shared_paths(shared_url))
        _remote_dirs: Dict[PcsSharedPath, str] = dict(
            [(sp, remote_dir) for sp in shared_paths]
        )
        _dir_exists: Set[str] = set()

        while shared_paths:
            shared_path = shared_paths.popleft()
            rd = _remote_dirs[shared_path]

            # Make sure remote dir exists
            if rd not in _dir_exists:
                if not self.drive.exists(rd):
                    self.drive.makedir(rd)
                _dir_exists.add(rd)

            if shared_path.is_file and self.remote_path_exists(
                PurePosixPath(shared_path.path).name, rd
            ):
                logger.warning(f"{shared_path.path} has be in {rd}")
                continue

            uk, share_id, bdstoken = (
                shared_path.uk,
                shared_path.share_id,
                shared_path.bdstoken,
            )

            try:
                self.drive.transfer_shared_paths(
                    rd, [shared_path.fs_id], uk, share_id, bdstoken, shared_url
                )
                logger.info(f"save: {shared_path.path} to {rd}")
                continue
            except BaiduPCSError as err:
                if err.error_code == 12:
                    logger.warning(
                        f"error_code: {err.error_code},文件已经存在, {shared_path.path} has be in {rd}"
                    )
                elif err.error_code == -32:
                    logger.error(f"error_code:{err.error_code} 剩余空间不足，无法转存")
                elif err.error_code == -33:
                    logger.error(
                        f"error_code:{err.error_code} 一次支持操作999个，减点试试吧"
                    )
                elif err.error_code == 4:
                    logger.error(
                        f"error_code:{err.error_code} share transfer pcs error"
                    )
                elif err.error_code == 130:
                    logger.error(f"error_code:{err.error_code} 转存文件数超限")
                elif err.error_code == 120:
                    logger.error(f"error_code:{err.error_code} 转存文件数超限")
                else:
                    logger.error(f"error_code:{err.error_code}:{err}")
                    raise err

            if shared_path.is_dir:
                sub_paths = self.list_all_sub_paths(
                    shared_path.path, uk, share_id, bdstoken
                )
                rd = (Path(rd) / os.path.basename(shared_path.path)).as_posix()
                for sp in sub_paths:
                    _remote_dirs[sp] = rd
                shared_paths.extendleft(sub_paths[::-1])

    def remote_path_exists(
        self, name: str, rd: str, _cache: Dict[str, Set[str]] = {}
    ) -> bool:
        names = _cache.get(rd)
        if not names:
            names = set([PurePosixPath(sp.path).name for sp in self.drive.list(rd)])
            _cache[rd] = names
        return name in names

    def list_all_sub_paths(
        self, shared_path: str, uk: int, share_id: int, bdstoken: str, size=100
    ) -> List[PcsSharedPath]:
        sub_paths = []
        for page in range(1, 1000):
            sps = self.drive.list_shared_paths(
                shared_path, uk, share_id, bdstoken, page=page, size=size
            )
            sub_paths += sps
            if len(sps) < 100:
                break
        return sub_paths
