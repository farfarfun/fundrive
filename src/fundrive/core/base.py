import os
from typing import List, Optional


class DriveFile(dict):
    def __init__(self, fid, name, ext=None, *args, **kwargs):
        kwargs.update({"fid": fid, "name": name, "ext": ext})
        super().__init__(*args, **kwargs)
        self.fid = fid
        self.name = name
        self.ext = ext
        self.data = {"fid": fid, "name": name}

    @property
    def size(self):
        return len(self.data)


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
        pass

    def login(self, *args, **kwargs) -> bool:
        """
        登录
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        """
        创建目录，如果目录存在则返回目录id
        :param return_if_exist:
        :param fid:
        :param name:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def exist(self, fid, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def delete(self, fid, *args, **kwargs) -> bool:
        """
        删除
        :param fid:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_file_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        """
        获取文件列表
        :param fid:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_dir_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        """
        获取目录列表
        :param fid:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        """
        获取文件信息
        :param fid:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        """
        获取目录信息
        :param fid:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def download_file(
        self,
        fid,
        local_dir,
        filedir=None,
        filename=None,
        filepath=None,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载文件
        :param fid:
        :param local_dir:
        :param overwrite:
        :param filename:
        :param filepath:
        :param filedir:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def download_dir(
        self,
        fid,
        local_dir,
        recursion=True,
        overwrite=False,
        ignore_filter=None,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载目录
        :param fid:
        :param local_dir:
        :param recursion:
        :param overwrite:
        :param args:
        :param kwargs:
        :param ignore_filter
        :return:
        """
        if not self.exist(fid):
            return False
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
        for file in self.get_file_list(fid):
            if ignore_filter and ignore_filter(file.name):
                continue
            _drive_path = file.fid
            self.download_file(
                fid=file.fid,
                local_dir=local_dir,
                filedir=local_dir,
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
                local_dir=os.path.join(local_dir, os.path.basename(file.name)),
                overwrite=overwrite,
                recursion=recursion,
                ignore_filter=ignore_filter,
                *args,
                **kwargs,
            )

    def upload_file(
        self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        上传文件
        :param local_path:
        :param fid:
        :param recursion:
            :param overwrite:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def upload_dir(
        self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        上传目录
        :param local_path:
        :param fid:
         :param recursion:
        :param overwrite:
        :param args:
        :param kwargs:
        :return:
        """
        dir_map = dict([(file.name, file.fid) for file in self.get_dir_list(fid=fid)])
        for file in os.listdir(local_path):
            filepath = os.path.join(local_path, file)
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

    def share(self, *fids: str, password: str, expire_days: int = 0, description=""):
        raise NotImplementedError()

    def save_shared(self, shared_url: str, fid: str, password: Optional[str] = None):
        """
        保存共享链接
        :param shared_url:
        :param fid:
        :param password:
        :return:
        """
        raise NotImplementedError()
