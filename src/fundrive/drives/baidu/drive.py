import os
from typing import List, Optional

from fundrives.baidu import BaiduPCSApi, PcsFile
from funget import download
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
            download(
                link,
                filepath=f"{local_dir}/{os.path.basename(fid)}",
                headers=headers,
                overwrite=overwrite,
                *args,
                **kwargs,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to download file {fid}: {e}")
            return False

    def save_shared(
        self, shared_url: str, remote_dir: str, password: Optional[str] = None
    ):
        return self.drive.save_shared(shared_url, remote_dir, password=password)
