from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
import os
from aligo import Aligo
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


class AlipanDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        """
        初始化阿里云盘驱动
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        super(AlipanDrive, self).__init__(*args, **kwargs)

        self.drive: Aligo = None

    def login(
        self,
        server_url: Optional[str] = None,
        refresh_token: Optional[str] = None,
        is_resource: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        登录阿里云盘
        :param server_url: 服务器URL
        :param refresh_token: 刷新令牌，如未提供则从配置文件读取
        :param is_resource: 是否使用资源盘，默认False
        :return: 登录是否成功
        """
        refresh_token = refresh_token or read_secret(
            "fundrive", "drives", "alipan", "refresh_token"
        )

        self.drive = Aligo(refresh_token=refresh_token)
        if is_resource:
            logger.info("使用资源盘")
            self.drive.default_drive_id = self.drive.v2_user_get().resource_drive_id
        return True

    def mkdir(
        self, fid: str, name: str, return_if_exist: bool = True, *args, **kwargs
    ) -> str:
        """
        在指定目录下创建文件夹
        :param fid: 父目录ID
        :param name: 文件夹名称
        :param return_if_exist: 如果文件夹已存在，是否返回已存在的文件夹ID
        :return: 创建的文件夹ID
        """
        dir_map = dict([(file.name, file.fid) for file in self.get_dir_list(fid=fid)])
        if name in dir_map:
            logger.info(f"name={name} exists, return fid={fid}")
            return dir_map[name]
        return self.drive.create_folder(parent_file_id=fid, name=name).file_id

    def delete(self, fid: str, *args, **kwargs) -> bool:
        """
        删除文件或文件夹
        :param fid: 文件或文件夹ID
        :return: 删除是否成功
        """
        self.drive.move_file_to_trash(file_id=fid)
        return True

    def exist(self, fid: str, *args, **kwargs) -> bool:
        """
        检查文件或文件夹是否存在
        :param fid: 文件或文件夹ID
        :return: 是否存在
        """
        return self.drive.get_file(file_id=fid) is not None

    def get_file_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取指定目录下的文件列表
        :param fid: 目录ID，默认为根目录
        :return: 文件信息列表
        """
        result = []
        for file in self.drive.get_file_list(parent_file_id=fid):
            if file.type == "file":
                result.append(
                    DriveFile(
                        fid=file.file_id,
                        name=file.name,
                        size=file.size,
                        ext=file.to_dict(),
                    )
                )
        return result

    def get_dir_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取指定目录下的子目录列表
        :param fid: 目录ID，默认为根目录
        :return: 子目录信息列表
        """
        result = []
        for file in self.drive.get_file_list(parent_file_id=fid):
            if file.type == "folder":
                result.append(
                    DriveFile(fid=file.file_id, name=file.name, size=file.size)
                )
        return result

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.get_file(file_id=fid)
        return DriveFile(fid=res.file_id, name=res.name, size=res.size)

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.get_file(file_id=fid)
        return DriveFile(fid=res.file_id, name=res.name, size=res.size)

    def download_file(
        self,
        fid: str,
        filedir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        下载文件
        :param fid: 文件ID
        :param filedir: 文件保存目录
        :param filename: 文件名
        :param filepath: 完整的文件保存路径
        :param overwrite: 是否覆盖已存在的文件
        :return: 下载是否成功
        """
        save_path = get_filepath(filedir, filename, filepath)
        if not save_path:
            raise ValueError("必须提供有效的文件保存路径")
        self.drive.download_file(file_id=fid, local_folder=os.path.dirname(save_path))
        return True

    def upload_file(
        self,
        filedir: str,
        fid: str,
        recursion: bool = True,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传文件
        :param filedir: 本地文件路径
        :param fid: 目标目录ID
        :param recursion: 是否递归上传
        :param overwrite: 是否覆盖已存在的文件
        :return: 上传是否成功
        """
        self.drive.upload_file(
            file_path=filedir,
            parent_file_id=fid,
            check_name_mode="overwrite" if overwrite else "refuse",
        )
        return True

    def share(
        self, *fids: str, password: str, expire_days: int = 0, description: str = ""
    ) -> None:
        """
        分享文件或文件夹
        :param fids: 要分享的文件或文件夹ID列表
        :param password: 分享密码
        :param expire_days: 分享链接有效期（天），0表示永久有效
        :param description: 分享描述
        """
        now = datetime.now(timezone.utc) + timedelta(days=expire_days)
        expiration = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        self.drive.share_files(
            [fid for fid in fids], share_pwd=password, expiration=expiration
        )

    def save_shared(
        self, shared_url: str, fid: str, password: Optional[str] = None
    ) -> None:
        """
        保存他人分享的文件到自己的网盘
        :param shared_url: 分享链接
        :param fid: 保存到的目标目录ID
        :param password: 分享密码，如果未提供则尝试自动获取
        """
        r = self.drive.share_link_extract_code(shared_url)
        r.share_pwd = password or r.share_pwd
        self.drive.share_file_save_all_to_drive(share_token=r, to_parent_file_id=fid)
