from typing import Any, List, Dict

import requests
from fundrive.core import DriveSystem
from fundrive.download import simple_download


class TSingHuaDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def __get_url(share_key=None, path=""):
        return f"https://cloud.tsinghua.edu.cn/api/v2.1/share-links/{share_key}/dirents/?path={path}"

    def get_dir_list(self, share_key=None, path="", *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        with requests.Session() as sess:
            r = sess.get(self.__get_url(share_key, path))
            objects = r.json()["dirent_list"]
            for obj in objects:
                if obj["is_dir"]:
                    result.append(
                        {
                            "name": obj["folder_name"],
                            "time": obj["last_modified"],
                            "size": obj["size"],
                            "path": obj["folder_path"],
                        }
                    )
        return result

    def get_file_list(self, share_key=None, path="", pwd=None, *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        with requests.Session() as sess:
            r = sess.get(self.__get_url(share_key, path))
            objects = r.json()["dirent_list"]
            for obj in objects:
                if not obj["is_dir"]:
                    result.append(
                        {
                            "name": obj["file_name"],
                            "time": obj["last_modified"],
                            "size": obj["size"],
                            "path": obj["file_path"],
                        }
                    )
        return result

    def download_file(self, dir_path="./cache", overwrite=False, share_key=None, path="", *args, **kwargs) -> bool:
        file_url = f"https://cloud.tsinghua.edu.cn/d/{share_key}/files/?p={path}&dl=1"
        return simple_download(url=file_url, filepath=f"{dir_path}/{path}")

    def download_dir(self, dir_path="./cache", overwrite=False, share_key=None, path="", *args, **kwargs) -> bool:
        file_list = self.get_file_list(share_key=share_key, path=path)
        dir_list = self.get_dir_list(share_key=share_key, path=path)

        for file in file_list:
            self.download_file(dir_path=dir_path, share_key=share_key, path=file["path"], overwrite=overwrite)
        for file in dir_list:
            self.download_dir(dir_path=dir_path, share_key=share_key, path=file["path"], overwrite=overwrite)
        return True


def download(share_key, dir_path=".cache", path="/", is_dir=True, overwrite=False, *args, **kwargs):
    drive = TSingHuaDrive()
    if is_dir:
        drive.download_dir(share_key=share_key, dir_path=dir_path, path=path, overwrite=overwrite, *args, **kwargs)
    else:
        drive.download_file(share_key=share_key, dir_path=dir_path, path=path, overwrite=overwrite, *args, **kwargs)
