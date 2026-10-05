"""
蓝奏云网盘API封装
"""

import os
from typing import Any

from fundrives.lanzou import LanZouCloud
from fundrives.lanzou.utils import convert_file_size_to_int
from farlog import getLogger
from funsecret import read_secret
from tqdm import tqdm

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class Task:
    """
    蓝奏云下载任务类

    Args:
        url: 分享链接
        pwd: 提取密码
        path: 保存路径
        now_size: 当前下载大小
        folder_id: 文件夹ID
    """

    def __init__(self, url, pwd="", path="./download", now_size=0, folder_id=-1):
        """
        初始化下载/上传任务

        Args:
            url (str): 分享链接
            pwd (str): 提取密码，无密码时传空串
            path (str): 本地保存路径（下载）或待上传文件路径（上传）
            now_size (int): 已完成字节数
            folder_id (int): 目标文件夹ID，-1 表示根目录
        """
        self.url = url
        self.pwd = pwd
        self.path = path
        self.now_size = now_size
        self.folder_id = folder_id


class ProgressWrap:
    """
    下载进度条包装类
    """

    def __init__(self, callback: tqdm = None):
        """
        初始化进度条包装

        Args:
            callback (tqdm, optional): 外部传入的 tqdm 进度条；为 None 时在
                :meth:`init` 中自动创建。
        """
        self.callback = callback
        self.last_size = 0

    def init(self, file_name, total_size):
        """
        按文件名与总大小初始化进度条（已有进度条时不重复创建）

        Args:
            file_name (str): 进度条显示的文件名
            total_size (int): 文件总字节数

        Returns:
            None
        """
        if self.callback is None:
            self.callback = tqdm(
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=file_name,
                total=total_size,
            )

    def update(self, now_size):
        """
        把累计完成字节数刷新到进度条

        Args:
            now_size (int): 当前累计完成的字节数

        Returns:
            None
        """
        self.callback.update(now_size - self.last_size)
        self.last_size = now_size


class LanZouDrive(BaseDrive):
    """
    蓝奏云网盘操作类
    """

    def __init__(self, *args, **kwargs):
        """初始化蓝奏云网盘"""
        super().__init__(*args, **kwargs)
        self.allow_big_file = False
        self.drive = None

    def ignore_limit(self):
        """忽略大文件限制"""
        self.allow_big_file = True

    def instance(self):
        """
        惰性创建底层 ``LanZouCloud`` 客户端（已创建则直接返回）

        Returns:
            None
        """
        if self.drive is not None:
            return
        self.drive = LanZouCloud()

    def login(
        self, cookie=None, ylogin=None, phpdisk_info=None, *args, **kwargs
    ) -> bool:
        """
        使用 Cookie 登录蓝奏云

        Args:
            cookie (dict, optional): 完整 Cookie 字典；传入后忽略下面两个参数
            ylogin (str, optional): Cookie 中的 ``ylogin`` 字段，缺省时从 funsecret
                的 ``fundrive/drives/funlanzou/ylogin`` 读取
            phpdisk_info (str, optional): Cookie 中的 ``phpdisk_info`` 字段，缺省时从
                funsecret 的 ``fundrive/drives/funlanzou/phpdisk_info`` 读取
            *args: 兼容 BaseDrive 契约的可变位置参数
            **kwargs: 兼容 BaseDrive 契约的可变关键字参数

        Returns:
            bool: 登录是否成功
        """
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
        """
        把 ``path`` 解析成 (文件ID, 分享链接, 提取密码) 三元组

        Args:
            path (str | int): 文件/目录ID，或 ``"分享链接,提取密码"`` 形式的字符串

        Returns:
            tuple[Any, str | None, str | None]: ``(fid, url, pwd)``；传入ID时后两项
            为 ``None``，传入分享链接时第一项为 ``None``
        """
        fid = None
        url = None
        pwd = None
        if isinstance(path, int) or "," not in path:
            fid = path
        else:
            url, pwd = path.split(",")
        return fid, url, pwd

    def exist(self, fid: str, *args, **kwargs) -> bool:
        """
        判断文件/目录是否存在

        蓝奏云官方接口没有提供"按ID判断是否存在"的查询，这里按 BaseDrive 契约恒返回
        ``True``，真实的存在性由后续具体操作（下载/删除等）的返回值体现。

        Args:
            fid (str): 文件/目录ID
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 恒为 ``True``
        """
        return True

    def mkdir(
        self,
        fid,
        name,
        return_if_exist: bool = True,
        *args,
        url=None,
        pwd=None,
        **kwargs,
    ) -> str:
        """
        在指定目录下创建子目录

        按 ``BaseDrive`` 契约返回**新目录的ID**（不是布尔值）：
        ``BaseDrive.upload_dir`` 与 ``fundrive.core.copy_data`` 都会把返回值直接当成
        下一层的 ``fid`` 使用。蓝奏云同名目录已存在时底层接口直接返回已有目录ID。

        Args:
            fid (int | str): 父目录ID，``-1`` 表示根目录
            name (str): 新目录名（蓝奏云会把空格替换成下划线并过滤非法字符）
            return_if_exist (bool): 同名目录已存在时返回其ID，蓝奏云接口本身即如此
            *args: 可变位置参数
            url (str, optional): 预留的分享链接参数，蓝奏云建目录不使用
            pwd (str, optional): 预留的提取密码参数，蓝奏云建目录不使用
            **kwargs: 可变关键字参数

        Returns:
            str: 新目录（或已存在的同名目录）的ID；创建失败返回空字符串
        """
        folder_id = self.drive.mkdir(fid, name, *args, **kwargs)
        if folder_id == LanZouCloud.MKDIR_ERROR:
            logger.error("蓝奏云创建目录失败，parent_fid={} name={}", fid, name)
            return ""
        return str(folder_id)

    def delete(self, fid=None, *args, **kwargs) -> bool:
        """
        删除文件或目录

        Args:
            fid (int | str, optional): 待删除的文件/目录ID
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 删除是否成功
        """
        return self.drive.delete(fid, *args, **kwargs) == 0

    def get_dir_list(self, fid, url=None, pwd=None, *args, **kwargs) -> list[DriveFile]:
        """
        获取指定目录下的子目录列表

        Args:
            fid (int | str): 目录ID
            url (str, optional): 预留的分享链接参数，当前实现只按 ``fid`` 查询
            pwd (str, optional): 预留的提取密码参数
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 子目录信息列表，目录不存在或为空时返回空列表
        """
        result = []
        for item in self.drive.get_dir_list(folder_id=fid)[0]:
            result.append(DriveFile(fid=item.id, name=item.name, desc=item.desc))
        return result

    def get_file_list(
        self, fid, url=None, pwd=None, *args, **kwargs
    ) -> list[DriveFile]:
        """
        获取文件列表，支持按目录ID查询和按分享链接查询

        Args:
            fid (int | str, optional): 目录ID；为 ``None`` 时跳过目录查询
            url (str, optional): 文件夹分享链接；给出时追加该分享内的文件
            pwd (str, optional): 分享链接的提取密码
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 文件信息列表；``fid`` 与 ``url`` 都为 ``None`` 时返回空列表
        """
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

    def get_file_info(
        self, fid, url=None, pwd=None, *args, **kwargs
    ) -> DriveFile[Any] | None:
        """
        获取单个文件的详细信息

        Args:
            fid (int | str, optional): 文件ID，优先按ID查询
            url (str, optional): 文件分享链接，``fid`` 查不到时回退到该链接
            pwd (str, optional): 分享链接的提取密码
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            DriveFile | None: 文件信息；两种方式都查不到时返回 ``None``
        """
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
        return None

    def get_dir_info(
        self, fid, url=None, pwd=None, *args, **kwargs
    ) -> DriveFile | None:
        """
        获取单个目录的详细信息

        Args:
            fid (int | str, optional): 目录ID，优先按ID查询
            url (str, optional): 文件夹分享链接，``fid`` 查不到时回退到该链接
            pwd (str, optional): 分享链接的提取密码
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            DriveFile | None: 目录信息；两种方式都查不到时返回 ``None``
        """
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
        return None

    def download_file(
        self,
        fid: str,
        save_dir: str | None = None,
        filename: str | None = None,
        filepath: str | None = None,
        overwrite: bool = False,
        *args,
        url: str | None = None,
        pwd: str | None = None,
        **kwargs,
    ) -> bool:
        """
        下载单个文件

        Args:
            fid: 文件ID；为 ``None`` 时必须给出 ``url``
            save_dir: 文件保存目录，缺省为当前目录
            filename: 文件名（蓝奏云直链自带文件名，此处仅为满足 BaseDrive 契约）
            filepath: 完整的文件保存路径，给出时其所在目录作为保存目录
            overwrite: 是否覆盖已存在的文件
            url: 文件分享链接，没有文件ID时按链接下载
            pwd: 分享链接的提取密码

        Returns:
            bool: 下载是否成功
        """
        file_info = self.get_file_info(fid=fid, url=url, pwd=pwd)
        if file_info is None:
            logger.error("蓝奏云下载失败：未找到文件 fid={} url={}", fid, url)
            return False
        save_directory = (
            save_dir or (os.path.dirname(filepath) if filepath else None) or "."
        )
        task = Task(url=file_info["url"], pwd=file_info["pwd"], path=save_directory)
        os.makedirs(save_directory, exist_ok=True)
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

    def upload_file(
        self,
        filepath: str,
        fid: str,
        url=None,
        pwd=None,
        recursion=True,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        """
        上传单个文件到指定目录

        大于蓝奏云单文件限制的文件需要先调用 :meth:`ignore_limit` 开启分卷上传。

        Args:
            filepath (str): 本地文件路径
            fid (int | str): 目标目录ID
            url (str, optional): 预留的分享链接参数
            pwd (str, optional): 预留的提取密码参数
            recursion (bool): 兼容 BaseDrive 契约的递归标记，单文件上传不使用
            overwrite (bool): 兼容 BaseDrive 契约的覆盖标记，蓝奏云不支持同名覆盖
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 上传是否成功
        """
        task = Task(url=url, pwd=pwd, path=filepath, folder_id=fid)
        wrap = ProgressWrap()
        wrap.init(os.path.basename(filepath), os.stat(filepath).st_size)

        def clb():
            wrap.update(task.now_size)

        return (
            self.drive.upload_file(
                task=task,
                file_path=filepath,
                folder_id=fid,
                callback=clb,
                allow_big_file=self.allow_big_file,
            )[0]
            == 0
        )

    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """移动文件到目标目录（BaseDrive 契约）。"""
        return self.move_file(source_fid, target_fid)

    def move_file(self, file_id, folder_id) -> bool:
        """
        把文件移动到目标目录

        Args:
            file_id (int | str): 待移动的文件ID
            folder_id (int | str): 目标目录ID

        Returns:
            bool: 移动是否成功（底层接口返回码 0 表示成功）
        """
        return self.drive.move_file(file_id, folder_id) == 0
