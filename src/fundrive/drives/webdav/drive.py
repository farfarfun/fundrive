import os.path
import subprocess
from typing import Any, List, Dict

from fundrive.core import BaseDrive
from funsecret import read_secret


class WebDavDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(WebDavDrive, self).__init__(*args, **kwargs)
        self.drive = None

    def login(self, server_url=None, username=None, password=None, *args, **kwargs) -> bool:
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

    def mkdir(self, path, exist_ok=True, *args, **kwargs) -> bool:
        self.drive.mkdir(path=path)
        return True

    def delete(self, path, *args, **kwargs) -> bool:
        self.drive.remove(path=path)
        return True

    def exist(self, path, *args, **kwargs) -> bool:
        return self.drive.exists(path)

    def get_file_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        return [file for file in self.drive.ls(path=path) if file["type"] == "file"]

    def get_dir_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        return [
            file for file in self.drive.ls(path=path) if file["type"] == "directory"
        ]

    def get_file_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        return self.drive.info(path)

    def get_dir_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        return self.drive.info(path)

    def download_file(
        self, local_path, drive_path, overwrite=False, *args, **kwargs
    ) -> bool:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if os.path.exists(local_path) and not overwrite:
            return False
        if not self.exist(drive_path):
            return False
        self.drive.download_file(from_path=drive_path, to_path=local_path)
        return True

    def upload_file(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if self.exist(drive_path) and not overwrite:
            return False

        self.drive.upload_file(
            from_path=local_path, to_path=drive_path, overwrite=overwrite
        )
        return True
