import os
import subprocess
from typing import Any, List, Dict

from fundrive.core import DriveSystem
from tqdm import tqdm


def public_oss_url(
    bucket_name="nm-algo", endpoint="oss-cn-hangzhou.aliyuncs.com", path=""
):
    return f"https://{bucket_name}.{endpoint}/{path}"


class OSSDrive(DriveSystem):
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
        try:
            import oss2
        except Exception as e:
            subprocess.check_call(["pip", "install", "oss2"])
            import oss2

        if access_key is None:
            from funsecret import read_secret

            access_key = read_secret(cate1="fundrive", cate2="oss", cate3="access_key")
            access_secret = read_secret(
                cate1="fundrive", cate2="oss", cate3="access_secret"
            )
            bucket_name = read_secret(
                cate1="fundrive", cate2="oss", cate3="bucket_name"
            )
            endpoint = read_secret(cate1="fundrive", cate2="oss", cate3="endpoint")
        self.bucket = oss2.Bucket(
            oss2.Auth(access_key, access_secret),
            endpoint,
            bucket_name,
            connect_timeout=connect_timeout,
            *args,
            **kwargs,
        )
        return True

    def __get_file_list(self, oss_path) -> List[Dict[str, Any]]:
        result = []
        for file in self.bucket.list_objects(oss_path).object_list:
            result.append(
                {
                    "name": os.path.basename(file.key),
                    "path": file.key,
                    "size": file.size,
                }
            )
        return result

    def get_file_info(self, oss_path, *args, **kwargs) -> Dict[str, Any]:
        result = {}
        files = self.__get_file_list(oss_path=oss_path)
        if len(files) == 1:
            return files[0]
        return result

    def get_dir_info(self, oss_path, *args, **kwargs) -> Dict[str, Any]:
        result = {}
        files = self.__get_file_list(oss_path=oss_path)
        for file in files:
            if file["path"] == oss_path:
                return file
        return result

    def get_file_list(
        self, oss_path, recursion=True, *args, **kwargs
    ) -> List[Dict[str, Any]]:
        result = []
        for file in self.__get_file_list(oss_path):
            if not file["path"].endswith("/"):
                if recursion or len(file["path"].split("/")) == len(
                    oss_path.split("/")
                ):
                    result.append(file)
        return result

    def get_dir_list(
        self, oss_path, recursion=True, *args, **kwargs
    ) -> List[Dict[str, Any]]:
        result = []
        for file in self.__get_file_list(oss_path):
            if file["path"].endswith("/"):
                if (
                    recursion
                    or len(file["path"].split("/")) == len(oss_path.split("/")) + 1
                ):
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
        if (
            not overwrite
            and os.path.exists(file_path)
            and size == os.path.getsize(file_path)
        ):
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
            self.bucket.get_object_to_file(
                oss_path, file_path, progress_callback=progress_callback
            )
        return True

    def download_file(
        self, dir_path="./cache", oss_path=None, overwrite=False, *args, **kwargs
    ) -> bool:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_info = self.get_file_info(oss_path=oss_path)
        return self.__download_file(
            dir_path=dir_path,
            oss_path=oss_path,
            size=file_info["size"],
            overwrite=overwrite,
        )

    def download_dir(
        self, dir_path="./cache", oss_dir=None, overwrite=False, *args, **kwargs
    ) -> bool:
        if oss_dir is None:
            return False
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        for file in self.get_file_list(oss_dir):
            file_path = os.path.join(
                dir_path, os.path.dirname(file["path"].replace(oss_dir, ""))
            )
            self.__download_file(
                dir_path=file_path,
                oss_path=file["path"],
                size=file["size"],
                overwrite=overwrite,
            )
        return True

    def upload_file(
        self, file_path="./cache", oss_dir=None, overwrite=False, *args, **kwargs
    ) -> bool:
        filename = os.path.basename(file_path)
        oss_path = os.path.join(oss_dir, filename)
        size = os.path.getsize(file_path)
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

        with open(file_path, "rb") as f:
            self.bucket.put_object(oss_path, f, progress_callback=progress_callback)

        return True

    def upload_dir(
        self, dir_path="./cache", oss_dir=None, overwrite=False, *args, **kwargs
    ) -> bool:
        for file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file)
            if os.path.isfile(file_path):
                self.upload_file(file_path, oss_dir, overwrite=overwrite)
            elif os.path.isdir(file_path):
                self.upload_dir(file_path, os.path.join(oss_dir, file))
        return True
