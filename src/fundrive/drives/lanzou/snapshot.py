"""蓝奏云目录快照：把本地目录打包上传并保留有限个历史版本。"""

import os

from farlog import getLogger
from funfile.compress import tarfile

from fundrive.core import DriveSnapshot

from .drive import LanZouDrive

logger = getLogger("fundrive")


class LanZouSnapshot(DriveSnapshot):
    """
    蓝奏云目录快照

    把本地目录打成 tar 包上传到蓝奏云指定目录，只保留最近 ``version_num`` 个版本；
    下载时取文件名排序最大（即最新）的那个快照并解包。

    Args:
        fid (int | str, optional): 云端存放快照的目录ID，上传时必填
        url (str, optional): 快照目录的分享链接，下载时可用它免登录读取
        pwd (str): 分享链接的提取密码，没有就留空
        *args: 透传给 ``DriveSnapshot`` 的可变位置参数
        **kwargs: 透传给 ``DriveSnapshot`` 的可变关键字参数（如 ``version_num``）
    """

    def __init__(self, fid=None, url=None, pwd="", *args, **kwargs):
        """初始化蓝奏云快照，详见类文档。"""
        super().__init__(*args, **kwargs)
        self.drive = LanZouDrive()
        self.fid = fid
        self.url = url
        self.pwd = pwd

    def delete_outed_version(self):
        """
        删除超出 ``version_num`` 的旧快照（按文件名倒序保留最新的若干个）

        Returns:
            None
        """
        datas = self.drive.get_file_list(fid=self.fid)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        if len(datas) > self.version_num:
            for i in range(self.version_num, len(datas)):
                self.drive.delete(datas[i]["fid"], is_file=True)

    def update(self, file_path, *args, **kwargs):
        """
        把本地目录打包上传为一个新快照，并清理过期版本

        Args:
            file_path (str): 待打包的本地目录
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            None
        """
        gz_path = self._tar_path(file_path)
        tarfile.file_entar(file_path, gz_path)
        self.drive.login()
        self.drive.upload_file(gz_path, fid=self.fid)
        os.remove(gz_path)
        self.delete_outed_version()

    def download(self, dir_path, *args, **kwargs):
        """
        下载最新快照并解包到本地目录

        Args:
            dir_path (str): 本地解包目录，不存在时自动创建
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            None
        """
        self.drive.instance()
        datas = self.drive.get_file_list(url=self.url, pwd=self.pwd, fid=None)
        if len(datas) == 0:
            logger.warning("蓝奏云快照目录为空，url={}", self.url)
            return
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        if not self.drive.download_file(
            fid=None,
            save_dir=dir_path,
            url=datas[0]["url"],
            pwd=datas[0]["pwd"],
            overwrite=True,
        ):
            logger.error("蓝奏云快照下载失败，name={}", datas[0]["name"])
            return
        tar_path = f"{dir_path}/{datas[0]['name']}"
        tarfile.file_detar(tar_path)
        os.remove(tar_path)
