import os.path
import subprocess
from typing import Any, List, Dict

from fundrive.core import DriveSystem
from funsecret import read_secret


class WebDavDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super(WebDavDrive, self).__init__(*args, **kwargs)
        self.drive = None

    def login(self, server_url, username, password, *args, **kwargs) -> bool:
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

    def mkdir(self, path, *args, **kwargs) -> bool:
        self.drive.mkdir(path=path)
        return True

    def delete(self, path, *args, **kwargs) -> bool:
        self.drive.remove(path=path)
        return True

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
        self, dir_path="./cache", path=None, overwrite=False, *args, **kwargs
    ) -> bool:
        os.makedirs(dir_path, exist_ok=True)
        self.drive.download_file(
            from_path=path, to_path=f"{dir_path}/{os.path.basename(path)}"
        )
        return True

    def download_dir(
        self, dir_path="./cache", path=None, overwrite=False, *args, **kwargs
    ) -> bool:
        for file in self.get_file_list(path):
            self.download_file(dir_path=f"{dir_path}/{file['name']}", path=file["name"])
        return True

    def upload_file(
        self, file_path="./cache", to_path=None, overwrite=False, *args, **kwargs
    ) -> bool:
        self.drive.upload_file(
            from_path=file_path, to_path=to_path, overwrite=overwrite
        )
        return True

    def upload_dir(
        self, file_path="./cache", path=None, overwrite=False, *args, **kwargs
    ) -> bool:
        return True
