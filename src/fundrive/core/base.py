import os
from abc import abstractmethod
from pathlib import Path
from typing import Any, Callable, List, Optional, Dict, TypeVar, Generic

T = TypeVar("T")


class DriveFile(dict, Generic[T]):
    """
    网盘文件/目录信息类
    继承自dict，作为文件/目录属性的容器，支持字典式的属性访问
    基础属性包括：
        - fid: 文件/目录ID
        - name: 文件/目录名称
        - size: 文件大小(字节)
        - ext: 扩展信息字典

    Args:
        fid (str): 文件/目录ID
        name (str): 文件/目录名称
        size (Optional[int], optional): 文件大小(字节). Defaults to None.
        ext (Optional[dict], optional): 扩展信息字典. Defaults to None.
    """

    def __init__(
        self,
        fid: str,
        name: str,
        size: Optional[int] = None,
        ext: Optional[Dict[str, Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        初始化文件信息

        Args:
            fid (str): 文件/目录ID
            name (str): 文件/目录名称
            size (Optional[int], optional): 文件大小(字节). Defaults to None.
            ext (Optional[Dict[str, Any]], optional): 扩展信息字典. Defaults to None.

        Raises:
            ValueError: 如果fid或name为空
        """
        if not fid or not name:
            raise ValueError("fid and name must not be empty")

        if size is not None and size < 0:
            raise ValueError("size must be non-negative")

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

    def __getitem__(self, key: str) -> Any:
        """支持通过下标访问属性"""
        return super().__getitem__(key)

    def __getattr__(self, name: str) -> Any:
        """支持通过点语法访问属性"""
        return self.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """支持通过点语法设置属性"""
        self[name] = value

    def __delattr__(self, name: str) -> None:
        """支持通过点语法删除属性"""
        if name in self:
            del self[name]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

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
    filedir: Optional[str] = None,
    filename: Optional[str] = None,
    filepath: Optional[str] = None,
) -> str:
    """
    获取文件完整路径

    Args:
        filedir (Optional[str], optional): 文件目录路径. Defaults to None.
        filename (Optional[str], optional): 文件名. Defaults to None.
        filepath (Optional[str], optional): 完整的文件路径. Defaults to None.

    Returns:
        str: 文件的完整路径

    Raises:
        ValueError: 如果参数组合无效
    """
    if filepath:
        return str(Path(filepath).resolve())
    elif filedir and filename:
        return str(Path(filedir).joinpath(filename).resolve())
    else:
        raise ValueError("Either filepath or (filedir and filename) must be provided")


class BaseDrive:
    """
    网盘操作基类

    提供网盘操作的基本接口定义
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        初始化网盘基类

        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        self._is_logged_in = False
        self._root_fid = None
        super().__init__(*args, **kwargs)

    @property
    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self._is_logged_in

    @property
    def root_fid(self) -> Optional[str]:
        """根目录ID"""
        return self._root_fid

    def login(self, *args: Any, **kwargs: Any) -> bool:
        """
        登录网盘

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 登录是否成功

        Raises:
            NotImplementedError: 子类必须实现此方法
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

        Args:
            fid (str): 父目录ID
            name (str): 目录名称
            return_if_exist (bool, optional): 如果目录已存在，是否返回已存在目录的ID. Defaults to True.
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 创建的目录ID

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

    @abstractmethod
    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid (str): 文件或目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 是否存在

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录

        Args:
            fid (str): 文件或目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 删除是否成功

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的文件列表

        Args:
            fid (str): 目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 文件列表

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的子目录列表

        Args:
            fid (str): 目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 子目录列表

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """
        获取文件详细信息

        Args:
            fid (str): 文件ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            DriveFile: 文件信息对象

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile:
        """
        获取目录详细信息

        Args:
            fid (str): 目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            DriveFile: 目录信息对象

        Raises:
            ValueError: 如果fid为空
            NotImplementedError: 子类必须实现此方法
        """
        if not fid:
            raise ValueError("fid must not be empty")
        raise NotImplementedError()

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
        下载单个文件

        Args:
            fid: 文件ID
            filedir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 下载是否成功
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
        return True

    def upload_file(
        self,
        filedir: str,
        fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传单个文件

        Args:
            filedir: 本地文件路径
            fid: 目标目录ID
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 上传是否成功
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

        Args:
            fids: 要分享的文件或目录ID列表
            password: 分享密码
            expire_days: 分享链接有效期(天),0表示永久有效
            description: 分享描述

        Returns:
            Any: 分享链接信息
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

        Args:
            shared_url: 分享链接
            fid: 保存到的目标目录ID
            password: 分享密码

        Returns:
            bool: 保存是否成功
        """
        raise NotImplementedError()

    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        """
        搜索文件或目录

        Args:
            keyword: 搜索关键词
            fid: 搜索的起始目录ID,默认从根目录开始
            file_type: 文件类型筛选,如'doc','video','image'等
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            List[DriveFile]: 符合条件的文件列表
        """
        raise NotImplementedError()

    def move(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        移动文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 移动是否成功
        """
        raise NotImplementedError()

    def copy(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        复制文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 复制是否成功
        """
        raise NotImplementedError()

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        """
        重命名文件或目录

        Args:
            fid: 文件/目录ID
            new_name: 新名称
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 重命名是否成功
        """
        raise NotImplementedError()

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """
        获取网盘空间使用情况
        Args:
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            dict: 包含总空间、已用空间等信息的字典
        """
        raise NotImplementedError()

    def get_recycle_list(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        """
        获取回收站文件列表

        Args:
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            List[DriveFile]: 回收站中的文件列表
        """
        raise NotImplementedError()

    def restore(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        从回收站恢复文件

        Args:
            fid: 文件ID
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 恢复是否成功
        """
        raise NotImplementedError()

    def clear_recycle(self, *args: Any, **kwargs: Any) -> bool:
        """
        清空回收站

        Args:
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            bool: 清空是否成功
        """
        raise NotImplementedError()

    def get_download_url(
        self,
        fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        获取文件下载链接

        Args:
            fid: 文件ID
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            str: 下载链接
        """
        raise NotImplementedError()

    def get_upload_url(
        self,
        fid: str,
        filename: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        获取文件上传链接

        Args:
            fid: 目标目录ID
            filename: 文件名
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            str: 上传链接
        """
        raise NotImplementedError()
