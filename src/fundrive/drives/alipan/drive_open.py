from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from fundrives.aliopen import AliOpenManage
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


class AliopenDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        """
        初始化阿里云盘驱动
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        super(AliopenDrive, self).__init__(*args, **kwargs)

        self.drive: AliOpenManage = AliOpenManage()

    def login(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        is_resource: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        登录阿里云盘
        :param refresh_token: 刷新令牌，如未提供则从配置文件读取
        :param is_resource: 是否使用资源盘，默认False
        :return: 登录是否成功
        """
        refresh_token = refresh_token or read_secret(
            "fundrive", "drives", "aliopen", "refresh_token"
        )
        client_id = client_id or read_secret(
            "fundrive", "drives", "aliopen", "client_id"
        )
        client_secret = client_secret or read_secret(
            "fundrive", "drives", "aliopen", "client_secret"
        )

        self.drive.login(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            is_resource=is_resource,
        )
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
        return self.drive.create_file(parent_file_id=fid, name=name, type="folder")[
            "file_id"
        ]

    def delete(self, fid: str, *args, **kwargs) -> bool:
        """
        删除文件或文件夹
        :param fid: 文件或文件夹ID
        :return: 删除是否成功
        """
        self.drive.delete_file(file_id=fid)
        return True

    def exist(self, fid: str, *args, **kwargs) -> bool:
        """
        检查文件或文件夹是否存在
        :param fid: 文件或文件夹ID
        :return: 是否存在
        """
        return "file_id" in self.drive.get_file_details(file_id=fid)

    def get_file_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取指定目录下的文件列表
        :param fid: 目录ID，默认为根目录
        :return: 文件信息列表
        """
        result = []
        for file in self.drive.get_file_list(parent_file_id=fid, type="file")["items"]:
            if file["type"] == "file":
                result.append(
                    DriveFile(
                        fid=file["file_id"],
                        name=file["name"],
                        size=file["size"],
                        ext=file,
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
        for file in self.drive.get_file_list(parent_file_id=fid, type="folder")[
            "items"
        ]:
            result.append(
                DriveFile(
                    fid=file["file_id"], name=file["name"], size=file["size"], ext=file
                )
            )
        return result

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.get_file_details(file_id=fid)
        return DriveFile(
            fid=res["file_id"], name=res["name"], size=res["size"], ext=res
        )

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.get_file_details(file_id=fid)
        return DriveFile(
            fid=res["file_id"], name=res["name"], size=res["size"], ext=res
        )

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
        self.drive.download_file(file_id=fid, filepath=save_path)
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
            filepath=filedir,
            file_id=fid,
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

        self.drive.create_share(
            [fid for fid in fids], share_pwd=password, expiration=expiration
        )
