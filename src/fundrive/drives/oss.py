import os
from typing import List

from funsecret import read_secret
from tqdm import tqdm

from fundrive.core import BaseDrive
from fundrive.core.base import DriveFile


def public_oss_url(bucket_name="nm-algo", endpoint="oss-cn-hangzhou.aliyuncs.com", path=""):
    return f"https://{bucket_name}.{endpoint}/{path}"


class OSSDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(OSSDrive, self).__init__(*args, **kwargs)
        self.bucket = None

    def login(
        self,
        access_key=None,
        access_secret=None,
        bucket_name=None,
        endpoint=None,
        connect_timeout=3600,
        *args,
        **kwargs,
    ) -> bool:
        import oss2

        access_key = access_key or read_secret(cate1="fundrive", cate2="oss", cate3="access_key")
        access_secret = access_secret or read_secret(cate1="fundrive", cate2="oss", cate3="access_secret")
        bucket_name = bucket_name or read_secret(cate1="fundrive", cate2="oss", cate3="bucket_name")
        endpoint = endpoint or read_secret(cate1="fundrive", cate2="oss", cate3="endpoint")
        self.bucket = oss2.Bucket(
            oss2.Auth(access_key, access_secret),
            endpoint,
            bucket_name,
            connect_timeout=connect_timeout,
            *args,
            **kwargs,
        )
        return True

    def __get_file_list(self, oss_path) -> List[DriveFile]:
        result = []
        for file in self.bucket.list_objects(oss_path).object_list:
            result.append(
                DriveFile(
                    fid=file.key,
                    name=os.path.basename(file.key),
                    path=file.key,
                    size=file.size,
                )
            )
        return result

    def delete(self, fid, *args, **kwargs) -> bool:
        self.bucket.delete_object(key=fid)
        return True

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        files = self.__get_file_list(oss_path=fid)
        if len(files) == 1:
            return files[0]

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        files = self.__get_file_list(oss_path=fid)
        for file in files:
            if file["path"] == fid:
                return file

    def get_file_list(self, fid, recursion=True, *args, **kwargs) -> List[DriveFile]:
        result = []
        for file in self.__get_file_list(fid):
            if not file["path"].endswith("/"):
                if recursion or len(file["path"].split("/")) == len(fid.split("/")):
                    result.append(file)
        return result

    def get_dir_list(self, fid, recursion=True, *args, **kwargs) -> List[DriveFile]:
        result = []
        for file in self.__get_file_list(fid):
            if file["path"].endswith("/"):
                if recursion or len(file["path"].split("/")) == len(fid.split("/")) + 1:
                    result.append(file)
        return result

    def __download_file(
        self,
        dir_path="./cache",
        oss_path=None,
        size=0,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        filename = os.path.basename(oss_path)

        file_path = os.path.join(dir_path, os.path.basename(oss_path))
        if not overwrite and os.path.exists(file_path) and size == os.path.getsize(file_path):
            return False

        bar = tqdm(
            total=size,
            ncols=120,
            desc=filename,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        )

        def progress_callback(consumed_bytes, total_bytes):
            bar.update(consumed_bytes - bar.n)

        if not os.path.exists(file_path):
            self.bucket.get_object_to_file(oss_path, file_path, progress_callback=progress_callback)
        return True

    def download_file(self, fid, local_dir, overwrite=False, *args, **kwargs) -> bool:
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        file_info = self.get_file_info(fid=fid)
        return self.__download_file(
            dir_path=local_dir,
            oss_path=fid,
            size=file_info["size"],
            overwrite=overwrite,
        )

    def upload_file(self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs) -> bool:
        filename = os.path.basename(local_path)
        oss_path = os.path.join(fid, filename)
        size = os.path.getsize(local_path)
        file_info = self.get_file_info(oss_path)
        if not overwrite and "size" in file_info.keys() and size == file_info["size"]:
            return False
        bar = tqdm(
            total=size,
            ncols=120,
            desc=filename,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        )

        def progress_callback(consumed_bytes, total_bytes):
            bar.update(consumed_bytes - bar.n)

        with open(local_path, "rb") as f:
            self.bucket.put_object(oss_path, f, progress_callback=progress_callback)

        return True

    def upload_dir(self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs) -> bool:
        for file in os.listdir(local_path):
            file_path = os.path.join(local_path, file)
            if os.path.isfile(file_path):
                self.upload_file(file_path, fid, overwrite=overwrite)
            elif os.path.isdir(file_path):
                self.upload_dir(file_path, os.path.join(fid, file))
        return True
