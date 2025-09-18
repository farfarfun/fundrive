import os.path
from typing import List, Optional

from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile
from webdav4.client import Client

logger = getLogger("fundrive")


class WebDavDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(WebDavDrive, self).__init__(*args, **kwargs)
        self.drive = None

    def login(
        self, server_url=None, username=None, password=None, *args, **kwargs
    ) -> bool:
        server_url = server_url or read_secret("fundrive", "webdav", "server_url")
        username = username or read_secret("fundrive", "webdav", "username")
        password = password or read_secret("fundrive", "webdav", "password")
        if not server_url or not username or not password:
            raise Exception("server_url, username, password is None")

        self.drive = Client(server_url, auth=(username, password))
        return True

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        dir_map = dict([(file.name, file.fid) for file in self.get_dir_list(fid=fid)])
        if name in dir_map:
            logger.info(f"name={name} exists, return fid={fid}")
            return dir_map[name]
        path = str(os.path.join(fid, name))
        self.drive.mkdir(path=path)
        return path

    def delete(self, fid, *args, **kwargs) -> bool:
        self.drive.remove(path=fid)
        return True

    def exist(self, fid: str, *args, **kwargs) -> bool:
        return self.drive.exists(fid)

    def get_file_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        result = []
        for file in self.drive.ls(path=fid):
            if file["type"] == "file":
                result.append(
                    DriveFile(
                        fid=file["name"],
                        name=os.path.basename(file["name"]),
                        size=file["content_length"],
                    )
                )

        return result

    def get_dir_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        result = []
        for file in self.drive.ls(path=fid):
            if file["type"] == "directory":
                result.append(
                    DriveFile(
                        fid=file["name"],
                        name=os.path.basename(file["name"]),
                        size=file["content_length"],
                    )
                )

        return result

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.info(fid)
        return DriveFile(
            fid=res["name"],
            name=os.path.basename(res["name"]),
            size=res["content_length"],
        )

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.info(fid)
        return DriveFile(
            fid=res["name"],
            name=os.path.basename(res["name"]),
            size=res["content_length"],
        )

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载单个文件

        Args:
            fid: 文件ID（远程路径）
            save_dir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 下载是否成功
        """
        # 确定保存路径
        if filepath:
            local_path = filepath
        elif save_dir and filename:
            local_path = os.path.join(save_dir, filename)
        elif save_dir:
            local_path = os.path.join(save_dir, os.path.basename(fid))
        else:
            local_path = os.path.basename(fid)

        # 确保目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # 检查文件是否已存在
        if os.path.exists(local_path) and not overwrite:
            return False

        # 检查远程文件是否存在
        if not self.exist(fid):
            return False

        # 执行下载
        self.drive.download_file(from_path=fid, to_path=local_path)
        return True

    def upload_file(
        self, filepath: str, fid: str, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if self.exist(fid) and not overwrite:
            logger.warning(f"File {fid} already exists, skipping upload")
            return False
        logger.info(f"Uploading {filepath} to {fid}")
        self.drive.upload_file(
            from_path=filepath,
            to_path=os.path.join(fid, os.path.basename(filepath)),
            overwrite=overwrite,
        )
        return True
