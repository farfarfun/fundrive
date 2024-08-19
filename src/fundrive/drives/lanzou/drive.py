import os
import subprocess
from typing import List

from fundrive.core import BaseDrive
from fundrive.core import DriveSnapshot
from fundrive.core.base import DriveFile
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

    def mkdir(self, fid, name, url=None, pwd=None, *args, **kwargs) -> bool:
        return self.drive.mkdir(fid, name, *args, **kwargs) == 0

    def delete(self, fid=None, *args, **kwargs) -> bool:
        return self.drive.delete(fid, *args, **kwargs) == 0

    def get_dir_list(self, fid, url=None, pwd=None, *args, **kwargs) -> List[DriveFile]:
        result = []
        for item in self.drive.get_dir_list(folder_id=fid)[0]:
            result.append(DriveFile(fid=item.id, name=item.name, desc=item.desc))
        return result

    def get_file_list(
        self, fid, url=None, pwd=None, *args, **kwargs
    ) -> List[DriveFile]:
        from lanzou.api.utils import convert_file_size_to_int

        result = []
        if fid is not None:
            for item in self.drive.get_file_list(folder_id=fid):
                result.append(
                    DriveFile(
                        fid=item.id,
                        name=item.name,
                        time=item.time,
                    )
                )
        if url is not None:
            data = self.drive.get_folder_info_by_url(url, pwd)
            for item in data.files:
                result.append(
                    DriveFile(
                        fid=item.id,
                        name=item.name,
                        time=item.time,
                        size=convert_file_size_to_int(item.size),
                        url=item.url,
                        pwd=item.pwd,
                    )
                )
        return result

    def get_file_info(self, fid, url=None, pwd=None, *args, **kwargs) -> DriveFile:
        from lanzou.api.utils import convert_file_size_to_int

        data = None
        if fid is not None:
            data = self.drive.get_file_info_by_id(fid)
        if data is None and url is not None:
            data = self.drive.get_file_info_by_url(url, pwd)
        if data is not None:
            return DriveFile(
                fid=data.durl,
                name=data.name,
                desc=data.desc,
                time=data.time,
                size=convert_file_size_to_int(data.size),
                url=data.url,
                pwd=data.pwd,
            )

    def get_dir_info(self, fid, url=None, pwd=None, *args, **kwargs) -> DriveFile:
        data = None
        if fid is not None:
            data = self.drive.get_folder_info_by_id(fid)
        if data is None and url is not None:
            data = self.drive.get_folder_info_by_url(url, pwd)
        if data is not None:
            data = data.folder
            return DriveFile(
                fid=data.id,
                name=data.name,
                desc=data.desc,
                time=data.time,
                url=data.url,
            )

    def download_file(self, fid, local_dir, overwrite=False, *args, **kwargs) -> bool:
        file_info = self.get_file_info(fid=fid)
        task = Task(url=file_info["url"], pwd=file_info["pwd"], path=local_dir)
        os.makedirs(local_dir, exist_ok=True)
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
        self, fid, local_dir, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if not self.exist(fid):
            return False
        os.makedirs(local_dir, exist_ok=True)
        for file in self.get_file_list(fid):
            self.download_file(
                fid=file["fid"],
                local_dir=local_dir,
                overwrite=overwrite,
                *args,
                **kwargs,
            )
        if not recursion:
            return True

        for file in self.get_dir_list(fid):
            _local_path = os.path.join(local_dir, file["name"])
            self.download_dir(
                fid=file["fid"],
                local_dir=local_dir,
                overwrite=overwrite,
                recursion=recursion,
                *args,
                **kwargs,
            )

    def upload_file(
        self,
        local_path,
        fid,
        url=None,
        pwd=None,
        recursion=True,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        task = Task(url=url, pwd=pwd, path=local_path, folder_id=fid)
        wrap = ProgressWrap()
        wrap.init(os.path.basename(local_path), os.stat(local_path).st_size)

        def clb():
            wrap.update(task.now_size)

        return (
            self.drive.upload_file(
                task=task,
                file_path=local_path,
                folder_id=fid,
                callback=clb,
                allow_big_file=self.allow_big_file,
            )[0]
            == 0
        )

    def move_file(self, file_id, folder_id):
        self.drive.move_file(file_id, folder_id)


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
