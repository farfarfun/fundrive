import os.path
import subprocess
from typing import Any, List, Dict

from fundrive.core import DriveSystem


class WebDavDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super(WebDavDrive, self).__init__(*args, **kwargs)
        from webdav4.client import Client

        self.drive = None  # Client("")

    def login(self, server_url, username, password, *args, **kwargs) -> bool:
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
        return self.drive.ls(path=path)

    def get_dir_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        return self.drive.ls(path)

    def get_file_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        return self.drive.info(path)

    def get_dir_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        return self.drive.info(path)

    def download_file(
        self, dir_path="./cache", path=None, overwrite=False, *args, **kwargs
    ) -> bool:
        self.drive.download_file(
            from_path=path, to_path=f"{dir_path}/{os.path.basename(path)}"
        )
        return True

    def download_dir(
        self, dir_path="./cache", path=None, overwrite=False, *args, **kwargs
    ) -> bool:
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


drive = WebDavDrive()
drive.login(
    server_url="https://openapi.alipan.com", username="fwWsC4", password="jfm6A3"
)
print(drive.get_file_list(""))
