# 标准库导入
import os
from typing import Any, List, Optional


# 第三方库导入
from fundrives.baidu import BaiduPCSApi, PcsFile
from funget import download
from funsecret import read_secret
from funutil import getLogger

# 项目内部导入
from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


def convert(file: PcsFile) -> DriveFile:
    """
    转换百度网盘文件对象为通用文件对象
    :param file: 百度网盘文件对象
    :return: 通用文件对象
    """
    return DriveFile(
        fid=file.path,
        name=os.path.basename(file.path),
        size=file.size,
        ext=file._asdict(),
    )


class BaiDuDrive(BaseDrive):
    def __init__(self, *args: Any, **kwargs: Any):
        """
        初始化百度网盘驱动
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        super(BaiDuDrive, self).__init__(*args, **kwargs)
        self.drive: BaiduPCSApi = None

    def login(
        self, bduss=None, stoken=None, ptoken=None, *args: Any, **kwargs: Any
    ) -> bool:
        """
        登录百度网盘
        :param bduss: 百度用户身份标识
        :param stoken: 安全Token
        :param ptoken: 持久化Token
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 登录是否成功
        """
        bduss = bduss or read_secret("fundrive", "baidu", "bduss")
        stoken = stoken or read_secret("fundrive", "baidu", "stoken")
        ptoken = ptoken or read_secret("fundrive", "baidu", "ptoken")
        self.drive = BaiduPCSApi(bduss=bduss, stoken=stoken, ptoken=ptoken)
        return True

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        创建目录
        :param fid: 父目录ID
        :param name: 目录名称
        :param return_if_exist: 如果目录已存在，是否返回已存在目录的ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 创建的目录ID
        """
        dir_map = dict([(file.name, file.fid) for file in self.get_dir_list(fid=fid)])
        if name in dir_map:
            logger.info(f"name={name} exists, return fid={fid}")
            return dir_map[name]
        path = f"{fid}/{name}"
        try:
            self.drive.makedir(path)
        except Exception as e:
            logger.error(f"makedir ({path}) error :{e}")
        return path

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录
        :param fid: 文件或目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 删除是否成功
        """
        return self.drive.remove(fid)

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在
        :param fid: 文件或目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 是否存在
        """
        return self.drive.exists(fid)

    def upload_file(
        self,
        filepath: str,
        fid: str,
        recursion: bool = True,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传文件
        :param filepath: 本地文件路径
        :param fid: 目标文件ID
        :param recursion: 是否递归上传
        :param overwrite: 是否覆盖已存在的文件
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 上传是否成功
        """
        with open(filepath, "rb") as f:
            self.drive.upload_file(f, remotepath=fid)
        return True

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """
        获取文件详细信息
        :param fid: 文件ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 文件信息对象
        """
        return convert(self.drive.meta(fid)[0]) if self.drive.is_file(fid) else None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """
        获取目录详细信息
        :param fid: 目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 目录信息对象
        """
        return convert(self.drive.meta(fid)[0]) if self.drive.is_dir(fid) else None

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的文件列表
        :param fid: 目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 文件列表
        """
        return [convert(file) for file in self.drive.list(fid) if file.is_file]

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的子目录列表
        :param fid: 目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 子目录列表
        """
        return [convert(file) for file in self.drive.list(fid) if file.is_dir]

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        下载文件
        :param fid: 文件ID
        :param save_dir: 文件保存目录
        :param filename: 文件名
        :param filepath: 完整的文件保存路径
        :param overwrite: 是否覆盖已存在的文件
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 下载是否成功
        """
        link = self.drive.download_link(fid)

        headers = {
            "User-Agent": "softxm;netdisk",
            "Connection": "Keep-Alive",
            "Cookie": f"BDUSS={self.drive.bduss};ptoken={self.drive.ptoken}",
        }
        try:
            filepath = get_filepath(save_dir, filename, filepath)
            download(
                link,
                filepath=filepath
                or os.path.join(save_dir, filename or os.path.basename(fid)),
                headers=headers,
                overwrite=overwrite,
                *args,
                **kwargs,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to download file {fid}: {e}")
            return False

    def share(
        self, *fids: str, password: str, expire_days: int = 0, description: str = ""
    ):
        """
        分享文件或目录
        :param fids: 要分享的文件或目录ID列表
        :param password: 分享密码
        :param expire_days: 分享链接有效期（天），0表示永久有效
        :param description: 分享描述
        """
        self.drive.share(*fids, password=password, period=expire_days)

    def save_shared(
        self, shared_url: str, remote_dir: str, password: Optional[str] = None
    ):
        """
        保存他人的分享内容到自己的网盘
        :param shared_url: 分享链接
        :param remote_dir: 保存到的目标目录
        :param password: 分享密码
        :return: 保存是否成功
        """
        return self.drive.save_shared(shared_url, remote_dir, password=password)
