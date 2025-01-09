import os
from typing import Any, Callable, List, Optional


class DriveFile(dict):
    """
    网盘文件/目录信息类
    继承自dict，作为文件/目录属性的容器，支持字典式的属性访问
    基础属性包括：
        - fid: 文件/目录ID
        - name: 文件/目录名称
        - size: 文件大小(字节)
        - ext: 扩展信息字典
    """

    def __init__(
        self,
        fid: str,
        name: str,
        size: Optional[int] = None,
        ext: Optional[dict] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        初始化文件信息
        :param fid: 文件/目录ID
        :param name: 文件/目录名称
        :param size: 文件大小(字节)
        :param ext: 扩展信息字典
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        # 构建基础属性字典
        base_dict = {
            "fid": fid,
            "name": name,
            "size": size,
        }

        # 合并扩展信息
        if ext:
            base_dict.update(ext)

        # 合并其他关键字参数
        base_dict.update(kwargs)

        # 调用父类初始化
        super().__init__(base_dict)

    @property
    def fid(self) -> str:
        """文件/目录ID"""
        return self["fid"]

    @property
    def name(self) -> str:
        """文件/目录名称"""
        return self["name"]

    @property
    def size(self) -> Optional[int]:
        """文件大小(字节)"""
        return self.get("size")

    @property
    def ext(self) -> dict:
        """
        扩展信息字典
        排除基础属性后的其他所有属性
        """
        return {k: v for k, v in self.items() if k not in {"fid", "name", "size"}}

    @property
    def filename(self) -> str:
        """
        获取文件名（不含路径）
        :return: 文件名
        """
        return os.path.basename(self.name)

    def __repr__(self) -> str:
        """
        字符串表示
        :return: 文件信息的字符串表示
        """
        return f"DriveFile(fid='{self.fid}', name='{self.name}', size={self.size})"


def get_filepath(
    filedir: str = None,
    filename: str = None,
    filepath: str = None,
) -> str:
    if filepath is not None:
        return filepath
    elif filedir is not None and filename is not None:
        return os.path.join(filedir, filename)


class BaseDrive:
    def __init__(self, *args, **kwargs):
        """
        初始化网盘基类
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        pass

    def login(self, *args: Any, **kwargs: Any) -> bool:
        """
        登录网盘
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 登录是否成功
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在
        :param fid: 文件或目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 是否存在
        """
        raise NotImplementedError()

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录
        :param fid: 文件或目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 删除是否成功
        """
        raise NotImplementedError()

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的文件列表
        :param fid: 目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 文件列表
        """
        raise NotImplementedError()

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的子目录列表
        :param fid: 目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 子目录列表
        """
        raise NotImplementedError()

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """
        获取文件详细信息
        :param fid: 文件ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 文件信息对象
        """
        raise NotImplementedError()

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """
        获取目录详细信息
        :param fid: 目录ID
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 目录信息对象
        """
        raise NotImplementedError()

    def download_file(
        self,
        fid: str,
        local_dir: str,
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
        :param local_dir: 本地保存目录
        :param filedir: 文件保存目录
        :param filename: 文件名
        :param filepath: 完整的文件保存路径
        :param overwrite: 是否覆盖已存在的文件
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 下载是否成功
        """
        raise NotImplementedError()

    def download_dir(
        self,
        fid: str,
        filedir: str,
        recursion: bool = True,
        overwrite: bool = False,
        ignore_filter: Optional[Callable[[str], bool]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        下载目录
        :param fid: 目录ID
        :param filedir: 本地保存目录
        :param recursion: 是否递归下载子目录
        :param overwrite: 是否覆盖已存在的文件
        :param ignore_filter: 忽略文件的过滤函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 下载是否成功
        """
        if not self.exist(fid):
            return False
        if not os.path.exists(filedir):
            os.makedirs(filedir, exist_ok=True)
        for file in self.get_file_list(fid):
            if ignore_filter and ignore_filter(file.name):
                continue
            _drive_path = file.fid
            self.download_file(
                fid=file.fid,
                filedir=filedir,
                filename=os.path.basename(file.name),
                overwrite=overwrite,
                *args,
                **kwargs,
            )
        if not recursion:
            return True

        for file in self.get_dir_list(fid):
            self.download_dir(
                fid=file.fid,
                filedir=os.path.join(filedir, os.path.basename(file.name)),
                overwrite=overwrite,
                recursion=recursion,
                ignore_filter=ignore_filter,
                *args,
                **kwargs,
            )

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
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 上传是否成功
        """
        raise NotImplementedError()

    def upload_dir(
        self,
        filedir: str,
        fid: str,
        recursion: bool = True,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传目录
        :param filedir: 本地目录路径
        :param fid: 目标目录ID
        :param recursion: 是否递归上传子目录
        :param overwrite: 是否覆盖已存在的文件
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 上传是否成功
        """
        dir_map = dict([(file.name, file.fid) for file in self.get_dir_list(fid=fid)])
        for file in os.listdir(filedir):
            filepath = os.path.join(filedir, file)
            if os.path.isfile(filepath):
                self.upload_file(filepath, fid)
            elif os.path.isdir(filepath):
                if file not in dir_map:
                    dir_map[file] = self.mkdir(fid, file)
                self.upload_dir(
                    filepath,
                    dir_map[file],
                    recursion=recursion,
                    overwrite=overwrite,
                    *args,
                    **kwargs,
                )
        return True

    def share(
        self,
        *fids: str,
        password: str,
        expire_days: int = 0,
        description: str = "",
    ) -> Any:
        """
        分享文件或目录
        :param fids: 要分享的文件或目录ID列表
        :param password: 分享密码
        :param expire_days: 分享链接有效期（天），0表示永久有效
        :param description: 分享描述
        :return: 分享链接信息
        """
        raise NotImplementedError()

    def save_shared(
        self,
        shared_url: str,
        fid: str,
        password: Optional[str] = None,
    ) -> bool:
        """
        保存他人的分享内容到自己的网盘
        :param shared_url: 分享链接
        :param fid: 保存到的目标目录ID
        :param password: 分享密码
        :return: 保存是否成功
        """
        raise NotImplementedError()
