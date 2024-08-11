import os
from typing import Any, List, Dict

from aligo import Aligo
from fundrive.core import DriveSnapshot
from fundrive.core import DriveSystem
from funfile.compress import tarfile
from tqdm import tqdm


class ProgressWrap:
    def __init__(self, callback: tqdm = None):
        self.callback = callback
        self.last_size = 0

    def init(self, file_name, total_size):
        if self.callback is None:
            self.callback = tqdm(unit="B", unit_scale=True, unit_divisor=1024, desc=file_name, total=total_size)

    def update(self, now_size):
        self.callback.update(now_size - self.last_size)
        self.last_size = now_size


class ALiDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super(ALiDrive, self).__init__(*args, **kwargs)
        # self.drive = None
        self.drive = Aligo()

    def login_with_refresh_token(self, refresh_token=None):
        # 特别注意：登录完后请在下次使用之前，删除此参数，因为理论上 refresh_token 只能用一次。
        # 如果不删除会导致，第二次使用无效的 refresh_token 登录，登录失败，并且可能覆盖第一次录成功的信息
        self.drive = Aligo(refresh_token=refresh_token)

    def login(self) -> bool:
        self.drive = Aligo()
        return True

    def mkdir(self, path, fid=None, *args, **kwargs) -> bool:
        return self.drive.mkdir(fid, path, *args, **kwargs) == 0

    def delete(self, fid=None, *args, **kwargs) -> bool:
        return self.drive.delete(fid, *args, **kwargs) == 0

    def get_file_list(self, fid=None, *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        for item in self.drive.get_file_list(parent_file_id=fid):
            if item.type == "file":
                result.append({"fid": item.file_id, "name": item.name, "pid": item.parent_file_id})
        return result

    def get_dir_list(self, fid=None, url=None, pwd=None, *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        for item in self.drive.get_file_list(parent_file_id=fid):
            if item.type == "folder":
                result.append({"fid": item.file_id, "name": item.name, "pid": item.parent_file_id})
        return result

    def get_file_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        file = self.drive.get_file_by_path(path)
        if file is not None:
            return {
                "name": file.name,
                "size": file.size
            }
        else:
            return {}

    def get_dir_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        file = self.drive.get_folder_by_path(path)
        if file is not None:
            return {
                "name": file.name,
                "size": file.size
            }
        else:
            return {}

    def download_file(self, dir_path="./cache", fid=None, overwrite=False, *args, **kwargs) -> bool:
        self.drive.download_file(file_id=fid, local_folder=dir_path)
        return True

    def download_dir(self, dir_path="./cache", fid=None, overwrite=False, *args, **kwargs):
        self.drive.download_folder(local_folder=dir_path, folder_file_id=fid)
        return True

    def upload_file(self, file_path="./cache", fid=None, overwrite=False, *args, **kwargs) -> bool:
        self.drive.upload_file(file_path=file_path, parent_file_id=fid)
        return True

    def upload_dir(self, file_path="./cache", fid=None, overwrite=False, *args, **kwargs) -> dict:
        self.drive.upload_folder(folder_path=file_path, parent_file_id=fid)
        return {}


class ALiDriveSnapshot(DriveSnapshot):
    def __init__(self, fid=None, url=None, pwd="", *args, **kwargs):
        super(ALiDriveSnapshot, self).__init__(*args, **kwargs)
        self.drive = ALiDrive()
        self.fid = fid
        self.url = url
        self.pwd = pwd

    def delete_outed_version(self):
        datas = self.drive.get_file_list(fid=self.fid)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        if len(datas) > self.version_num:
            for i in range(self.version_num, len(datas)):
                self.drive.delete(datas[i]["fid"], is_file=True)

    def update(self, file_path, *args, **kwargs):
        gz_path = self._tar_path(file_path)
        tarfile.file_entar(file_path, gz_path)
        self.drive.login()
        self.drive.upload_file(gz_path, fid=self.fid)
        os.remove(gz_path)
        self.delete_outed_version()

    def download(self, dir_path, *args, **kwargs):
        self.drive.instance()
        datas = self.drive.get_file_list(url=self.url, pwd=self.pwd)
        if len(datas) == 0:
            print("没有快照文件")
            return
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        self.drive.download_file(dir_path=dir_path, url=datas[0]["url"], pwd=datas[0]["pwd"], overwrite=True)
        tar_path = f"{dir_path}/{datas[0]['name']}"
        tarfile.file_detar(tar_path)
        os.remove(tar_path)


def download(url, dir_pwd="./download", pwd=""):
    downer = ALiDrive()
    downer.ignore_limit()
    downer.download_file(url, save_path=dir_pwd, pwd=pwd)
