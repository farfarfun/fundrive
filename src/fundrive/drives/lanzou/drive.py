import os
import subprocess
from typing import Any, List, Dict

from fundrive.core import DriveSnapshot
from fundrive.core import DriveSystem
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
            self.callback = tqdm(unit="B", unit_scale=True, unit_divisor=1024, desc=file_name, total=total_size)

    def update(self, now_size):
        self.callback.update(now_size - self.last_size)
        self.last_size = now_size


class LanZouDrive(DriveSystem):
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
            subprocess.check_call(["pip", "install", "git+https://github.com/Leon406/lanzou-gui.git", "--no-deps"])
            from lanzou.api import LanZouCloud
        self.drive = LanZouCloud()

    def login(self, cookie=None, ylogin=None, phpdisk_info=None, *args, **kwargs) -> bool:
        self.instance()
        if cookie is None:
            ylogin = ylogin or read_secret("fundrive", "drives", "funlanzou", "ylogin")
            phpdisk_info = phpdisk_info or read_secret("fundrive", "drives", "funlanzou", "phpdisk_info")
            cookie = {
                "ylogin": ylogin,
                "phpdisk_info": phpdisk_info,
            }
        return self.drive.login_by_cookie(cookie) == 0

    def mkdir(self, path, fid=None, *args, **kwargs) -> bool:
        return self.drive.mkdir(fid, path, *args, **kwargs) == 0

    def delete(self, fid=None, *args, **kwargs) -> bool:
        return self.drive.delete(fid, *args, **kwargs) == 0

    def get_dir_list(self, fid=None, url=None, pwd=None, *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        for item in self.drive.get_dir_list(folder_id=fid)[0]:
            result.append({"fid": item.id, "name": item.name, "desc": item.desc})
        return result

    def get_file_list(self, fid=None, url=None, pwd=None, *args, **kwargs) -> List[Dict[str, Any]]:
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

    def get_file_info(self, fid=None, url=None, pwd=None, *args, **kwargs) -> Dict[str, Any]:
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

    def get_dir_info(self, fid=None, url=None, pwd=None, *args, **kwargs) -> Dict[str, Any]:
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

    def download_file(self, dir_path="./cache", overwrite=False, fid=None, url=None, pwd=None, *args, **kwargs) -> bool:
        file_info = self.get_file_info(fid=fid, url=url, pwd=pwd)
        task = Task(url=file_info["url"], pwd=file_info["pwd"], path=dir_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        wrap = ProgressWrap()
        wrap.init(file_info["name"], file_info["size"])

        def clb():
            wrap.update(task.now_size)

        return self.drive.down_file_by_url(share_url=file_info["url"], task=task, callback=clb) == 0

    def download_dir(self, dir_path="./cache", fid=None, url=None, pwd=None, overwrite=False, *args, **kwargs):
        dir_info = self.get_dir_info(fid=fid, url=url, pwd=pwd)
        task = Task(url=dir_info["url"], pwd=dir_info["pwd"], path=dir_path)

        def clb():
            pass

        return self.drive.down_file_by_url(share_url=dir_info["url"], task=task, callback=clb) == 0

    def upload_file(self, file_path="./cache", fid=None, overwrite=False, *args, **kwargs) -> bool:
        task = Task(url=file_path, pwd="", path=file_path, folder_id=fid)
        wrap = ProgressWrap()
        wrap.init(os.path.basename(file_path), os.stat(file_path).st_size)

        def clb():
            wrap.update(task.now_size)

        return (
            self.drive.upload_file(
                task=task, file_path=file_path, folder_id=fid, callback=clb, allow_big_file=self.allow_big_file
            )[0]
            == 0
        )

    def upload_dir(
        self, file_path="./cache", fid=None, only_directory=False, overwrite=False, filter_fun=None, remove_local=False
    ) -> dict:
        """
        将本地的文件同步到云端，单向同步
        :param file_path: 本地路径
        :param fid: 云端路径
        :param only_directory: 是否只同步文件夹
        :param overwrite: 是否需要覆盖重写
        :param filter_fun: 针对部分文件需要过滤
        :param remove_local: 同步完成后是否删除本地文件
        :return: 文件到folder_id的映射关系
        """
        yun_dir_list = self.get_dir_list(fid)
        yun_file_list = self.get_file_list(fid)
        yun_dir_dict = dict([(yun["name"], yun["id"]) for yun in yun_dir_list])
        yun_file_dict = dict([(yun["name"], yun["id"]) for yun in yun_file_list])

        file_dict = {}
        for file in os.listdir(file_path):
            local_path = os.path.join(file_path, file)
            # 根据传入的函数进行过滤，某些文件可以不同步
            if filter_fun is not None and (filter_fun(local_path) or filter_fun(file)):
                continue

            # 文件夹同步，支持递归同步
            if os.path.isdir(local_path):
                if file in yun_dir_dict.keys():
                    yun_id = yun_dir_dict[file]
                else:
                    yun_id = self.mkdir(fid=fid, path=file, desc=file)
                file_dict[local_path] = yun_id
                file_dict.update(
                    self.upload_dir(
                        file_path=local_path,
                        fid=yun_id,
                        only_directory=only_directory,
                        overwrite=overwrite,
                        filter_fun=filter_fun,
                        remove_local=remove_local,
                    )
                )
            else:
                # 只同步文件夹
                if only_directory:
                    continue
                # 文件在云端已存在，如果覆盖重写，删除云端文件，重新上传
                if file in yun_file_dict.keys():
                    if overwrite:
                        self.delete(yun_file_dict[file], is_file=True)
                        yun_id = self.upload_file(file_path=local_path, fid=fid)
                    else:
                        yun_id = yun_file_dict[file]
                else:
                    yun_id = self.upload_file(file_path=local_path, fid=fid)

                file_dict[local_path] = yun_id
                if yun_id > 100 and remove_local:
                    os.remove(local_path)

        return file_dict


class LanZouSnapshot(DriveSnapshot):
    def __init__(self, fid=None, url=None, pwd="", *args, **kwargs):
        super(LanZouSnapshot, self).__init__(*args, **kwargs)
        self.drive = LanZouDrive()
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
    downer = LanZouDrive()
    downer.ignore_limit()
    downer.download_file(url, save_path=dir_pwd, pwd=pwd)
