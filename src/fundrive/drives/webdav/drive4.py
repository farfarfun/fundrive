import os.path
from typing import Any

from farlog import getLogger
from funsecret import read_secret
from webdav4.client import Client

from fundrive.core import BaseDrive, DriveFile, ensure_parent_dir
from fundrive.core.exceptions import InvalidParameterError

logger = getLogger("fundrive")


class WebDavDrive4(BaseDrive):
    """基于 webdav4 的 WebDAV 网盘驱动。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """初始化 WebDAV 驱动。"""
        super().__init__(*args, **kwargs)
        self.drive = None

    def login(
        self,
        server_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """使用服务器地址、用户名和密码登录。"""
        server_url = server_url or read_secret("fundrive", "webdav", "server_url")
        username = username or read_secret("fundrive", "webdav", "username")
        password = password or read_secret("fundrive", "webdav", "password")
        if not server_url or not username or not password:
            raise InvalidParameterError(
                "server_url、username、password 均不能为空",
                parameter="server_url/username/password",
            )

        self.drive = Client(server_url, auth=(username, password))
        return True

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """在远程目录中创建子目录并返回其路径。"""
        dir_map = {file.name: file.fid for file in self.get_dir_list(fid=fid)}
        if name in dir_map:
            logger.info(f"name={name} exists, return fid={fid}")
            return dir_map[name]
        path = str(os.path.join(fid, name))
        self.drive.mkdir(path=path)
        return path

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """删除远程文件或目录。"""
        self.drive.remove(path=fid)
        return True

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """检查远程路径是否存在。"""
        return self.drive.exists(fid)

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        """返回目录中的文件列表。"""
        result = []
        for file in self.drive.ls(path=fid):
            if file["type"] == "file":
                result.append(
                    DriveFile(
                        fid=file["name"],
                        name=os.path.basename(file["name"]),
                        size=file["content_length"],
                    )
                )

        return result

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        """返回目录中的子目录列表。"""
        result = []
        for file in self.drive.ls(path=fid):
            if file["type"] == "directory":
                result.append(
                    DriveFile(
                        fid=file["name"],
                        name=os.path.basename(file["name"]),
                        size=file["content_length"],
                    )
                )

        return result

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """返回远程文件信息。"""
        res = self.drive.info(fid)
        return DriveFile(
            fid=res["name"],
            name=os.path.basename(res["name"]),
            size=res["content_length"],
        )

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """返回远程目录信息。"""
        res = self.drive.info(fid)
        return DriveFile(
            fid=res["name"],
            name=os.path.basename(res["name"]),
            size=res["content_length"],
        )

    def download_file(
        self,
        fid: str,
        save_dir: str | None = None,
        filename: str | None = None,
        filepath: str | None = None,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载单个文件

        Args:
            fid: 文件ID（远程路径）
            save_dir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 下载是否成功
        """
        # 确定保存路径
        if filepath:
            local_path = filepath
        elif save_dir and filename:
            local_path = os.path.join(save_dir, filename)
        elif save_dir:
            local_path = os.path.join(save_dir, os.path.basename(fid))
        else:
            local_path = os.path.basename(fid)

        # 确保目录存在
        ensure_parent_dir(local_path)

        # 检查文件是否已存在
        if os.path.exists(local_path) and not overwrite:
            return False

        # 检查远程文件是否存在
        if not self.exist(fid):
            return False

        # 执行下载
        self.drive.download_file(from_path=fid, to_path=local_path)
        return True

    def upload_file(
        self,
        filepath: str,
        fid: str,
        recursion: bool = True,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """将本地文件上传到远程目录。"""
        if self.exist(fid) and not overwrite:
            logger.warning(f"File {fid} already exists, skipping upload")
            return False
        logger.info(f"Uploading {filepath} to {fid}")
        self.drive.upload_file(
            from_path=filepath,
            to_path=os.path.join(fid, os.path.basename(filepath)),
            overwrite=overwrite,
        )
        return True
