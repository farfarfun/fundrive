"""
OSS云存储驱动

声明:
本模块实现了阿里云OSS存储服务的驱动接口。
主要功能包括文件的上传、下载、删除等基本操作。
"""

import os
from typing import List

from funsecret import read_secret
from tqdm import tqdm

from fundrive.core import BaseDrive, DriveFile


def public_oss_url(
    bucket_name="nm-algo", endpoint="oss-cn-hangzhou.aliyuncs.com", path=""
):
    """生成OSS公共访问URL

    声明:
    此函数用于生成阿里云OSS对象存储的公共访问URL。

    Args:
        bucket_name (str): OSS bucket名称
        endpoint (str): OSS访问域名
        path (str): 文件路径
    Returns:
        str: 完整的OSS URL
    """
    return f"https://{bucket_name}.{endpoint}/{path}"


class OSSDrive(BaseDrive):
    """阿里云OSS存储驱动实现

    声明:
    此类实现了阿里云OSS存储服务的基本操作接口，包括文件上传下载、目录管理等功能。
    """

    def __init__(self, *args, **kwargs):
        """初始化OSS驱动

        声明:
        初始化OSS驱动实例，设置基本属性。

        Args:
            *args: 可变位置参数
            **kwargs: 可变关键字参数
        """
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
        """
        登录OSS服务

        声明:
        使用访问密钥登录阿里云OSS服务，建立连接。

        Args:
            access_key (str, optional): 访问密钥ID
            access_secret (str, optional): 访问密钥密码
            bucket_name (str, optional): Bucket名称
            endpoint (str, optional): 访问域名
            connect_timeout (int, optional): 连接超时时间(秒)
        Returns:
            bool: 登录是否成功
        """
        import oss2

        access_key = access_key or read_secret(
            cate1="fundrive", cate2="oss", cate3="access_key"
        )
        access_secret = access_secret or read_secret(
            cate1="fundrive", cate2="oss", cate3="access_secret"
        )
        bucket_name = bucket_name or read_secret(
            cate1="fundrive", cate2="oss", cate3="bucket_name"
        )
        endpoint = endpoint or read_secret(
            cate1="fundrive", cate2="oss", cate3="endpoint"
        )
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
        """获取指定路径下的文件列表

        Args:
            oss_path: OSS路径
        Returns:
            List[DriveFile]: 文件列表
        """
        result = []
        dir_name = []
        for file in self.bucket.list_objects(oss_path, max_keys=1000).object_list:
            solve_path = file.key.replace(oss_path, "").strip("/")
            paths = solve_path.split("/")

            solve_size = len(solve_path.split("/"))
            solve_name = paths[0]

            if not file.key.endswith("/") and solve_size == 1:
                result.append(
                    DriveFile(
                        isfile=True,
                        fid=file.key,
                        name=os.path.basename(file.key),
                        path=file.key,
                        size=file.size,
                    )
                )
            if solve_name not in dir_name:
                dir_name.append(solve_name)
                result.append(
                    DriveFile(
                        isfile=False,
                        fid=os.path.join(oss_path, solve_name),
                        name=solve_name,
                        path=os.path.join(oss_path, solve_name),
                        size=file.size,
                    )
                )

        return result

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        """创建目录

        Args:
            fid: 父目录ID
            name: 目录名
            return_if_exist: 如果目录存在是否返回
        Returns:
            str: 创建的目录路径
        """
        return os.path.join(fid, name)

    def delete(self, fid, *args, **kwargs) -> bool:
        """删除文件或目录

        Args:
            fid: 文件或目录ID
        Returns:
            bool: 是否删除成功
        """
        self.bucket.delete_object(key=fid)
        return True

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        """获取文件信息

        Args:
            fid: 文件ID
        Returns:
            DriveFile: 文件信息对象
        """
        for file in self.bucket.list_objects(fid, max_keys=10).object_list:
            return DriveFile(
                isfile=False,
                fid=file.key,
                name=os.path.basename(file.key),
                path=file.key,
                size=file.size,
            )

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        """获取目录信息

        Args:
            fid: 目录ID
        Returns:
            DriveFile: 目录信息对象
        """
        files = self.__get_file_list(oss_path=fid)
        for file in files:
            if file["path"] == fid:
                return file

    def get_file_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        """获取目录下的文件列表

        Args:
            fid: 目录ID
        Returns:
            List[DriveFile]: 文件列表
        """
        result = []
        for file in self.__get_file_list(fid):
            if file["isfile"]:
                result.append(file)
        return result

    def get_dir_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        """获取目录下的子目录列表

        Args:
            fid: 目录ID
        Returns:
            List[DriveFile]: 目录列表
        """
        result = []
        for file in self.__get_file_list(fid):
            if not file["isfile"] and len(file["name"]) > 0:
                result.append(file)
        return result

    def __download_file(
        self,
        save_path="./cache",
        oss_path=None,
        size=0,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        """下载单个文件的内部实现

        声明:
        实现单个文件的下载逻辑，支持进度显示。

        Args:
            save_path (str): 保存路径
            oss_path (str): OSS文件路径
            size (int): 文件大小
            overwrite (bool): 是否覆盖已存在文件
        Returns:
            bool: 下载是否成功
        """
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        filename = os.path.basename(oss_path)
        file_path = os.path.join(save_path, filename)

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

    def download_file(self, fid, filepath, overwrite=False, *args, **kwargs) -> bool:
        """下载单个文件

        声明:
        从OSS下载指定文件到本地。

        Args:
            fid (str): 文件ID(OSS路径)
            save_path (str): 保存路径(文件路径或目录路径)
            overwrite (bool): 是否覆盖已存在文件
        Returns:
            bool: 下载是否成功
        """
        save_dir = (
            os.path.dirname(filepath) if os.path.splitext(filepath)[1] else filepath
        )
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        file_info = self.get_file_info(fid=fid)
        return self.__download_file(
            save_path=save_dir,
            oss_path=fid,
            size=file_info["size"],
            overwrite=overwrite,
        )

    def upload_file(
        self, filepath, fid, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """上传单个文件

        声明:
        将本地文件上传到OSS指定路径。

        Args:
            filepath (str): 本地文件路径
            fid (str): 目标文件夹ID(OSS路径)
            recursion (bool): 是否递归上传(目录)
            overwrite (bool): 是否覆盖已存在文件
        Returns:
            bool: 上传是否成功
        """
        filename = os.path.basename(filepath)
        oss_path = os.path.join(fid, filename)
        size = os.path.getsize(filepath)
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

        with open(filepath, "rb") as f:
            self.bucket.put_object(oss_path, f, progress_callback=progress_callback)

        return True
