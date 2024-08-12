import os
import subprocess
from typing import Any, List, Dict

from fundrive.core import BaseDrive
from fundrive.core import DriveSnapshot
from funfile.compress import tarfile
from funsecret import read_secret
from tqdm import tqdm


class Task:
    def __init__(self, url, pwd="", path="./download", now_size=0, folder_id=-1):
        self.url = url
        self.pwd = pwd
        self.path = path
        self.now_size = now_size
        self.folder_id = folder_id


class ProgressWrap:
    def __init__(self, callback: tqdm = None):
        self.callback = callback
        self.last_size = 0

    def init(self, file_name, total_size):
        if self.callback is None:
            self.callback = tqdm(
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=file_name,
                total=total_size,
            )

    def update(self, now_size):
        self.callback.update(now_size - self.last_size)
        self.last_size = now_size


class LanZouDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(LanZouDrive, self).__init__(*args, **kwargs)
        self.allow_big_file = False
        self.drive = None

    def ignore_limit(self):
        self.allow_big_file = True

    def instance(self):
        if self.drive is not None:
            return
        try:
            from lanzou.api import LanZouCloud
        except Exception as e:
            subprocess.check_call(["pip", "install", "fundrive-lanzou"])
            from lanzou.api import LanZouCloud
        self.drive = LanZouCloud()

    def login(
        self, cookie=None, ylogin=None, phpdisk_info=None, *args, **kwargs
    ) -> bool:
        self.instance()
        if cookie is None:
            ylogin = ylogin or read_secret("fundrive", "drives", "funlanzou", "ylogin")
            phpdisk_info = phpdisk_info or read_secret(
                "fundrive", "drives", "funlanzou", "phpdisk_info"
            )
            cookie = {
                "ylogin": ylogin,
                "phpdisk_info": phpdisk_info,
            }
        return self.drive.login_by_cookie(cookie) == 0

    def parse_fid_url_pwd(self, path):
        fid = None
        url = None
        pwd = None
        if isinstance(path, int) or "," not in path:
            fid = path
        else:
            url, pwd = path.split(",")
        return fid, url, pwd

    def exist(self, path, *args, **kwargs) -> bool:
        return True

    def mkdir(self, path, *args, **kwargs) -> bool:
        fid, url, pwd = self.parse_fid_url_pwd(path)
        return self.drive.mkdir(url, pwd, *args, **kwargs) == 0

    def delete(self, path=None, *args, **kwargs) -> bool:
        fid, url, pwd = self.parse_fid_url_pwd(path)
        return self.drive.delete(fid, *args, **kwargs) == 0

    def get_dir_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        fid, url, pwd = self.parse_fid_url_pwd(path)
        result = []
        for item in self.drive.get_dir_list(folder_id=fid)[0]:
            result.append({"fid": item.id, "name": item.name, "desc": item.desc})
        return result

    def get_file_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        fid, url, pwd = self.parse_fid_url_pwd(path)
        from lanzou.api.utils import convert_file_size_to_int

        result = []
        if fid is not None:
            for item in self.drive.get_file_list(folder_id=fid):
                result.append(
                    {
                        "fid": item.id,
                        "name": item.name,
                        "size": item.size,
                        "type": item.type,
                        "time": item.time,
                        "has_pwd": item.has_pwd,
                    }
                )
        if url is not None:
            data = self.drive.get_folder_info_by_url(url, pwd)
            for item in data.files:
                result.append(
                    {
                        "name": item.name,
                        "size": convert_file_size_to_int(item.size),
                        "type": item.type,
                        "time": item.time,
                        "url": item.url,
                        "pwd": item.pwd,
                    }
                )
        return result

    def get_file_info(self, path=None, *args, **kwargs) -> Dict[str, Any]:
        fid, url, pwd = self.parse_fid_url_pwd(path)
        from lanzou.api.utils import convert_file_size_to_int

        data = None
        if fid is not None:
            data = self.drive.get_file_info_by_id(fid)
        if data is None and url is not None:
            data = self.drive.get_file_info_by_url(url, pwd)
        if data is not None:
            return {
                "fid": fid,
                "name": data.name,
                "size": convert_file_size_to_int(data.size),
                "type": data.type,
                "time": data.time,
                "desc": data.desc,
                "pwd": data.pwd,
                "url": data.url,
                "durl": data.durl,
            }
        return {}

    def get_dir_info(self, path=None, *args, **kwargs) -> Dict[str, Any]:
        fid, url, pwd = self.parse_fid_url_pwd(path)
        data = None
        if fid is not None:
            data = self.drive.get_folder_info_by_id(fid)
        if data is None and url is not None:
            data = self.drive.get_folder_info_by_url(url, pwd)
        if data is not None:
            data = data.folder
            return {
                "name": data.name,
                "fid": data.id,
                "pwd": data.pwd,
                "time": data.time,
                "desc": data.desc,
                "url": data.url,
            }
        return {}

    def download_file(
        self, local_path, drive_path, overwrite=False, *args, **kwargs
    ) -> bool:
        file_info = self.get_file_info(path=drive_path)
        task = Task(url=file_info["url"], pwd=file_info["pwd"], path=local_path)
        if not os.path.exists(local_path):
            os.makedirs(local_path, exist_ok=True)
        wrap = ProgressWrap()
        wrap.init(file_info["name"], file_info["size"])

        def clb():
            wrap.update(task.now_size)

        return (
            self.drive.down_file_by_url(
                share_url=file_info["url"], task=task, callback=clb
            )
            == 0
        )

    def download_dir(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if not self.exist(drive_path):
            return False
        if not os.path.exists(local_path):
            os.makedirs(local_path, exist_ok=True)
        for file in self.get_file_list(drive_path):
            self.download_file(
                local_path=local_path,
                drive_path=file["fid"],
                overwrite=overwrite,
                *args,
                **kwargs,
            )
        if not recursion:
            return True

        for file in self.get_dir_list(drive_path):
            _local_path = os.path.join(local_path, file["name"])
            self.download_dir(
                local_path=_local_path,
                drive_path=file["fid"],
                overwrite=overwrite,
                recursion=recursion,
                *args,
                **kwargs,
            )

    def upload_file(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        fid, url, pwd = self.parse_fid_url_pwd(drive_path)
        task = Task(url=url, pwd=pwd, path=local_path, folder_id=drive_path)
        wrap = ProgressWrap()
        wrap.init(os.path.basename(local_path), os.stat(local_path).st_size)

        def clb():
            wrap.update(task.now_size)

        return (
            self.drive.upload_file(
                task=task,
                local_path=local_path,
                folder_id=drive_path,
                callback=clb,
                allow_big_file=self.allow_big_file,
            )[0]
            == 0
        )


class LanZouSnapshot(DriveSnapshot):
    def __init__(self, fid=None, url=None, pwd="", *args, **kwargs):
        super(LanZouSnapshot, self).__init__(*args, **kwargs)
        self.drive = LanZouDrive()
        self.fid = fid
        self.url = url
        self.pwd = pwd

    def delete_outed_version(self):
        datas = self.drive.get_file_list(path=self.fid)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        if len(datas) > self.version_num:
            for i in range(self.version_num, len(datas)):
                self.drive.delete(datas[i]["fid"], is_file=True)

    def update(self, file_path, *args, **kwargs):
        gz_path = self._tar_path(file_path)
        tarfile.file_entar(file_path, gz_path)
        self.drive.login()
        self.drive.upload_file(gz_path, drive_path=self.fid)
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
        self.drive.download_file(
            dir_path=dir_path,
            url=datas[0]["url"] + "," + datas[0]["pwd"],
            overwrite=True,
        )
        tar_path = f"{dir_path}/{datas[0]['name']}"
        tarfile.file_detar(tar_path)
        os.remove(tar_path)
