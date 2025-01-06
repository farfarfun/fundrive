import os
from typing import List, Optional

from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath
from fundrives.baidu import BaiduPCSApi, PcsFile
from funget import download
from funsecret import read_secret
from funutil import getLogger

logger = getLogger("fundrive")


def convert(file: PcsFile) -> DriveFile:
    return DriveFile(
        fid=file.path,
        name=os.path.basename(file.path),
        size=file.size,
        ext=file._asdict(),
    )


class BaiDuDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(BaiDuDrive, self).__init__(*args, **kwargs)
        self.drive: BaiduPCSApi = None

    def login(self, bduss=None, stoken=None, ptoken=None, *args, **kwargs) -> bool:
        bduss = bduss or read_secret("fundrive", "baidu", "bduss")
        stoken = stoken or read_secret("fundrive", "baidu", "stoken")
        ptoken = ptoken or read_secret("fundrive", "baidu", "ptoken")
        self.drive = BaiduPCSApi(bduss=bduss, stoken=stoken, ptoken=ptoken)
        return True

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        dir_map = dict([(file.name, file.fid) for file in self.get_dir_list(fid=fid)])
        if name in dir_map:
            logger.info(f"name={name} exists, return fid={fid}")
            return dir_map[name]
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

    def download_file(
        self,
        fid,
        local_dir,
        filedir=None,
        filename=None,
        filepath=None,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        link = self.drive.download_link(fid)

        headers = {
            "User-Agent": "softxm;netdisk",
            "Connection": "Keep-Alive",
            "Cookie": f"BDUSS={self.drive.bduss};ptoken={self.drive.ptoken}",
        }
        try:
            filepath = get_filepath(filedir or local_dir, filename, filepath)
            download(
                link,
                filepath=filepath or f"{local_dir}/{filename or os.path.basename(fid)}",
                headers=headers,
                overwrite=overwrite,
                *args,
                **kwargs,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to download file {fid}: {e}")
            return False

    def share(self, *fids: str, password: str, expire_days: int = 0, description=""):
        self.drive.share(*fids, password=password, period=expire_days)

    def save_shared(
        self, shared_url: str, remote_dir: str, password: Optional[str] = None
    ):
        return self.drive.save_shared(shared_url, remote_dir, password=password)
