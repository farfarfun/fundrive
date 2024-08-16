import os.path
import subprocess
from typing import List

from fundrive.core import BaseDrive
from fundrive.core.base import DriveFile
from funsecret import read_secret


class WebDavDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(WebDavDrive, self).__init__(*args, **kwargs)
        self.drive = None

    def login(
        self, server_url=None, username=None, password=None, *args, **kwargs
    ) -> bool:
        server_url = server_url or read_secret(
            "fundrive", "webdav", "alipan", "server_url"
        )
        username = username or read_secret("fundrive", "webdav", "alipan", "username")
        password = password or read_secret("fundrive", "webdav", "alipan", "password")
        if not server_url or not username or not password:
            raise Exception("server_url, username, password is None")
        try:
            from webdav4.client import Client
        except Exception as e:
            subprocess.check_call(["pip", "install", "fundrive-webdav"])
            from webdav4.client import Client
        self.drive = Client(server_url, auth=(username, password))
        return True

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        path = str(os.path.join(fid, name))
        self.drive.mkdir(path=path)
        return path

    def delete(self, fid, *args, **kwargs) -> bool:
        self.drive.remove(path=fid)
        return True

    def exist(self, fid, *args, **kwargs) -> bool:
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

    def download_file(self, fid, local_dir, overwrite=False, *args, **kwargs) -> bool:
        local_path = os.path.join(local_dir, os.path.basename(fid))
        os.makedirs(local_dir, exist_ok=True)
        if os.path.exists(local_path) and not overwrite:
            return False
        if not self.exist(fid):
            return False
        self.drive.download_file(from_path=fid, to_path=local_path)
        return True

    def upload_file(
        self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if self.exist(fid) and not overwrite:
            return False
        self.drive.upload_file(
            from_path=local_path,
            to_path=os.path.join(fid, os.path.basename(local_path)),
            overwrite=overwrite,
        )
        return True
